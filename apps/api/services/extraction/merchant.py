import re
from typing import Optional

# Pre-defined list of common Indian & Global merchant keywords and their clean names
MERCHANT_LOOKUP = {
    r'zomato': 'Zomato',
    r'swiggy': 'Swiggy',
    r'domino': 'Dominos',
    r'netflix': 'Netflix',
    r'spotify': 'Spotify',
    r'amazon': 'Amazon',
    r'flipkart': 'Flipkart',
    r'myntra': 'Myntra',
    r'jio': 'Jio',
    r'airtel': 'Airtel',
    r'uber': 'Uber',
    r'ola\s*ride': 'Ola',
    r'irctc': 'IRCTC',
    r'zerodha': 'Zerodha',
    r'groww': 'Groww',
    r'paytm': 'Paytm',
    r'phonepe': 'PhonePe',
    r'gpay': 'Google Pay',
    r'electricity': 'Electricity Bill',
    r'bescom': 'BESCOM',
    r'besl': 'Electricity Bill',
    r'rent': 'Rent',
    r'salary': 'Salary Credit',
    r'interest': 'Savings Interest',
    r'atm': 'ATM Withdrawal',
    r'nach': 'EMI Payment',
    r'emi': 'EMI Payment',
    r'lic': 'LIC Insurance',
}

def extract_merchant(raw_desc: str) -> str:
    """
    Cleans raw description and extracts a structured merchant name.
    If no pre-defined merchant is found, cleans up the transaction string
    by removing references, IDs, and UPI noise, returning a readable merchant token.
    """
    desc_lower = raw_desc.lower()
    
    # 1. Check pre-defined regular expressions first
    for pattern, clean_name in MERCHANT_LOOKUP.items():
        if re.search(pattern, desc_lower):
            return clean_name
            
    # 2. Heuristics for cleanup of UPI / IMPS / NEFT descriptions
    s = raw_desc
    
    # Remove standard UPI patterns:
    # e.g., UPI/MerchantName/TransactionID/Reference/Payment
    # or UPI-MerchantName-xxxx@okaxis
    upi_match = re.search(r'(?:upi|imps|neft|rtgs|ach|nach)[-/]([^-/]+)', desc_lower)
    if upi_match:
        s = upi_match.group(1)
    else:
        # Check if contains UPI handle (e.g. name@okaxis) and grab name
        handle_match = re.search(r'([^@\s/]+)@[a-zA-Z]{3,}', desc_lower)
        if handle_match:
            s = handle_match.group(1)
            
    # Strip common transaction noise
    s = re.sub(r'[\d/\-_]', ' ', s)  # Remove digits, slashes, dashes, underscores
    s = re.sub(r'\b(transfer|trf|payment|pay|order|ref|txn|tx|val|value|dr|cr|neft|rtgs|imps|upi|to|from|acct|saving|current)\b', ' ', s, flags=re.IGNORECASE)
    
    # Collapse multiple spaces
    s = re.sub(r'\s+', ' ', s).strip()
    
    # Capitalize words
    words = s.split()
    if words:
        # Keep at most 3 words for merchant name to prevent description overflow
        merchant_name = " ".join(words[:3]).title()
        return merchant_name
        
    return "Other"
