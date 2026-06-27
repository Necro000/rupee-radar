import re
import uuid
from datetime import datetime
from typing import List, Dict, Any

class RecurringDetector:
    def __init__(self):
        pass

    def _normalize_string(self, s: str) -> str:
        if not s:
            return ""
        s = s.lower().strip()
        # Remove numbers, special characters, retain only letters and spaces
        s = re.sub(r'[^a-z\s]', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    def detect_and_tag(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Groups debit transactions, checks amount variance and intervals,
        classifies recurring type/frequency, and tags transactions.
        """
        # Filter debits (expenses)
        debits = [tx for tx in transactions if tx.get("type") == "debit"]
        
        # Group by merchant (or clean description if merchant is empty or generic)
        groups = {}
        for tx in debits:
            merchant = tx.get("merchant") or ""
            desc = tx.get("cleanDescription") or ""
            
            merchant_norm = self._normalize_string(merchant)
            if merchant_norm and merchant_norm != "other":
                group_key = f"m:{merchant_norm}"
            else:
                desc_norm = self._normalize_string(desc)
                group_key = f"d:{desc_norm}"
                
            if group_key not in groups:
                groups[group_key] = []
            groups[group_key].append(tx)
            
        # Analyze each group for recurrence pattern
        for key, tx_list in groups.items():
            if len(tx_list) < 2:
                continue
                
            # Sort chronologically by date
            tx_list = sorted(tx_list, key=lambda x: x["date"])
            
            # Check amount variance (within ±5% of group average)
            amounts = [abs(tx["amount"]) for tx in tx_list]
            avg_amount = sum(amounts) / len(amounts)
            if avg_amount == 0:
                continue
                
            max_amount = max(amounts)
            min_amount = min(amounts)
            
            # Check if variance is <= 5%
            if (max_amount - min_amount) / avg_amount > 0.05:
                continue
                
            # Calculate days differences between consecutive occurrences
            intervals = []
            try:
                for i in range(1, len(tx_list)):
                    d1 = datetime.strptime(tx_list[i-1]["date"], "%Y-%m-%d")
                    d2 = datetime.strptime(tx_list[i]["date"], "%Y-%m-%d")
                    intervals.append((d2 - d1).days)
            except Exception as e:
                print(f"Warning: Failed to parse dates for interval check: {str(e)}")
                continue
                
            if not intervals:
                continue
                
            avg_interval = sum(intervals) / len(intervals)
            
            # Classify frequency based on average interval
            frequency = None
            if 5 <= avg_interval <= 9:
                frequency = "weekly"
            elif 27 <= avg_interval <= 33:
                frequency = "monthly"
            elif 80 <= avg_interval <= 100:
                frequency = "quarterly"
            elif 350 <= avg_interval <= 380:
                frequency = "yearly"
                
            if not frequency:
                continue
                
            # Classify recurring type based on keywords
            merchant_name = tx_list[0].get("merchant") or ""
            desc_text = tx_list[0].get("cleanDescription") or ""
            combined_text = f"{merchant_name} {desc_text}".lower()
            
            rec_type = "other"
            if any(k in combined_text for k in ["netflix", "spotify", "amazon prime", "youtube", "premium", "google", "apple", "zoom", "github", "subscription", "sub"]):
                rec_type = "subscription"
            elif any(k in combined_text for k in ["loan", "emi", "bajaj", "finance", "nach", "credit card emi"]):
                rec_type = "emi"
            elif any(k in combined_text for k in ["rent", "house rent", "pg rent"]):
                rec_type = "rent"
            elif any(k in combined_text for k in ["mutual fund", "sip", "zerodha", "groww", "investment", "wealth"]):
                rec_type = "sip"
            elif any(k in combined_text for k in ["insurance", "lic", "ergo", "max life", "premium"]):
                rec_type = "insurance"
                
            # Generate recurringGroupId
            group_id = str(uuid.uuid4())
            
            # Tag all transactions in this group
            for tx in tx_list:
                tx["isRecurring"] = True
                tx["recurringGroupId"] = group_id
                
                if "metadata" not in tx or tx["metadata"] is None:
                    tx["metadata"] = {}
                    
                tx["metadata"]["recurring"] = {
                    "frequency": frequency,
                    "type": rec_type,
                    "avgAmount": round(avg_amount, 2)
                }
                
        return transactions
