#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取维基文库《酉阳杂俎》原文（序 + 前集20卷 + 续集10卷）"""
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.parse

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
API = "https://zh.wikisource.org/w/api.php"

PAGES = ["酉陽雜俎/酉陽雜俎序"] + [f"酉陽雜俎/卷{n}" for n in
                                  ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
                                   "十一", "十二", "十三", "十四", "十五", "十六", "十七",
                                   "十八", "十九", "二十"]] + \
        [f"酉陽雜俎/續集/卷{n}" for n in
         ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]]


def curl(url, timeout=40):
    fd, tmp = tempfile.mkstemp()
    os.close(fd)
    cmd = ["curl", "-s", "-L", "-m", str(timeout), "-A", UA,
           "-H", "Accept-Encoding: identity", "-o", tmp, "-w", "%{http_code}", url]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout + 15)
        body = open(tmp, "rb").read()
        if body[:2] == b"\x1f\x8b":
            import gzip
            body = gzip.decompress(body)
        return int((r.stdout or "0").strip() or 0), body
    finally:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def html_to_text(h):
    h = re.sub(r"(?is)<(script|style|sup)[^>]*>.*?</\1>", "", h)
    h = re.sub(r"(?is)<br\s*/?>", "\n", h)
    h = re.sub(r"(?is)</(p|div|dd|li|h[1-6])>", "\n", h)
    h = re.sub(r"(?is)<[^>]+>", "", h)
    h = (h.replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">")
          .replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'"))
    h = re.sub(r"[ \t\u3000]+", "", h)
    h = re.sub(r"\n{2,}", "\n", h)
    return h.strip()


def fetch(page):
    q = urllib.parse.urlencode({
        "action": "parse", "page": page, "prop": "text",
        "format": "json", "formatversion": "2", "disableeditsection": "1",
    })
    status, body = curl(f"{API}?{q}")
    if status != 200:
        return None, f"HTTP {status}"
    try:
        d = json.loads(body.decode("utf-8"))
    except Exception as e:  # noqa: BLE001
        return None, f"json: {e}"
    if "error" in d:
        return None, str(d["error"].get("info"))
    return html_to_text(d["parse"]["text"]), None


def main():
    allparts = []
    for i, p in enumerate(PAGES, 1):
        txt, err = fetch(p)
        title = p.replace("酉陽雜俎/", "")
        if err:
            print(f"[{i:02d}] FAIL {title}: {err}", file=sys.stderr)
            continue
        n = len(txt)
        print(f"[{i:02d}] OK   {title}: {n} chars", file=sys.stderr)
        allparts.append((title, txt))
        time.sleep(0.5)
    # 保存分卷
    for title, txt in allparts:
        fn = "vol_" + title.replace("/", "_") + ".txt"
        with open(fn, "w", encoding="utf-8") as f:
            f.write(txt)
    full = "\n\n".join(f"【{t}】\n{x}" for t, x in allparts)
    with open("酉阳杂俎_原文全本.txt", "w", encoding="utf-8") as f:
        f.write(full)
    print(f"\n[+] volumes={len(allparts)}  total chars={len(full)}", file=sys.stderr)


if __name__ == "__main__":
    main()
