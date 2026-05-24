#!/usr/bin/env python3
"""
RBI Circulars and Notifications Scraper
Designed for the Agentic Regulatory Intelligence & Compliance Platform (Hackathon)

Features:
- RSS parsing from the official notifications XML feed.
- Targeted HTML parsing to extract absolute PDF links from individual notification pages.
- Robust HTTP headers and User-Agent rotating/spoofing to bypass bot-detection algorithms.
- Rate limiting and polite delays to prevent IP bans.
- File-based metadata storage (metadata.json) to track processed notifications and avoid redundant scraping.
- Custom CLI configuration options.
"""

import os
import re
import sys
import json
import time
import random
import logging
import argparse
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

import requests
import feedparser
from bs4 import BeautifulSoup

# Define absolute paths where necessary or keep relative to root
DEFAULT_OUTPUT_DIR = "./downloaded_pdfs"
DEFAULT_METADATA_FILE = "./metadata.json"
DEFAULT_RSS_URL = "https://www.rbi.org.in/notifications_rss.xml"

# List of modern browser User-Agents to prevent bot detection
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
]

def setup_logging():
    """Sets up unified logging to stdout and log file."""
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("scraper.log", encoding="utf-8")
        ]
    )

def normalize_url(url: Optional[str]) -> Optional[str]:
    """Normalizes the RBI URLs to force HTTPS and correct directory casing."""
    if not url:
        return url
    # Replace http:// with https://
    url = url.replace("http://", "https://")
    # Replace /scripts/ with /Scripts/
    url = url.replace("/scripts/", "/Scripts/")
    return url

class RBIScraper:
    def __init__(self, output_dir: str, metadata_file: str, limit: int = 5, dry_run: bool = False):
        self.output_dir = output_dir
        self.metadata_file = metadata_file
        self.limit = limit
        self.dry_run = dry_run
        
        # Ensure output directory exists
        if not self.dry_run:
            os.makedirs(self.output_dir, exist_ok=True)
            
        self.session = self._initialize_session()
        self.metadata = self._load_metadata()

    def _initialize_session(self) -> requests.Session:
        """Creates a session with realistic browser headers and configuration."""
        session = requests.Session()
        
        # Choose a random User-Agent from our rotating pool
        ua = random.choice(USER_AGENTS)
        
        session.headers.update({
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.rbi.org.in/",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0"
        })
        return session

    def _load_metadata(self) -> Dict[str, Dict]:
        """Loads already-processed notifications metadata to avoid duplicates."""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error loading metadata file: {e}. Starting fresh.")
        return {}

    def _save_metadata(self):
        """Saves current state metadata back to disk."""
        if self.dry_run:
            return
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=4, ensure_ascii=False)
            logging.info("Saved progress metadata successfully.")
        except Exception as e:
            logging.error(f"Failed to save metadata: {e}")

    def _polite_sleep(self, min_sec=2, max_sec=5):
        """Sleeps for a random duration to mimic natural human reading/browsing behavior."""
        sleep_time = random.uniform(min_sec, max_sec)
        logging.debug(f"Sleeping for {sleep_time:.2f} seconds to be polite...")
        time.sleep(sleep_time)

    def fetch_rss_notifications(self, rss_url: str) -> List[Dict]:
        """Fetches and parses the official RBI RSS XML feed."""
        logging.info(f"Fetching RSS feed from: {rss_url}")
        
        try:
            # We fetch using our session to ensure proper headers are used even for RSS
            response = self.session.get(rss_url, timeout=15)
            response.raise_for_status()
            
            # Parse feed XML content
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                logging.warning("The RSS feed returned a XML parsing warning (Bozo). Proceeding anyway.")
                
            entries = feed.entries
            logging.info(f"Successfully found {len(entries)} items in the RSS feed.")
            return entries
            
        except Exception as e:
            logging.error(f"Failed to retrieve or parse RSS feed: {e}")
            return []

    def extract_pdf_url(self, page_url: str) -> Optional[str]:
        """
        Fetches an individual notification's details page,
        parses the HTML, and extracts the absolute URL of the PDF version.
        """
        logging.info(f"Extracting PDF link from details page: {page_url}")
        
        # Polite sleep before fetching detail page to prevent rate-limit
        self._polite_sleep(1, 3)
        
        retries = 3
        backoff = 2
        for attempt in range(retries):
            try:
                response = self.session.get(page_url, timeout=15)
                
                # Check for rate-limiting status codes (e.g. HTTP 429)
                if response.status_code == 429:
                    wait_time = backoff ** (attempt + 1) + random.uniform(1, 3)
                    logging.warning(f"HTTP 429 (Rate Limited) on {page_url}. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                    
                response.raise_for_status()
                break
            except Exception as e:
                if attempt == retries - 1:
                    logging.error(f"Failed to fetch notification page after {retries} attempts: {e}")
                    return None
                wait_time = backoff ** (attempt + 1)
                logging.warning(f"Error fetching page {page_url}: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Look for explicit .pdf links (most reliable)
        pdf_anchors = soup.find_all('a', href=re.compile(r'\.pdf', re.IGNORECASE))
        
        # 2. If no .pdf links, check anchors with "PDF" text or "Adobe Acrobat"
        if not pdf_anchors:
            for anchor in soup.find_all('a'):
                text = anchor.get_text(strip=True).lower()
                href = anchor.get('href', '')
                if href and ("pdf" in text or "acrobat" in text or "circular" in text):
                    pdf_anchors.append(anchor)
                    
        # 3. Clean up and resolve absolute links
        for anchor in pdf_anchors:
            href = anchor.get('href')
            if not href:
                continue
                
            # Filter out external PDF sharing platforms if any exist
            if any(domain in href.lower() for domain in ["facebook", "twitter", "linkedin"]):
                continue
                
            absolute_pdf_url = urljoin(page_url, href)
            logging.info(f"Found PDF URL candidate: {absolute_pdf_url}")
            return absolute_pdf_url
            
        logging.warning(f"No PDF link found on notification page: {page_url}")
        return None

    def download_pdf(self, pdf_url: str, title: str, entry_id: str) -> bool:
        """Downloads a PDF file politely with connection session and chunk streaming."""
        sanitized_title = re.sub(r'[\\/*?:"<>|]', "_", title)[:100]  # Prevent invalid filename chars and truncate
        filename = f"{sanitized_title}.pdf"
        dest_filepath = os.path.join(self.output_dir, filename)
        
        logging.info(f"Downloading PDF: {filename} from {pdf_url}")
        
        if self.dry_run:
            logging.info(f"[DRY-RUN] Would download to: {dest_filepath}")
            return True
            
        self._polite_sleep(2, 5)
        
        retries = 3
        backoff = 2
        for attempt in range(retries):
            try:
                response = self.session.get(pdf_url, stream=True, timeout=30)
                
                # Check for rate-limiting
                if response.status_code == 429:
                    wait_time = backoff ** (attempt + 1) + random.uniform(1, 3)
                    logging.warning(f"HTTP 429 (Rate Limited) on {pdf_url}. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                    
                response.raise_for_status()
                
                # Download chunk by chunk
                with open(dest_filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            
                logging.info(f"Successfully downloaded and saved: {dest_filepath}")
                return True
                
            except Exception as e:
                if attempt == retries - 1:
                    logging.error(f"Failed to download PDF {pdf_url} after {retries} attempts: {e}")
                    if os.path.exists(dest_filepath):
                        os.remove(dest_filepath) # Clean up partial download
                    return False
                wait_time = backoff ** (attempt + 1)
                logging.warning(f"Error downloading PDF: {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
                
        return False

    def run(self, rss_url: str):
        """Orchestrates the entire scraping lifecycle."""
        entries = self.fetch_rss_notifications(rss_url)
        if not entries:
            logging.warning("No entries fetched. Scraping finished.")
            return

        processed_count = 0
        new_downloads = 0
        
        for entry in entries:
            if processed_count >= self.limit:
                logging.info(f"Reached the limit of {self.limit} notifications. Stopping.")
                break

            entry_id = entry.get('id') or entry.get('link')
            if not entry_id:
                continue

            title = entry.get('title', 'untitled_circular')
            sanitized_title = re.sub(r'[\\/*?:"<>|]', "_", title)[:100]
            published_date = entry.get('published', '')
            page_url = normalize_url(entry.get('link'))
            
            processed_count += 1
            logging.info(f"\n--- Processing Notification {processed_count}: {title} ---")
            
            # Check if already processed
            if entry_id in self.metadata and self.metadata[entry_id].get('downloaded', False):
                logging.info(f"Notification already downloaded previously. Skipping.")
                continue

            if not page_url:
                logging.warning("No detail page URL found for entry. Skipping.")
                continue

            # Extract absolute PDF URL from page
            pdf_url = normalize_url(self.extract_pdf_url(page_url))
            
            if not pdf_url:
                logging.warning(f"Could not locate PDF for circular. Skipping download.")
                # Record that we attempted but failed so we don't spam requests to it again
                self.metadata[entry_id] = {
                    "title": title,
                    "published": published_date,
                    "page_url": page_url,
                    "pdf_url": None,
                    "downloaded": False,
                    "timestamp": time.time(),
                    "status": "failed_pdf_extraction"
                }
                self._save_metadata()
                continue

            # Download the PDF file
            success = self.download_pdf(pdf_url, title, entry_id)
            
            if success:
                new_downloads += 1
                self.metadata[entry_id] = {
                    "title": title,
                    "published": published_date,
                    "page_url": page_url,
                    "pdf_url": pdf_url,
                    "downloaded": True,
                    "timestamp": time.time(),
                    "status": "success",
                    "file_path": os.path.join(self.output_dir, f"{sanitized_title}.pdf")
                }
            else:
                self.metadata[entry_id] = {
                    "title": title,
                    "published": published_date,
                    "page_url": page_url,
                    "pdf_url": pdf_url,
                    "downloaded": False,
                    "timestamp": time.time(),
                    "status": "download_failed"
                }
                
            self._save_metadata()
            
        logging.info(f"\n==========================================")
        logging.info(f"Scraping Completed. Processed: {processed_count}, Newly Downloaded: {new_downloads}")
        logging.info(f"==========================================")

def main():
    setup_logging()
    
    parser = argparse.ArgumentParser(description="RBI Circulars and Notices PDF Scraper.")
    parser.add_argument("--rss-url", type=str, default=DEFAULT_RSS_URL, help="The RSS feed URL to monitor.")
    parser.add_argument("--output-dir", type=str, default=DEFAULT_OUTPUT_DIR, help="Directory to save downloaded PDFs.")
    parser.add_argument("--metadata", type=str, default=DEFAULT_METADATA_FILE, help="Path to JSON file to keep state metadata.")
    parser.add_argument("--limit", type=int, default=5, help="Limit number of feed entries to process.")
    parser.add_argument("--dry-run", action="store_true", help="Find feed notifications and PDF links without downloading.")
    
    args = parser.parse_args()
    
    logging.info("Starting RBI Circular and Notification Scraper...")
    logging.info(f"Settings: Limit={args.limit}, Output={args.output_dir}, Metadata={args.metadata}, DryRun={args.dry_run}")
    
    scraper = RBIScraper(
        output_dir=args.output_dir,
        metadata_file=args.metadata,
        limit=args.limit,
        dry_run=args.dry_run
    )
    
    scraper.run(args.rss_url)

if __name__ == "__main__":
    main()
