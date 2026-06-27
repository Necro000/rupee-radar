import re
from typing import Dict, List, Tuple, Optional

def sniff_delimiter(file_path: str) -> str:
    """Sniff the CSV delimiter by looking at occurrence counts in the first few lines."""
    delimiters = [',', ';', '\t', '|']
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [f.readline() for _ in range(10)]
    
    # Filter out empty lines
    lines = [line.strip() for line in lines if line.strip()]
    if not lines:
        return ','
        
    counts = {d: 0 for d in delimiters}
    for line in lines:
        for d in delimiters:
            counts[d] += line.count(d)
            
    # Find the delimiter with highest occurrence
    best_delimiter = max(counts, key=counts.get)
    # Default to comma if no delimiter found
    return best_delimiter if counts[best_delimiter] > 0 else ','

def detect_header_and_delimiter(file_path: str) -> Tuple[int, str]:
    """
    Detect the index of the header row (0-based) and the delimiter.
    Looks for row with keywords like 'date', 'description', 'narration', 'debit', 'credit', etc.
    """
    delimiter = sniff_delimiter(file_path)
    
    header_keywords = {
        'date', 'description', 'narration', 'particulars', 'remarks', 
        'debit', 'withdrawal', 'credit', 'deposit', 'amount', 'balance'
    }
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for idx, line in enumerate(f):
            # Split line using detected delimiter
            tokens = [t.strip().lower() for t in line.split(delimiter)]
            # Count matches of keywords
            matches = sum(1 for token in tokens if any(kw in token for kw in header_keywords))
            # If a line contains 2 or more header keywords, assume it's the header row
            if matches >= 2:
                return idx, delimiter
                
    # Fallback: assume header is on row 0
    return 0, delimiter

def map_columns(headers: List[str]) -> Dict[str, str]:
    """
    Map raw column names to canonical names using heuristics.
    Canonical fields: date, description, debit, credit, amount, balance
    """
    mapping = {}
    
    # Match lists (lowercased)
    keywords = {
        'date': ['date', 'txn date', 'transaction date', 'value date', 'val date'],
        'description': ['description', 'narration', 'particulars', 'remarks', 'transaction remarks', 'memo', 'narration/remarks'],
        'debit': ['debit', 'withdrawal', 'dr', 'withdrawals', 'withdrawal amount', 'debit amount', 'payment'],
        'credit': ['credit', 'deposit', 'cr', 'deposits', 'deposit amount', 'credit amount', 'receipt'],
        'amount': ['amount', 'txn amount', 'transaction amount', 'value', 'net amount'],
        'balance': ['balance', 'closing balance', 'running balance', 'bal']
    }
    
    for header in headers:
        header_clean = header.strip().lower()
        matched_canonical = None
        
        # Exact match check first
        for canonical, matches in keywords.items():
            if header_clean in matches:
                matched_canonical = canonical
                break
                
        # Substring match check next
        if not matched_canonical:
            for canonical, matches in keywords.items():
                if any(match in header_clean for match in matches):
                    matched_canonical = canonical
                    break
                    
        if matched_canonical and matched_canonical not in mapping.values():
            mapping[header] = matched_canonical
            
    return mapping
