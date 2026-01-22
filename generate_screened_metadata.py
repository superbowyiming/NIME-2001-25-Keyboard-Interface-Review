
import pandas as pd
import os

# Paths
SCREENING_CSV = r"D:/Uni of Auckland Dropbox/Li Yiming/My NIME Analyzer/KWIC_Screening/kwic_context_screening.csv"
RENAME_MAP_CSV = r"D:/Uni of Auckland Dropbox/Li Yiming/My NIME Analyzer/Renamed_PDFs/rename_map.csv"
NIME_PAPERS_CSV = r"D:/Uni of Auckland Dropbox/Li Yiming/My NIME Analyzer/nime_papers.csv"
OUTPUT_CSV = r"D:/Uni of Auckland Dropbox/Li Yiming/My NIME Analyzer/KWIC_Screening/screened_metadata_results.csv"

def main():
    if not os.path.exists(SCREENING_CSV):
        print(f"Error: {SCREENING_CSV} not found.")
        return

    # 1. Load screening results and filter for KEEP
    print("Loading screening results...")
    df_screen = pd.read_csv(SCREENING_CSV)
    # Check if column exists (it might have spaces or different case if manually edited)
    keep_col = [c for c in df_screen.columns if 'KEEP' in c.upper()][0]
    df_keep = df_screen[df_screen[keep_col] == 1].copy()
    print(f"Found {len(df_keep)} papers marked as KEEP.")

    # 2. Load rename map
    print("Loading rename map...")
    df_map = pd.read_csv(RENAME_MAP_CSV)
    
    # 3. Load full metadata
    print("Loading full metadata (this may take a moment)...")
    # nime_papers.csv is large, we only need specific columns
    df_meta = pd.read_csv(NIME_PAPERS_CSV)
    
    # 4. Merge
    # df_keep [pdf_name] -> df_map [new_name]
    merged = pd.merge(df_keep, df_map, left_on='pdf_name', right_on='new_name', how='left')
    
    # merged [ID] -> df_meta [ID]
    final_df = pd.merge(merged, df_meta, on='ID', how='left')
    
    # 5. Clean up and select columns
    # We want a readable summary
    cols_to_keep = [
        'Year_x', 'pdf_name', 'Auto_Priority_Score', 'Hit_Count',
        'title', 'author', 'abstract', 'url_y'
    ]
    # Check if columns exists (some might be slightly different)
    available_cols = [c for c in cols_to_keep if c in final_df.columns]
    
    result = final_df[available_cols].rename(columns={
        'Year_x': 'Year',
        'url_y': 'original_url'
    })
    
    # Sort by score descending
    result = result.sort_values(by='Auto_Priority_Score', ascending=False)
    
    # 6. Save
    result.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
    print(f"✓ Screened metadata saved to: {OUTPUT_CSV}")
    print(f"Total entries: {len(result)}")

if __name__ == "__main__":
    main()
