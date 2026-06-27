import pandas as pd
from typing import List, Dict, Any

def parse_csv_to_rows(file_path: str, delimiter: str, header_idx: int) -> List[Dict[str, Any]]:
    """
    Parse a CSV statement file into a list of raw rows (dictionaries).
    Handles basic cleaning of empty rows and standardizes column names.
    """
    try:
        # Load CSV using pandas
        # skiprows helps us start reading directly from the header row index
        df = pd.read_csv(file_path, sep=delimiter, skiprows=header_idx, skip_blank_lines=True, encoding='utf-8-sig')
        
        # Drop rows where all elements are NaN
        df = df.dropna(how='all')
        
        # Convert columns to string, strip whitespaces
        df.columns = [str(c).strip() for c in df.columns]
        
        # Replace NaN values with empty string or None for easier serialization/processing
        df = df.fillna("")
        
        # Convert to list of dictionaries
        rows = df.to_dict(orient='records')
        return rows
    except Exception as e:
        raise ValueError(f"Failed to parse CSV file: {str(e)}")
