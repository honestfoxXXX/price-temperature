#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从「中国农业农村信息网」(agri.cn) 抓《国内外农产品市场动态》周报，
把猪肉、牛羊肉、白条鸡、鸡蛋、蔬菜、水果、草鱼 的周均价按月采样，
写入 data/food_series.json。

用法：
    python tools/scrape_food.py            # 采最近 12 个月
    python tools/scrape_food.py --months 24

前置：无。结果由 seed_history.py 合并进 history.json。
说明：每月取该月最后一期周报，作为该月的代表值。
"""

import argparse
import collections
import json
import pathlib
import re
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "food_series.json"
BASE = "https://www.agri.cn/sj/jcyj/"
UA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

# 报告里的名称 -> 站点条目 id
FIELD_MAP = {
    "猪肉": "pork",
    "牛肉": "beef",
    "羊肉": "lamb",
    "白条鸡": "chicken",
    "鸡蛋": "egg",
    "蔬菜28": "veg",
    "水果6": "fruit",
    "草鱼": "fish",
}


def get(url, timeout=25):
    """抓页面并按实际编码解码。agri.cn 老页面有 gb2312，直接当 utf-8 读会全是乱码。"""
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read()
    head = raw[:400].decode("latin-1", "ignore")
    m = re.search(r'charset=["\']?([\w-]+)', head, re.I)
    cands = []
    if m:
        cands.append(m.group(1).lower().replace("gb2312", "gb18030"))
    cands += ["utf-8", "gb18030", "gbk"]
    best = ""
    for enc in cands:
        try:
            t = raw.decode(enc)
        except Exception:
            continue
        if t.count("猪肉") > best.count("猪肉"):
            best = t
    return best or raw.decode("utf-8", "ignore")


def collect_index(pages=26):
    """翻列表页，收集周报链接。"""
    found = {}
    for i in range(1, pages + 1):
        suffix = "index.htm" if i == 1 else "index_%d.htm" % i
        try:
            html = get(BASE + suffix)
        except Exception:
            continue
        for m in re.finditer(
            r'<a[^>]+href="([^"]*t(20\d{6})_\d+\.htm)"[^>]*>(.*?)</a>', html, re.S
        ):
            url, date, title = m.group(1), m.group(2), re.sub(r"<[^>]+>", "", m.group(3))
            if "国内外农产品市场动态" not in title:
                continue
            if url.startswith("./"):
                url = BASE + url[2:]
            elif url.startswith("/"):
                url = "https://www.agri.cn" + url
            found[date] = (url, title.strip())
        time.sleep(0.25)
    return found


def parse(html):
    """从一期周报正文里抽各项周均价（元/公斤）。"""
    # 正文里的数字常被 <span lang="EN-US"> 包着，先剥掉标签再匹配
    text = re.sub(r"<[^>]+>", "", html)
    text = (text.replace("&nbsp;", " ").replace("\u00a0", " ")
                .replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">"))
    text = re.sub(r"[ \t\r\n]+", " ", text)

    vals = {}
    for key in ("猪肉", "牛肉", "羊肉", "白条鸡", "鸡蛋"):
        m = re.search(key + r"[^。；]{0,30}?每公斤\s*([\d.]+)\s*元", text)
        if m:
            vals[key] = float(m.group(1))

    m = re.search(r"28种蔬菜[^。；]{0,30}?每公斤\s*([\d.]+)\s*元", text)
    if m:
        vals["蔬菜28"] = float(m.group(1))
    m = re.search(r"6种水果[^。；]{0,30}?每公斤\s*([\d.]+)\s*元", text)
    if m:
        vals["水果6"] = float(m.group(1))

    # 水产写成"鲫鱼、花鲢鱼、…每公斤分别为19.35元、17.56元…"，按名字对位取草鱼
    for sent in re.split(r"[。；]", text):
        if "分别为" not in sent or "每公斤" not in sent or "草鱼" not in sent:
            continue
        left, right = sent.split("分别为", 1)
        names = []
        for raw in re.split(r"[、和]", left):
            n = re.sub(r"^.*?[）)]", "", raw)
            n = re.sub(r"(批发市场|周均价|均价|价格).*$", "", n).strip()
            if n:
                names.append(n)
        nums = [float(x) for x in re.findall(r"([\d.]+)\s*元", right)]
        if len(names) == len(nums) and "草鱼" in names:
            vals["草鱼"] = nums[names.index("草鱼")]
        break
    return vals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--months", type=int, default=12)
    args = ap.parse_args()

    prices = json.loads((ROOT / "data" / "prices.json").read_text(encoding="utf-8"))
    cur = prices["meta"]["asOf"][:7]

    print("收集周报列表…")
    found = collect_index()
    if not found:
        print("[x] 没拿到任何周报链接，站点结构可能变了")
        return 1
    dates = sorted(found)
    print("  共 %d 期，%s ~ %s" % (len(dates), dates[0], dates[-1]))

    # 每月取最后一期
    by_month = collections.defaultdict(list)
    for d in dates:
        by_month[d[:6]].append(d)
    months = sorted(by_month)[-args.months:]
    print("  采样月份：%s ~ %s（%d 个月）" % (months[0], months[-1], len(months)))

    data = collections.defaultdict(dict)
    for ym in months:
        d = max(by_month[ym])
        url = found[d][0]
        try:
            vals = parse(get(url))
        except Exception as e:
            print("  %s 抓取失败：%s" % (d, e))
            continue
        if not vals:
            print("  %s 解析为空，跳过" % d)
            continue
        for k, v in vals.items():
            data[FIELD_MAP[k]]["%s-%s" % (ym[:4], ym[4:6])] = v
        print("  %s  %d 项" % (d, len(vals)))
        time.sleep(0.4)

    OUT.write_text(
        json.dumps({"generatedAt": prices["meta"]["asOf"], "series": data},
                   ensure_ascii=False, indent=1),
        encoding="utf-8",
    )

    keys = sorted(FIELD_MAP.values())
    print("\n写入 %s" % OUT)
    print("月份   " + " ".join("%-7s" % k for k in keys))
    for ym in months:
        row = " ".join("%-7s" % data[k].get(ym, "--") for k in keys)
        print(ym + " " + row)
    return 0


if __name__ == "__main__":
    sys.exit(main())
