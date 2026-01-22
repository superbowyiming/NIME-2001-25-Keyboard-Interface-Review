# NIME Keyboard Interface Research Pipeline

Automated workflow for building, intelligently scoring, and screening a corpus of research papers from the **NIME (New Interfaces for Musical Expression)** conference (2001–2025), specifically focusing on **Keyboard Interfaces**.

---

## 🚀 Quick Start

1. **Setup Environment**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Execute Pipeline**:
   Run the scripts in the following order:
   ```bash
   python rename_pdfs_by_nime_id.py
   python filter_renamed_pdfs_combined.py
   python extract_keyboard_pdfs_to_txt.py
   python kwic_screening.py
   # After manual labeling in CSV:
   python merge_screening_with_metadata.py
   ```

---

## 🔍 Overview
This project provides a robust pipeline to transform unordered NIME paper collections into a filtered, high-quality text corpus for systematic review. It addresses common challenges like messy file naming, bibliography noise, and extraction artifacts.

---

## 📊 Data & Source Verification
To ensure high accuracy and coverage, the pipeline cross-references multiple data sources:
- **NIME Official Bibliography**: Metadata sourced from the [NIME Bibliography](https://nime-conference.github.io/NIME-bibliography/).
- **Metadata Analyzers**: `export.csv` data generated via the [NIME Proceedings Analyzer](https://github.com/jacksongoode/NIME-proceedings-analyzer).
- **Official PDF Archives**: Support for both legacy ZIP archives and modern PubPub-hosted papers.

---

## ⚙️ Processing Pipeline

### 1. Standardization & File Alignment
**Script**: [rename_pdfs_by_nime_id.py](rename_pdfs_by_nime_id.py)
Standardizes raw PDF filenames into a consistent `nimeYYYY_Author.pdf` format. It employs a dual-mapping system to handle both legacy URL-based filenames and modern PubPub IDs, ensuring every paper aligns perfectly with its metadata.

### 2. Taxonomy-based Filtering
**Script**: [filter_renamed_pdfs_combined.py](filter_renamed_pdfs_combined.py)
Filters the corpus into thematic categories (e.g., `organ_piano/`) while performing critical pre-screening:
- **Reference Removal**: Automatically truncates text at the "References" or "Citations" section to eliminate false positives from bibliographies.
- **Instrument Dependency**: Keywords like `Interface` or `Layout` are only flagged if they co-occur with specific instrument terms (Piano, Organ, Accordion, etc.).

### 3. High-Fidelity Text Extraction
**Script**: [extract_keyboard_pdfs_to_txt.py](extract_keyboard_pdfs_to_txt.py)
Converts curated PDFs into plain text using the **`pypdf`** engine.
- **Key Solution**: This engine specifically fixes the "word spacing bug" found in NIME 2013 papers, where older extractors would produce run-on words (e.g., `keyboardplayer`).

### 4. Intelligent KWIC Screening & Scoring
**Script**: [kwic_screening.py](kwic_screening.py)
Generates a Keyword In Context (KWIC) report and applies a heuristic scoring model to help prioritize relevant research.

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
