#!/usr/bin/env python3
"""簡報檢查（對應 CLAUDE.md 第 5 節）。
用法：python3 pipeline/check_slides.py
檢查：
  S1 每張投影片都有 data-wiki，且頁面存在
  S2 投影片上的每個數字都能在它引用的 wiki 頁找到
  S3 內文 ≤ 120 字（不含標題 h1/h2、.note、.src）
  S4 教學結構：opening → map → concept… → debate → quiz → refs
  S5 術語第一次出現必須用 <dfn> 解釋
  S6 outline.md 與 index.html 的投影片 id 一一對應
  S7 （run-001 後新增）段落文字必須逐字出現在 outline.md 該投影片的「文案」中
"""
import re, sys, pathlib, html

ROOT = pathlib.Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
deck = (ROOT / "slides/index.html").read_text(encoding="utf-8")
outline = (ROOT / "slides/outline.md").read_text(encoding="utf-8")
glossary = re.findall(r"^### (.+)$", (WIKI / "glossary.md").read_text(encoding="utf-8"), re.M)
wiki_text = {f.stem: f.read_text(encoding="utf-8") for f in WIKI.glob("*.md")}
ORDER = ["opening", "map", "concept", "debate", "quiz", "refs"]

errors = []
def err(sid, rule, msg): errors.append(f"FAIL [{sid}] {rule}: {msg}")

def strip(s):
    s = re.sub(r"<(script|style)\b.*?</\1>", "", s, flags=re.S)
    return html.unescape(re.sub(r"<[^>]+>", " ", s))   # pass1 修正：標籤換成空白，避免相鄰數字黏在一起

def norm(s): return s.replace(",", "").replace("，", "")

slides = re.findall(r'<section class="slide"([^>]*)>(.*?)</section>', deck, re.S)
if not slides: err("deck", "S0", "找不到任何 <section class=\"slide\">")

roles, ids, seen_terms = [], [], set()
for attrs, body in slides:
    sid = (re.search(r'id="([^"]+)"', attrs) or [None, "?"])[1]
    role = (re.search(r'data-role="([^"]+)"', attrs) or [None, "?"])[1]
    refs = (re.search(r'data-wiki="([^"]*)"', attrs) or [None, ""])[1].split()
    ids.append(sid); roles.append(role)

    # S1
    if not refs: err(sid, "S1", "缺少 data-wiki")
    for r in refs:
        if r not in wiki_text: err(sid, "S1", f"data-wiki 引用了不存在的頁面 {r}")
    src = norm("\n".join(wiki_text.get(r, "") for r in refs))

    # S2 數字（.src 註腳中的來源編號與年份標示除外）
    visible = strip(re.sub(r'<(?:p|div|span) class="(?:src|kicker)">.*?</(?:p|div|span)>', "", body, flags=re.S))  # pass1 修正：kicker 是標籤不是事實
    for num in re.findall(r"\d[\d,\.]*", visible):
        n = norm(num).rstrip(".")
        if len(n) == 1 and role in ("quiz", "refs", "map"): continue   # 題號、步驟編號
        if re.fullmatch(r"S?0?\d", n) and role != "concept": continue
        if n not in src: err(sid, "S2", f"數字「{num}」在 {refs} 中找不到")

    # S3 字數
    content = re.sub(r"<h[12][^>]*>.*?</h[12]>", "", body, flags=re.S)
    content = re.sub(r'<(?:p|div|span|aside) class="(?:note|src)">.*?</(?:p|div|span|aside)>', "", content, flags=re.S)
    text = re.sub(r"\s+", "", strip(content))
    limit = 200 if role == "quiz" else 120
    if role != "refs" and len(text) > limit:   # pass1 修正：參考資料頁不限字數
        err(sid, "S3", f"內文 {len(text)} 字，超過 {limit}")

    # S5 術語第一次出現要用 <dfn>
    plain = strip(body)
    for term in glossary:
        if term in seen_terms or term not in plain: continue
        # 較長的術語（如「隨機小卡」）包含較短術語（「小卡」）時，以 dfn 內含即可
        if not re.search(rf"<dfn[^>]*>[^<]*{re.escape(term)}[^<]*</dfn>", body):
            err(sid, "S5", f"術語「{term}」第一次出現沒有用 <dfn> 解釋")
        seen_terms.add(term)

# S7 文案逐字對照 claim ledger
sections = dict(re.findall(r"^## (s\d{2})[^\n]*\n(.*?)(?=^## s\d{2}|\Z)", outline, re.M | re.S))
for attrs, body in slides:
    sid = (re.search(r'id="([^"]+)"', attrs) or [None, "?"])[1]
    role = (re.search(r'data-role="([^"]+)"', attrs) or [None, "?"])[1]
    if role in ("quiz", "refs"): continue
    ledger = sections.get(sid, "")
    for cls, inner in re.findall(r'<p(?: class="([^"]*)")?[^>]*>(.*?)</p>', body, re.S):
        if cls in ("src", "kicker"): continue
        s = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", inner))).strip()
        if s and f"`{s}`" not in ledger:
            err(sid, "S7", f"段落不在 outline.md 文案中（可能是未審過的改寫）：{s[:30]}…")

# S4 結構
compressed = [r for i, r in enumerate(roles) if i == 0 or r != roles[i - 1]]
if compressed != ORDER: err("deck", "S4", f"教學結構應為 {ORDER}，目前為 {compressed}")

# S6 outline 對照
outline_ids = re.findall(r"^## (s\d{2})", outline, re.M)
if outline_ids != ids: err("deck", "S6", f"outline.md 投影片 {outline_ids} 與 index.html {ids} 不一致")

print(f"check_slides  slides={len(slides)}  glossary_terms={len(glossary)}")
for e in errors: print(e)
print("RESULT:", "PASS" if not errors else f"FAIL ({len(errors)} errors)")
sys.exit(1 if errors else 0)
