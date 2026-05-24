"""
Entrypoint to run the RBI PDF Parser API server.

Usage:
    python run_api.py

Environment variables:
    API_HOST        — Bind address (default: 0.0.0.0)
    API_PORT        — Port number  (default: 8000)
    LOG_LEVEL       — Logging level (default: INFO)
    CORS_ORIGINS    — Comma-separated allowed origins (default: *)
"""

import os
import uvicorn


def main():
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    reload = os.getenv("API_RELOAD", "false").lower() == "true"

    uvicorn.run(
        "api.app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
    )


if __name__ == "__main__":
    main()
