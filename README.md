# Initialize and activate Virtual Environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 1. Scraper Usage (`scraper.py`)

Downloads raw PDF circulars from the RBI RSS feed.

```bash
# Process the latest 5 circulars (saved to ./downloaded_pdfs/)
python scraper.py --limit 5

# Options:
#  --limit <int>       Number of notifications to process
#  --output-dir <path> Custom folder to save PDFs
#  --metadata <path>   JSON file tracking download states
#  --dry-run           Locates PDF links without downloading
```

---

## 2. Parser CLI Usage (`parser/`)

Parses PDF circulars into structured JSON files (metadata, sections, amendments, and tables).

```bash
# Parse a single PDF (outputs to data/processed/)
python -m parser.main "downloaded_pdfs/circular.pdf"

# Parse an entire folder
python -m parser.main downloaded_pdfs/

# Parse files matching a pattern, extract tables only, and output to a custom directory
python -m parser.main "downloaded_pdfs/*Financial Statements*.pdf" -s tables -o data/custom_processed

# Options:
#  -s, --section       Extract specific key: metadata, content, sections, amendments, tables, full (default)
#  -o, --output-dir    Custom output directory for JSONs (default: data/processed)
#  -v, --verbose       Enable verbose logging
```

---


