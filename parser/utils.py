import os
import json
from pathlib import Path
import logging

def get_project_root() -> Path:
    """Returns the project root directory (hackathon directory)."""
    return Path(__file__).resolve().parents[1]

def get_processed_dir() -> Path:
    """Returns the data/processed directory path and ensures it exists."""
    root = get_project_root()
    processed = root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    return processed

def load_scraper_metadata() -> dict:
    """Loads the metadata.json file created by the scraper if it exists."""
    root = get_project_root()
    metadata_path = root / "metadata.json"
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logging.warning(f"Could not load scraper metadata: {e}")
    return {}
