import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
from path_manager import get_project_paths

def download_volume1_pdfs(base_url, max_pages=10):
    """
    Searches for 'BudgetEstimates_2026_Volume1.pdf' (case-insensitively)
    across paginated results. If found, it downloads that file and all other
    PDFs from the same page containing 'Volume1' or 'Volume_1' in their name.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    paths = get_project_paths()
    output_dir = paths.get('sources')
    if not output_dir:
        print("Error: 'sources' path not found in path_manager. Exiting.")
        return
    
    output_dir.mkdir(exist_ok=True)
    print(f"Files will be saved to: {output_dir.resolve()}")

    target_file = 'BudgetEstimates_2026_Volume1.pdf'.lower()
    target_found_and_processed = False

    print(f"Starting case-insensitive search for '{target_file}'...")
    for page_num in range(1, max_pages + 1):
        if page_num == 1:
            page_url = base_url
        else:
            page_url = f"{base_url.rstrip('/')}/page/{page_num}/"
        
        print(f"Accessing {page_url}...")
        try:
            response = requests.get(page_url, headers=headers)
            if response.status_code == 404:
                print(f"Page {page_num} not found. Ending search.")
                break
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Could not access {page_url}. Error: {e}")
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        page_links = soup.find_all('a', href=True)
        
        if not page_links and page_num > 1:
            print(f"No links found on page {page_num}, assuming it's the end.")
            break

        # Check if the target file exists on this page (case-insensitively)
        target_link_on_page = None
        for link in page_links:
            # Extract filename from URL for a more reliable check
            filename_in_link = link['href'].split('/')[-1].lower()
            if filename_in_link == target_file:
                target_link_on_page = link
                break
        
        # If target is found, process this page and stop
        if target_link_on_page:
            print(f"Found '{target_file}' on page {page_num}. Downloading relevant files from this page.")
            target_found_and_processed = True
            processed_urls = set()
            downloaded_count = 0

            # Download all relevant PDFs from this specific page
            for link in page_links:
                href_lower = link['href'].lower()
                # Check for Volume1 or Volume_1 and ensure it's a PDF link
                if ('volume1' in href_lower or 'volume_1' in href_lower) and href_lower.endswith('.pdf'):
                    full_url = urljoin(page_url, link['href'])
                    if full_url in processed_urls:
                        continue
                    try:
                        download_file(full_url, output_dir, headers)
                        processed_urls.add(full_url)
                        downloaded_count += 1
                    except requests.RequestException as e:
                        filename = full_url.split("/")[-1]
                        print(f"Failed to download {filename}: {e}")
            
            print(f"\nDownload process complete. Total files downloaded: {downloaded_count}")
            break # Exit the pagination loop

    if not target_found_and_processed:
        print(f"\nCould not find the target file '{target_file}' within the first {max_pages} pages. No files were downloaded.")

def download_file(url, save_dir, headers):
    """Downloads a single file from a URL to a specified directory."""
    filename = url.split("/")[-1]
    # Clean filename to handle potential query strings, though unlikely for PDFs
    clean_filename = filename.split('?')[0]
    save_path = save_dir / clean_filename
    
    if save_path.exists():
        print(f"Skipping: {clean_filename} (already exists)")
        return

    print(f"Downloading: {clean_filename}")
    file_response = requests.get(url, headers=headers)
    file_response.raise_for_status()
    save_path.write_bytes(file_response.content)

if __name__ == "__main__":
    TARGET_URL = "https://finance.gov.gy/budget/budget-estimates/"
    download_volume1_pdfs(TARGET_URL)
