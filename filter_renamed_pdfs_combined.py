# filter_renamed_pdfs_combined.py
import os
import sys
import csv
import shutil
from pathlib import Path
from typing import Dict, List, Tuple
import re

try:
    from pdfminer.high_level import extract_text
    from pdfminer.layout import LAParams
    import pandas as pd
except ImportError:
    print("pdfminer.six and pandas are required.")
    print("Install with: pip install pdfminer.six pandas")
    sys.exit(1)

from tqdm import tqdm

KEYWORDS = ["Organ", "Keyboard", "Piano", "Clavichord", "Harpsichord", "Accordion", "Interface", "Layout"]
SOURCE_DIR = os.path.join(os.getcwd(), "Renamed_PDFs")
MATCHED_DIR = os.path.join(SOURCE_DIR, "Matched")
UNMATCHED_DIR = os.path.join(SOURCE_DIR, "Unmatched")
OUTPUT_BASE = os.path.join(os.getcwd(), "Metadata_Filtered_Results")
FILTERED_YES_DIR = os.path.join(OUTPUT_BASE, "Keyword_Match")
FILTERED_NO_DIR = os.path.join(OUTPUT_BASE, "No_Keyword_Match")
CSV_NIME = os.path.join(os.getcwd(), "nime_papers.csv")
RESULTS_CSV = os.path.join(OUTPUT_BASE, "filter_results.csv")

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using pdfminer."""
    try:
        text = extract_text(pdf_path, laparams=LAParams())
        return text if text else ""
    except Exception as e:
        print(f"  Warning: Failed to extract text from {os.path.basename(pdf_path)}: {e}")
        return ""

def safe_str(value) -> str:
    """Convert pandas NaN/None to empty string."""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        if value is None:
            return ""
    return str(value)

def normalize(s: str) -> str:
    """Normalize string to lowercase."""
    return (s or "").lower()

def remove_references_section(text: str) -> str:
    """Remove References/Citations section from text.
    
    NIME papers typically use 'References' as the section header,
    except for 2021-2022 which use 'Citations'.
    This function finds the last occurrence of these headers and truncates the text.
    """
    if not text:
        return text
    
    text_lower = text.lower()
    
    # Find last occurrence of 'references' or 'citations' as section header
    # Look for patterns like "References\n" or "REFERENCES" or "Citations\n"
    import re
    
    # Pattern to match section headers (word at start of line or after newline)
    # Match: newline + optional whitespace + References/Citations + optional whitespace + newline
    patterns = [
        r'\n\s*references\s*\n',
        r'\n\s*citations\s*\n',
    ]
    
    last_pos = -1
    for pattern in patterns:
        for match in re.finditer(pattern, text_lower):
            if match.start() > last_pos:
                last_pos = match.start()
    
    if last_pos > 0:
        # Truncate at the start of the References/Citations section
        return text[:last_pos]
    
    return text

def search_keywords_in_text(text: str, keywords: List[str]) -> Tuple[bool, List[str]]:
    """Search for keywords in text (case-insensitive). Returns (found, list_of_found_keywords_lowercase).

    Special-case: match 'organ' only as whole word (organ or organs) to avoid matching 'organization', 'organic', etc.
    """
    t = normalize(text)
    found_keywords = []
    for kw in keywords:
        kw_lower = normalize(kw)
        if kw_lower == "organ":
            # match whole word 'organ' or 'organs'
            if re.search(r"\borgans?\b", t):
                if kw_lower not in found_keywords:
                    found_keywords.append(kw_lower)
        else:
            if kw_lower in t:
                if kw_lower not in found_keywords:
                    found_keywords.append(kw_lower)
    return (len(found_keywords) > 0, found_keywords)

def create_keyword_folder_name(keywords_list: List[str]) -> str:
    """Create folder name from keywords list. e.g., ['organ', 'piano'] -> 'organ_piano'"""
    sorted_kws = sorted(keywords_list)
    return "_".join(sorted_kws)

def extract_id_from_filename(filename: str) -> str:
    """Extract ID from renamed PDF filename."""
    if filename.endswith(".pdf"):
        return filename[:-4]
    return filename

def build_id_to_meta_map(csv_path: str) -> Dict[str, Dict[str, str]]:
    """Build a map from ID -> {title, abstract, keywords} from nime_papers.csv"""
    meta: Dict[str, Dict[str, str]] = {}
    try:
        df = pd.read_csv(csv_path, dtype=str, keep_default_na=False, na_filter=False)
    except Exception as e:
        print(f"Error: Could not read {csv_path}: {e}")
        sys.exit(1)
    
    for _, row in df.iterrows():
        pdf_id = safe_str(row.get("ID")).strip()
        if not pdf_id:
            continue
        meta[pdf_id] = {
            "title": safe_str(row.get("title")),
            "abstract": safe_str(row.get("abstract")),
            "keywords": safe_str(row.get("keywords")),
        }
    return meta

def collect_pdfs_from_folder(folder: str) -> List[Tuple[str, str]]:
    """Collect all PDFs from folder. Returns list of (full_path, filename) tuples."""
    pdfs = []
    if not os.path.isdir(folder):
        return pdfs
    
    for pdf_file in Path(folder).glob("*.pdf"):
        pdfs.append((str(pdf_file), pdf_file.name))
    return pdfs

def main():
    # Create output directories
    Path(OUTPUT_BASE).mkdir(parents=True, exist_ok=True)
    Path(FILTERED_YES_DIR).mkdir(parents=True, exist_ok=True)
    Path(FILTERED_NO_DIR).mkdir(parents=True, exist_ok=True)

    # Ensure parent folder for keyboard/interface/layout-related keyword combos exists
    keyboard_parent = os.path.join(FILTERED_YES_DIR, "Keyboard_Interface_Related")
    Path(keyboard_parent).mkdir(parents=True, exist_ok=True)

    # Load metadata
    print(f"Loading metadata from {CSV_NIME}...")
    id_to_meta = build_id_to_meta_map(CSV_NIME)
    print(f"Loaded metadata for {len(id_to_meta)} papers\n")

    # Collect PDFs
    print("Collecting PDFs from Renamed_PDFs folder...")
    all_pdfs = []
    all_pdfs.extend(collect_pdfs_from_folder(MATCHED_DIR))
    all_pdfs.extend(collect_pdfs_from_folder(UNMATCHED_DIR))
    
    if not all_pdfs:
        print(f"Error: No PDFs found in {MATCHED_DIR} or {UNMATCHED_DIR}")
        sys.exit(1)
    
    print(f"Found {len(all_pdfs)} PDFs to process\n")

    # Process each PDF: full-text search, then metadata filter
    results = []
    copied_yes = 0
    copied_no = 0
    keyword_folders = set()

    print("Scanning PDFs and filtering...")
    for pdf_path, pdf_name in tqdm(all_pdfs, desc="Progress"):
        pdf_id = extract_id_from_filename(pdf_name)
        
        # Step 1: Full-text search for keywords (excluding References/Citations section)
        pdf_text = extract_text_from_pdf(pdf_path)
        pdf_text = remove_references_section(pdf_text)  # Remove references section
        found_fulltext, found_kw_fulltext = search_keywords_in_text(pdf_text, KEYWORDS)

        # Treat 'interface' and 'layout' as dependent keywords: they only count if they co-occur with an instrument keyword (organ, keyboard, piano, clavichord, harpsichord, accordion)
        instrument_kws = {"organ", "keyboard", "piano", "clavichord", "harpsichord", "accordion"}
        found_instruments = [kw for kw in found_kw_fulltext if kw in instrument_kws]
        found_ui_layout = [kw for kw in found_kw_fulltext if kw in ("interface", "layout")]

        # If no keywords or only interface/layout without any instrument keyword, treat as no match
        if (not found_fulltext) or (found_ui_layout and not found_instruments):
            # No eligible keywords in full text - copy to No_Keyword_Match
            results.append({
                "pdf_name": pdf_name,
                "contains_keywords": "No",
                "keywords_found": "; ".join(found_kw_fulltext) if found_kw_fulltext else "",
                "reason": "No instrument keyword found in full text (only interface/layout present)" if found_ui_layout else "No keyword match in full text"
            })
            try:
                shutil.copy2(pdf_path, os.path.join(FILTERED_NO_DIR, pdf_name))
                copied_no += 1
            except Exception as e:
                print(f"Error copying {pdf_name}: {e}")
            continue
        
        # Step 2: Metadata filter (only for PDFs with keywords in full text)
        meta = id_to_meta.get(pdf_id, {})
        title = meta.get("title", "")
        abstract = meta.get("abstract", "")
        keywords_field = meta.get("keywords", "")
        
        # Create subfolder based on full-text keywords
        folder_name = create_keyword_folder_name(found_kw_fulltext)
        # If this keyword combo includes 'keyboard', 'interface' or 'layout', place it under Keyboard_Interface_Related parent
        if any(x in folder_name for x in ("keyboard", "interface", "layout")):
            keyword_folder = os.path.join(FILTERED_YES_DIR, "Keyboard_Interface_Related", folder_name)
        else:
            keyword_folder = os.path.join(FILTERED_YES_DIR, folder_name)
        Path(keyword_folder).mkdir(parents=True, exist_ok=True)
        keyword_folders.add(folder_name)
        
        # Check metadata
        if not (title or abstract or keywords_field):
            # No metadata - copy to No_Metadata_Match subfolder
            no_meta_dir = os.path.join(keyword_folder, "No_Metadata_Match")
            Path(no_meta_dir).mkdir(parents=True, exist_ok=True)
            
            results.append({
                "pdf_name": pdf_name,
                "contains_keywords": "Yes",
                "keywords_found": "; ".join(found_kw_fulltext),
                "reason": "Full-text match; no metadata available"
            })
            try:
                shutil.copy2(pdf_path, os.path.join(no_meta_dir, pdf_name))
                copied_yes += 1
            except Exception as e:
                print(f"Error copying {pdf_name}: {e}")
            continue
        
        # Combine metadata text
        text_blob = " ".join([title, abstract, keywords_field])
        
        # Check if keywords also in metadata
        found_metadata, found_kw_metadata = search_keywords_in_text(text_blob, KEYWORDS)
        
        if found_metadata:
            # Keywords in both full-text and metadata - copy to Metadata_Match subfolder
            meta_match_dir = os.path.join(keyword_folder, "Metadata_Match")
            Path(meta_match_dir).mkdir(parents=True, exist_ok=True)
            
            results.append({
                "pdf_name": pdf_name,
                "contains_keywords": "Yes",
                "keywords_found": "; ".join(found_kw_fulltext),
                "reason": "Full-text and metadata match"
            })
            try:
                shutil.copy2(pdf_path, os.path.join(meta_match_dir, pdf_name))
                copied_yes += 1
            except Exception as e:
                print(f"Error copying {pdf_name}: {e}")
        else:
            # Keywords in full-text but not metadata - copy to No_Metadata_Match subfolder
            no_meta_dir = os.path.join(keyword_folder, "No_Metadata_Match")
            Path(no_meta_dir).mkdir(parents=True, exist_ok=True)
            
            results.append({
                "pdf_name": pdf_name,
                "contains_keywords": "Yes",
                "keywords_found": "; ".join(found_kw_fulltext),
                "reason": "Full-text match; no keyword match in metadata"
            })
            try:
                shutil.copy2(pdf_path, os.path.join(no_meta_dir, pdf_name))
                copied_yes += 1
            except Exception as e:
                print(f"Error copying {pdf_name}: {e}")

    # Write results CSV
    print(f"\nWriting results to {RESULTS_CSV}...")
    fieldnames = ["pdf_name", "contains_keywords", "keywords_found", "reason"]
    try:
        with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in results:
                writer.writerow(row)
        print(f"Results CSV written: {RESULTS_CSV}")
    except Exception as e:
        print(f"Error writing results CSV: {e}")

    # Print summary
    print("\n" + "="*70)
    print("COMBINED FILTER SUMMARY (Full-Text + Metadata)")
    print("="*70)
    print(f"Total PDFs processed:                    {len(all_pdfs)}")
    print(f"PDFs with keyword match (full-text):     {copied_yes}")
    print(f"PDFs without keyword match:              {copied_no}")
    print(f"\nKeyword combinations found:")
    for kw_folder in sorted(keyword_folders):
        print(f"  - {kw_folder}/")
        print(f"      ├── Metadata_Match/")
        print(f"      └── No_Metadata_Match/")

    # Report keyboard/interface/layout-related folders placed under Keyboard_Interface_Related
    keyboard_parent = os.path.join(FILTERED_YES_DIR, "Keyboard_Interface_Related")
    keyboard_folders = [kf for kf in keyword_folders if any(x in kf for x in ("keyboard", "interface", "layout"))]
    files_in_keyboard = 0
    for kf in sorted(keyboard_folders):
        src_dir = os.path.join(keyboard_parent, kf)
        if not os.path.isdir(src_dir):
            # fallback: older runs might have top-level folder (rare), also check there
            src_dir = os.path.join(FILTERED_YES_DIR, kf)
            if not os.path.isdir(src_dir):
                continue
        for _, _, files in os.walk(src_dir):
            files_in_keyboard += len(files)
    print(f"\nPlaced keyboard/interface/layout-related folders under {keyboard_parent} with {len(keyboard_folders)} subfolders and {files_in_keyboard} files")

    print(f"\nOutput structure:")
    print(f"  {OUTPUT_BASE}/")
    print(f"  ├── Keyword_Match/")
    print(f"  │   └── [keyword_combination]/")
    print(f"  │       ├── Metadata_Match/")
    print(f"  │       └── No_Metadata_Match/")
    print(f"  ├── No_Keyword_Match/")
    print(f"  └── filter_results.csv")
    print("="*70)

if __name__ == "__main__":
    main()