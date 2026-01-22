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
- `Crawler/`: Contains the scraping pipeline for NIME papers spanning **2001–2025**.
- `Keyboard_Interface_Texts/`: The processed text corpus (Ready for analysis).
- `Metadata_Filtered_Results/`: Final output storage for screened CSVs.
- `*.py`: Core pipeline scripts for standardization, filtering, and extraction.
- **Note**: The `Renamed_PDFs/` and `NIME Papers/` directories are excluded (~17GB) to comply with GitHub limits.

---

## 📊 Data Source Verification
To ensure maximum accuracy and coverage, the pipeline cross-references multiple data sources to calibrate the corpus:

- **Metadata Analysis**: `export.csv` is generated via [NIME Proceedings Analyzer](https://github.com/jacksongoode/NIME-proceedings-analyzer) to extract structural metadata.
- **NIME Official Bibliography**: `nime_papers.csv` is sourced from the [NIME Bibliography Archive](https://nime-conference.github.io/NIME-bibliography/).
- **Crawled Data & Archives**:
  - The `Crawler/` folder contains scripts used to scrape the NIME portal for papers from **2001–2024**, plus a dedicated script for **2025**.
  - Historical data is also supplemented by the official [NIME ZIP Archives](https://www.nime.org/proceedings/ZIPs/).
- **Validation**: This multi-source comparison ensures that renamed PDFs align perfectly with official bibliography entries.

---

## ⚙️ Data Preparation & Corpus Rebuilding
If you need to rebuild the corpus or add new conference years, follow these steps:

1. **Acquisition**: Use the `Crawler/` tools to fetch metadata and PDFs for **2001–2025**, or download ZIP containers from the official [NIME Archives](https://www.nime.org/proceedings/ZIPs/).
2. **Standardization**: [rename_pdfs_by_nime_id.py](rename_pdfs_by_nime_id.py)  
   Aligns raw PDFs with official metadata and resolves inconsistent naming schemes.
3. **Filtering**: [filter_renamed_pdfs_combined.py](filter_renamed_pdfs_combined.py)  
   Categorizes papers and performs pre-screening by stripping bibliographies to avoid false positives.
4. **Extraction**: [extract_keyboard_pdfs_to_txt.py](extract_keyboard_pdfs_to_txt.py)  
   Converts PDFs to TXT (specifically fixing the 2013 word-spacing bug).

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
