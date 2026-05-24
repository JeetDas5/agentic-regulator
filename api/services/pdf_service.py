"""
Concurrent PDF processing service.
Bridges uploaded files to the existing parser.parser.parse_pdf() function
via temp files and asyncio thread offloading.
"""

import os
import asyncio
import tempfile
import logging
from typing import Any, Dict, List, Optional, Tuple

from parser.parser import parse_pdf

logger = logging.getLogger("api.services.pdf_service")

# PDF magic bytes — every valid PDF starts with this
PDF_MAGIC = b"%PDF"


def validate_pdf_bytes(content: bytes, filename: str) -> Optional[str]:
    """
    Validates that the uploaded bytes look like a real PDF.
    Returns an error message string if invalid, or None if valid.
    """
    if not content:
        return f"File '{filename}' is empty."

    if not content[:4].startswith(PDF_MAGIC):
        return f"File '{filename}' is not a valid PDF (invalid header bytes)."

    return None


def _parse_single_pdf(
    tmp_path: str,
    filename: str,
    section: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Synchronous wrapper that calls the existing parse_pdf on a temp file.
    Runs inside a thread via asyncio.to_thread.
    """
    logger.info("Parsing PDF: %s (temp: %s)", filename, tmp_path)
    result = parse_pdf(tmp_path, section=section, output_dir=None, save_output=False)
    return result


async def process_pdfs_concurrently(
    files: List[Tuple[str, bytes]],
    section: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Processes multiple PDFs concurrently using asyncio.to_thread.

    Args:
        files: List of (filename, raw_bytes) tuples.
        section: Optional section filter forwarded to parse_pdf.

    Returns:
        List of dicts, one per file:
          {"filename": str, "status": "success"|"error", "data": {...}|None, "error": str|None}
    """
    tmp_dir = tempfile.mkdtemp(prefix="cyberhack_api_")
    logger.debug("Using temp directory: %s", tmp_dir)

    async def _handle_one(filename: str, content: bytes) -> Dict[str, Any]:
        # Validate
        validation_err = validate_pdf_bytes(content, filename)
        if validation_err:
            logger.warning("Validation failed for %s: %s", filename, validation_err)
            return {
                "filename": filename,
                "status": "error",
                "data": None,
                "error": validation_err,
            }

        # Write to temp file
        safe_name = filename.replace(os.sep, "_").replace("/", "_")
        tmp_path = os.path.join(tmp_dir, safe_name)
        try:
            with open(tmp_path, "wb") as f:
                f.write(content)
        except OSError as exc:
            logger.error("Failed to write temp file for %s: %s", filename, exc)
            return {
                "filename": filename,
                "status": "error",
                "data": None,
                "error": f"Failed to stage file for processing: {exc}",
            }

        # Parse in a background thread (parse_pdf is CPU-bound / synchronous)
        try:
            parsed = await asyncio.to_thread(
                _parse_single_pdf, tmp_path, filename, section
            )
            logger.info("Successfully parsed: %s", filename)
            return {
                "filename": filename,
                "status": "success",
                "data": parsed,
                "error": None,
            }
        except Exception as exc:
            logger.exception("Error parsing %s: %s", filename, exc)
            return {
                "filename": filename,
                "status": "error",
                "data": None,
                "error": str(exc),
            }
        finally:
            # Clean up temp file
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except OSError:
                pass

    # Fire all file processing tasks concurrently
    tasks = [_handle_one(name, data) for name, data in files]
    results = await asyncio.gather(*tasks)

    # Clean up temp directory
    try:
        os.rmdir(tmp_dir)
    except OSError:
        pass

    return list(results)
