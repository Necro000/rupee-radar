import os
import pandas as pd
from services.ingestion.excel_parser import detect_excel_sheet_and_header, parse_excel_to_rows

def test_excel_parsing():
    print("Running test_excel_parsing...")
    
    # 1. Create a dummy Excel sheet structure
    file_path = "dummy_statement.xlsx"
    
    # Create sheets:
    # Sheet 1: Instructions (irrelevant)
    # Sheet 2: Bank Statement (relevant)
    df_instr = pd.DataFrame({"Notes": ["Confidential", "Please look at page 2 for transactions"]})
    
    df_tx = pd.DataFrame({
        "Unrelated Header": ["", "", ""],
        "Txn Date": ["", "2026-03-01", "2026-03-02"],
        "Narration": ["", "Salary Credit", "Amazon Store"],
        "Withdrawal": ["", 0, 1500],
        "Deposit": ["", 50000, 0],
        "Running Bal": ["", 50000, 48500]
    })
    
    with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
        df_instr.to_excel(writer, sheet_name="Instructions", index=False)
        df_tx.to_excel(writer, sheet_name="Transactions Activity", index=False)
        
    try:
        # Run detection
        sheet, header_idx = detect_excel_sheet_and_header(file_path)
        assert sheet == "Transactions Activity", f"Expected 'Transactions Activity', got {sheet}"
        # Header is on row 0 in Transactions Activity
        assert header_idx == 0, f"Expected header index 0, got {header_idx}"
        
        # Parse rows
        rows = parse_excel_to_rows(file_path, sheet, header_idx)
        assert len(rows) == 2, f"Expected 2 data rows, got {len(rows)}"
        assert rows[0]["Narration"] == "Salary Credit"
        assert rows[1]["Withdrawal"] == 1500
        
        print("test_excel_parsing: PASSED")
    finally:
        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    test_excel_parsing()
