#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清洗维基文库残留，合并为《酉阳杂俎》原文全本 + 卷目索引"""
import json
import os
import re
import sys

ORDER = (["酉陽雜俎序"] +
         [f"卷{n}" for n in ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十",
                            "十一", "十二", "十三", "十四", "十五", "十六", "十七",
                            "十八", "十九", "二十"]] +
         [f"續集_卷{n}" for n in ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]])

# 卷名（维基标题行里的篇目）
VOL_TITLE = {
    "卷一": "忠志 · 禮異 · 天咫",
    "卷二": "玉格 · 壺史",
    "卷三": "貝編",
    "卷四": "境異",
    "卷五": "怪術",
    "卷六": "藝絕",
    "卷七": "酒食",
    "卷八": "黥",
    "卷九": "事感",
    "卷十": "盜俠",
    "卷十一": "物異",
    "卷十二": "語資",
    "卷十三": "冥跡",
    "卷十四": "諾皋記上",
    "卷十五": "諾皋記下",
    "卷十六": "毛篇",
    "卷十七": "鱗介篇 · 蟲篇",
    "卷十八": "木篇",
    "卷十九": "草篇",
    "卷二十": "肉攫部",
    "續集_卷一": "支諾皋上",
    "續集_卷二": "支諾皋中",
    "續集_卷三": "支諾皋下",
    "續集_卷四": "貶誤",
    "續集_卷五": "寺塔記上",
    "續集_卷六": "寺塔記下",
    "續集_卷七": "金剛經鳩異",
    "續集_卷八": "支動",
    "續集_卷九": "支植上",
    "續集_卷十": "支植下",
}

DROP_EXACT = {
    "目錄", "酉陽雜俎", "全書始", "下一卷▶", "上一卷◀", "→", "←",
    "姊妹计划:数据项", "姊妹计划：数据项",
}
DROP_RE = [
    r"^此作品在全世界都属于公有领域",
    r"^Publicdomain",
    r"^姊妹计划",
    r"^[←→]+$",
    r"^下一卷",
    r"^上一卷",
]


def clean_line(l):
    l = l.strip().replace("\u3000", "")
    if not l:
        return None
    if l in DROP_EXACT:
        return None
    for pat in DROP_RE:
        if re.search(pat, l):
            return None
    # 去掉维基内链残留 [1] 之类
    l = re.sub(r"\[\d+\]", "", l)
    l = l.strip()
    if not l:
        return None
    # 纯页眉：卷X / 卷二十 / 續集·卷X
    if re.fullmatch(r"(續集[·/]?)?卷[一二三四五六七八九十]+", l):
        return None
    return l


def main():
    volumes = []
    for name in ORDER:
        fn = f"vol_{name}.txt"
        if not os.path.exists(fn):
            print(f"MISSING {fn}", file=sys.stderr)
            continue
        raw = open(fn, encoding="utf-8").read()
        lines = [clean_line(x) for x in raw.split("\n")]
        lines = [x for x in lines if x]

        # 第一行若为卷标题（含卷名/篇目名），剥掉
        if lines:
            head = lines[0]
            if len(head) <= 20 and ("卷" in head or "雜俎" in head or "忠志" in head):
                lines = lines[1:]

        # 合并被硬断的行：不以句末标点结尾且下一行不像新条目首句时拼接
        # （维基按“条”分段，一般一行一条；此处仅处理明显截断的小字注）
        merged = []
        for l in lines:
            if merged and merged[-1].endswith(("（", "(", "「", "：", ":")) and len(merged[-1]) < 12:
                merged[-1] += l
            else:
                merged.append(l)

        title = "序" if name == "酉陽雜俎序" else (
            name.replace("續集_", "續集·").replace("卷", "卷")
        )
        meta = VOL_TITLE.get(name, "")
        volumes.append({"name": name, "label": title, "meta": meta, "items": merged})
        # 每卷单独落一个 clean 文件，供翻译使用
        with open(f"clean_{name}.txt", "w", encoding="utf-8") as cf:
            for i, it in enumerate(merged, 1):
                cf.write(f"{i:03d}. {it}\n")
        print(f"{name:<12} 条目 {len(merged):>4}  字数 {sum(len(x) for x in merged):>6}", file=sys.stderr)

    # 输出全本
    out = []
    out.append("《酉阳杂俎》原文全本")
    out.append("唐·段成式 撰")
    out.append("（据维基文库整理，繁体原文，共序 + 前集二十卷 + 续集十卷）")
    out.append("")
    for v in volumes:
        head = f"【{v['label']}】" + (f"　{v['meta']}" if v['meta'] else "")
        out.append(head)
        out.append("")
        for i, it in enumerate(v["items"], 1):
            out.append(f"{i:03d}. {it}")
        out.append("")
    full = "\n".join(out)
    with open("酉阳杂俎_原文全本.txt", "w", encoding="utf-8") as f:
        f.write(full)

    total_items = sum(len(v["items"]) for v in volumes)
    total_chars = sum(len(x) for v in volumes for x in v["items"])
    print(f"\n[+] 卷数 {len(volumes)}  条目 {total_items}  字数 {total_chars}", file=sys.stderr)
    json.dump(volumes, open("_clean.json", "w", encoding="utf-8"), ensure_ascii=False)


if __name__ == "__main__":
    main()
