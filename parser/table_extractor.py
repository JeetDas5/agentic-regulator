import fitz
import re
from typing import List, Dict, Any

def clean_cell(text: Any) -> str:
    """Cleans a single cell's text by stripping spaces and normalizing newlines."""
    if text is None:
        return ""
    text = str(text)
    text = text.replace('\xa0', ' ').replace('\v', '\n')
    # Replace multiple spaces with a single space, but keep newlines
    text = re.sub(r'[ \t]+', ' ', text)
    # Strip leading/trailing whitespaces from each line
    lines = [line.strip() for line in text.split('\n')]
    return '\n'.join(lines).strip()

def is_signature_block(rows: List[List[str]]) -> bool:
    """
    Heuristic to determine if a small table is just a signature block.
    Signature blocks often contain signatory titles or names in parentheses.
    """
    if not rows or len(rows) > 3:
        return False
    
    signature_keywords = {
        "general manager", "deputy governor", "executive director", 
        "chief general manager", "officer-in-charge", "cgms", "cgm"
    }
    
    for row in rows:
        for cell in row:
            val = cell.lower()
            # Check for signature keywords
            if any(kw in val for kw in signature_keywords):
                return True
            # Check for names in parentheses (e.g. "(Sunil T S Nair)")
            if re.search(r"\(\s*[a-zA-Z\s\.]+\s*\)", val):
                return True
    return False

def extract_tables(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extracts tabular data from all pages of the PDF using PyMuPDF.
    
    Returns:
        A list of dicts, each representing a table:
        {
            "page": int,
            "headers": List[str],
            "rows": List[List[str]]
        }
    """
    extracted_tables = []
    
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        # Return empty list if PDF cannot be opened
        return []

    for page_idx, page in enumerate(doc):
        try:
            tables = page.find_tables()
            table_list = list(tables)
        except Exception:
            continue
            
        for table in table_list:
            raw_data = table.extract()
            if not raw_data or len(raw_data) == 0:
                continue
                
            # Clean all cells
            cleaned_data = []
            for row in raw_data:
                cleaned_row = [clean_cell(cell) for cell in row]
                cleaned_data.append(cleaned_row)
                
            # Filter out signature blocks
            if is_signature_block(cleaned_data):
                continue
                
            # Headers are the first row
            headers = cleaned_data[0]
            rows = cleaned_data[1:] if len(cleaned_data) > 1 else []
            
            # If all rows are empty, skip
            if not any(any(cell for cell in row) for row in rows) and not any(headers):
                continue
                
            extracted_tables.append({
                "page": page_idx + 1,
                "headers": headers,
                "rows": rows
            })
            
    return extracted_tables
