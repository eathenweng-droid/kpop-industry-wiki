#!/usr/bin/env python3
"""Wiki 健康檢查（對應 CLAUDE.md 第 4 節規則）。
用法：python3 pipeline/lint_wiki.py [--today YYYY-MM-DD]
"""
import re, sys, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
WIKI, RAW = ROOT / "wiki", ROOT / "raw"
SPECIAL = {"index", "log", "glossary"}
TODAY = datetime.date.fromisoformat(sys.argv[sys.argv.index("--today") + 1]) if "--today" in sys.argv else datetime.date.today()

errors, warnings = [], []
def err(page, rule, msg): errors.append(f"FAIL [{page}] R{rule}: {msg}")
def warn(page, msg): warnings.append(f"WARN [{page}] {msg}")

def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m: return None, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1); meta[k.strip()] = v.strip()
    return meta, text[m.end():]

# ---- raw 來源 ----
raw_ids, raw_date = set(), {}
for f in RAW.glob("S*.md"):
    meta, _ = frontmatter(f.read_text(encoding="utf-8"))
    sid = meta["id"]; raw_ids.add(sid)
    try: raw_date[sid] = datetime.date.fromisoformat(meta.get("published", "")[:10])
    except ValueError: raw_date[sid] = None   # 持續更新的來源（如百科）

pages = {f.stem: f for f in WIKI.glob("*.md")}
index_text = pages["index"].read_text(encoding="utf-8") if "index" in pages else ""
glossary_text = pages["glossary"].read_text(encoding="utf-8") if "glossary" in pages else ""
glossary_terms = set(re.findall(r"^### (.+)$", glossary_text, re.M))

for slug, f in sorted(pages.items()):
    text = f.read_text(encoding="utf-8")
    if "[[" in text: err(slug, 4, "使用了 [[ ]] 連結，請改為相對 Markdown 連結")

    # R4 相對連結都要存在
    for target in re.findall(r"\]\(([^)#]+\.md)\)", text):
        if not (f.parent / target).resolve().exists():
            err(slug, 4, f"連結目標不存在：{target}")

    if slug in SPECIAL: continue
    meta, body = frontmatter(text)
    if meta is None: err(slug, 0, "缺少 frontmatter"); continue
    for k in ("title", "slug", "sources", "updated"):
        if k not in meta: err(slug, 0, f"frontmatter 缺少 {k}")
    if meta.get("slug") != slug: err(slug, 0, f"slug 欄位 {meta.get('slug')} 與檔名不一致")

    cited = set(re.findall(r"\[(S\d{2})\]", body))
    declared = set(re.findall(r"S\d{2}", meta.get("sources", "")))
    # R1 引用存在
    for sid in cited - raw_ids: err(slug, 1, f"引用了不存在的來源 {sid}")
    # R6 sources 欄位一致
    if cited != declared:
        err(slug, 6, f"sources 欄位 {sorted(declared)} ≠ 內文引用 {sorted(cited)}")

    # R1 「重點」中每個事實句都要有來源
    sec = re.search(r"## 重點\n(.*?)(\n## |\Z)", body, re.S)
    if not sec: err(slug, 1, "缺少「## 重點」段落")
    else:
        for line in sec.group(1).splitlines():
            s = line.strip()
            item = re.match(r"^(?:- |\d+\. )(.*)", s)   # pass1 後加入：編號清單也算事實句
            if item and not re.search(r"\[S\d{2}\]", s) and not item.group(1).startswith("也就是說"):
                err(slug, 1, f"事實句沒有來源：{s[:40]}…")

    # R2 / R7 數字表
    tab = re.search(r"## 數字\n(.*?)(\n## |\Z)", body, re.S)
    if not tab: err(slug, 2, "缺少「## 數字」表格")
    else:
        rows = [r for r in tab.group(1).splitlines() if r.startswith("|")][2:]
        for r in rows:
            cells = [c.strip() for c in r.strip("|").split("|")]
            if len(cells) < 4 or not cells[2]: err(slug, 2, f"數字缺少時間：{r[:50]}")
            ids = re.findall(r"S\d{2}", cells[-1] if cells else "")
            if not ids: err(slug, 2, f"數字缺少來源：{r[:50]}")
            for sid in ids:
                d = raw_date.get(sid)
                if d and (TODAY - d).days > 3 * 365 and "較舊資料" not in r:
                    err(slug, 7, f"{sid} 已超過 3 年，數字需標「較舊資料」：{r[:50]}")

    # 爭議段落（使用者在 round-01 的決定）
    if "## 爭議與限制" not in body: err(slug, 0, "缺少「## 爭議與限制」段落（round-01 決定）")

    # R5 收錄於 index、非孤兒頁
    if f"({slug}.md)" not in index_text: err(slug, 5, "沒有列在 wiki/index.md")
    out_links = {t for t in re.findall(r"\]\(([a-z0-9-]+)\.md\)", body) if t != slug and t not in SPECIAL}
    if not out_links: err(slug, 5, "沒有連到任何其他概念頁（孤兒頁）")

    # R8 粗體術語要在 glossary
    for term in dict.fromkeys(re.findall(r"\*\*(.+?)\*\*", body)):
        if term not in glossary_terms: err(slug, 8, f"粗體術語「{term}」沒有收錄在 glossary.md")

print(f"lint_wiki  today={TODAY}  pages={len(pages)}  raw={len(raw_ids)}")
for w in warnings: print(w)
for e in errors: print(e)
print("RESULT:", "PASS" if not errors else f"FAIL ({len(errors)} errors)")
sys.exit(1 if errors else 0)
