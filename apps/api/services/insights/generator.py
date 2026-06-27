import os
import json
import httpx
import uuid
from datetime import datetime
from typing import List, Dict, Any
from db.session_store import SessionLocal, DBLLMLog
from services.insights.templates import generate_templated_insights

class InsightsGenerator:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"

    def generate_insights(self, summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generates financial insights based on the calculated metrics summary.
        If GROQ_API_KEY is present, it uses the Groq API to polish and rewrite the insights.
        Otherwise, returns the templated insights directly.
        """
        # 1. Generate default templated insights
        templated_insights = generate_templated_insights(summary)
        
        # 2. If API Key is missing, return templates directly
        if not self.api_key:
            print("Info: GROQ_API_KEY is not set. Returning templated insights directly.")
            return templated_insights[:5]  # Limit to top 5

        # 3. Call Groq LLM to polish titles and descriptions
        try:
            # Prepare instructions
            system_prompt = (
                "You are an empathetic, expert personal finance advisor.\n"
                "You are given a list of raw, templated financial insights generated from a bank statement.\n"
                "Your task is to rewrite the 'title' and 'text' of each insight to make them more professional, actionable, and engaging.\n\n"
                "Rules:\n"
                "1. Keep all exact numbers, currencies (₹), dates, and categories. DO NOT change them.\n"
                "2. Maintain the same 'id', 'type', 'amount', and 'relevance' values for each insight.\n"
                "3. Ensure the output is a valid JSON object matching this structure exactly:\n"
                "{\n"
                "  \"insights\": [\n"
                "     {\"id\": \"...\", \"type\": \"...\", \"title\": \"Polished Title\", \"text\": \"Polished text...\", \"amount\": ..., \"relevance\": ...}\n"
                "  ]\n"
                "}\n"
                "4. Do not output any chat meta-text, markdown tags, or explanations. Return only the JSON object."
            )

            user_prompt = f"Polish these templated financial insights:\n{json.dumps(templated_insights)}"

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
                "temperature": 0.3
            }

            # Call API with 8-second timeout to prevent stalling response
            with httpx.Client(timeout=8.0) as client:
                response = client.post(self.api_url, headers=headers, json=payload)
                response.raise_for_status()
                res_data = response.json()

            content = res_data["choices"][0]["message"]["content"]
            result = json.loads(content)
            
            polished_insights = result.get("insights", [])

            # Log LLM token usage
            try:
                usage = res_data.get("usage", {})
                tokens_used = usage.get("total_tokens", 250)
                
                with SessionLocal() as db:
                    log_entry = DBLLMLog(
                        id=str(uuid.uuid4()),
                        timestamp=datetime.utcnow(),
                        model=self.model,
                        tokens_used=tokens_used
                    )
                    db.add(log_entry)
                    db.commit()
            except Exception as log_err:
                print(f"Warning: Failed to log insight LLM usage: {str(log_err)}")

            # Merge polished titles/texts back (matching by ID)
            # This ensures we don't lose any insights or break the structure
            reconstructed = []
            for raw in templated_insights:
                matched = next((p for p in polished_insights if p.get("id") == raw["id"]), None)
                if matched:
                    reconstructed.append({
                        "id": raw["id"],
                        "type": raw["type"],
                        "title": matched.get("title", raw["title"]),
                        "text": matched.get("text", raw["text"]),
                        "amount": raw["amount"],
                        "relevance": raw["relevance"]
                    })
                else:
                    reconstructed.append(raw)
            
            return reconstructed[:5]  # Limit to top 5 ranked insights
            
        except Exception as e:
            print(f"Warning: Failed to polish insights with Groq ({str(e)}). Falling back to templated insights.")
            return templated_insights[:5]
