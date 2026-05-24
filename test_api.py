"""Quick test script for the PDF parsing API."""
import requests
import os
import json

API_URL = "http://localhost:8000"

# 1. Health check
print("=" * 60)
print("TEST 1: Health Check")
print("=" * 60)
r = requests.get(f"{API_URL}/health")
print(f"Status: {r.status_code}")
print(f"Body:   {r.json()}")

# 2. Parse real PDFs
print("\n" + "=" * 60)
print("TEST 2: Parse Multiple PDFs")
print("=" * 60)

pdf_dir = "downloaded_pdfs"
pdfs = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")][:2]
print(f"Uploading {len(pdfs)} PDF(s):")
for p in pdfs:
    print(f"  - {p}")

files = []
for p in pdfs:
    path = os.path.join(pdf_dir, p)
    files.append(("files", (p, open(path, "rb"), "application/pdf")))

r = requests.post(f"{API_URL}/api/v1/parse", files=files, params={"section": "full"})
print(f"\nHTTP Status: {r.status_code}")

data = r.json()
print(f"total_files: {data['total_files']}")
print(f"successful:  {data['successful']}")
print(f"failed:      {data['failed']}")

for result in data["results"]:
    fn = result["filename"]
    st = result["status"]
    print(f"\n--- {fn[:70]} ---")
    print(f"  status: {st}")
    if result["data"]:
        d = result["data"]
        meta = d["metadata"]
        title = (meta["title"] or "N/A")[:80]
        print(f"  title:       {title}")
        print(f"  date:        {meta['date']}")
        print(f"  rbi_id:      {meta['rbi_id']}")
        print(f"  signatory:   {meta['signatory_name']}")
        print(f"  sections:    {len(d['sections'])}")
        print(f"  amendments:  {len(d['amendments'])}")
        print(f"  tables:      {len(d['tables'])}")
        print(f"  clean_text:  {len(d['content']['clean_text'])} chars")
    if result["error"]:
        print(f"  error: {result['error']}")

# 3. Test validation — non-PDF file
print("\n" + "=" * 60)
print("TEST 3: Validation - Non-PDF File")
print("=" * 60)
fake_files = [("files", ("readme.txt", b"this is not a pdf", "text/plain"))]
r = requests.post(f"{API_URL}/api/v1/parse", files=fake_files)
print(f"HTTP Status: {r.status_code}")
print(f"Body: {json.dumps(r.json(), indent=2)}")

# 4. Test validation — invalid section
print("\n" + "=" * 60)
print("TEST 4: Validation - Invalid Section")
print("=" * 60)
r = requests.post(
    f"{API_URL}/api/v1/parse",
    files=[("files", ("test.pdf", b"%PDF-fake", "application/pdf"))],
    params={"section": "invalid_section"},
)
print(f"HTTP Status: {r.status_code}")
print(f"Body: {json.dumps(r.json(), indent=2)}")

# 5. Test section filter - metadata only
print("\n" + "=" * 60)
print("TEST 5: Section Filter - metadata only")
print("=" * 60)
one_pdf = pdfs[0]
one_file = [("files", (one_pdf, open(os.path.join(pdf_dir, one_pdf), "rb"), "application/pdf"))]
r = requests.post(f"{API_URL}/api/v1/parse", files=one_file, params={"section": "metadata"})
print(f"HTTP Status: {r.status_code}")
result = r.json()["results"][0]
print(f"Has metadata: {'metadata' in (result['data'] or {})}")
print(f"Keys in data: {list((result['data'] or {}).keys())}")

print("\n" + "=" * 60)
print("ALL TESTS COMPLETE")
print("=" * 60)
