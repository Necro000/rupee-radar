from typing import List, Dict, Any


def format_inr(amount: float) -> str:
    """
    Format a number in Indian rupee style with comma grouping.
    e.g. 123456.78 → '1,23,456.78'  (GAP-09 / UI-11)
    Uses Python's locale-independent implementation.
    """
    if amount is None:
        return "0"
    # Round to 2 decimal places
    amount = round(float(amount), 2)
    # Split integer and decimal parts
    int_part = int(abs(amount))
    dec_part = round(abs(amount) - int_part, 2)

    s = str(int_part)
    # Indian grouping: last 3 digits, then groups of 2
    if len(s) > 3:
        first_group = s[-3:]
        rest = s[:-3]
        groups = []
        while rest:
            groups.append(rest[-2:])
            rest = rest[:-2]
        groups.reverse()
        s = ','.join(groups) + ',' + first_group

    # Add decimal part if non-zero
    if dec_part > 0:
        dec_str = f"{dec_part:.2f}"[1:]  # e.g. '.78'
        s = s + dec_str

    prefix = '-' if amount < 0 else ''
    return f"{prefix}₹{s}"


def generate_templated_insights(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generates rule-based financial insights based on the calculated metrics summary.
    Returns a list of insight dictionaries.
    All ₹ amounts are formatted with Indian comma grouping (GAP-09).
    """
    insights = []

    income = summary.get("income", 0.0)
    spend = summary.get("spend", 0.0)
    savings = summary.get("savings", 0.0)
    savings_rate = summary.get("savingsRate", 0.0)
    biggest_tx = summary.get("biggestTransaction")
    top_categories = summary.get("topCategories", [])
    monthly_agg = summary.get("monthlyAggregation", [])
    recurring_total = summary.get("recurringTotal", 0.0)

    # 1. Savings Rate Insight
    if income > 0:
        if savings_rate >= 20.0:
            insights.append({
                "id": "insight_savings_healthy",
                "type": "savings_rate",
                "title": "Healthy Savings Rate",
                "text": f"Great job! You saved {format_inr(savings)} ({savings_rate}%) of your income this period, which is above the recommended 20% benchmark.",
                "amount": savings,
                "relevance": 0.70
            })
        elif savings_rate > 0.0:
            insights.append({
                "id": "insight_savings_low",
                "type": "savings_rate",
                "title": "Savings Rate Below Target",
                "text": f"You saved {format_inr(savings)} ({savings_rate}%) of your income. Aim to save at least 20% by identifying non-essential expenditures.",
                "amount": savings,
                "relevance": 0.80
            })
        else:
            # Negative savings (INS-04)
            insights.append({
                "id": "insight_savings_negative",
                "type": "savings_rate",
                "title": "Negative Savings Alert",
                "text": f"Your spending exceeded your income by {format_inr(abs(savings))} this period. Review your major expense categories to reduce outgoings.",
                "amount": savings,
                "relevance": 0.95
            })
    else:
        # No income recorded (MET-01)
        insights.append({
            "id": "insight_savings_no_income",
            "type": "savings_rate",
            "title": "No Income Detected",
            "text": f"No income transactions were found in this statement. Total spending was {format_inr(spend)}. Focus on creating a structured budget.",
            "amount": spend,
            "relevance": 0.50
        })

    # 2. Top Category Spend Insight
    if spend > 0 and top_categories:
        top_cat = top_categories[0]
        cat_name = top_cat["category"]
        cat_amount = top_cat["amount"]
        cat_pct = top_cat["percentage"]

        relevance = min(0.90, 0.40 + (cat_pct / 100.0) * 0.50)
        insights.append({
            "id": "insight_top_category",
            "type": "top_category",
            "title": f"High Spend on {cat_name}",
            "text": f"You spent {format_inr(cat_amount)} on {cat_name} this period, which accounts for {cat_pct}% of your total spending. This is your largest spending area.",
            "amount": cat_amount,
            "relevance": round(relevance, 2)
        })

    # 3. Biggest Transaction Insight
    if biggest_tx and spend > 0:
        tx_amount = abs(biggest_tx["amount"])
        tx_desc = biggest_tx["description"]
        tx_date = biggest_tx["date"]
        tx_cat = biggest_tx["category"]

        ratio = tx_amount / spend
        relevance = min(0.90, 0.30 + ratio * 0.60)

        insights.append({
            "id": "insight_biggest_purchase",
            "type": "biggest_purchase",
            "title": "Largest Single Expense",
            "text": f"Your single largest expense was {format_inr(tx_amount)} at {tx_desc} on {tx_date} (Category: {tx_cat}). This transaction represents {round(ratio * 100.0, 2)}% of your entire spend.",
            "amount": tx_amount,
            "relevance": round(relevance, 2)
        })

    # 4. Recurring Burden Insight
    if recurring_total > 0:
        ratio = (recurring_total / income * 100.0) if income > 0 else 0.0
        relevance = 0.50 + (ratio / 100.0) * 0.40 if ratio > 0 else 0.60

        burden_text = f"You have recurring commitments (subscriptions, EMIs, rent, etc.) totaling {format_inr(recurring_total)} per month."
        if ratio > 0:
            burden_text += f" This consumes {round(ratio, 2)}% of your monthly income."

        insights.append({
            "id": "insight_recurring_burden",
            "type": "recurring_burden",
            "title": "Recurring Payment Burden",
            "text": burden_text,
            "amount": recurring_total,
            "relevance": round(relevance, 2)
        })

    # 5. Month-over-Month Comparison Insight (INS-02: skip if only 1 month)
    if len(monthly_agg) >= 2:
        last_month = monthly_agg[-1]
        prev_month = monthly_agg[-2]

        last_spend = last_month["spend"]
        prev_spend = prev_month["spend"]

        if prev_spend > 0:
            change_pct = ((last_spend - prev_spend) / prev_spend) * 100.0

            if change_pct > 0:
                relevance = min(0.85, 0.50 + (change_pct / 100.0) * 0.35)
                insights.append({
                    "id": "insight_month_comparison",
                    "type": "month_comparison",
                    "title": "Increase in Monthly Spend",
                    "text": f"Your spending in {last_month['month']} ({format_inr(last_spend)}) rose by {round(change_pct, 2)}% compared to {prev_month['month']} ({format_inr(prev_spend)}).",
                    "amount": last_spend,
                    "relevance": round(relevance, 2)
                })
            else:
                insights.append({
                    "id": "insight_month_comparison",
                    "type": "month_comparison",
                    "title": "Decrease in Monthly Spend",
                    "text": f"Excellent! Your spending in {last_month['month']} ({format_inr(last_spend)}) decreased by {round(abs(change_pct), 2)}% compared to {prev_month['month']} ({format_inr(prev_spend)}).",
                    "amount": last_spend,
                    "relevance": 0.60
                })

    # Fallback general insights to guarantee at least 3 insights are always returned (INS-01)
    fallback_tips = [
        {
            "id": "insight_fallback_emergency",
            "type": "budget_tip",
            "title": "Build an Emergency Fund",
            "text": "Aim to set aside 3 to 6 months of basic living expenses in a high-yield liquid account to cover unforeseen expenses.",
            "amount": None,
            "relevance": 0.30
        },
        {
            "id": "insight_fallback_budget",
            "type": "budget_tip",
            "title": "The 50/30/20 Budgeting Rule",
            "text": "Try allocating 50% of your income to Needs (rent, bills), 30% to Wants (dining out, shopping), and 20% to Savings or Investments.",
            "amount": None,
            "relevance": 0.25
        },
        {
            "id": "insight_fallback_track",
            "type": "budget_tip",
            "title": "Regular Expense Auditing",
            "text": "Regularly check your monthly statements for inactive subscriptions and membership fees that you can cancel to immediately save money.",
            "amount": None,
            "relevance": 0.20
        }
    ]

    # Rank insights by relevance descending
    insights.sort(key=lambda x: x["relevance"], reverse=True)

    # If we have fewer than 3 insights, append fallbacks until we have 3 (INS-01)
    for tip in fallback_tips:
        if len(insights) >= 3:
            break
        if not any(i["id"] == tip["id"] for i in insights):
            insights.append(tip)

    # Final sort to ensure correct ranking sequence
    insights.sort(key=lambda x: x["relevance"], reverse=True)

    return insights
