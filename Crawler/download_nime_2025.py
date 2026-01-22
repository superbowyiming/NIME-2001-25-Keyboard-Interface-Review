import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# --- Configuration ---
# 1. Set the year to download
TARGET_YEAR = 2025

# 2. Set the save path (directory)
#    - Direct path or relative path
SAVE_BASE_PATH = "E:\\" 
# --- End of Configuration ---


# Paper portal and website root index
PAPERS_URL = "https://nime.org/papers/"
BASE_URL = "https://nime.org/"

def download_nime_papers():
    """
    Accesses the NIME paper portal and downloads all PDF papers for the specified year.
    """
    # Construct final save directory name
    save_dir_name = f"NIME_{TARGET_YEAR}_Papers"
    final_save_dir = os.path.join(SAVE_BASE_PATH, save_dir_name)

    # 1. Create local save directory
    try:
        if not os.path.exists(final_save_dir):
            os.makedirs(final_save_dir)
            print(f"Successfully created directory: {final_save_dir}")
        else:
            print(f"Directory already exists: {final_save_dir}")
    except OSError as e:
        print(f"Error: Could not create directory {final_save_dir}.")
        print(f"Please check if '{SAVE_BASE_PATH}' exists and has write permissions. Error: {e}")
        return

    # 2. Access the single paper listing page
    try:
        print(f"Accessing paper portal: {PAPERS_URL}")
        response = requests.get(PAPERS_URL, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Network error or request failed: {e}")
        return

    # 3. Parse HTML and filter links using BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    pdf_links = []
    # Find all <a> tags
    for link in soup.find_all('a', href=True):
        href = link['href']
        # Key filtering logic:
        # 1. Link path must contain the target year (e.g., "/2025/")
        # 2. Link must end with ".pdf"
        if f"/{TARGET_YEAR}/" in href and href.lower().endswith('.pdf'):
            # Convert relative links (e.g., /proceedings/2024/paper.pdf) to absolute URLs
            full_pdf_url = urljoin(BASE_URL, href)
            if full_pdf_url not in pdf_links: # Avoid duplicates
                pdf_links.append(full_pdf_url)

    # 4. Check if papers were found
    if not pdf_links:
        print(f"\nNo {TARGET_YEAR} papers found on the portal.")
        print("This likely means papers for this year haven't been released yet. Please run this script after release.")
        return

    print(f"\nSuccessfully found {len(pdf_links)} papers for {TARGET_YEAR}. Starting download...")

    # 5. Iterate and download found PDF files
    for i, pdf_url in enumerate(pdf_links):
        # Extract filename from URL
        filename = os.path.basename(pdf_url)
        save_path = os.path.join(final_save_dir, filename)

        # Check if file exists for resuming/skipping
        if os.path.exists(save_path):
            print(f"({i+1}/{len(pdf_links)}) File already exists, skipping: {filename}")
            continue

        try:
            print(f"({i+1}/{len(pdf_links)}) Downloading: {filename} ...")
            pdf_response = requests.get(pdf_url, stream=True, timeout=60)
            pdf_response.raise_for_status()

            with open(save_path, 'wb') as f:
                for chunk in pdf_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"  -> Download complete: {filename}")

        except requests.exceptions.RequestException as e:
            print(f"  -> Download failed: {filename}, Error: {e}")
            if os.path.exists(save_path):
                os.remove(save_path) # Cleanup incomplete file

    print(f"\nAll {TARGET_YEAR} downloads completed! Files are saved in: {final_save_dir}")

if __name__ == "__main__":
    download_nime_papers()
