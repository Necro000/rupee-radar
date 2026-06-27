import os
import json
import httpx
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import func
from db.session_store import SessionLocal, DBLLMLog

class LLMCategorizer:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def _check_rate_limits(self, db, estimated_tokens: int):
        # Only enforce if model is llama-3.3-70b-versatile
        if self.model != "llama-3.3-70b-versatile":
            return
            
        now = datetime.utcnow()
        one_minute_ago = now - timedelta(minutes=1)
        one_day_ago = now - timedelta(days=1)
        
        # 1. Minute limits (30 RPM, 1K TPM)
        minute_stats = db.query(
            func.count(DBLLMLog.id),
            func.sum(DBLLMLog.tokens_used)
        ).filter(
            DBLLMLog.model == self.model,
            DBLLMLog.timestamp >= one_minute_ago
        ).first()
        
        minute_requests = minute_stats[0] or 0
        minute_tokens = int(minute_stats[1] or 0)
        
        if minute_requests + 1 > 30:
            raise ValueError(f"Rate limit exceeded: 30 RPM limit reached (Current: {minute_requests}/min)")
            
        if minute_tokens + estimated_tokens > 1000:
            raise ValueError(f"Rate limit exceeded: 1K TPM limit reached (Current: {minute_tokens} tokens/min, Estimate: {estimated_tokens})")
            
        # 2. Daily limits (12K RPD, 100K TPD)
        day_stats = db.query(
            func.count(DBLLMLog.id),
            func.sum(DBLLMLog.tokens_used)
        ).filter(
            DBLLMLog.model == self.model,
            DBLLMLog.timestamp >= one_day_ago
        ).first()
        
        day_requests = day_stats[0] or 0
        day_tokens = int(day_stats[1] or 0)
        
        if day_requests + 1 > 12000:
            raise ValueError(f"Rate limit exceeded: 12K RPD limit reached (Current: {day_requests}/day)")
            
        if day_tokens + estimated_tokens > 100000:
            raise ValueError(f"Rate limit exceeded: 100K TPD limit reached (Current: {day_tokens} tokens/day, Estimate: {estimated_tokens})")


    def categorize_batch(self, transactions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """
        Sends a batch of transactions to the Groq API for categorization.
        Returns a dict mapping transaction ID -> {'category': str, 'confidence': float, 'reasoning': str}
        """
        if not self.api_key:
            print("Warning: GROQ_API_KEY is not set. Falling back to rules/Other categorization.")
            return self._generate_fallbacks(transactions, "Groq API key missing")

        # Estimate tokens (200 base prompt + ~55 tokens per transaction)
        estimated_tokens = 200 + 55 * len(transactions)
        
        try:
            with SessionLocal() as db:
                self._check_rate_limits(db, estimated_tokens)
        except ValueError as limit_err:
            error_msg = str(limit_err)
            print(f"Rate limit block: {error_msg}")
            return self._generate_fallbacks(transactions, error_msg)
        except Exception as db_err:
            print(f"Warning: Failed to check rate limits due to DB error: {str(db_err)}")

        # Select columns to reduce prompt size
        prompt_data = []
        for tx in transactions:
            prompt_data.append({
                "id": tx["id"],
                "description": tx["cleanDescription"],
                "merchant": tx.get("merchant", ""),
                "amount": tx["amount"]
            })

        system_prompt = (
            "You are a personal finance assistant specializing in Indian transaction statement analysis.\n"
            "Your task is to categorize each transaction in the input batch into one of these exact categories:\n"
            "Food, Travel, Shopping, Bills, EMI, Subscriptions, Salary, Rent, Investments, Other.\n\n"
            "Do not output anything except a valid JSON object matching this structure:\n"
            "{\n"
            "  \"categories\": [\n"
            "    {\"id\": \"tx-id\", \"category\": \"Food\", \"confidence\": 0.95, \"reasoning\": \"Swiggy food delivery\"}\n"
            "  ]\n"
            "}\n\n"
            "Ensure that category is exactly one of the ten categories listed. No exceptions."
        )

        user_prompt = f"Categorize these transactions:\n{json.dumps(prompt_data)}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }

        try:
            # Set timeout to 10 seconds to fail fast and prevent blocking pipeline
            with httpx.Client(timeout=10.0) as client:
                response = client.post(self.api_url, headers=headers, json=payload)
                response.raise_for_status()
                res_data = response.json()
                
            content = res_data["choices"][0]["message"]["content"]
            # CAT-22: retry JSON parse once before falling back
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # Strip markdown code fences if present and retry
                stripped = content.strip().strip("```json").strip("```").strip()
                result = json.loads(stripped)  # raises on 2nd failure → caught by outer except

            # Log successful API usage
            try:
                usage = res_data.get("usage", {})
                actual_tokens = usage.get("total_tokens", estimated_tokens)
                
                with SessionLocal() as db:
                    log_entry = DBLLMLog(
                        id=str(uuid.uuid4()),
                        timestamp=datetime.utcnow(),
                        model=self.model,
                        tokens_used=actual_tokens
                    )
                    db.add(log_entry)
                    db.commit()
            except Exception as log_err:
                print(f"Warning: Failed to log LLM usage: {str(log_err)}")
            
            # Map transaction ID to prediction details
            mappings = {}
            for item in result.get("categories", []):
                tx_id = item.get("id")
                category = item.get("category", "Other")
                # Normalize category casing
                category_mapped = self._normalize_category(category)
                
                mappings[tx_id] = {
                    "category": category_mapped,
                    "confidence": float(item.get("confidence", 0.8)),
                    "reasoning": item.get("reasoning", "")
                }
                
            # Verify all input transactions received a mapping. If any are missing, fill fallback
            for tx in transactions:
                if tx["id"] not in mappings:
                    mappings[tx["id"]] = {
                        "category": "Other",
                        "confidence": 0.3,
                        "reasoning": "Missing mapping in LLM output"
                    }
                    
            return mappings
            
        except Exception as e:
            print(f"Error in Groq LLM categorization: {str(e)}")
            return self._generate_fallbacks(transactions, str(e))


    def _normalize_category(self, category: str) -> str:
        """Helper to ensure category strings strictly match the enum casings."""
        mapping = {
            "food": "Food",
            "travel": "Travel",
            "shopping": "Shopping",
            "bills": "Bills",
            "emi": "EMI",
            "subscriptions": "Subscriptions",
            "salary": "Salary",
            "rent": "Rent",
            "investments": "Investments",
            "other": "Other"
        }
        return mapping.get(category.strip().lower(), "Other")

    def _generate_fallbacks(self, transactions: List[Dict[str, Any]], error_msg: str) -> Dict[str, Dict[str, Any]]:
        """Generates fallback 'Other' categories for the batch in case of failures."""
        fallbacks = {}
        for tx in transactions:
            fallbacks[tx["id"]] = {
                "category": "Other",
                "confidence": 0.3,
                "reasoning": f"LLM Fallback: {error_msg}"
            }
        return fallbacks
