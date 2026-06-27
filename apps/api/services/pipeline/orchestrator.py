import os
import uuid
import json
import re
from sqlalchemy.orm import Session
from db.session_store import DBSession, DBTransaction, update_session_status, get_session
from services.ingestion.detector import detect_header_and_delimiter, map_columns
from services.ingestion.csv_parser import parse_csv_to_rows
from services.extraction.cleaner import parse_date, clean_description, extract_and_normalize_amount, deduplicate_transactions
from services.extraction.merchant import extract_merchant
from services.categorization.service import CategorizationService

class ColumnMappingRequiredError(Exception):
    def __init__(self, headers: list, suggested_mapping: dict):
        self.headers = headers
        self.suggested_mapping = suggested_mapping
        super().__init__("Column mapping required")

def is_self_transfer(description: str) -> bool:
    if not description:
        return False
    desc_lower = description.lower()
    patterns = [
        r'\bself\b',
        r'transfer to credit card',
        r'own account',
        r'transfer to own',
        r'transfer to self',
        r'\bto self\b',
        r'\bfrom self\b',
        r'transfer to my',
        r'transfer to card',
        r'self transfer',
        r'internal transfer'
    ]
    return any(re.search(pat, desc_lower) for pat in patterns)

def run_pipeline(db: Session, session_id: str, file_path: str, manual_mapping: dict = None) -> dict:
    """
    Executes the transaction ingestion and extraction pipeline.
    Saves cleaned transaction records to the database.
    """
    # 1. Update session status to processing
    update_session_status(db, session_id, "processing")
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Uploaded statement file not found at: {file_path}")
            
        # 2. Sniff layout & delimiter OR parse Excel
        is_excel = file_path.lower().endswith('.xlsx')
        
        if is_excel:
            from services.ingestion.excel_parser import detect_excel_sheet_and_header, parse_excel_to_rows
            sheet_name, header_idx = detect_excel_sheet_and_header(file_path)
            raw_rows = parse_excel_to_rows(file_path, sheet_name, header_idx)
        else:
            header_idx, delimiter = detect_header_and_delimiter(file_path)
            raw_rows = parse_csv_to_rows(file_path, delimiter, header_idx)
            
        if not raw_rows:
            raise ValueError("The uploaded statement is empty or has no readable transaction rows.")
            
        # 4. Map columns
        first_row_headers = list(raw_rows[0].keys())
        if manual_mapping:
            column_map = {}
            for canonical, raw in manual_mapping.items():
                if raw and raw in first_row_headers:
                    column_map[raw] = canonical
        else:
            column_map = map_columns(first_row_headers)
            
        # Verify essential columns are mapped
        # We must have at least date and (amount or debit or credit)
        reverse_map = {v: k for k, v in column_map.items()}
        if 'date' not in reverse_map:
            raise ColumnMappingRequiredError(headers=first_row_headers, suggested_mapping=reverse_map)
        if 'amount' not in reverse_map and 'debit' not in reverse_map and 'credit' not in reverse_map:
            raise ColumnMappingRequiredError(headers=first_row_headers, suggested_mapping=reverse_map)
            
        # 5. Clean & structure transaction candidates
        transactions_candidates = []
        skipped_rows_count = 0
        
        date_col = reverse_map.get('date')
        desc_col = reverse_map.get('description')
        
        for idx, row in enumerate(raw_rows):
            try:
                # parse_date raises ValueError for unparseable dates (BUG-03 fix),
                # which is caught below so the row is counted as skipped.
                raw_date = row.get(date_col)
                if not raw_date or str(raw_date).strip() == "":
                    skipped_rows_count += 1
                    continue
                date_iso = parse_date(raw_date)
                
                # Parse amount and type
                amount, tx_type = extract_and_normalize_amount(row, column_map)
                
                # Zero amounts can represent balance forwards or header rows, skip them
                if amount == 0.0:
                    skipped_rows_count += 1
                    continue
                    
                # Clean description
                raw_desc = row.get(desc_col, "")
                clean_desc = clean_description(raw_desc)
                if not clean_desc and not raw_desc:
                    clean_desc = "Unnamed Transaction"
                elif not clean_desc:
                    clean_desc = str(raw_desc)
                    
                # Extract merchant token
                merchant = extract_merchant(clean_desc or raw_desc)
                
                # Check for self-transfers
                is_internal = is_self_transfer(str(raw_desc)) or is_self_transfer(clean_desc)
                metadata = {}
                if is_internal:
                    metadata["is_internal_transfer"] = True
                
                # Construct intermediate transaction dict
                tx_dict = {
                    "id": str(uuid.uuid4()),
                    "date": date_iso,
                    "rawDescription": str(raw_desc),
                    "cleanDescription": clean_desc,
                    "merchant": merchant,
                    "amount": amount,
                    "type": tx_type,
                    "category": "Other",
                    "categoryConfidence": 1.0,
                    "categorySource": "rule",
                    "isRecurring": False,
                    "recurringGroupId": None,
                    "metadata": metadata
                }
                transactions_candidates.append(tx_dict)
            except Exception as row_error:
                # Log individual row errors and continue processing the rest
                skipped_rows_count += 1
                print(f"Skipped row {idx} due to error: {str(row_error)}")
                
        if not transactions_candidates:
            raise ValueError("No valid transaction rows could be parsed from the statement.")
            
        # 6. Deduplicate transactions
        deduped_txs, duplicates_removed = deduplicate_transactions(transactions_candidates)
        
        # 6.5 Categorize transactions using hybrid rules + LLM engine
        categorizer = CategorizationService()
        categorized_txs = categorizer.categorize_transactions(db, session_id, deduped_txs)
        
        # Override categories for self-transfers to 'Other'
        for tx in categorized_txs:
            tx_meta = tx.get("metadata") or {}
            if tx_meta.get("is_internal_transfer"):
                tx["category"] = "Other"
                tx["categoryConfidence"] = 1.0
                tx["categorySource"] = "rule"
        
        # 6.6 Detect recurring transactions
        from services.recurring.detector import RecurringDetector
        detector = RecurringDetector()
        final_txs = detector.detect_and_tag(categorized_txs)
        
        # 7. Purge any existing transactions for this session (for re-runs)
        db.query(DBTransaction).filter(DBTransaction.session_id == session_id).delete()
        
        # 8. Save transactions to database
        db_transactions = []
        for tx in final_txs:
            db_tx = DBTransaction(
                id=tx["id"],
                session_id=session_id,
                date=tx["date"],
                raw_description=tx["rawDescription"],
                clean_description=tx["cleanDescription"],
                merchant=tx["merchant"],
                amount=tx["amount"],
                type=tx["type"],
                category=tx["category"],
                category_confidence=tx["categoryConfidence"],
                category_source=tx["categorySource"],
                is_recurring=tx["isRecurring"],
                recurring_group_id=tx["recurringGroupId"],
                metadata_json=json.dumps(tx.get("metadata", {}))
            )
            db_transactions.append(db_tx)
            db.add(db_tx)
            
        db.commit()
        
        # 9. Update status to complete
        meta_summary = {
            "total_parsed": len(raw_rows),
            "valid_extracted": len(db_transactions),
            "skipped": skipped_rows_count,
            "duplicates_removed": duplicates_removed,
            "column_mapping": column_map
        }
        
        update_session_status(db, session_id, "complete")
        
        # We can write execution details to session_statuses table if we extend it,
        # but returning it here is sufficient.
        return meta_summary
        
    except Exception as e:
        db.rollback()
        # Update session status to error
        update_session_status(db, session_id, "error", error_message=str(e))
        raise e
