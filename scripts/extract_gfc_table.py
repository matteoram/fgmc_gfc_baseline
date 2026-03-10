"""
This script extracts the table for the "Guyana Forestry Commission" from
the "Volume 1" budget estimate PDFs using the 'camelot' library.

It performs the following steps:
1.  Finds all relevant 'Volume1' or 'Volume_1' PDF files in the 'sources' directory.
2.  For each PDF, it uses 'pdfplumber' to efficiently find the page containing
    "Statutory Body: Guyana Forestry Commission".
3.  It then uses 'camelot' with its "stream" algorithm to robustly extract
    the complex, whitespace-separated table from that page.
4.  The extracted table is cleaned and saved as a CSV file in the
    'analysis/gfc_tables_csv' directory.

Required libraries & dependencies:
1.  System-level: 'ghostscript' (e.g., 'brew install ghostscript' on macOS).
2.  Python: 'camelot-py[cv]' and 'pandas'
    - Install using: pip install "camelot-py[cv]" pandas
"""

import pdfplumber
import camelot
import pandas as pd
from pathlib import Path
import re

try:
    from path_manager import get_project_paths
except ImportError:
    print("Error: Could not import 'get_project_paths' from 'path_manager.py'.")
    print("Please ensure 'path_manager.py' is in the same directory as this script.")
    exit(1)

def find_and_extract_gfc_table(pdf_path, output_dir):
    """
    Finds the correct page using pdfplumber, then extracts the table using camelot.
    """
    print(f"Processing: {pdf_path.name}")
    target_text = "Statutory Body: Guyana Forestry Commission"
    found_page = -1

    # Step 1: Use pdfplumber to find the page number efficiently
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text(x_tolerance=2)
            if page_text and target_text in page_text:
                print(f"  Found target text on page {i + 1}.")
                found_page = i + 1
                break
    
    if found_page == -1:
        print(f"  - Could not find the target text '{target_text}' in this PDF.")
        return

    # Step 2: Use camelot with the "stream" flavor on the specific page
    try:
        # Camelot uses 1-based page numbers, so 'found_page' is correct.
        tables = camelot.read_pdf(str(pdf_path), pages=str(found_page), flavor='stream')
        
        if not tables:
            print(f"  - Warning: Camelot found the page but could not extract any tables.")
            return
            
        print(f"  - Camelot extracted {tables.n} table(s) from the page.")
        # Assume the first table found is the one we want
        df = tables[0].df

        # --- Clean and structure the extracted data ---
        # Replace empty strings with NaN and then drop rows/cols
        # where all elements are NaN
        df.replace({None: pd.NA, '': pd.NA}, inplace=True)
        df.dropna(how='all', axis=0, inplace=True) # Drop empty rows
        df.dropna(how='all', axis=1, inplace=True) # Drop empty columns

        # --- Save the result to a CSV file ---
        output_filename = f"{pdf_path.stem}.csv"
        output_path = output_dir / output_filename
        df.to_csv(output_path, index=False, header=False) # Camelot often gets headers right
        
        print(f"  - Successfully extracted table and saved to {output_path}")

    except Exception as e:
        print(f"  - An error occurred during Camelot extraction: {e}")


def main():
    """
    Main function to orchestrate the PDF processing.
    """
    paths = get_project_paths()
    sources_dir = paths.get('sources')
    analysis_dir = paths.get('analysis')

    if not sources_dir or not analysis_dir:
        print("Error: Could not resolve 'sources' or 'analysis' directories from path_manager.")
        return

    output_csv_dir = analysis_dir / "gfc_tables_csv"
    output_csv_dir.mkdir(exist_ok=True)
    
    print(f"Searching for PDF files in: {sources_dir}")
    
    pdf_pattern = re.compile(r"Volume[_]?1.*\.pdf", re.IGNORECASE)
    pdf_files = [p for p in sources_dir.rglob('*.pdf') if pdf_pattern.search(p.name)]

    if not pdf_files:
        print("No relevant 'Volume1' PDF files found.")
        return
        
    print(f"Found {len(pdf_files)} PDF files to process.")
    for pdf_file in pdf_files:
        find_and_extract_gfc_table(pdf_file, output_csv_dir)
    
    print("\nProcessing complete.")


if __name__ == "__main__":
    main()