"""
This script extracts the table for the "Guyana Forestry Commission" from
the "Volume 1" budget estimate PDFs.

It performs the following steps:
1.  Finds all relevant 'Volume1' or 'Volume_1' PDF files in the 'sources' directory.
2.  For each PDF, it searches for the page containing the text
    "Statutory Body: Guyana Forestry Commission".
3.  It uses the 'pdfplumber' library to extract the table from that page.
4.  The extracted table is cleaned and saved as a CSV file in the
    'analysis/gfc_tables_csv' directory.

Required libraries:
- pandas
- pdfplumber

Install them using: pip install pandas pdfplumber
"""

import pdfplumber
import pandas as pd
from pathlib import Path
import re

# Assuming path_manager.py is in the same directory
try:
    from path_manager import get_project_paths
except ImportError:
    print("Error: Could not import 'get_project_paths' from 'path_manager.py'.")
    print("Please ensure 'path_manager.py' is in the same directory as this script.")
    exit(1)

def find_and_extract_gfc_table(pdf_path, output_dir):
    """
    Finds and extracts the Guyana Forestry Commission table from a single PDF.
    """
    print(f"Processing: {pdf_path.name}")
    target_text = "Statutory Body: Guyana Forestry Commission"
    
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            # Extract text from the page to find our target
            page_text = page.extract_text(x_tolerance=2)
            
            if page_text and target_text in page_text:
                print(f"  Found target text on page {i + 1}.")
                
                # --- Extract the table from this page ---
                # The settings for table extraction might need tuning if the
                # table structure is very complex (e.g., "vertical_strategy": "lines")
                table = page.extract_table()
                
                if not table:
                    print(f"  - Warning: Found target text but could not extract a table from page {i + 1}.")
                    continue

                # --- Clean and structure the extracted data ---
                # Convert to DataFrame
                df = pd.DataFrame(table)

                # The first row often contains the headers. Let's promote it.
                if not df.empty:
                    df.columns = df.iloc[0]
                    df = df[1:].reset_index(drop=True)

                # Replace None and empty strings with NaN and then drop rows
                # where all elements are NaN (often empty separator rows in tables)
                df.replace({None: pd.NA, '': pd.NA}, inplace=True)
                df.dropna(how='all', inplace=True)

                # --- Save the result to a CSV file ---
                output_filename = f"{pdf_path.stem}.csv"
                output_path = output_dir / output_filename
                df.to_csv(output_path, index=False)
                
                print(f"  - Successfully extracted table and saved to {output_path}")
                return # Stop after finding the first match

    print(f"  - Could not find the target text '{target_text}' in this PDF.")


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

    # Create a specific output directory for the CSVs
    output_csv_dir = analysis_dir / "gfc_tables_csv"
    output_csv_dir.mkdir(exist_ok=True)
    
    print(f"Searching for PDF files in: {sources_dir}")
    
    # Regex to find PDF files with 'Volume1' or 'Volume_1' case-insensitively
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