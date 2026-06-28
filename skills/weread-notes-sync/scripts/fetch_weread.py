#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""拉取微信读书数据（阅读统计 + 全部有笔记的书的划线与想法），写入 JSON。

用法:
    WEREAD_API_KEY=wrk-xxxx python3 fetch_weread.py [输出JSON路径]

输出默认 ./weread_data.json。API Key 必须通过环境变量 WEREAD_API_KEY 提供。
"""
import json, os, ssl, sys, time, urllib.request

API_KEY = os.environ.get("WEREAD_API_KEY", "").strip()
if not API_KEY:
    sys.exit("错误：未设置环境变量 WEREAD_API_KEY。请先执行：export WEREAD_API_KEY=wrk-你的密钥")

GW = "https://i.weread.qq.com/api/agent/gateway"
VER = "1.0.3"
OUT = sys.argv[1] if len(sys.argv) > 1 else "weread_data.json"

# 绕过代理（部分网络环境代理到不了微信读书）+ 跳过 SSL 校验（macOS Python 常缺根证书）
_ctx = ssl.create_default_context()
_ctx.check_hostname = False
_ctx.verify_mode = ssl.CERT_NONE
opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({}),
    urllib.request.HTTPSHandler(context=_ctx))


def call(api_name, **params):
    body = {"api_name": api_name, "skill_version": VER, **params}
    req = urllib.request.Request(
        GW, data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
        method="POST")
    for attempt in range(3):
        try:
            with opener.open(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            if attempt == 2:
                print(f"  ! {api_name} 失败: {e}", file=sys.stderr)
                return {}
            time.sleep(1)


out = {}

print("拉取阅读统计...", file=sys.stderr)
out["stats"] = call("/readdata/detail", mode="overall")

print("拉取笔记本列表...", file=sys.stderr)
books, last_sort = [], None
while True:
    p = {"count": 30}
    if last_sort is not None:
        p["lastSort"] = last_sort
    dd = call("/user/notebooks", **p)
    bs = dd.get("books", [])
    books.extend(bs)
    out.setdefault("notebook_meta", {
        "totalBookCount": dd.get("totalBookCount"),
        "totalNoteCount": dd.get("totalNoteCount"),
    })
    if not dd.get("hasMore") or not bs:
        break
    last_sort = bs[-1].get("sort")
out["notebooks"] = books
print(f"  共 {len(books)} 本有笔记的书", file=sys.stderr)


def total_notes(b):
    return (b.get("noteCount") or 0) + (b.get("bookmarkCount") or 0) + (b.get("reviewCount") or 0)


out["details"] = []
for b in sorted(books, key=total_notes, reverse=True):
    bid = b.get("bookId")
    book = b.get("book", {})
    print(f"拉取《{book.get('title')}》的划线与想法...", file=sys.stderr)

    bm = call("/book/bookmarklist", bookId=bid)
    marks = [{
        "text": m.get("markText", ""),
        "chapter": m.get("chapterTitle") or m.get("chapterName") or "",
        "chapterUid": m.get("chapterUid"),
        "range": m.get("range"),
        "bookmarkId": m.get("bookmarkId"),
        "createTime": m.get("createTime"),
    } for m in (bm.get("updated") or [])]

    mine = call("/review/list/mine", bookid=bid, count=50)
    thoughts = []
    for r in (mine.get("reviews") or []):
        rv = r.get("review", {}) or {}
        mp = rv.get("refMpInfo") or {}
        thoughts.append({
            "content": rv.get("content") or "",
            "abstract": rv.get("abstract") or "",
            "chapter": rv.get("chapterTitle") or "",
            "chapterUid": rv.get("chapterUid"),
            "range": rv.get("range"),
            "userVid": rv.get("userVid"),
            # 公众号笔记的来源文章标题（普通书为空）
            "mpTitle": mp.get("title") or "",
            "createTime": rv.get("createTime"),
        })

    out["details"].append({
        "bookId": bid,
        "title": book.get("title"),
        "author": book.get("author"),
        "cover": book.get("cover"),
        "intro": book.get("intro", ""),
        "noteCount": b.get("noteCount"),
        "bookmarkCount": b.get("bookmarkCount"),
        "reviewCount": b.get("reviewCount"),
        "marks": marks,
        "thoughts": thoughts,
    })

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
print(f"已写入 {OUT}（{len(out['details'])} 本书）", file=sys.stderr)
