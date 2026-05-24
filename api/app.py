"""
FastAPI application factory for the RBI Circular PDF Parser API.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from api.routes.parse import router as parse_router


def _setup_logging():
    """Configures structured logging for the API."""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle hook."""
    _setup_logging()
    logger = logging.getLogger("api")
    logger.info("RBI PDF Parser API starting up...")
    yield
    logger.info("RBI PDF Parser API shutting down.")


app = FastAPI(
    title="RBI Circular PDF Parser API",
    description=(
        "Production-ready REST API for parsing RBI circular/notification PDFs "
        "into structured JSON. Supports batch uploads with concurrent processing."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS (configurable via env) ──
allowed_origins = os.getenv("CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routes ──
app.include_router(parse_router)


def custom_openapi():
    """Generate OpenAPI 3.0 docs so Swagger renders file arrays as uploads."""
    if app.openapi_schema:
        return app.openapi_schema

    app.openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        openapi_version="3.0.3",
    )

    for schema in app.openapi_schema.get("components", {}).get("schemas", {}).values():
        for prop in schema.get("properties", {}).values():
            items = prop.get("items", {})
            if items.get("contentMediaType") == "application/octet-stream":
                items.pop("contentMediaType", None)
                items["format"] = "binary"

    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/health", tags=["Health"])
async def health_check():
    """Simple liveness probe."""
    return {"status": "healthy", "service": "rbi-pdf-parser-api"}
