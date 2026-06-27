import sys
import os
import json

# Add current folder to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.recurring.detector import RecurringDetector
from services.metrics.calculator import MetricsCalculator
from services.insights.templates import generate_templated_insights

def test_recurring_detection():
    print("Running test_recurring_detection...")
    
    # Mock transactions
    txs = [
        # Group A: Monthly Subscription (Netflix) - variance 0%, 30 days apart
        {"id": "tx1", "date": "2026-04-01", "cleanDescription": "NETFLIX subscription", "merchant": "Netflix", "amount": -499.00, "type": "debit", "category": "Subscriptions", "isRecurring": False, "recurringGroupId": None, "metadata": {}},
        {"id": "tx2", "date": "2026-05-01", "cleanDescription": "NETFLIX subscription", "merchant": "Netflix", "amount": -499.00, "type": "debit", "category": "Subscriptions", "isRecurring": False, "recurringGroupId": None, "metadata": {}},
        {"id": "tx3", "date": "2026-06-01", "cleanDescription": "NETFLIX subscription", "merchant": "Netflix", "amount": -499.00, "type": "debit", "category": "Subscriptions", "isRecurring": False, "recurringGroupId": None, "metadata": {}},
        
        # Group B: Weekly Spend (Active) - 7 days apart
        {"id": "tx4", "date": "2026-05-01", "cleanDescription": "Grocery", "merchant": "Local Store", "amount": -1000.00, "type": "debit", "category": "Food", "isRecurring": False, "recurringGroupId": None, "metadata": {}},
        {"id": "tx5", "date": "2026-05-08", "cleanDescription": "Grocery", "merchant": "Local Store", "amount": -1020.00, "type": "debit", "category": "Food", "isRecurring": False, "recurringGroupId": None, "metadata": {}},
        {"id": "tx6", "date": "2026-05-15", "cleanDescription": "Grocery", "merchant": "Local Store", "amount": -980.00, "type": "debit", "category": "Food", "isRecurring": False, "recurringGroupId": None, "metadata": {}},
        
        # Non-recurring random spends
        {"id": "tx7", "date": "2026-05-10", "cleanDescription": "Amazon Shopping", "merchant": "Amazon", "amount": -4500.00, "type": "debit", "category": "Shopping", "isRecurring": False, "recurringGroupId": None, "metadata": {}},
        {"id": "tx8", "date": "2026-05-20", "cleanDescription": "Restaurant Dinner", "merchant": "Zomato", "amount": -1200.00, "type": "debit", "category": "Food", "isRecurring": False, "recurringGroupId": None, "metadata": {}},
        
        # Credit transaction (Salary)
        {"id": "tx9", "date": "2026-05-01", "cleanDescription": "Salary Transfer", "merchant": "Salary Credit", "amount": 100000.00, "type": "credit", "category": "Salary", "isRecurring": False, "recurringGroupId": None, "metadata": {}},
    ]
    
    detector = RecurringDetector()
    tagged = detector.detect_and_tag(txs)
    
    # Assertions
    netflix_txs = [t for t in tagged if t["merchant"] == "Netflix"]
    assert all(t["isRecurring"] for t in netflix_txs), "Netflix txs should be marked as recurring"
    assert len(set(t["recurringGroupId"] for t in netflix_txs)) == 1, "Netflix txs should share the same groupId"
    assert netflix_txs[0]["metadata"]["recurring"]["frequency"] == "monthly", "Netflix should be classified as monthly"
    assert netflix_txs[0]["metadata"]["recurring"]["type"] == "subscription", "Netflix should be classified as subscription"
    
    weekly_txs = [t for t in tagged if t["merchant"] == "Local Store"]
    assert all(t["isRecurring"] for t in weekly_txs), "Local Store txs should be marked as recurring"
    assert weekly_txs[0]["metadata"]["recurring"]["frequency"] == "weekly", "Local Store should be classified as weekly"
    assert weekly_txs[0]["metadata"]["recurring"]["type"] == "other", "Local Store should fallback to other type"
    
    random_tx = next(t for t in tagged if t["id"] == "tx7")
    assert not random_tx["isRecurring"], "Random spend should not be recurring"
    
    print("test_recurring_detection: PASSED")

def test_metrics_calculation():
    print("Running test_metrics_calculation...")
    
    txs = [
        # Credits
        {"id": "1", "date": "2026-05-01", "cleanDescription": "Salary", "merchant": "Salary Credit", "amount": 100000.00, "type": "credit", "category": "Salary", "is_recurring": False, "recurring_group_id": None},
        # Debits
        {"id": "2", "date": "2026-05-02", "cleanDescription": "Netflix", "merchant": "Netflix", "amount": -500.00, "type": "debit", "category": "Subscriptions", "is_recurring": True, "recurring_group_id": "group1", "metadata_json": '{"recurring": {"frequency": "monthly", "type": "subscription"}}'},
        {"id": "3", "date": "2026-05-03", "cleanDescription": "Rent", "merchant": "House Rent", "amount": -20000.00, "type": "debit", "category": "Rent", "is_recurring": True, "recurring_group_id": "group2", "metadata_json": '{"recurring": {"frequency": "monthly", "type": "rent"}}'},
        {"id": "4", "date": "2026-05-04", "cleanDescription": "Shopping", "merchant": "Amazon", "amount": -5000.00, "type": "debit", "category": "Shopping", "is_recurring": False, "recurring_group_id": None},
    ]
    
    calculator = MetricsCalculator()
    metrics = calculator.calculate_metrics(txs)
    
    # Assertions
    assert metrics["income"] == 100000.0, f"Expected 100000, got {metrics['income']}"
    assert metrics["spend"] == 25500.0, f"Expected 25500, got {metrics['spend']}"
    assert metrics["savings"] == 74500.0, f"Expected 74500, got {metrics['savings']}"
    assert metrics["savingsRate"] == 74.5, f"Expected 74.5, got {metrics['savingsRate']}"
    
    assert metrics["biggestTransaction"]["id"] == "3", "Rent should be the biggest transaction"
    assert metrics["biggestTransaction"]["amount"] == -20000.0
    
    assert len(metrics["topCategories"]) == 3
    assert metrics["topCategories"][0]["category"] == "Rent"
    assert metrics["topCategories"][0]["amount"] == 20000.0
    assert metrics["topCategories"][0]["percentage"] == 78.43  # 20000 / 25500 * 100
    
    assert len(metrics["monthlyAggregation"]) == 1
    assert metrics["monthlyAggregation"][0]["month"] == "2026-05"
    assert metrics["monthlyAggregation"][0]["income"] == 100000.0
    assert metrics["monthlyAggregation"][0]["spend"] == 25500.0
    
    # Recurring total (monthly equivalents: Netflix = 500, Rent = 20000. Total = 20500)
    assert metrics["recurringTotal"] == 20500.0, f"Expected 20500, got {metrics['recurringTotal']}"
    
    print("test_metrics_calculation: PASSED")

def test_insights_generation():
    print("Running test_insights_generation...")
    
    mock_summary = {
        "income": 100000.0,
        "spend": 25500.0,
        "savings": 74500.0,
        "savingsRate": 74.5,
        "biggestTransaction": {
            "id": "3",
            "date": "2026-05-03",
            "description": "Rent",
            "merchant": "House Rent",
            "amount": -20000.0,
            "category": "Rent"
        },
        "topCategories": [
            {"category": "Rent", "amount": 20000.0, "percentage": 78.43},
            {"category": "Shopping", "amount": 5000.0, "percentage": 19.61},
            {"category": "Subscriptions", "amount": 500.0, "percentage": 1.96}
        ],
        "monthlyAggregation": [
            {"month": "2026-05", "income": 100000.0, "spend": 25500.0}
        ],
        "recurringTotal": 20500.0
    }
    
    insights = generate_templated_insights(mock_summary)
    
    # Assertions
    assert len(insights) >= 3, f"Expected at least 3 insights, got {len(insights)}"
    
    types = [i["type"] for i in insights]
    assert "savings_rate" in types, "Should have savings_rate insight"
    assert "top_category" in types, "Should have top_category insight"
    assert "biggest_purchase" in types, "Should have biggest_purchase insight"
    assert "recurring_burden" in types, "Should have recurring_burden insight"
    
    print("test_insights_generation: PASSED")

def test_internal_transfer_exclusion():
    print("Running test_internal_transfer_exclusion...")
    
    txs = [
        # Normal Salary
        {"id": "1", "date": "2026-05-01", "cleanDescription": "Salary", "merchant": "Salary Credit", "amount": 100000.00, "type": "credit", "category": "Salary", "is_recurring": False, "recurring_group_id": None},
        # Normal Spend
        {"id": "2", "date": "2026-05-02", "cleanDescription": "Netflix", "merchant": "Netflix", "amount": -500.00, "type": "debit", "category": "Subscriptions", "is_recurring": False, "recurring_group_id": None},
        # Self Transfer Debit
        {"id": "3", "date": "2026-05-03", "cleanDescription": "Transfer to credit card", "merchant": "Self Account", "amount": -10000.00, "type": "debit", "category": "Other", "is_recurring": False, "recurring_group_id": None, "metadata_json": '{"is_internal_transfer": true}'},
        # Self Transfer Credit
        {"id": "4", "date": "2026-05-04", "cleanDescription": "Self account transfer", "merchant": "Self Account", "amount": 10000.00, "type": "credit", "category": "Other", "is_recurring": False, "recurring_group_id": None, "metadata_json": '{"is_internal_transfer": true}'},
    ]
    
    calculator = MetricsCalculator()
    metrics = calculator.calculate_metrics(txs)
    
    # Check that income and spend do NOT include self transfers!
    # Expected: income = 100000, spend = 500
    assert metrics["income"] == 100000.0, f"Expected 100000, got {metrics['income']}"
    assert metrics["spend"] == 500.0, f"Expected 500, got {metrics['spend']}"
    assert metrics["savings"] == 99500.0, f"Expected 99500, got {metrics['savings']}"
    
    print("test_internal_transfer_exclusion: PASSED")

if __name__ == "__main__":
    try:
        test_recurring_detection()
        test_metrics_calculation()
        test_insights_generation()
        test_internal_transfer_exclusion()
        print("\nAll tests completed successfully!")
        sys.exit(0)
    except AssertionError as ae:
        print(f"\nAssertion Error: {str(ae)}")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)
