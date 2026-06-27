import json
from typing import List, Dict, Any, Union

class MetricsCalculator:
    def __init__(self):
        pass

    def _get_val(self, tx: Any, field: str) -> Any:
        """Helper to access fields from either SQLAlchemy models or dicts."""
        if isinstance(tx, dict):
            return tx.get(field)
        return getattr(tx, field, None)

    def calculate_metrics(self, transactions: List[Any]) -> Dict[str, Any]:
        """
        Calculates personal finance metrics from a list of transactions.
        Handles both dictionary formats and DBTransaction objects.
        """
        income = 0.0
        spend = 0.0
        biggest_tx = None
        biggest_tx_amt = 0.0
        
        category_spends = {}
        monthly_data = {}
        
        # Track unique recurring groups to calculate monthly recurring total
        recurring_groups = {}  # recurring_group_id -> {amount, frequency}

        for tx in transactions:
            # Check if this transaction is an internal transfer
            metadata = self._get_val(tx, "metadata_json") or self._get_val(tx, "metadata")
            is_internal = False
            if metadata:
                if isinstance(metadata, str):
                    try:
                        meta_dict = json.loads(metadata)
                    except Exception:
                        meta_dict = {}
                else:
                    meta_dict = metadata
                is_internal = bool(meta_dict.get("is_internal_transfer", False))
                
            if is_internal:
                # Exclude internal transfers from total income, spend, categories, etc.
                continue

            amount = float(self._get_val(tx, "amount") or 0.0)
            tx_type = self._get_val(tx, "type")
            date = self._get_val(tx, "date")
            category = self._get_val(tx, "category") or "Other"
            is_recurring = bool(self._get_val(tx, "is_recurring") or self._get_val(tx, "isRecurring") or False)
            group_id = self._get_val(tx, "recurring_group_id") or self._get_val(tx, "recurringGroupId")
            
            # Check date format to get month (YYYY-MM)
            month = date[:7] if date and len(date) >= 7 else "Unknown"

            if month not in monthly_data:
                monthly_data[month] = {"income": 0.0, "spend": 0.0}

            if tx_type == "credit" or (tx_type is None and amount > 0):
                # Income (credit)
                income += amount
                monthly_data[month]["income"] += amount
            elif tx_type == "debit" or (tx_type is None and amount < 0):
                # Expense (debit)
                abs_amt = abs(amount)
                spend += abs_amt
                monthly_data[month]["spend"] += abs_amt
                
                # Category spend tracking
                category_spends[category] = category_spends.get(category, 0.0) + abs_amt
                
                # Track biggest transaction
                if abs_amt > biggest_tx_amt:
                    biggest_tx_amt = abs_amt
                    biggest_tx = tx

            # Recurring payments tracking
            if is_recurring and group_id and tx_type == "debit":
                # Find metadata containing the frequency details
                metadata = self._get_val(tx, "metadata_json") or self._get_val(tx, "metadata")
                frequency = "monthly"  # default fallback
                
                if metadata:
                    if isinstance(metadata, str):
                        try:
                            meta_dict = json.loads(metadata)
                        except Exception:
                            meta_dict = {}
                    else:
                        meta_dict = metadata
                    
                    frequency = meta_dict.get("recurring", {}).get("frequency", "monthly")
                
                # Store group details (since amounts inside the same group are matching ±5%, we can take average)
                if group_id not in recurring_groups:
                    recurring_groups[group_id] = []
                recurring_groups[group_id].append((abs(amount), frequency))

        # Calculate savings
        savings = income - spend
        savings_rate = (savings / income * 100.0) if income > 0.0 else 0.0
        
        # Round core aggregates
        income = round(income, 2)
        spend = round(spend, 2)
        savings = round(savings, 2)
        savings_rate = round(savings_rate, 2)  # Can be negative when spend > income (MET-04)

        # Construct top categories summary
        top_categories = []
        for cat, amt in category_spends.items():
            percentage = (amt / spend * 100.0) if spend > 0.0 else 0.0
            top_categories.append({
                "category": cat,
                "amount": round(amt, 2),
                "percentage": round(percentage, 2)
            })
        top_categories.sort(key=lambda x: x["amount"], reverse=True)

        # Construct monthly aggregation list
        monthly_aggregation = []
        for m, m_vals in monthly_data.items():
            if m != "Unknown":
                monthly_aggregation.append({
                    "month": m,
                    "income": round(m_vals["income"], 2),
                    "spend": round(m_vals["spend"], 2)
                })
        monthly_aggregation.sort(key=lambda x: x["month"])

        # Calculate monthly recurring total (sum of monthly equivalents for unique groups)
        recurring_total = 0.0
        for group_id, items in recurring_groups.items():
            # Calculate average amount for the group
            group_avg_amt = sum(item[0] for item in items) / len(items)
            frequency = items[0][1]
            
            # Compute monthly equivalent
            if frequency == "weekly":
                equiv = group_avg_amt * 4.33
            elif frequency == "monthly":
                equiv = group_avg_amt * 1.0
            elif frequency == "quarterly":
                equiv = group_avg_amt / 3.0
            elif frequency == "yearly":
                equiv = group_avg_amt / 12.0
            else:
                equiv = group_avg_amt * 1.0
                
            recurring_total += equiv
            
        recurring_total = round(recurring_total, 2)

        # Construct biggest transaction details
        biggest_tx_details = None
        if biggest_tx is not None:
            # We output clean descriptions and merchant fields
            desc = self._get_val(biggest_tx, "clean_description") or self._get_val(biggest_tx, "cleanDescription")
            raw_desc = self._get_val(biggest_tx, "raw_description") or self._get_val(biggest_tx, "rawDescription")
            biggest_tx_details = {
                "id": self._get_val(biggest_tx, "id"),
                "date": self._get_val(biggest_tx, "date"),
                "description": desc or raw_desc,
                "merchant": self._get_val(biggest_tx, "merchant"),
                "amount": round(float(self._get_val(biggest_tx, "amount")), 2),
                "category": self._get_val(biggest_tx, "category") or "Other"
            }

        return {
            "income": income,
            "spend": spend,
            "savings": savings,
            "savingsRate": savings_rate,
            "biggestTransaction": biggest_tx_details,
            "topCategories": top_categories,
            "monthlyAggregation": monthly_aggregation,
            "recurringTotal": recurring_total
        }
