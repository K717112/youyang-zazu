#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把对照全本拆成按卷的 Markdown 文件（原文 / 译文 / 对照）"""
import os
import re
import sys

SRC = "酉阳杂俎_原文译文对照全本.txt"

# 卷 -> (序号, 简体篇名, 繁体标题原文)
VOLS = [
    ("序", "00", "序", "序"),
    ("卷一", "01", "忠志 · 礼异 · 天咫", "卷一"),
    ("卷二", "02", "玉格 · 壶史", "卷二"),
    ("卷三", "03", "贝编", "卷三"),
    ("卷四", "04", "境异", "卷四"),
    ("卷五", "05", "怪术", "卷五"),
    ("卷六", "06", "艺绝", "卷六"),
    ("卷七", "07", "酒食", "卷七"),
    ("卷八", "08", "黥", "卷八"),
    ("卷九", "09", "事感", "卷九"),
    ("卷十", "10", "盗侠", "卷十"),
    ("卷十一", "11", "物异", "卷十一"),
    ("卷十二", "12", "语资", "卷十二"),
    ("卷十三", "13", "冥迹", "卷十三"),
    ("卷十四", "14", "诺皋记上", "卷十四"),
    ("卷十五", "15", "诺皋记下", "卷十五"),
    ("卷十六", "16", "毛篇", "卷十六"),
    ("卷十七", "17", "鳞介篇 · 虫篇", "卷十七"),
    ("卷十八", "18", "木篇", "卷十八"),
    ("卷十九", "19", "草篇", "卷十九"),
    ("卷二十", "20", "肉攫部", "卷二十"),
    ("續集·卷一", "21", "支诺皋上", "續集·卷一"),
    ("續集·卷二", "22", "支诺皋中", "續集·卷二"),
    ("續集·卷三", "23", "支诺皋下", "續集·卷三"),
    ("續集·卷四", "24", "贬误", "續集·卷四"),
    ("續集·卷五", "25", "寺塔记上", "續集·卷五"),
    ("續集·卷六", "26", "寺塔记下", "續集·卷六"),
    ("續集·卷七", "27", "金刚经鸠异", "續集·卷七"),
    ("續集·卷八", "28", "支动", "續集·卷八"),
    ("續集·卷九", "29", "支植上", "續集·卷九"),
    ("續集·卷十", "30", "支植下", "續集·卷十"),
]


def slug(num, name):
    n = name.replace(" · ", "-").replace(" ", "")
    return f"{num}-{n}"


def main():
    text = open(SRC, encoding="utf-8").read()
    # 按 【卷X】 切块
    chunks = re.split(r"\n【([^】]+)】[^\n]*\n-{10,}\n", text)
    # chunks: [前言, 卷名, 正文, 卷名, 正文, ...]
    blocks = {}
    for i in range(1, len(chunks) - 1, 2):
        head = chunks[i].strip()
        body = chunks[i + 1]
        blocks[head] = body

    made = 0
    index_rows = []
    for key, num, simp, head in VOLS:
        # 匹配 key（对照本里卷名是繁体，如 "續集·卷一"）
        body = None
        for h, b in blocks.items():
            if key in h or h == key:
                body = b
                break
        if body is None:
            print(f"MISS {key}", file=sys.stderr)
            continue

        items = []
        cur = None
        for line in body.split("\n"):
            m = re.match(r"^(\d{3})\. 原文：(.*)$", line.strip())
            if m:
                if cur:
                    items.append(cur)
                cur = {"n": m.group(1), "src": m.group(2), "tr": ""}
                continue
            m = re.match(r"^译文：(.*)$", line.strip())
            if m and cur:
                cur["tr"] = m.group(1)
        if cur:
            items.append(cur)

        title = f"{key}　{simp}" if simp != "序" else "序"
        fname = slug(num, simp) + ".md"
        index_rows.append((num, simp, len(items), fname))

        # 原文
        out = [f"# {title}", "", f"> 《酉阳杂俎》原文（繁体）· 共 {len(items)} 条", "",
               "[← 返回目录](../README.md)", "", "---", ""]
        for it in items:
            out.append(f"**{it['n']}.** {it['src']}")
            out.append("")
        open(os.path.join("原文", fname), "w", encoding="utf-8").write("\n".join(out))

        # 译文
        out = [f"# {title}", "", f"> 《酉阳杂俎》白话译文 · 共 {len(items)} 条", "",
               "[← 返回目录](../README.md)", "", "---", ""]
        for it in items:
            out.append(f"**{it['n']}.** {it['tr']}")
            out.append("")
        open(os.path.join("译文", fname), "w", encoding="utf-8").write("\n".join(out))

        # 对照
        out = [f"# {title}", "", f"> 原文 · 译文对照 · 共 {len(items)} 条", "",
               "[← 返回目录](../README.md)", "", "---", ""]
        for it in items:
            out.append(f"#### {it['n']}")
            out.append("")
            out.append(f"> {it['src']}")
            out.append("")
            out.append(it["tr"])
            out.append("")
        open(os.path.join("对照", fname), "w", encoding="utf-8").write("\n".join(out))

        made += 1
        print(f"OK {key:<10} {len(items):>4} 条  {fname}", file=sys.stderr)

    # 索引
    rows = ["| 卷 | 篇目 | 条数 | 原文 | 译文 | 对照 |", "|---|---|---:|---|---|---|"]
    for num, simp, cnt, fname in index_rows:
        rows.append(f"| {num} | {simp} | {cnt} | [原文](原文/{fname}) | [译文](译文/{fname}) | [对照](对照/{fname}) |")
    open("_index.md", "w", encoding="utf-8").write("\n".join(rows))
    print(f"\n[+] volumes={made}", file=sys.stderr)


if __name__ == "__main__":
    main()
