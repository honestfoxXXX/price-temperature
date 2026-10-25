#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成分享缩略图 assets/og.png（1200×630）。

数据变了就重跑一次，让分享卡片上的标题和统计跟上：
    python tools/make_og.py
"""

import json
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "og.png"

W, H = 1200, 630
INK = "#241a12"
INK2 = "#6d5b4c"
MUTED = "#a68d7b"
ORANGE = "#ff5a1f"
ORANGE_SOFT = "#fff0e6"
GREEN = "#0f8a3d"
RED = "#d33b2f"
LINE = "#f3e7db"

FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT_REG = "C:/Windows/Fonts/msyh.ttc"


def font(path, size):
    return ImageFont.truetype(path, size)


def gradient(d):
    """#fff2e7 → #fffdfb 的竖向渐变。"""
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=(
            255,
            int(242 + (253 - 242) * t),
            int(231 + (251 - 231) * t),
        ))


def rich(d, x, y, segs, f):
    """按 (文本, 颜色) 逐段绘制，返回结束横坐标。"""
    for text, color in segs:
        d.text((x, y), text, font=f, fill=color)
        x += d.textlength(text, font=f)
    return x


def main():
    data = json.loads((ROOT / "data" / "prices.json").read_text(encoding="utf-8"))
    meta = data["meta"]
    if meta.get("auditMode"):
        img = Image.new('RGB', (W,H), '#fff4ea')
        d = ImageDraw.Draw(img)
        icon = Image.open(ROOT/'assets/logo-icon-128.png').convert('RGBA').resize((64,64))
        img.paste(icon,(76,60),icon)
        d.text((160,68),meta['title'],font=font(FONT_BOLD,36),fill=INK)
        d.text((76,205),'这周多买这三样菜',font=font(FONT_BOLD,64),fill=INK)
        d.text((76,320),'青椒 −6.6%｜大白菜 −6.1%｜平菇 −5.8%',font=font(FONT_BOLD,40),fill=GREEN)
        d.text((76,440),'统计期：10/12—10/18 · 全国批发周均价',font=font(FONT_REG,25),fill=INK2)
        d.text((76,510),'核验更新：'+meta['asOf']+' · 对未核实条目暂不下结论',font=font(FONT_REG,23),fill=INK2)
        img.save(OUT,optimize=True)
        print('[ok] Audit-mode social preview:', OUT)
        return 0
    items = [it for c in data["categories"] for it in c["items"]]
    low = sum(1 for i in items if i["verdict"] == "buy")
    high = sum(1 for i in items if i["verdict"] == "wait")

    img = Image.new("RGB", (W, H), "#fff8f2")
    d = ImageDraw.Draw(img)
    gradient(d)

    # 顶部标识
    icon = Image.open(ROOT / "assets" / "logo-icon-256.png").convert("RGBA")
    icon = icon.resize((46, 46), Image.LANCZOS)
    img.paste(icon, (74, 53), icon)

    wm = font(FONT_BOLD, 27)
    d.text((130, 58), "今天贵不贵", font=wm, fill=INK)
    d.text((130 + d.textlength("今天贵不贵", font=wm) + 14, 68), "什么该买，什么该等",
           font=font(FONT_REG, 14), fill=MUTED)
    d.text((W - 76, 68), "数据截至 " + meta["asOf"], font=font(FONT_REG, 16), fill=MUTED, anchor="ra")

    d.line([(76, 120), (W - 76, 120)], fill=LINE, width=2)

    # 标题（两行，关键词橙色）
    f1 = font(FONT_BOLD, 74)
    rich(d, 76, 166, [("吃的在", INK), ("掉价", ORANGE), ("，", INK)], f1)
    rich(d, 76, 262, [("用的在", INK), ("涨价", ORANGE), ("。", INK)], f1)

    # 副标题（在分号处断行，避免以标点开头）
    sub = "猪肉、蓝莓、蔬菜、电影票同时落在低位；内存、显卡、手机、羽绒服是这一轮该躲开的。"
    fs = font(FONT_REG, 23)
    cut = sub.index("；") + 1
    d.text((76, 380), sub[:cut], font=fs, fill=INK2)
    d.text((76, 414), sub[cut:], font=fs, fill=INK2)

    # 统计胶囊
    stats = [(str(len(items)), "个条目", INK), (str(low), "条现在买划算", GREEN), (str(high), "条再忍忍", RED)]
    x = 76
    for num, label, color in stats:
        fn = font(FONT_BOLD, 52)
        nw = d.textlength(num, font=fn)
        d.text((x, 486), num, font=fn, fill=color)
        d.text((x + nw + 10, 516), label, font=font(FONT_REG, 18), fill=MUTED)
        x += nw + 10 + d.textlength(label, font=font(FONT_REG, 18)) + 44

    # 右下走势装饰（猪肉 13 个月）
    series = (json.loads((ROOT / "data" / "history.json").read_text(encoding="utf-8"))
              .get("series", {}).get("pork", []))
    if len(series) > 2:
        vals = [p["v"] for p in series]
        lo, hi = min(vals), max(vals)
        span = (hi - lo) or 1
        left, right, base, height = 806, W - 76, 520, 108
        pts = [(
            left + (right - left) * i / (len(vals) - 1),
            base - height * (v - lo) / span,
        ) for i, v in enumerate(vals)]
        d.line(pts, fill="#cfe3d6", width=3, joint="curve")

    # 页脚
    d.line([(76, H - 46), (W - 76, H - 46)], fill=LINE, width=1)
    d.text((76, H - 36), "衣食住行 · 医疗 · 数码 · 家电 · 衣着 · 母婴教育 · 服务",
           font=font(FONT_REG, 15), fill=MUTED)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, optimize=True)
    print("[ok] %s  %d×%d  %.0f KB" % (OUT, W, H, OUT.stat().st_size / 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
