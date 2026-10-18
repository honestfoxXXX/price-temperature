#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
把 data/prices.json 注入 template/index.template.html，生成自包含的 index.html。

用法：
    python tools/build.py

校验不通过会直接失败并打印问题，不会产出半成品页面。
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

DATA = ROOT / "data" / "prices.json"
HIST = ROOT / "data" / "history.json"
WATCH = ROOT / "data" / "watchlist.json"
CPIDATA = ROOT / "data" / "cpi.json"
TPL = ROOT / "template" / "index.template.html"
OUT = ROOT / "index.html"
TOKEN = "__PRICE_DATA__"

VERDICTS = {"buy", "neutral", "wait", "must"}
QUALITIES = {"官方", "媒体", "估算"}
REQUIRED = ("id", "name", "spec", "verdict", "quality", "pct5", "reason", "note", "source", "asOf")


def fail(msg):
    print("  [x] " + msg)
    return 1


def main():
    errors = []

    try:
        data = json.loads(DATA.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print("[x] 找不到 %s" % DATA)
        return 1
    except json.JSONDecodeError as e:
        print("[x] JSON 语法错误：%s 行 %s 列 %s" % (e.msg, e.lineno, e.colno))
        return 1

    # ---- meta ----
    meta = data.get("meta") or {}
    for key in ("title", "tagline", "period", "asOf", "summary", "readme", "changelog"):
        if not meta.get(key):
            errors.append("meta 缺少字段：%s" % key)

    # ---- categories / items ----
    cats = data.get("categories") or []
    if not cats:
        errors.append("categories 为空")

    seen = set()
    total = 0
    for c in cats:
        for key in ("id", "name", "icon", "blurb"):
            if not c.get(key):
                errors.append("分类 %s 缺少字段 %s" % (c.get("id", "?"), key))
        for it in c.get("items") or []:
            total += 1
            tag = "%s/%s" % (c.get("id"), it.get("id", "?"))
            for key in REQUIRED:
                if it.get(key) in (None, ""):
                    errors.append("%s 缺少字段 %s" % (tag, key))
            if it.get("id") in seen:
                errors.append("条目 id 重复：%s" % it.get("id"))
            seen.add(it.get("id"))
            if it.get("verdict") not in VERDICTS:
                errors.append("%s verdict 非法：%s" % (tag, it.get("verdict")))
            if it.get("quality") not in QUALITIES:
                errors.append("%s quality 非法：%s" % (tag, it.get("quality")))
            p = it.get("pct5")
            if not isinstance(p, int) or not 0 <= p <= 100:
                errors.append("%s pct5 必须是 0-100 的整数，当前 %r" % (tag, p))
            if it.get("price") is None and not it.get("priceText"):
                errors.append("%s 既无 price 也无 priceText" % tag)
            for f in ("mom", "yoy"):
                v = it.get(f)
                if v is not None and not isinstance(v, (int, float)):
                    errors.append("%s %s 必须是数字或 null" % (tag, f))

    if not data.get("sources"):
        errors.append("sources 为空，页面页脚会没有信源")

    # ---- history ----
    hist = None
    if HIST.exists():
        try:
            hist = json.loads(HIST.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append("history.json 语法错误：%s 行 %s" % (e.msg, e.lineno))
        else:
            series = (hist or {}).get("series") or {}
            for iid, pts in series.items():
                if iid not in seen:
                    errors.append("history 里有未知条目：%s" % iid)
                    continue
                if not isinstance(pts, list) or len(pts) < 2:
                    errors.append("history.%s 少于 2 个点，画不出线" % iid)
                    continue
                for p in pts:
                    d, v = p.get("d"), p.get("v")
                    if not (isinstance(d, str) and len(d) >= 7 and d[4] == "-"):
                        errors.append("history.%s 日期格式应为 YYYY-MM：%r" % (iid, d))
                    if not isinstance(v, (int, float)):
                        errors.append("history.%s 数值非法：%r" % (iid, v))
            data["history"] = series
    else:
        print("  [!] 没有 history.json，卡片不会画走势；先跑 python tools/seed_history.py")

    # ---- 监控池 ----
    cat_ids = {c["id"] for c in cats}
    watch = []
    if WATCH.exists():
        try:
            w = json.loads(WATCH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append("watchlist.json 语法错误：%s 行 %s" % (e.msg, e.lineno))
        else:
            for it in w.get("items") or []:
                tag = "watch/%s" % it.get("id", "?")
                for key in ("id", "name", "cat", "source", "asOf"):
                    if not it.get(key):
                        errors.append("%s 缺少字段 %s" % (tag, key))
                if it.get("cat") not in cat_ids:
                    errors.append("%s 的 cat 不在品类里：%s" % (tag, it.get("cat")))
                if it.get("mom") is None and it.get("yoy") is None:
                    errors.append("%s 至少要有一个变化指标" % tag)
                if it.get("quality") not in QUALITIES:
                    errors.append("%s quality 非法：%s" % (tag, it.get("quality")))
                watch.append(it)
            data["watch"] = watch
    else:
        print("  [!] 没有 watchlist.json，监控池为空")

    # ---- CPI 分项（查漏基准）----
    if CPIDATA.exists():
        try:
            data["cpi"] = json.loads(CPIDATA.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append("cpi.json 语法错误：%s 行 %s" % (e.msg, e.lineno))
    else:
        print("  [!] 没有 cpi.json，「覆盖缺口」区块不会出现")

    if errors:
        print("[x] 校验未通过，共 %d 个问题：" % len(errors))
        for e in errors:
            print("  - " + e)
        return 1

    # ---- render ----
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if "</script" in payload.lower():
        print("[x] 数据里含有 </script，注入后会破坏页面")
        return 1

    tpl = TPL.read_text(encoding="utf-8")
    if TOKEN not in tpl:
        print("[x] 模板里找不到占位符 %s" % TOKEN)
        return 1

    OUT.write_text(tpl.replace(TOKEN, payload, 1), encoding="utf-8")

    # ---- report ----
    from collections import Counter
    vc = Counter(it["verdict"] for c in cats for it in c["items"])
    qc = Counter(it["quality"] for c in cats for it in c["items"])
    size = OUT.stat().st_size / 1024

    print("[ok] 生成 %s" % OUT)
    print("     %d 个品类 / %d 个条目 / %.1f KB" % (len(cats), total, size))
    print("     结论：现在买划算 %d · 再忍忍 %d · 价格平稳 %d · 躲不掉 %d"
          % (vc["buy"], vc["wait"], vc["neutral"], vc["must"]))
    print("     口径：官方 %d · 媒体 %d · 估算 %d" % (qc["官方"], qc["媒体"], qc["估算"]))
    if hist:
        n = len((hist.get("series") or {}))
        pts = sum(len(v) for v in (hist.get("series") or {}).values())
        print("     走势：%d 条有曲线，共 %d 个价格点" % (n, pts))
    if watch:
        print("     监控池：%d 条（不进卡片，只参与异动检测）" % len(watch))
    if data.get("cpi"):
        gaps = [r for r in data["cpi"].get("rows", []) if not r.get("covered")]
        print("     CPI %s：%d 个分项，其中 %d 个是覆盖缺口"
              % (data["cpi"]["meta"]["period"], len(data["cpi"]["rows"]), len(gaps)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
