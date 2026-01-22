# NIME Keyboard Interface Research Pipeline

Automated workflow for building, intelligently scoring, and screening a corpus of research papers from the **NIME (New Interfaces for Musical Expression)** conference (2001–2025), specifically focusing on **Keyboard Interfaces**.

---

## 🚀 Quick Start (Using Provided Data)

The repository includes the pre-extracted text corpus in [Keyboard_Interface_Texts/](Keyboard_Interface_Texts/). You can run the analysis immediately without the original PDF files.

1. **Setup Environment**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Run Analysis**:
   ```bash
   # Generate the screening report (KWIC)
   python kwic_screening.py
   
   # After manual labeling in 'kwic_context_screening.csv':
   python merge_screening_with_metadata.py
   ```

---

## 🔍 Project Structure
- `Keyboard_Interface_Texts/`: The processed text corpus (Ready for analysis).
- `Metadata_Filtered_Results/`: Final output storage.
- `*.py`: Processing and analysis scripts.
- **Note**: The `Renamed_PDFs/` and `NIME Papers/` directories are excluded (~17GB) to comply with GitHub limits.

---

## 📊 Data & Source Verification
To ensure high accuracy and coverage, the pipeline cross-references multiple data sources:
- **NIME Official Bibliography**: Metadata sourced from the [NIME Bibliography](https://nime-conference.github.io/NIME-bibliography/).
- **Metadata Analyzers**: `export.csv` data generated via the [NIME Proceedings Analyzer](https://github.com/jacksongoode/NIME-proceedings-analyzer).
- **Official PDF Archives**: Support for both legacy ZIP archives and PubPub-hosted papers.

---

## ⚙️ Rebuilding from Scratch
If you have access to the original NIME PDF archives, you can rebuild the corpus using these scripts:

1. **Standardization**: [rename_pdfs_by_nime_id.py](rename_pdfs_by_nime_id.py)  
   Standardizes raw PDF filenames (`nimeYYYY_Author.pdf`) using a dual-mapping system for legacy and modern PubPub IDs.
2. **Filtering**: [filter_renamed_pdfs_combined.py](filter_renamed_pdfs_combined.py)  
   Categorizes papers and performs critical pre-screening by removing bibliographies to eliminate false positive keyword hits.
3. **Extraction**: [extract_keyboard_pdfs_to_txt.py](extract_keyboard_pdfs_to_txt.py)  
   Converts curated PDFs into plain text using the **`pypdf`** engine, which specifically resolves the "word spacing bug" found in NIME 2013 papers.

---

## 🔬 Scoring Logic (kwic_screening.py)
The pipeline applies a heuristic scoring model to prioritize relevant research within the text corpus.

**Mathematical Foundation (IDF Weights):**
The script calculates the **Inverse Document Frequency (IDF)** for each keyword across the corpus to ignore common terms and highlight rare instruments:
$$IDF_w = \log_{10}\left(\frac{N}{df_w}\right)$$

**Heuristic Scoring Model ($S_{total}$):**
Papers are ranked based on a weighted four-factor score:
$$S_{total} = S_{hits} + S_{instrument} + S_{context} - S_{noise}$$
- **Hits**: Logarithmic frequency bonus to avoid rewarding length over relevance.
- **Instrument Boost**: Fixed bonuses for definitive keyboard terms (Piano, Organ, Accordion) to override low IDF scores.
- **Musical Context**: Reward points for co-occurring terms like `MIDI`, `sensor`, or `velocity`.
- **Typing Noise Penalty**: Significant penalty for office/computing context like `QWERTY` or `text entry`.

---

## 📝 Manual Review & Final Export
The final stage involves human validation of the high-priority papers identified by the pipeline.
- **Manual Decision**: Review snippets in `kwic_context_screening.csv` and mark relevant papers in the `KEEP(1)_or_EXCLUDE(0)` column.
- **Metatada Export**: Use [merge_screening_with_metadata.py](merge_screening_with_metadata.py) to unify your final selection with BibTeX entries and full metadata for your literature review.
