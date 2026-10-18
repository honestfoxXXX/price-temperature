#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
维护 data/history.json —— 每个条目的价格时间序列。

每次更新完 data/prices.json 后跑一次：
    1. 给新条目补锚点（去年同期、上月、当前）
    2. 给已有条目追加/更新当期快照
    3. 已有的历史点一律不动

锚点是用 price / (1 + yoy) 和 price / (1 + mom) 反推的，标 t="反推"；
当期值是 prices.json 里的真实数字，标 t="实测"。

这份文件只增不减：跑得越多，曲线越密。
"""

import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRICES = ROOT / "data" / "prices.json"
HISTORY = ROOT / "data" / "history.json"
FOOD = ROOT / "data" / "food_series.json"

MIN_DELTA = 1e-9  # 仅用于浮点比较


def month_shift(ym, delta):
    """ym = '2026-10'，delta 为月份偏移，返回 'YYYY-MM'。"""
    y, m = (int(x) for x in ym.split("-"))
    idx = y * 12 + (m - 1) + delta
    return "%04d-%02d" % (idx // 12, idx % 12 + 1)


def cur_month_of(it, fallback):
    """每个条目用自己的数据时点，别用页面统一时点。
    蓝莓是 4 月应季价、手机是 3 月、笔记本是 1 月，混用会把曲线压错位置。"""
    m = str(it.get("asOf") or "")
    if len(m) >= 7 and m[4] == "-":
        return m[:7]
    return fallback


def anchors(it, cur_month):
    """由一个条目的 price / yoy / mom 反推锚点。"""
    price = it.get("price")
    if not isinstance(price, (int, float)):
        return []

    out = []
    yoy = it.get("yoy")
    if isinstance(yoy, (int, float)) and yoy > -100:
        out.append({"d": month_shift(cur_month, -12), "v": round(price / (1 + yoy / 100.0), 2), "t": "反推"})

    mom = it.get("mom")
    if isinstance(mom, (int, float)) and mom > -100:
        out.append({"d": month_shift(cur_month, -1), "v": round(price / (1 + mom / 100.0), 2), "t": "反推"})

    out.append({"d": cur_month, "v": price, "t": "实测"})
    return out


def main():
    data = json.loads(PRICES.read_text(encoding="utf-8"))
    cur_month = data["meta"]["asOf"][:7]

    if HISTORY.exists():
        hist = json.loads(HISTORY.read_text(encoding="utf-8"))
    else:
        hist = {"meta": {"createdAt": data["meta"]["asOf"],
                         "note": "每条 = 一个已知价格点。反推=由同比/环比反算，实测=当期录入。"},
                "series": {}}

    series = hist.setdefault("series", {})
    added_ids, added_pts, updated_pts = 0, 0, 0
    by_id = {}

    for c in data["categories"]:
        for it in c["items"]:
            by_id[it["id"]] = it
            fresh = anchors(it, cur_month_of(it, cur_month))
            if not fresh:
                continue
            cur = series.get(it["id"])
            if cur is None:
                series[it["id"]] = _dedupe(fresh)
                added_ids += 1
                added_pts += len(fresh)
                continue

            have = {p["d"] for p in cur}
            for p in fresh:
                if p["d"] in have:
                    # 同一月份只更新实测值，不碰历史
                    for q in cur:
                        if q["d"] == p["d"] and p["t"] == "实测" and q["v"] != p["v"]:
                            q["v"] = p["v"]
                            q["t"] = "实测"
                            updated_pts += 1
                else:
                    cur.append(p)
                    added_pts += 1
            series[it["id"]] = _dedupe(cur)

    # 真实月度序列（scrape_food.py 的产物）覆盖同期反推锚点。
    # 当期月份不用抓来的值，保留 prices.json 里录入的当期价，避免卡片和曲线打架。
    if FOOD.exists():
        food = (json.loads(FOOD.read_text(encoding="utf-8")) or {}).get("series") or {}
        for iid, by_month in food.items():
            it = by_id.get(iid)
            if not it:
                continue
            cutoff = cur_month_of(it, cur_month)
            merged = {p["d"]: p for p in series.get(iid, [])}
            for ym, v in by_month.items():
                if ym >= cutoff:
                    continue
                merged[ym] = {"d": ym, "v": round(v, 2), "t": "实测"}
            series[iid] = sorted(merged.values(), key=lambda x: x["d"])

    HISTORY.write_text(
        json.dumps(hist, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    span = [len(v) for v in series.values()]
    print("[ok] 写入 %s" % HISTORY)
    print("     覆盖 %d 个条目，共 %d 个价格点（单条最多 %d 点）"
          % (len(series), sum(span), max(span) if span else 0))
    print("     新增条目 %d · 新增数据点 %d · 更新当期 %d" % (added_ids, added_pts, updated_pts))
    return 0


def _dedupe(points):
    """同月只留一个点（实测优先），按时间排序。"""
    best = {}
    for p in points:
        old = best.get(p["d"])
        if old is None or (p.get("t") == "实测" and old.get("t") != "实测"):
            best[p["d"]] = p
    return sorted(best.values(), key=lambda x: x["d"])


if __name__ == "__main__":
    sys.exit(main())
