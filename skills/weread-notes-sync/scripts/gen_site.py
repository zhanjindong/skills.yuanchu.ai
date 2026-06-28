#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读取 weread_data.json，生成读书笔记：
   - reading/index.html        全部书的列表
   - reading/book-<id>.html     每本书的划线与想法
   风格对齐 yuanchu.ai。
"""
import json, os, html, datetime, sys

# 用法: python3 gen_site.py <输出目录> [数据JSON路径]
HERE = os.path.dirname(__file__)
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "reading_out")
DATA = sys.argv[2] if len(sys.argv) > 2 else "weread_data.json"
os.makedirs(OUT, exist_ok=True)
d = json.load(open(DATA, encoding="utf-8"))

def esc(s):
    return html.escape(s or "").strip()

# 全局 userVid（精确划线深链需要）
USER_VID = ""
for _b in d.get("details", []):
    for _t in (_b.get("thoughts") or []):
        if _t.get("userVid"):
            USER_VID = str(_t["userVid"]); break
    if USER_VID:
        break

def is_mp(bid):
    """是否公众号类'书'（MP_WXS_*）。"""
    return bool(bid) and str(bid).startswith("MP_")


def mark_link(bid, chapter_uid, rng, mp=False):
    """构造跳转到具体划线/想法位置的深链；逐级降级。
    公众号：网关不支持 bestbookmark 定位；有 chapterUid 时给章节级（可落到文章），
    没有 chapterUid（公众号划线即如此）则返回 None，表示无法定位、不放跳转。"""
    if mp:
        if chapter_uid:
            return f"weread://reading?bId={bid}&chapterUid={chapter_uid}"
        return None
    if chapter_uid and rng and "-" in str(rng):
        a, _, b2 = str(rng).partition("-")
        return (f"weread://bestbookmark?bookId={bid}&chapterUid={chapter_uid}"
                f"&rangeStart={a}&rangeEnd={b2}&userVid={USER_VID}")
    if chapter_uid:
        return f"weread://reading?bId={bid}&chapterUid={chapter_uid}"
    return f"weread://reading?bId={bid}"

stats = d.get("stats", {}) or {}
meta = d.get("notebook_meta", {}) or {}
read_days = stats.get("readDays") or 0
read_hours = round((stats.get("totalReadTime") or 0) / 3600)
total_books = meta.get("totalBookCount") or len(d.get("details", []))
total_notes = meta.get("totalNoteCount") or 0
prefer = [esc(c.get("categoryTitle")) for c in (stats.get("preferCategory") or [])][:6]

# ---------- 公共样式 ----------
BASE_CSS = """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #fff; color: #1a1a1a; min-height: 100vh; overflow-x: hidden;
        }
        .content { position: relative; z-index: 1; padding: 40px 60px; max-width: 900px; margin: 0 auto; }
        .back {
            display: inline-block; font-size: 14px; color: rgba(0,0,0,0.4);
            text-decoration: none; letter-spacing: 4px; margin-bottom: 60px; transition: color 0.3s;
        }
        .back:hover { color: #1a1a1a; }
        .back::before { content: '\\2190 '; }
        .section-title {
            font-size: 14px; color: rgba(0,0,0,0.4); letter-spacing: 12px;
            text-transform: uppercase; margin-bottom: 20px;
        }
        h1 { font-size: 48px; font-weight: 300; letter-spacing: 12px; margin-bottom: 24px; }
        footer {
            margin-top: 100px; padding-top: 40px; border-top: 1px solid rgba(0,0,0,0.1);
            text-align: center; font-size: 12px; color: rgba(0,0,0,0.3);
        }
"""

FOOTER = '<footer><p>&copy; 2026 元初AI &middot; ORIGIN OF INTELLIGENCE</p></footer>'

def book_id(b):
    return esc(b.get("bookId"))

def book_page_name(b):
    return "book-" + book_id(b) + ".html"

def cnt(b):
    return (b.get("noteCount") or 0) + (b.get("bookmarkCount") or 0)

# ---------- 列表页（书架形式） ----------
books = d.get("details", [])
items = []
for b in books:
    title = esc(b.get("title"))
    author = esc(b.get("author"))
    cover = esc(b.get("cover"))
    nmark = b.get("bookmarkCount") or len(b.get("marks", []))
    nnote = b.get("noteCount") or len(b.get("thoughts", []))
    cover_html = (f'<img class="cover" src="{cover}" alt="{title}" loading="lazy">'
                  if cover else '<div class="cover cover-ph"></div>')
    items.append(f"""            <a href="{book_page_name(b)}" class="book-card" title="{title}">
                <div class="cover-wrap">{cover_html}</div>
                <div class="card-title">{title}</div>
                <div class="card-author">{author}</div>
                <div class="card-meta">划线 {nmark} · 想法 {nnote}</div>
            </a>""")

list_css = BASE_CSS + """
        .intro { font-size: 16px; color: rgba(0,0,0,0.45); line-height: 1.7; max-width: 640px; margin-bottom: 50px; }
        .stats { display: flex; flex-wrap: wrap; gap: 48px; padding: 32px 0;
            border-top: 1px solid rgba(0,0,0,0.08); border-bottom: 1px solid rgba(0,0,0,0.08); margin-bottom: 16px; }
        .stat .num { font-size: 36px; font-weight: 300; letter-spacing: 1px; }
        .stat .label { font-size: 12px; color: rgba(0,0,0,0.4); letter-spacing: 3px; text-transform: uppercase; margin-top: 6px; }
        .prefer { font-size: 13px; color: rgba(0,0,0,0.4); letter-spacing: 2px; margin-bottom: 70px; }
        .prefer span { color: rgba(0,0,0,0.7); }
        /* 书架网格 */
        .shelf { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 48px 36px; }
        .book-card { text-decoration: none; display: block; }
        .cover-wrap {
            position: relative; aspect-ratio: 3 / 4; margin-bottom: 16px;
            border-radius: 4px; overflow: hidden;
            box-shadow: 0 6px 18px rgba(0,0,0,0.14), 0 1px 3px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }
        /* 书脊高光，增强书架质感 */
        .cover-wrap::before {
            content: ''; position: absolute; top: 0; left: 0; width: 6px; height: 100%;
            background: linear-gradient(90deg, rgba(0,0,0,0.18), rgba(255,255,255,0.12) 60%, rgba(0,0,0,0));
            z-index: 2; pointer-events: none;
        }
        .cover { width: 100%; height: 100%; object-fit: cover; display: block; background: #efefef; }
        .cover-ph { display: flex; }
        .book-card:hover .cover-wrap {
            transform: translateY(-6px);
            box-shadow: 0 16px 34px rgba(0,0,0,0.2), 0 2px 6px rgba(0,0,0,0.12);
        }
        .card-title { font-size: 14px; font-weight: 400; line-height: 1.45; color: rgba(0,0,0,0.82);
            letter-spacing: 0.5px; margin-bottom: 6px;
            display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
        .book-card:hover .card-title { color: #1a1a1a; }
        .card-author { font-size: 12px; color: rgba(0,0,0,0.4); margin-bottom: 4px;
            white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
        .card-meta { font-size: 11px; color: rgba(0,0,0,0.32); letter-spacing: 0.5px; }
        @media (max-width: 768px) {
            .content { padding: 30px 22px; }
            h1 { font-size: 30px; letter-spacing: 6px; }
            .stats { gap: 28px; } .stat .num { font-size: 28px; }
            .shelf { grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); gap: 32px 20px; }
        }
"""

list_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>读书笔记 - 元初AI</title>
    <style>{list_css}</style>
</head>
<body>
    <div class="content">
        <a href="../index.html" class="back">BACK</a>
        <div class="section-title">READING NOTES</div>
        <h1>读书笔记</h1>
        <p class="intro">这里是我在微信读书里划下的句子，与读到某处时写下的想法。书是输入，想法才是真正留下来的东西。点击任一本书查看全部笔记。</p>

        <div class="stats">
            <div class="stat"><div class="num">{read_hours}</div><div class="label">Hours</div></div>
            <div class="stat"><div class="num">{read_days}</div><div class="label">Days</div></div>
            <div class="stat"><div class="num">{total_books}</div><div class="label">Books</div></div>
            <div class="stat"><div class="num">{total_notes}</div><div class="label">Notes</div></div>
        </div>
        <p class="prefer">偏好领域　<span>{' · '.join(prefer)}</span></p>

        <div class="shelf">
{chr(10).join(items)}
        </div>
        {FOOTER}
    </div>
    <script defer src="/tracker.js"></script>
</body>
</html>
"""
with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
    f.write(list_html)

# ---------- 每本书页面 ----------
detail_css = BASE_CSS + """
        .book-head { display: flex; gap: 24px; align-items: flex-start; margin: 10px 0 16px; }
        .cover { width: 80px; height: 110px; object-fit: cover; border-radius: 3px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.12); flex-shrink: 0; background: #f2f2f2; }
        .book-author { font-size: 15px; color: rgba(0,0,0,0.4); margin: 14px 0 14px; }
        .book-meta2 { display: flex; gap: 20px; font-size: 13px; color: rgba(0,0,0,0.35); letter-spacing: 1px; margin-bottom: 14px; }
        .book-link { font-size: 13px; color: rgba(0,0,0,0.45); text-decoration: none; letter-spacing: 1px; transition: color 0.3s; }
        .book-link:hover { color: #1a1a1a; }
        .intro2 { font-size: 14px; line-height: 1.7; color: rgba(0,0,0,0.4); margin: 22px 0 50px;
            padding: 18px 22px; background: rgba(0,0,0,0.02); border-radius: 6px; }
        .tabs { display: flex; gap: 36px; border-bottom: 1px solid rgba(0,0,0,0.08);
            margin: 44px 0 30px; }
        .tab { background: none; border: none; padding: 0 0 14px; font-family: inherit;
            font-size: 15px; letter-spacing: 3px; color: rgba(0,0,0,0.38); cursor: pointer;
            position: relative; transition: color 0.25s; }
        .tab .cnt { font-size: 12px; letter-spacing: 0; color: rgba(0,0,0,0.28); margin-left: 5px; }
        .tab:hover { color: rgba(0,0,0,0.65); }
        .tab.active { color: #1a1a1a; }
        .tab.active::after { content: ''; position: absolute; bottom: -1px; left: 0;
            width: 100%; height: 2px; background: #1a1a1a; }
        .panel { display: none; }
        .panel.active { display: block; }
        .notes { display: flex; flex-direction: column; gap: 24px; }
        .note { display: block; text-decoration: none; color: inherit; position: relative;
            transition: background 0.25s, padding 0.25s; border-radius: 0 4px 4px 0; }
        .note:hover { background: rgba(0,0,0,0.025); }
        .note-text { font-size: 16px; line-height: 1.78; }
        .mark { padding: 4px 0 4px 18px; border-left: 2px solid rgba(0,0,0,0.15); }
        .mark:hover { border-left-color: rgba(0,0,0,0.45); }
        .mark .note-text { color: rgba(0,0,0,0.62); }
        .thought { padding: 4px 0 4px 18px; border-left: 2px solid #1a1a1a; }
        .thought .note-text { color: rgba(0,0,0,0.88); }
        .thought .ref { font-size: 13px; line-height: 1.6; color: rgba(0,0,0,0.38);
            margin-top: 8px; padding-left: 12px; border-left: 1px solid rgba(0,0,0,0.1); }
        .thought .ref::before { content: '\\539f\\6587\\ff1a'; color: rgba(0,0,0,0.3); }
        .jump { display: inline-block; font-size: 12px; color: rgba(0,0,0,0.0);
            letter-spacing: 0.5px; margin-top: 8px; transition: color 0.25s; }
        .note:hover .jump { color: rgba(0,0,0,0.4); }
        /* 公众号笔记来源文章标题 */
        .from-article { font-size: 12px; color: rgba(0,0,0,0.4); letter-spacing: 0.5px;
            margin-bottom: 8px; }
        .from-article::before { content: '\\6765\\81ea\\300a'; }
        .from-article::after { content: '\\300b'; }
        /* 不可定位的笔记（公众号划线）：不显示可点击态 */
        .note.noloc { cursor: default; }
        .note.noloc:hover { background: none; }
        .loc-notice { font-size: 12px; color: rgba(0,0,0,0.4); letter-spacing: 0.5px;
            padding: 10px 14px; margin-bottom: 6px; background: rgba(0,0,0,0.03); border-radius: 4px; }
        .empty { font-size: 15px; color: rgba(0,0,0,0.35); padding: 40px 0; }
        @media (max-width: 768px) { .content { padding: 30px 22px; } h1 { font-size: 26px; letter-spacing: 4px; } }
"""

for b in books:
    bid = book_id(b)
    title = esc(b.get("title"))
    author = esc(b.get("author"))
    cover = esc(b.get("cover"))
    intro = esc(b.get("intro"))
    if len(intro) > 160:
        intro = intro[:160] + "…"
    nmark = b.get("bookmarkCount") or len(b.get("marks", []))
    nnote = b.get("noteCount") or len(b.get("thoughts", []))
    deeplink = f"weread://reading?bId={bid}"
    mp = is_mp(bid)

    thought_html = []
    for t in (b.get("thoughts") or []):
        content = esc(t.get("content"))
        if not content:
            continue
        abstract = esc(t.get("abstract"))
        ab = f'<div class="ref">{abstract}</div>' if abstract else ""
        # 公众号：显示来源文章标题
        src = f'<div class="from-article">{esc(t.get("mpTitle"))}</div>' if (mp and t.get("mpTitle")) else ""
        link = mark_link(bid, t.get("chapterUid"), t.get("range"), mp)
        if link:
            thought_html.append(
                f'<a class="note thought" href="{link}">{src}<div class="note-text">{content}</div>{ab}'
                f'<span class="jump">在微信读书中查看 ↗</span></a>')
        else:
            thought_html.append(
                f'<div class="note thought noloc">{src}<div class="note-text">{content}</div>{ab}</div>')
    mark_html = []
    # 公众号划线无法定位到文章，整组顶部给一条说明，且不放跳转
    if mp and (b.get("marks")):
        mark_html.append('<div class="loc-notice">公众号划线暂无法定位到具体文章，点击不跳转</div>')
    for m in (b.get("marks") or []):
        text = esc(m.get("text"))
        if not text:
            continue
        link = mark_link(bid, m.get("chapterUid"), m.get("range"), mp)
        if link:
            mark_html.append(
                f'<a class="note mark" href="{link}"><div class="note-text">{text}</div>'
                f'<span class="jump">在微信读书中查看 ↗</span></a>')
        else:
            mark_html.append(
                f'<div class="note mark noloc"><div class="note-text">{text}</div></div>')

    # 想法 / 划线 两个 tab，第一个默认激活；空的 tab 不显示
    # 计数排除非笔记元素（如公众号划线的说明条）
    n_thoughts = len(thought_html)
    n_marks = sum(1 for x in mark_html if 'class="note mark' in x)
    tab_defs = []
    if thought_html:
        tab_defs.append(("我的想法", thought_html, n_thoughts))
    if mark_html:
        tab_defs.append(("划线", mark_html, n_marks))

    if not tab_defs:
        body_html = '<div class="empty">这本书暂无可展示的划线或想法（可能只有书签）。</div>'
    else:
        tabs, panels = [], []
        for i, (label, notes, count) in enumerate(tab_defs):
            act = " active" if i == 0 else ""
            tabs.append(f'<button class="tab{act}" data-tab="panel-{i}">{label}'
                        f'<span class="cnt">{count}</span></button>')
            panels.append(f'<div class="panel{act}" id="panel-{i}"><div class="notes">'
                          + "\n".join(notes) + '</div></div>')
        body_html = ('<div class="tabs">' + "".join(tabs) + '</div>'
                     + "".join(panels))

    cover_html = f'<img class="cover" src="{cover}" alt="{title}" loading="lazy">' if cover else ''
    intro_html = f'<p class="intro2">{intro}</p>' if intro else ''

    page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - 读书笔记 - 元初AI</title>
    <style>{detail_css}</style>
</head>
<body>
    <div class="content">
        <a href="index.html" class="back">读书笔记</a>
        <div class="book-head">
            {cover_html}
            <div>
                <h1 style="font-size:30px;letter-spacing:2px;font-weight:400;margin:0;">{title}</h1>
                <div class="book-author">{author}</div>
                <div class="book-meta2"><span>划线 {nmark}</span><span>想法 {nnote}</span></div>
                <a class="book-link" href="{deeplink}">在微信读书中打开 →</a>
            </div>
        </div>
        {intro_html}
        {body_html}
        {FOOTER}
    </div>
    <script>
        document.querySelectorAll('.tab').forEach(function (btn) {{
            btn.addEventListener('click', function () {{
                document.querySelectorAll('.tab').forEach(function (x) {{ x.classList.remove('active'); }});
                document.querySelectorAll('.panel').forEach(function (x) {{ x.classList.remove('active'); }});
                btn.classList.add('active');
                document.getElementById(btn.dataset.tab).classList.add('active');
            }});
        }});
    </script>
    <script defer src="/tracker.js"></script>
</body>
</html>
"""
    with open(os.path.join(OUT, book_page_name(b)), "w", encoding="utf-8") as f:
        f.write(page)

print(f"已生成 {OUT}：1 个列表页 + {len(books)} 个书页")
