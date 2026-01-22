# rename_pdfs_by_nime_id.py
# 精确匹配 PDF -> ID，支持 PubPub (2021-2022) 和传统格式
import os
import sys
import csv
import shutil
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("pandas is required. Install with: pip install pandas")
    sys.exit(1)

CSV_NIME = os.path.join(os.getcwd(), "nime_papers.csv")
SOURCE_DIR = os.path.join(os.getcwd(), "NIME Papers")
OUT_DIR = os.path.join(os.getcwd(), "Renamed_PDFs")

def safe_str(value) -> str:
    try:
        if pd.isna(value):
            return ""
    except:
        if value is None:
            return ""
    return str(value)

def basename_from_url(url: str) -> str:
    return os.path.basename(safe_str(url).strip())

def main():
    df = pd.read_csv(CSV_NIME, dtype=str, keep_default_na=False, na_filter=False)
    
    # 建立两个映射:
    # 1. url文件名 -> ID (传统格式)
    # 2. ID -> ID (用于 PubPub 年份，文件名本身就是 ID)
    url_to_id = {}
    id_set = set()
    
    for _, row in df.iterrows():
        url = safe_str(row.get("url"))
        nime_id = safe_str(row.get("ID")).strip()
        if not nime_id:
            continue
        id_set.add(nime_id)
        pdf_name = basename_from_url(url)
        if pdf_name.endswith(".pdf"):
            url_to_id[pdf_name] = nime_id

    print(f"Loaded {len(url_to_id)} URL->ID mappings")
    print(f"Loaded {len(id_set)} total IDs")

    source_path = Path(SOURCE_DIR)
    pdf_files = sorted(source_path.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDFs in {SOURCE_DIR}")

    # 创建输出文件夹结构
    out_path = Path(OUT_DIR)
    matched_dir = out_path / "Matched"
    unmatched_dir = out_path / "Unmatched"
    
    matched_dir.mkdir(parents=True, exist_ok=True)
    unmatched_dir.mkdir(parents=True, exist_ok=True)

    renamed = []
    unmatched = []
    
    for pdf in pdf_files:
        original_name = pdf.name
        matched_id = None
        match_method = ""
        
        # 方法1: URL精确匹配 (传统格式)
        if original_name in url_to_id:
            matched_id = url_to_id[original_name]
            match_method = "url"
        else:
            # 方法2: 文件名去掉.pdf后匹配ID (PubPub格式)
            stem = pdf.stem  # 例如 nime2021_1
            if stem in id_set:
                matched_id = stem
                match_method = "id_direct"
        
        if matched_id:
            # 复制到 Matched 文件夹
            new_name = f"{matched_id}.pdf"
            dest = matched_dir / new_name
            # 处理重复
            counter = 1
            while dest.exists():
                dest = matched_dir / f"{matched_id}_{counter}.pdf"
                counter += 1
            shutil.copy2(pdf, dest)
            renamed.append({
                "original": original_name,
                "new_name": dest.name,
                "ID": matched_id,
                "method": match_method
            })
        else:
            # 复制到 Unmatched 文件夹（保持原名）
            dest = unmatched_dir / original_name
            shutil.copy2(pdf, dest)
            unmatched.append(original_name)

    # 写映射CSV - 放在 Renamed_PDFs 根目录
    map_csv = out_path / "rename_map.csv"
    with open(map_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["original", "new_name", "ID", "method"])
        writer.writeheader()
        writer.writerows(renamed)

    # 写未匹配CSV - 放在 Renamed_PDFs 根目录
    unm_csv = out_path / "rename_unmatched.csv"
    with open(unm_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["original"])
        for m in unmatched:
            writer.writerow([m])

    print(f"\nDone!")
    print(f"Matched PDFs: {len(renamed)} -> {matched_dir}")
    print(f"Unmatched PDFs: {len(unmatched)} -> {unmatched_dir}")
    print(f"Mapping saved to: {map_csv}")
    print(f"Unmatched list saved to: {unm_csv}")

if __name__ == "__main__":
    main()