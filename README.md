# KPOP 產業 LLM Wiki → 教學 HTML 簡報

🔗 **網站**：https://eathenweng-droid.github.io/kpop-industry-wiki/
▶ **簡報**：https://eathenweng-droid.github.io/kpop-industry-wiki/slides/

## 這是什麼
1. 先用「先討論、後生成」的方式，把 8 篇關於 KPOP 產業的來源整理成 LLM Wiki。
2. 再讓 AI **只根據 Wiki** 產生一份給初學者的教學簡報〈KPOP 產業怎麼運作？〉。
3. 每一步都有檢查腳本，實際執行紀錄（包含失敗）都保留下來。

## 資料夾
| 路徑 | 內容 |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Wiki 的規則（給 AI 讀） |
| [`raw/`](raw/) | 8 張來源卡（S01–S08） |
| [`discuss/`](discuss/) | 每篇來源的討論 + [round-01 人類決定](discuss/round-01-outline.md) |
| [`wiki/`](wiki/index.md) | 9 個概念頁、術語表、索引、日誌 |
| [`slides/`](slides/) | [claim ledger](slides/outline.md) 與 [簡報](slides/index.html) |
| [`pipeline/`](pipeline/) | `lint_wiki.py`、`check_slides.py` |
| [`runs/`](runs/run-001.md) | 執行與檢查紀錄 |
| [`docs/workflow.md`](docs/workflow.md) | Loop / Graph 設計與反思 |

## 自己跑檢查
```bash
python3 pipeline/lint_wiki.py
python3 pipeline/check_slides.py
```
