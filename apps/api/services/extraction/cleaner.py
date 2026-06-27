import re
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional


def clean_amount_string(val: Any) -> float:
    """
    Clean string number representation and convert to float.
    Handles:
      - Currency symbols: '₹1,500.00' → 1500.00          (EXT-10)
      - Indian numbering: '1,23,456.78' → 123456.78       (EXT-11)
      - Parenthetical negatives: '(500.00)' → -500.0      (EXT-12 / BUG-02)
      - Scientific notation: '1.5e3' → 1500.0             (EXT-17 / GAP-02)
    """
    if val is None or val == "":
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)

    s = str(val).strip()

    # EXT-12: parenthetical negatives like (500.00) → -500.0
    paren_match = re.fullmatch(r'\(\s*([\d,\.]+)\s*\)', s)
    if paren_match:
        inner = paren_match.group(1).replace(',', '')
        try:
            return -float(inner)
        except ValueError:
            return 0.0

    # Strip currency prefix (letters, ₹, Rs., $, etc.) from the front
    s = re.sub(r'^[^\d\(\-\+\.]+', '', s)
    # Remove currency symbols, commas, spaces — but keep digits, dot, sign, e/E for sci notation
    s = re.sub(r'[^\d\.\-\+eE]', '', s)
    # Strip stray leading/trailing dots that are not decimal points (e.g. 'Rs. 500' → '.500')
    s = s.strip('.')
    if not s:
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_date(date_str: Any) -> str:
    """
    Parse a variety of common date formats and normalize to ISO YYYY-MM-DD.
    Raises ValueError if the date cannot be parsed (BUG-03) so callers can
    skip the row rather than silently assigning today's date.
    """
    if date_str is None or str(date_str).strip() == "":
        raise ValueError(f"Empty date value: {date_str!r}")

    s = str(date_str).strip()

    # EXT-05: strip time component from timestamps before format matching
    # e.g. '2025-01-15 14:32:00' → '2025-01-15', '15/01/2025 14:32' → '15/01/2025'
    s_date_only = re.split(r'[\sT]', s)[0]

    formats = [
        "%Y-%m-%d",      # 2026-06-23
        "%d-%m-%Y",      # 23-06-2026
        "%d/%m/%Y",      # 23/06/2026
        "%Y/%m/%d",      # 2026/06/23
        "%d-%b-%Y",      # 23-Jun-2026
        "%d/%b/%Y",      # 23/Jun/2026
        "%d-%B-%Y",      # 23-June-2026
        "%d-%m-%y",      # 23-06-26  (EXT-02: two-digit year)
        "%d/%m/%y",      # 23/06/26
        "%b %d, %Y",     # Jun 23, 2026
        "%B %d, %Y",     # June 23, 2026
        # Timestamp formats (BUG-04)
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
    ]

    # Try date-only portion first, then full string for timestamp formats
    for candidate in (s_date_only, s):
        for fmt in formats:
            try:
                dt = datetime.strptime(candidate, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

    # Regex fallbacks for ISO and Indian formats embedded in longer strings
    match_iso = re.search(r'(\d{4})[-/](\d{2})[-/](\d{2})', s)
    if match_iso:
        return f"{match_iso.group(1)}-{match_iso.group(2)}-{match_iso.group(3)}"

    match_ind = re.search(r'(\d{2})[-/](\d{2})[-/](\d{4})', s)
    if match_ind:
        return f"{match_ind.group(3)}-{match_ind.group(2)}-{match_ind.group(1)}"

    # BUG-03 fix: raise instead of silently returning today
    raise ValueError(f"Unparseable date value: {date_str!r}")


def clean_description(desc: Any) -> str:
    """Trim, collapse multiple spaces, and normalize description."""
    if desc is None:
        return ""
    s = str(desc).strip()
    s = re.sub(r'\s+', ' ', s)
    return s


def extract_and_normalize_amount(row: Dict[str, Any], column_map: Dict[str, str]) -> Tuple[float, str]:
    """
    Determine transaction amount (negative for debit/expense, positive for credit/income)
    and transaction type ('debit' or 'credit').
    Handles EXT-13: both debit and credit populated → prefer non-zero debit first.
    Handles EXT-15: both zero → returns (0.0, 'debit') which is then skipped by orchestrator.
    """
    # Find reverse mapping (canonical to raw column name)
    reverse_map = {v: k for k, v in column_map.items()}

    debit_col = reverse_map.get('debit')
    credit_col = reverse_map.get('credit')
    amount_col = reverse_map.get('amount')

    debit_val = clean_amount_string(row.get(debit_col)) if debit_col else 0.0
    credit_val = clean_amount_string(row.get(credit_col)) if credit_col else 0.0

    # Heuristics:
    # 1. Separate Debit and Credit columns are both defined
    if debit_col or credit_col:
        if debit_val > 0:
            return -debit_val, "debit"
        elif credit_val > 0:
            return credit_val, "credit"

    # 2. Only single Amount column is defined
    if amount_col:
        raw_amt = clean_amount_string(row.get(amount_col))

        # Look for Type indicator in the row
        type_indicator = None
        for key, val in row.items():
            val_str = str(val).strip().lower()
            if val_str in ['dr', 'debit', 'w', 'withdrawal', 'wd']:
                type_indicator = 'debit'
                break
            elif val_str in ['cr', 'credit', 'd', 'deposit', 'dp']:
                type_indicator = 'credit'
                break

        # If type indicator is found, apply it
        if type_indicator == 'debit':
            return -abs(raw_amt), "debit"
        elif type_indicator == 'credit':
            return abs(raw_amt), "credit"

        # Otherwise fall back to numerical sign
        if raw_amt < 0:
            return raw_amt, "debit"
        elif raw_amt > 0:
            return raw_amt, "credit"

    # Default fallback (EXT-15: both empty → zero amount, will be skipped)
    return 0.0, "debit"


def deduplicate_transactions(transactions: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]:
    """
    Remove duplicate transactions based on a unique hash of (date, amount, clean_description).
    EXT-32: Full normalized description is included in hash to prevent incorrect deduplication
    of legitimate same-day, same-amount, same-merchant transactions.
    Returns the deduplicated transactions list and the count of duplicates removed.
    """
    seen_hashes = set()
    deduped = []
    duplicates_count = 0

    for tx in transactions:
        # Create unique fingerprint
        fingerprint = f"{tx['date']}_{tx['amount']:.2f}_{tx['cleanDescription'].lower().strip()}"
        tx_hash = hashlib.md5(fingerprint.encode('utf-8')).hexdigest()

        if tx_hash in seen_hashes:
            duplicates_count += 1
        else:
            seen_hashes.add(tx_hash)
            # Add hash to transaction metadata just in case
            if 'metadata' not in tx or tx['metadata'] is None:
                tx['metadata'] = {}
            tx['metadata']['fingerprint_hash'] = tx_hash
            deduped.append(tx)

    return deduped, duplicates_count
