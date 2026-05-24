"""
RBI Circular/Notification Parser Package
"""

from typing import List, Dict, Any, Optional
from .parser import parse_pdf

def parse_pdfs(
    paths: List[str],
    section: Optional[str] = None,
    output_dir: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Parses a list of RBI notification PDFs and extracts structured info.
    
    Args:
        paths: List of file paths to the target PDFs.
        section: Optional section filter.
        output_dir: Optional custom directory to save output JSON files.
        
    Returns:
        A dictionary mapping PDF file path to the parsed results dictionary.
    """
    results = {}
    for path in paths:
        try:
            results[path] = parse_pdf(path, section=section, output_dir=output_dir)
        except Exception as e:
            import logging
            logging.error(f"Error parsing {path}: {e}")
            results[path] = {"error": str(e)}
    return results

__all__ = ["parse_pdf", "parse_pdfs"]

