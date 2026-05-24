"""
PDF parsing API routes.
"""

import logging
from typing import Annotated, List, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status

from api.schemas.response import ParseResponse
from api.services.pdf_service import process_pdfs_concurrently

logger = logging.getLogger("api.routes.parse")

router = APIRouter(prefix="/api/v1", tags=["PDF Parsing"])

# Limits — configurable via environment in app.py, but sensible defaults here
MAX_FILES_PER_REQUEST = 20
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB per file

VALID_SECTIONS = {"metadata", "content", "sections", "amendments", "tables", "full"}


@router.post(
    "/parse",
    response_model=ParseResponse,
    summary="Parse multiple RBI circular PDFs",
    description=(
        "Upload one or more PDF files. Each file is validated, parsed concurrently, "
        "and the structured JSON result is returned in the predefined schema."
    ),
    responses={
        200: {"description": "All files parsed successfully."},
        207: {"description": "Partial success — some files failed."},
        400: {"description": "No valid files provided."},
        422: {"description": "Validation error (e.g. invalid section parameter)."},
    },
)
async def parse_pdfs(
    files: Annotated[
        List[UploadFile],
        File(description="One or more PDF files to parse."),
    ],
    section: Annotated[
        Optional[str],
        Query(
            description="Extract specific section: metadata, content, sections, amendments, tables, or full (default)."
        ),
    ] = "full",
):
    """
    Accepts multiple PDF uploads, validates each, and returns a combined
    JSON response in the predefined schema.

    Example cURL:
        curl -X POST http://localhost:8000/api/v1/parse \
          -F "files=@circular1.pdf" \
          -F "files=@circular2.pdf" \
          -F "section=full"
    """
    # ── Validate section parameter ──
    if section and section.strip().lower() not in VALID_SECTIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid section '{section}'. Must be one of: {', '.join(sorted(VALID_SECTIONS))}",
        )
    section_clean = section.strip().lower() if section else "full"

    # ── Validate file count ──
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files uploaded. Provide at least one PDF file.",
        )
    if len(files) > MAX_FILES_PER_REQUEST:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too many files. Maximum {MAX_FILES_PER_REQUEST} files per request.",
        )

    # ── Read and pre-validate uploaded files ──
    validated_files = []
    pre_errors = []

    for upload in files:
        filename = upload.filename or "unknown.pdf"

        # Extension check
        if not filename.lower().endswith(".pdf"):
            pre_errors.append({
                "filename": filename,
                "status": "error",
                "data": None,
                "error": f"File '{filename}' does not have a .pdf extension.",
            })
            continue

        # Read file content
        try:
            content = await upload.read()
        except Exception as exc:
            logger.error("Failed to read upload %s: %s", filename, exc)
            pre_errors.append({
                "filename": filename,
                "status": "error",
                "data": None,
                "error": f"Failed to read uploaded file: {exc}",
            })
            continue

        # Size check
        if len(content) > MAX_FILE_SIZE_BYTES:
            pre_errors.append({
                "filename": filename,
                "status": "error",
                "data": None,
                "error": f"File '{filename}' exceeds maximum size of {MAX_FILE_SIZE_BYTES // (1024*1024)} MB.",
            })
            continue

        validated_files.append((filename, content))

    if not validated_files and pre_errors:
        from fastapi.responses import JSONResponse

        response = ParseResponse(
            total_files=len(pre_errors),
            successful=0,
            failed=len(pre_errors),
            results=pre_errors,
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=response.model_dump(),
        )

    # ── Process valid PDFs concurrently ──
    logger.info(
        "Processing %d valid PDF(s) (section=%s), %d pre-rejected",
        len(validated_files),
        section_clean,
        len(pre_errors),
    )

    parse_results = await process_pdfs_concurrently(
        validated_files, section=section_clean
    )

    # Combine pre-validation errors with parse results
    all_results = pre_errors + parse_results
    successful = sum(1 for r in all_results if r["status"] == "success")
    failed = sum(1 for r in all_results if r["status"] == "error")

    response = ParseResponse(
        total_files=len(all_results),
        successful=successful,
        failed=failed,
        results=all_results,
    )

    # Return appropriate status code
    if failed > 0 and successful > 0:
        # Partial success — FastAPI doesn't natively support 207,
        # so we use Response to set the status code via dependency
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=207,
            content=response.model_dump(),
        )

    if failed > 0 and successful == 0:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=response.model_dump(),
        )

    return response
