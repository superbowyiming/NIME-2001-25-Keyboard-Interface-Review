# extract_keyboard_pdfs_to_txt.py
import os
import sys
from pathlib import Path
from typing import List

try:
    from pypdf import PdfReader
except ImportError:
    print("pypdf is required.")
    print("Install with: pip install pypdf")
    sys.exit(1)

# tqdm removed to avoid extra dependencies

# Paths
SOURCE_DIR = os.path.join(
    os.getcwd(), 
    "Metadata_Filtered_Results", 
    "Keyword_Match", 
    "Keyboard_Interface_Related"
)
OUTPUT_DIR = os.path.join(os.getcwd(), "Keyboard_Interface_Texts")

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using pypdf."""
    try:
        reader = PdfReader(pdf_path)
        text_content = []
        for page in reader.pages:
            try:
                # extract_text() usually handles the 2013 spacing issue better than pdfminer
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
            except Exception as page_err:
                # If one page fails, continue to next
                continue
        return "\n".join(text_content)
    except Exception as e:
        print(f"  Warning: Failed to extract text from {os.path.basename(pdf_path)}: {e}")
        return ""

def collect_all_pdfs(root_dir: str) -> List[tuple]:
    """Recursively collect all PDFs from root directory and subdirectories.
    Returns list of (full_path, filename) tuples.
    """
    pdfs = []
    if not os.path.isdir(root_dir):
        return pdfs
    
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.lower().endswith('.pdf'):
                full_path = os.path.join(root, file)
                pdfs.append((full_path, file))
    
    return pdfs

def main():
    # Check source directory exists
    if not os.path.isdir(SOURCE_DIR):
        print(f"Error: Source directory not found: {SOURCE_DIR}")
        print("Please run filter_renamed_pdfs_combined.py first.")
        sys.exit(1)
    
    # Create output directory
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {OUTPUT_DIR}\n")
    
    # Collect all PDFs
    print(f"Collecting PDFs from {SOURCE_DIR}...")
    all_pdfs = collect_all_pdfs(SOURCE_DIR)
    
    if not all_pdfs:
        print(f"No PDFs found in {SOURCE_DIR}")
        sys.exit(0)
    
    print(f"Found {len(all_pdfs)} PDFs to convert\n")
    
    # Process each PDF
    success_count = 0
    failed_count = 0
    
    print("Extracting text from PDFs...")
    for i, (pdf_path, pdf_name) in enumerate(all_pdfs):
        # Simple progress tracking without tqdm
        if i % 50 == 0:
            print(f"  Processing {i}/{len(all_pdfs)}...")
            
        # Generate output filename (replace .pdf with .txt)
        txt_name = pdf_name[:-4] + ".txt" if pdf_name.lower().endswith('.pdf') else pdf_name + ".txt"
        txt_path = os.path.join(OUTPUT_DIR, txt_name)
        
        # Extract text
        text = extract_text_from_pdf(pdf_path)
        
        if text:
            try:
                # Write to text file
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                success_count += 1
            except Exception as e:
                print(f"  Error writing {txt_name}: {e}")
                failed_count += 1
        else:
            # Empty text - still create file but note it
            try:
                with open(txt_path, 'w', encoding='utf-8') as f:
                    f.write("")
                failed_count += 1
            except Exception as e:
                print(f"  Error writing {txt_name}: {e}")
                failed_count += 1
    
    # Print summary
    print("\n" + "="*70)
    print("EXTRACTION SUMMARY")
    print("="*70)
    print(f"Total PDFs processed:           {len(all_pdfs)}")
    print(f"Successfully extracted:         {success_count}")
    print(f"Failed or empty:                {failed_count}")
    print(f"\nOutput directory: {OUTPUT_DIR}")
    print("="*70)

if __name__ == "__main__":
    main()
