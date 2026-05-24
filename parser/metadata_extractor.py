import re
import os
import logging
from typing import Dict, Any, Optional
from .utils import load_scraper_metadata

# Regex patterns
RBI_ID_PATTERN = re.compile(r"\b(RBI/\d{4}-\d{2}/\d+)\b", re.IGNORECASE)
REF_NO_PATTERN = re.compile(r"\b([A-Z]{2,}(?:\.[A-Z0-9]+)+[\w\.\-\/]+/\d{4}-\d{2})\b", re.IGNORECASE)
DATE_PATTERN = re.compile(r"\b([A-Z][a-z]+ \d{1,2}, \d{4})\b")
# Matches "(Name Here)\nDesignation Here" blocks
SIGNATORY_PATTERN = re.compile(r"\(([^)]+)\)\s*\n\s*([A-Z][A-Za-z\s\&\-]+)", re.MULTILINE)

def _is_person_name(text: str) -> bool:
    """Heuristic check: a person's name contains only letters, spaces, dots, and hyphens."""
    cleaned = text.strip()
    if not cleaned:
        return False
    # Must be mostly alphabetic words (allow dots and hyphens for initials)
    if re.fullmatch(r"[A-Za-z\s\.\-]+", cleaned) and len(cleaned.split()) >= 2:
        return True
    return False

def extract_metadata(full_text: str, pdf_path: str) -> Dict[str, Any]:
    """
    Extracts key metadata from the PDF text (RBI ID, Reference Number, Date, Title, Signatory).
    Also tries to merge metadata from the scraper's metadata.json.
    """
    metadata = {
        "rbi_id": None,
        "ref_no": None,
        "date": None,
        "title": None,
        "source": "Reserve Bank of India",
        "signatory_name": None,
        "signatory_designation": None,
        "scraper_info": {}
    }
    
    # 1. Search for regex matches
    rbi_id_match = RBI_ID_PATTERN.search(full_text)
    if rbi_id_match:
        metadata["rbi_id"] = rbi_id_match.group(1).strip()
        
    ref_no_match = REF_NO_PATTERN.search(full_text)
    if ref_no_match:
        metadata["ref_no"] = ref_no_match.group(1).strip()
        
    date_match = DATE_PATTERN.search(full_text)
    if date_match:
        metadata["date"] = date_match.group(1).strip()
        
    # Find ALL signatory-like matches and pick the LAST one that looks like a person's name
    sig_matches = SIGNATORY_PATTERN.findall(full_text)
    for name_candidate, designation_candidate in reversed(sig_matches):
        if _is_person_name(name_candidate):
            metadata["signatory_name"] = name_candidate.strip()
            metadata["signatory_designation"] = designation_candidate.strip()
            break

    # 2. Extract Title using line-based heuristics
    lines = [line.strip() for line in full_text.split("\n") if line.strip()]
    
    # Find position of date and "please refer to"
    date_idx = -1
    refer_idx = -1
    for idx, line in enumerate(lines):
        if metadata["date"] and metadata["date"] in line:
            date_idx = idx
        if "please refer to" in line.lower():
            refer_idx = idx
            break
            
    if date_idx != -1 and refer_idx != -1 and refer_idx > date_idx + 1:
        title_lines = lines[date_idx + 1:refer_idx]
        # Join lines with spaces, normalize spaces
        raw_title = " ".join(title_lines)
        metadata["title"] = re.sub(r'\s+', ' ', raw_title).strip()
        
    # If heuristic failed, fallback to first non-empty lines
    if not metadata["title"] and len(lines) > 5:
        # Find index of ref_no and use the next few lines
        ref_idx = -1
        for idx, line in enumerate(lines):
            if metadata["ref_no"] and metadata["ref_no"] in line:
                ref_idx = idx
                break
        if ref_idx != -1 and len(lines) > ref_idx + 2:
            metadata["title"] = lines[ref_idx + 2]

    # 3. Merge with scraper's metadata.json
    scraper_meta = load_scraper_metadata()
    pdf_filename = os.path.basename(pdf_path)
    
    for key_url, entry in scraper_meta.items():
        entry_file_path = entry.get("file_path", "")
        # Match by filename or by matching paths
        if entry_file_path and os.path.basename(entry_file_path) == pdf_filename:
            metadata["scraper_info"] = {
                "scraped_title": entry.get("title"),
                "scraped_published": entry.get("published"),
                "scraped_page_url": entry.get("page_url"),
                "scraped_pdf_url": entry.get("pdf_url"),
                "timestamp": entry.get("timestamp")
            }
            # Fallbacks for missing fields from extraction
            if not metadata["title"]:
                metadata["title"] = entry.get("title")
            break
            
    return metadata
