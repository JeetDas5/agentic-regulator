"""
Pydantic response models for the PDF parsing API.
Mirrors the exact JSON schema produced by parser.parser.parse_pdf().
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ScraperInfo(BaseModel):
    """Optional metadata enrichment from the scraper's metadata.json."""
    scraped_title: Optional[str] = None
    scraped_published: Optional[str] = None
    scraped_page_url: Optional[str] = None
    scraped_pdf_url: Optional[str] = None
    timestamp: Optional[float] = None


class Metadata(BaseModel):
    """Extracted document metadata — RBI IDs, dates, signatory info."""
    rbi_id: Optional[str] = None
    ref_no: Optional[str] = None
    date: Optional[str] = None
    title: Optional[str] = None
    source: Optional[str] = "Reserve Bank of India"
    signatory_name: Optional[str] = None
    signatory_designation: Optional[str] = None
    scraper_info: Optional[ScraperInfo] = Field(default_factory=dict)


class Content(BaseModel):
    """Raw and cleaned text extracted from the PDF."""
    full_text: str = ""
    clean_text: str = ""


class Section(BaseModel):
    """A numbered paragraph extracted from the document."""
    id: str
    text: str


class Table(BaseModel):
    """A table extracted from the PDF, with page number, headers, and rows."""
    page: int
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)


class ParsedDocument(BaseModel):
    """
    Complete parsed output for a single PDF.
    Schema matches the JSON files produced by `parser.parser.parse_pdf()`.
    """
    metadata: Metadata = Field(default_factory=Metadata)
    content: Content = Field(default_factory=Content)
    sections: List[Section] = Field(default_factory=list)
    amendments: List[Section] = Field(default_factory=list)
    tables: List[Table] = Field(default_factory=list)


class FileResult(BaseModel):
    """Per-file result wrapper — success data or structured error."""
    filename: str
    status: str = Field(description="'success' or 'error'")
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ParseResponse(BaseModel):
    """Top-level API response combining results from all uploaded PDFs."""
    total_files: int
    successful: int
    failed: int
    results: List[FileResult]
