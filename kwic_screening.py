# kwic_screening.py
"""
KWIC (Keyword In Context) Screening Tool
Step 1: Generates context snippets around keyboard/interface keywords.
Step 2: Aggregates to paper-level with auto-scoring based on NIME context.
"""
import os
import csv
import re
from pathlib import Path
from typing import List
import pandas as pd

# Paths
TEXT_DIR = os.path.join(os.getcwd(), "Keyboard_Interface_Texts")
OUTPUT_DIR = os.path.join(os.getcwd(), "KWIC_Screening")
KWIC_DETAILS_CSV = os.path.join(OUTPUT_DIR, "kwic_details_all_instances.csv")
KWIC_SCREENING_CSV = os.path.join(OUTPUT_DIR, "kwic_context_screening.csv")

# Keywords
TARGET_KEYWORDS = ['organ', 'keyboard', 'piano', 'clavichord', 'harpsichord', 'accordion', 'interface', 'layout']
CONTEXT_WINDOW = 80

def get_kwic_snippets(text: str, keywords: List[str], window: int = CONTEXT_WINDOW) -> List[dict]:
    snippets = []
    t = text.lower()
    for keyword in keywords:
        if keyword in ['keyboard', 'piano', 'organ', 'accordion']:
            pattern = r'\b' + re.escape(keyword) + r'(s|ist|ists)?\b'
        else:
            pattern = r'\b' + re.escape(keyword) + r's?\b'
        
        for match in re.finditer(pattern, t):
            start_pos = max(0, match.start() - window)
            end_pos = min(len(text), match.end() + window)
            # Remove internal newlines for cleaner CSV
            before = text[start_pos:match.start()].replace('\n', ' ').strip()
            after = text[match.end():end_pos].replace('\n', ' ').strip()
            matched_word = text[match.start():match.end()]
            
            snippets.append({
                'keyword': keyword,
                'matched_word': matched_word,
                'before': before,
                'after': after
            })
    return snippets

def main():
    Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)
    txt_files = sorted(Path(TEXT_DIR).glob("*.txt")) + sorted(Path(TEXT_DIR).glob("*/*.txt"))
    if not txt_files:
        print(f"No .txt files found in {TEXT_DIR}")
        return

    print(f"1. Extracting KWIC from {len(txt_files)} files...")
    kwic_data = []
    for txt_file in txt_files:
        try:
            with open(txt_file, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
            pdf_name = txt_file.stem + '.pdf'
            
            # Extract Year from filename (e.g., nime2013_Batula.pdf -> 2013)
            year_match = re.search(r'nime(\d{4})_', pdf_name)
            year = year_match.group(1) if year_match else "Unknown"

            snippets = get_kwic_snippets(text, TARGET_KEYWORDS)
            for s in snippets:
                kwic_data.append({
                    'Year': year,
                    'pdf_name': pdf_name,
                    'context_before': s['before'],
                    'keyword': s['keyword'],
                    'matched_word': s['matched_word'],
                    'context_after': s['after'],
                    'manual_decision': ''
                })
        except Exception as e:
            print(f"Error processing {txt_file.name}: {e}")

    # Sorting
    kwic_data.sort(key=lambda x: (x['Year'], x['pdf_name'], x['keyword']))
    
    # Write Word-level Details (Detailed data for record)
    with open(KWIC_DETAILS_CSV, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['Year', 'pdf_name', 'context_before', 'keyword', 'matched_word', 'context_after', 'manual_decision']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kwic_data)
    print(f"✓ Detailed instance backup saved: {KWIC_DETAILS_CSV}")

    # Step 2: Aggregation for easier screening
    print("2. Calculating IDF weights for objective scoring...")
    
    # Read the data back for processing
    df = pd.read_csv(KWIC_DETAILS_CSV)
    
    # 2.1 Calculate IDF (Inverse Document Frequency)
    # This provides a mathematical weights based on keyword exclusivity
    # Formula: log10(Total Docs / Docs containing keyword)
    total_docs = consolidated_for_idf = df['pdf_name'].nunique()
    idf_weights = {}
    for kw in TARGET_KEYWORDS:
        # Number of papers containing this keyword
        docs_with_kw = df[df['keyword'] == kw]['pdf_name'].nunique()
        if docs_with_kw > 0:
            import math
            weight = math.log10(total_docs / docs_with_kw)
            idf_weights[kw] = weight
        else:
            idf_weights[kw] = 0
            
    print("   IDF Weights calculated:")
    for kw, w in idf_weights.items():
        print(f"   - {kw}: {w:.4f}")

    def aggregate_context(group):
        snippets = []
        for _, row in group.iterrows():
            before = str(row['context_before']) if pd.notnull(row['context_before']) else ""
            after = str(row['context_after']) if pd.notnull(row['context_after']) else ""
            word = str(row['matched_word']) if pd.notnull(row['matched_word']) else "KEYWORD"
            snip = f"...{before[-60:]} [{word.upper()}] {after[:60]}..."
            snippets.append(snip)
        unique_snippets = list(dict.fromkeys(snippets))[:8]
        return " \n\n ".join(unique_snippets)

    # Scoring Logic - Frequency-based Density Scoring (Objective + Contextual)
    # Applied to the ENTIRE set of snippets for a paper, not just the 8-snippet preview.
    def calculate_paper_score(group):
        # Flatten all snippets for this paper into one big text block for scoring
        full_paper_context = " ".join([
            f"{row['context_before']} {row['keyword']} {row['context_after']}" 
            for _, row in group.iterrows()
        ]).lower()
        
        hit_count = len(group)
        score = 0
        
        # 1. Global Hit Reward: The more times keywords appear in the paper, the more relevant.
        import math
        score += math.log2(hit_count + 1) * 2

        # 2. IDF-based Instrumental Density
        for kw, weight in idf_weights.items():
            # Count occurrences in all snippets
            count = len(re.findall(r'\b' + re.escape(kw) + r'\b', full_paper_context))
            if count > 0:
                # Basic contribution from mathematical rarity (IDF)
                contribution = (weight * 5) * count
                
                # Domain Knowledge Boost:
                # These terms are treated as "High Reliability Musical Instruments".
                # They receive a uniform +5.0 boost per occurrence because their presence
                # is a near-certain indicator of musical relevance, regardless of their frequency.
                if kw in ['piano', 'harpsichord', 'clavichord', 'accordion', 'organ']:
                    contribution += 5.0 * count
                
                score += contribution
            
        # 3. Musical Context Density (+1.5 points per occurrence)
        musical_terms = ['musical', 'expression', 'haptic', 'force', 'sensor', 'velocity', 'synthesizer', 'midi', 'controller', 'timbre']
        for w in musical_terms:
            count = len(re.findall(r'\b' + re.escape(w) + r'\b', full_paper_context))
            score += count * 1.5
            
        # 4. HCI/Typing Penalty (-2 points per occurrence)
        exclude_kw = ['qwerty', 'typing', 'text entry', 'alphanumeric', 'computer keyboard', 'password', 'office']
        for w in exclude_kw:
            count = len(re.findall(r'\b' + re.escape(w) + r'\b', full_paper_context))
            score -= count * 2.5 # Slightly higher penalty to filter noise
            
        return score

    # Group by year and paper
    consolidated = df.groupby(['Year', 'pdf_name']).apply(lambda x: pd.Series({
        'Aggregated_Context': aggregate_context(x),
        'Hit_Count': len(x),
        'Auto_Priority_Score': calculate_paper_score(x)
    })).reset_index()

    consolidated = consolidated.sort_values(by='Auto_Priority_Score', ascending=False).reset_index(drop=True)

    # Final Decision Columns
    consolidated['KEEP(1)_or_EXCLUDE(0)'] = ""
    consolidated['EXCLUSION_REASON'] = ""

    # Using the name requested by user for the main screening file
    consolidated.to_csv(KWIC_SCREENING_CSV, index=False, encoding='utf-8-sig')
    print(f"✓ Main Screening CSV saved: {KWIC_SCREENING_CSV}")
    print(f"Total Papers to screen: {len(consolidated)}")

if __name__ == "__main__":
    main()

