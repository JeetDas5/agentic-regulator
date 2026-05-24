import sys
import os
import glob
import logging
import argparse
from typing import List, Optional

# Ensure the parent directory is in python path so parser can be imported if run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser.parser import parse_pdf

def setup_logging(verbose: bool):
    """Configures logging for the CLI tool."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def expand_paths(inputs: List[str]) -> List[str]:
    """
    Expands input patterns (files, directories, glob/wildcard patterns)
    into a sorted list of unique absolute PDF file paths.
    """
    expanded = []
    for pattern in inputs:
        # Check if the pattern is directly a directory
        if os.path.isdir(pattern):
            logging.debug(f"Input is a directory, scanning for PDFs: {pattern}")
            for root, _, files in os.walk(pattern):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        expanded.append(os.path.abspath(os.path.join(root, file)))
        else:
            # Handle glob expansion (e.g. *.pdf, downloaded_pdfs/*.pdf)
            matches = glob.glob(pattern)
            if not matches:
                # If glob returns nothing, assume it's a literal path
                # and let downstream checks handle existence
                expanded.append(os.path.abspath(pattern))
            else:
                for match in matches:
                    if os.path.isdir(match):
                        for root, _, files in os.walk(match):
                            for file in files:
                                if file.lower().endswith('.pdf'):
                                    expanded.append(os.path.abspath(os.path.join(root, file)))
                    elif match.lower().endswith('.pdf') or os.path.isfile(match):
                        expanded.append(os.path.abspath(match))
                        
    # Deduplicate and sort
    return sorted(list(set(expanded)))

def main():
    parser = argparse.ArgumentParser(
        description="RBI PDF Circular & Notification Parser CLI tool. Parses one or more RBI PDFs into structured JSON."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="One or more PDF file paths, directories, or glob patterns (e.g. 'downloaded_pdfs/*.pdf')."
    )
    parser.add_argument(
        "-s", "--section",
        choices=["metadata", "content", "sections", "amendments", "tables", "full"],
        default="full",
        help="Extract only a specific section of the data (default: full)."
    )
    parser.add_argument(
        "-o", "--output-dir",
        help="Optional custom output directory for parsed JSON files. Defaults to project 'data/processed' directory."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose debug logging."
    )
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    logging.debug(f"Parsing inputs: {args.inputs}")
    expanded_files = expand_paths(args.inputs)
    
    if not expanded_files:
        logging.error("No input files resolved. Please verify your file paths or patterns.")
        sys.exit(1)
        
    logging.info(f"Resolved {len(expanded_files)} PDF file(s) for parsing.")
    
    successes = []
    failures = []
    
    for pdf_path in expanded_files:
        if not os.path.exists(pdf_path):
            logging.error(f"File not found: {pdf_path}")
            failures.append((pdf_path, "File not found"))
            continue
            
        logging.info(f"Processing PDF: {pdf_path}")
        try:
            parse_pdf(pdf_path, section=args.section, output_dir=args.output_dir)
            successes.append(pdf_path)
        except Exception as e:
            logging.exception(f"Error parsing {pdf_path}: {e}")
            failures.append((pdf_path, str(e)))
            
    # Print clear, formatted batch processing summary
    print("\n" + "="*60)
    print("RBI PDF PARSING BATCH SUMMARY")
    print("="*60)
    print(f"Total PDFs processed: {len(expanded_files)}")
    print(f"Successes:            {len(successes)}")
    print(f"Failures:             {len(failures)}")
    print("="*60)
    
    if successes:
        print("\nSuccesses:")
        for succ in successes:
            print(f"  [OK] {os.path.basename(succ)}")
            
    if failures:
        print("\nFailures:")
        for fail_path, err in failures:
            print(f"  [ERROR] {os.path.basename(fail_path)}: {err}")
            
    # Exit code behavior: exit with 1 if there were files to parse and all failed,
    # or if we started with files but got 0 successes. Otherwise exit 0.
    if failures and not successes:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()

