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



def gradient(size, top=BG1, bot=BG2):
    w, h = size
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / (h - 1)
        d.line([(0, y), (w, y)], fill=(
            int(top[0] + (bot[0] - top[0]) * t),
            int(top[1] + (bot[1] - top[1]) * t),
            int(top[2] + (bot[2] - top[2]) * t)))
    return img


def vertical_cover(path, size=(1080, 1440), safe=True):
    """视频号封面。3:4 用于主页和推荐流，9:16 可直接当首帧。"""
    w, h = size
    img = gradient((w, h))
    d = ImageDraw.Draw(img)

    icon = Image.open(ASSETS / "logo-icon-256.png").convert("RGBA").resize((88, 88), Image.LANCZOS)
    img.paste(icon, (72, 84), icon)
    d.text((182, 96), "今天贵不贵", font=ImageFont.truetype(FB, 46), fill=INK)
    d.text((182, 156), "什么该买，什么该等", font=ImageFont.truetype(FR, 25), fill=MUTED)

    cy = int(h * 0.40)
    d.text((72, cy - 150), "这一个月涨得最狠的", font=ImageFont.truetype(FB, 44), fill=MUTED)
    f = ImageFont.truetype(FB, 210 if w < 1100 else 190)
    d.text((64, cy - 92), "+46.7%", font=f, fill=RED)
    d.text((74, cy + 178), "数据存储设备", font=ImageFont.truetype(FB, 62), fill=INK)

    d.line([(72, cy + 286), (w - 72, cy + 286)], fill=(240, 224, 212), width=3)
    d.text((74, cy + 322), "同一个星期，叶菜在崩", font=ImageFont.truetype(FR, 34), fill=MUTED)
    d.text((74, cy + 378), "菠菜 −10.5%", font=ImageFont.truetype(FB, 58), fill=GREEN)

    d.text((74, h - 120), "第 42 周 · 每周日更新", font=ImageFont.truetype(FR, 30), fill=MUTED)
    img.save(path, optimize=True)
    return path



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

    for hh, label in ((1440, "3x4"), (1260, "6x7"), (1920, "9x16")):
        p = outdir / ("封面-视频号-%s.png" % label)
        vertical_cover(p, (1080, hh))
        print("[ok] %s  %.0f KB" % (p.name, p.stat().st_size / 1024))
    return 0


if __name__ == "__main__":
    sys.exit(main())
