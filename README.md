# Agentic Regulatory Intelligence

Agentic Regulatory Intelligence is an enterprise-grade platform designed to automate the intake, parsing, structured analysis, and operational routing of complex financial regulations. The system monitors live RSS feeds from regulators such as the Reserve Bank of India (RBI), downloads publication documents, parses highly complex PDF layouts (including tables, signature blocks, and multi-level sections), and employs advanced LLM mapping layers to convert raw text into concrete, measurable compliance requirements.

Deployed Application: https://agentic-regulator.vercel.app

---

## Architecture Overview

The platform uses a modular, service-oriented architecture designed to handle concurrent processing, heavy text extraction, and modern state visualization.

```
+--------------------+
|  RBI / Regulatory  |
|      RSS Feed      |
+---------+----------+
          |
          v
+--------------------+
| Scraper (Python)   |
+---------+----------+
          |
          v
+--------------------+      +-----------------------+
|  Local PDFs Folder | ---> | Parser Pipeline (Fitz) |
+--------------------+      +-----------+-----------+
                                        |
                                        v
+--------------------+      +-----------------------+
| Next.js Frontend   | ---> |  FastAPI Parser API   |
+---------+----------+      +-----------------------+
          |
          v (OpenAI GPT JSON Schema Extraction)
+--------------------+
| PostgreSQL via DB  |
+--------------------+
```

### 1. Scraper Service (Python)
- Automatically monitors specified RSS and HTTP endpoints of regulatory bodies.
- Resolves complex publication endpoints and downloads official PDF circulars.
- Maintains localized metadata history to track processed publications and prevent duplicate workloads.

### 2. PDF Parser Engine (Python)
- Text and Metadata Extraction: Extracts raw text while maintaining multi-level clause nesting and document structural hierarchies.
- Table Extraction: Detects and isolates embedded tables and structured financial schedules from the PDF flow.
- Signatory Extraction: Identifies signatory details, dates, and official designations.

### 3. Parser API (FastAPI)
- Provides a fast, asynchronous REST API (`/api/v1/parse`) for multi-document batch uploads and concurrent text extractions.
- Isolates extraction workloads from the application server, improving parallel task execution.

### 4. Next.js Web Application (React & Tailwind CSS)
- AI Extraction Layer: Interfaces with OpenAI's structured outputs using a strict JSON schema to perform deep regulatory mapping.
- Dashboard Interface: Visualizes regulatory documents, risk severities, compliance timelines, and action metrics.
- Measurable Action Points (MAPs): Dynamically extracts and visualizes action steps, mapping assignments to concrete bank departments (e.g., Compliance, IT, Risk, Legal).
- Validation Rules Engine: Defines automated validation checks and success criteria utilized by independent validation agents.

### 5. Persistent Storage Layer (PostgreSQL & Prisma)
- Models complex relational structures between regulatory documents, compliance requirements, impacted departments, measurable action points, and active validation rules.

---

## Database Schema Model

The database represents a deep regulatory relational structure:

- **RegulatoryDocument**: Core document structure storing title, reference numbers, published dates, risk severities, and AI auditor confidence metrics.
- **ComplianceRequirement**: Concrete, clause-level requirements extracted from the directive.
- **ImpactedDepartment**: Map of internal institutional units affected by the regulatory update along with specific impact rationale.
- **MeasurableActionPoint (MAP)**: Specific action-oriented tasks containing assigned departments, priority tags, concrete deadlines, and list of required verification evidence.
- **ValidationRule**: Targeted rules used by checking agents to programmatically evaluate if a bank meets compliance metrics.

---

## Directory Structure

```
.
├── api/                   # FastAPI Server backend code and route registry
├── parser/                # Core PDF parsing, clause, and table extraction modules
├── frontend/              # Next.js 16 web application codebase
│   ├── app/               # Next.js App Router (pages and API routing)
│   ├── components/        # Shared shadcn/UI components
│   ├── prisma/            # Database configurations and migrations
│   └── lib/               # Prisma client utilities
├── downloaded_pdfs/       # Destination folder for raw regulatory downloads
├── scraper.py             # RSS crawler script
├── run_api.py             # Main entry point for the FastAPI server
├── requirements.txt       # Python backend dependencies
└── README.md              # Main system documentation
```

---

## Installation and Setup

To run the entire system locally, configure both the Python parser service and the Next.js frontend client.

### Prerequisites
- Python 3.10 or higher
- Node.js 18 or higher
- PostgreSQL instance running locally or via cloud host (e.g., Supabase)

### Backend Services Setup

1. Create and activate a Virtual Environment in the project root:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

2. Install python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the FastAPI Parser API server:
   ```bash
   python run_api.py
   ```
   The API server will launch at `http://localhost:8000`. You can inspect the interactive documentation at `http://localhost:8000/docs`.

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node.js dependencies:
   ```bash
   npm install
   ```

3. Set up environment variables:
   Create a `.env` file in the `frontend` folder containing the following configurations:
   ```env
   DATABASE_URL="postgresql://username:password@host:port/database?sslmode=require"
   OPENAI_API_KEY="your-openai-api-key"
   PYTHON_API_URL="http://localhost:8000"
   ```

4. Initialize the Prisma client and push the schema structure to your database:
   ```bash
   npx prisma db push
   ```

5. Launch the Next.js local development server:
   ```bash
   npm run dev
   ```
   Open `http://localhost:3000` in your browser.

---

## Script and CLI Usage Reference

### 1. Web Scraper (`scraper.py`)
Collects PDF circulars from the official RBI RSS feed.
```bash
# Process the latest 5 circulars and save to local directory
python scraper.py --limit 5

# Options:
#  --limit <int>       Number of notifications to process
#  --output-dir <path> Custom folder to save PDFs (default: downloaded_pdfs/)
#  --metadata <path>   JSON file tracking download states (default: metadata.json)
#  --dry-run           Locates PDF links without performing downloads
```

### 2. Standalone Parser CLI (`parser/main.py`)
Processes local PDF circulars directly into structured JSON files for offline storage.
```bash
# Parse a single PDF (outputs JSON to data/processed/)
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

### 3. API Verification Script (`test_api.py`)
Quickly verifies the liveness and functional accuracy of your local FastAPI Parser instance.
```bash
# Run parsing test suites
python test_api.py
```
Built with 💝 by Team The-Sopranodes for Sukaksha Cyber Security Hackathon 2026