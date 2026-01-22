# NIME 2001-2025 键盘界面研究综述 (Keyboard Interface Review)

本项目旨在对 2001 年至 2025 年间 NIME (New Interfaces for Musical Expression) 会议论文进行系统性梳理，特别是针对键盘类界面 (Keyboard Interfaces) 的研究动态进行数据抓取、文本提取和内容分析。

## 🚀 项目功能
- **论文爬取**：自动从 NIME 官网下载指定年份的论文 PDF。
- **自动化整理**：按照 NIME ID 对 PDF 文件进行标准化重命名。
- **关键词筛选**：基于 KWIC (Keyword In Context) 算法对海量论文进行初步筛选。
- **文本提取**：将筛选后的 PDF 转换为结构化文本，方便后续分析。
- **探索性分析**：使用 Jupyter Notebook 进行词频统计、趋势分析等。

## 📂 目录结构
```text
.
├── download_nime_2025.py          # 论文下载脚本
├── rename_pdfs_by_nime_id.py      # PDF 重命名与整理
├── kwic_screening.py              # 关键词筛选脚本
├── extract_keyboard_pdfs_to_txt.py # PDF 转文本工具
├── text_processing.ipynb          # 数据分析与可视化
├── Keyboard_Interface_Texts/      # [已同步] 提取出的论文文本内容
├── requirements.txt               # 环境依赖列表
└── .gitignore                     # Git 忽略配置（排除大型 PDF 文件）
```
*注：由于 PDF 原始文件体积巨大（约 17GB），仓库仅包含脚本和提取后的文本数据。*

## 🛠️ 安装与执行

1. **克隆项目**：
   ```bash
   git clone [your-repo-url]
   cd NIME-2001-25-Keyboard-Interface-Review
   ```

2. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

3. **运行流程**：
   - 首先运行 `download_nime_2025.py` 获取原始 PDF。
   - 使用 `rename_pdfs_by_nime_id.py` 进行标准化处理。
   - 执行 `kwic_screening.py` 根据关键词定位目标论文。
   - 最后使用 `text_processing.ipynb` 进行深度分析。

## 📊 数据来源
数据来自 [NIME 官方论文库](https://nime.org/papers/)。

## ⚖️ 许可证
[如果您有特定的开源协议，请在此处注明，例如 MIT]
