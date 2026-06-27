import pandas as pd
from typing import List, Dict, Any, Tuple, Optional

def detect_excel_sheet_and_header(file_path: str) -> Tuple[str, int]:
    """
    Finds the best sheet in the Excel file and the 0-based header row index.
    Looks for the sheet and row containing standard bank transaction headers.
    """
    with pd.ExcelFile(file_path) as excel_file:
        sheet_names = excel_file.sheet_names
        
        # If only one sheet, use it
        if len(sheet_names) == 1:
            best_sheet = sheet_names[0]
            header_idx = find_excel_header_idx(file_path, best_sheet)
            return best_sheet, header_idx

        header_keywords = {
            'date', 'description', 'narration', 'particulars', 'remarks', 
            'debit', 'withdrawal', 'credit', 'deposit', 'amount', 'balance'
        }
        
        # Otherwise, score each sheet
        best_sheet = sheet_names[0]
        best_header_idx = 0
        max_score = -1
        
        for sheet in sheet_names:
            try:
                # Let's inspect the first 20 rows of this sheet
                df = pd.read_excel(excel_file, sheet_name=sheet, nrows=20, header=None)
                df = df.fillna("")
                
                # Check sheet name keywords for basic prioritization
                sheet_lower = sheet.lower()
                name_score = 0
                if any(kw in sheet_lower for kw in ['statement', 'transaction', 'activity', 'ledger', 'sheet1', 'sheet 1', 'bank']):
                    name_score = 5
                    
                for idx, row in df.iterrows():
                    tokens = [str(val).strip().lower() for val in row.values]
                    matches = sum(1 for token in tokens if any(kw in token for kw in header_keywords))
                    
                    # We want the sheet and row with the highest match of keywords
                    total_score = matches + name_score
                    if matches >= 2 and total_score > max_score:
                        max_score = total_score
                        best_sheet = sheet
                        best_header_idx = idx
            except Exception:
                continue
                
        return best_sheet, best_header_idx

def find_excel_header_idx(file_path: str, sheet_name: str) -> int:
    """Find header index in a specific sheet by scanning first 20 rows."""
    header_keywords = {
        'date', 'description', 'narration', 'particulars', 'remarks', 
        'debit', 'withdrawal', 'credit', 'deposit', 'amount', 'balance'
    }
    try:
        with pd.ExcelFile(file_path) as excel_file:
            df = pd.read_excel(excel_file, sheet_name=sheet_name, nrows=20, header=None)
            df = df.fillna("")
            for idx, row in df.iterrows():
                tokens = [str(val).strip().lower() for val in row.values]
                matches = sum(1 for token in tokens if any(kw in token for kw in header_keywords))
                if matches >= 2:
                    return idx
    except Exception:
        pass
    return 0

def parse_excel_to_rows(file_path: str, sheet_name: str, header_idx: int) -> List[Dict[str, Any]]:
    """Reads Excel sheet from the header index and converts it to a list of dicts."""
    try:
        with pd.ExcelFile(file_path) as excel_file:
            df = pd.read_excel(excel_file, sheet_name=sheet_name, skiprows=header_idx)
            df = df.dropna(how='all')
            df.columns = [str(c).strip() for c in df.columns]
            df = df.fillna("")
            
            # Convert any datetime columns or special values to strings or appropriate types
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    # format as ISO string YYYY-MM-DD
                    df[col] = df[col].dt.strftime('%Y-%m-%d')
                    
            rows = df.to_dict(orient='records')
            return rows
    except Exception as e:
        raise ValueError(f"Failed to parse Excel file: {str(e)}")
