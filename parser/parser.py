import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import fitz

from .text_cleaner import clean_text
from .metadata_extractor import extract_metadata
from .section_extractor import extract_sections
from .table_extractor import extract_tables
from .utils import get_processed_dir

def save_json(data: Dict[str, Any], pdf_path: str, section: Optional[str] = None, output_dir: Optional[str] = None) -> str:
    """Saves the parsed data dictionary to a JSON file in the target output directory."""
    if output_dir:
        processed_dir = Path(output_dir)
        processed_dir.mkdir(parents=True, exist_ok=True)
    else:
        processed_dir = get_processed_dir()
    
    # Get base filename without extension
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    section_label = section if section else "full"
    output_filename = f"{base_name}_{section_label}.json"
    output_path = processed_dir / output_filename
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logging.info(f"Successfully saved parsed JSON to: {output_path}")
    except Exception as e:
        logging.error(f"Error saving JSON to {output_path}: {e}")
        
    return str(output_path)

def parse_pdf(
    pdf_path: str,
    section: Optional[str] = None,
    output_dir: Optional[str] = None,
    save_output: bool = True,
) -> Dict[str, Any]:
    """
    Parses an RBI notification PDF and extracts structured information.
    
    Args:
        pdf_path: Path to the target PDF file.
        section: Optional section filter ('metadata', 'content', 'sections', 'amendments', 'tables').
        output_dir: Optional custom directory to save the output JSON file.
        save_output: Whether to write parsed JSON to disk.
        
    Returns:
        A dictionary containing the parsed data (full or filtered).
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found at: {pdf_path}")
        
    logging.info(f"Opening PDF for parsing: {pdf_path}")
    doc = fitz.open(pdf_path)
    
    # 1. Extract raw text page by page
    raw_text_parts = []
    for page in doc:
        raw_text_parts.append(page.get_text() or "")
    raw_text = "\n".join(raw_text_parts)
    
    # 2. Clean the raw text
    cleaned_text_val = clean_text(raw_text)
    
    # 3. Extract Metadata
    metadata = extract_metadata(cleaned_text_val, pdf_path)
    
    # 4. Extract Paragraphs & Amendments
    sections_data = extract_sections(cleaned_text_val)
    
    # 5. Extract Tables
    tables_data = extract_tables(pdf_path)
    
    # Combine everything into the full structure
    full_result = {
        "metadata": metadata,
        "content": {
            "full_text": raw_text,
            "clean_text": cleaned_text_val
        },
        "sections": sections_data.get("paragraphs", []),
        "amendments": sections_data.get("amendments", []),
        "tables": tables_data
    }
    
    # Apply section filtering if requested
    if section:
        section_clean = section.strip().lower()
        if section_clean == "full":
            result = full_result
            save_section = "full"
        elif section_clean in full_result:
            result = {section_clean: full_result[section_clean]}
            save_section = section_clean
        else:
            # Fallback/warning if invalid section
            logging.warning(f"Unknown section filter '{section}'. Returning full parsed data.")
            result = full_result
            save_section = "full"
    else:
        result = full_result
        save_section = "full"
        
    # Save output to JSON when used by the CLI/parser workflow. API callers can
    # disable this to avoid writing per-request artifacts to data/processed.
    if save_output:
        save_json(result, pdf_path, save_section, output_dir)
    
    return result
