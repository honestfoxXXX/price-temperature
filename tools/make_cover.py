#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成公众号头条封面（2.35:1）。

    python tools/make_cover.py [日期]

输出 output/<日期>/封面.png  1350×575（公众号建议 900×383，给 1.5 倍更清晰）
"""

import datetime
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FB = "C:/Windows/Fonts/msyhbd.ttc"
FR = "C:/Windows/Fonts/msyh.ttc"

W, H = 1350, 575
INK = (36, 26, 18)
MUTED = (166, 141, 123)
RED = (211, 59, 47)
GREEN = (15, 138, 61)
BG1, BG2 = (255, 248, 242), (255, 233, 218)


def main():
    day = sys.argv[1] if len(sys.argv) > 1 else datetime.date.today().isoformat()
    outdir = ROOT / "output" / day
    outdir.mkdir(parents=True, exist_ok=True)

    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=(
            int(BG1[0] + (BG2[0] - BG1[0]) * t),
            int(BG1[1] + (BG2[1] - BG1[1]) * t),
            int(BG1[2] + (BG2[2] - BG1[2]) * t)))

    icon = Image.open(ASSETS / "logo-icon-256.png").convert("RGBA").resize((64, 64), Image.LANCZOS)
    img.paste(icon, (72, 52), icon)
    d.text((150, 58), "今天贵不贵", font=ImageFont.truetype(FB, 34), fill=INK)
    d.text((150, 100), "什么该买，什么该等", font=ImageFont.truetype(FR, 19), fill=MUTED)

    f = ImageFont.truetype(FB, 82)
    d.text((72, 210), "吃的在", font=f, fill=INK)
    x = 72 + d.textlength("吃的在", font=f)
    d.text((x, 210), "跌", font=f, fill=GREEN)
    x += d.textlength("跌", font=f)
    d.text((x, 210), "，用的在", font=f, fill=INK)
    x += d.textlength("，用的在", font=f)
    d.text((x, 210), "涨", font=f, fill=RED)
    d.text((x + d.textlength("涨", font=f), 210), "。", font=f, fill=INK)

    d.text((74, 340), "第 42 周 · 70 个条目 · 15 个品类",
           font=ImageFont.truetype(FR, 26), fill=MUTED)

    d.line([(72, 400), (W - 72, 400)], fill=(240, 224, 212), width=2)
    d.text((74, 430), "猪肉、蓝莓、蔬菜在低位；显卡、视频会员先别碰",
           font=ImageFont.truetype(FR, 24), fill=(140, 120, 108))

    out = outdir / "封面.png"
    img.save(out, optimize=True)
    print("[ok] %s  %dx%d  %.0f KB" % (out, W, H, out.stat().st_size / 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
