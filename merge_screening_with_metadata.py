# merge_screening_with_metadata.py
import pandas as pd
import os

# Paths
SCREENING_CSV = os.path.join("KWIC_Screening", "kwic_context_screening.csv")
RENAME_MAP_CSV = os.path.join("Renamed_PDFs", "rename_map.csv")
METADATA_CSV = "nime_papers.csv"
OUTPUT_CSV = os.path.join("KWIC_Screening", "kwic_screened_metadata.csv")

def main():
    print("Loading data...")
    # 1. Load screening results and filter for KEEP=1
    screening_df = pd.read_csv(SCREENING_CSV)
    # Ensure column name matches exactly and handle potential type issues (some might be strings/ints)
    kept_df = screening_df[screening_df['KEEP(1)_or_EXCLUDE(0)'].astype(str) == '1'].copy()
    
    if kept_df.empty:
        print("No papers marked as KEEP(1). Exiting.")
        return
    
    # 2. Load rename map to link pdf_name to metadata ID
    rename_map = pd.read_csv(RENAME_MAP_CSV)
    # rename_map has columns: original, new_name, ID, method
    # we need to join on pdf_name (screening) == new_name (rename_map)
    
    # 3. Load full metadata
    metadata_df = pd.read_csv(METADATA_CSV, low_memory=False)
    
    # 4. Merge
    print(f"Merging {len(kept_df)} kept papers with metadata...")
    
    # First join screening with map
    merged_step1 = pd.merge(
        kept_df[['Year', 'pdf_name']], 
        rename_map[['new_name', 'ID']], 
        left_on='pdf_name', 
        right_on='new_name', 
        how='left'
    )
    
    # Then join with metadata
    final_merged = pd.merge(
        merged_step1,
        metadata_df[['ID', 'title', 'author', 'keywords', 'abstract', 'doi', 'bibtex']],
        on='ID',
        how='left'
    )
    
    # Drop the redundant 'new_name' column from the join
    final_merged = final_merged.drop(columns=['new_name'])
    
    # 5. Save output
    final_merged.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"✓ Final metadata for kept papers saved to: {OUTPUT_CSV}")
    print(f"Total papers exported: {len(final_merged)}")

if __name__ == "__main__":
    main()
