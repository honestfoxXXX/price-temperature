#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成视频号图卡 + 字幕 + 口播稿 + 分镜表。

    python tools/make_video_cards.py

产物在 output/<日期>/视频/：
    card-01.png … card-10.png   1080×1920 竖版图卡
    字幕.srt                    逐句字幕，剪映可直接导入
    口播稿.md                   配音用
    分镜.md                     每镜画面 + 时长

图卡上只放变化幅度，不放绝对价格——价格变化每期都要重新排版，
幅度是固定模板，换数字即可。
"""

import datetime
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FONT_BOLD = "C:/Windows/Fonts/msyhbd.ttc"
FONT_REG = "C:/Windows/Fonts/msyh.ttc"

W, H = 1080, 1920
BG_TOP, BG_BOT = (255, 248, 242), (255, 238, 226)
INK = (36, 26, 18)
MUTED = (166, 141, 123)
GREEN = (15, 138, 61)
RED = (211, 59, 47)
LINE = (243, 227, 219)

# 本期内容：只填数字，模板不动
EPISODE = [
    dict(section="本周", value="+46.7%", unit="环比", name="数据存储设备", cat="数码",
         src="国家统计局 CPI · 2026 年 9 月", dur=4, hot=True),
    dict(section="跌了", value="−10.5%", unit="环比", name="菠菜", cat="果蔬",
         src="农业农村部 · 第 40 周", dur=3),
    dict(section="跌了", value="−9.7%", unit="环比", name="生菜", cat="果蔬",
         src="农业农村部 · 第 40 周", dur=3),
    dict(section="跌了", value="−7.9%", unit="环比", name="平菇", cat="果蔬",
         src="农业农村部 · 第 40 周", dur=3),
    dict(section="涨了", value="+23.6%", unit="环比", name="平板电脑", cat="数码",
         src="国家统计局 CPI · 2026 年 9 月", dur=3),
    dict(section="涨了", value="+30%", unit="同比", name="婴幼儿奶粉", cat="母婴教育",
         src="杭州网 · 2026 年 3 月", dur=3),
    dict(section="涨了", value="+380%", unit="同比", name="DDR5 内存条", cat="数码",
         src="证券时报 · 2026 年 10 月", dur=3),
    dict(section="该等", value="+60%", unit="同比", name="显卡", cat="数码",
         src="17173 · 2026 年 10 月", dur=4),
    dict(section="该等", value="+12%", unit="同比", name="羽绒服", cat="衣着",
         src="市场调研估算", dur=4),
]

END = dict(section="", value="", unit="", name="", cat="", src="", dur=5)


def bg():
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=(
            int(BG_TOP[0] + (BG_BOT[0] - BG_TOP[0]) * t),
            int(BG_TOP[1] + (BG_BOT[1] - BG_TOP[1]) * t),
            int(BG_TOP[2] + (BG_BOT[2] - BG_TOP[2]) * t),
        ))
    return img


def fit(draw, text, path, start, max_w):
    size = start
    while size > 20:
        f = ImageFont.truetype(path, size)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 4
    return ImageFont.truetype(path, 20)


def brand(img, d):
    icon = Image.open(ASSETS / "logo-icon-256.png").convert("RGBA").resize((96, 96), Image.LANCZOS)
    img.paste(icon, (88, 96), icon)
    f = ImageFont.truetype(FONT_BOLD, 52)
    d.text((204, 108), "今天贵不贵", font=f, fill=INK)
    d.text((204, 168), "什么该买，什么该等", font=ImageFont.truetype(FONT_REG, 28), fill=MUTED)


def chip(d, text, color):
    f = ImageFont.truetype(FONT_BOLD, 34)
    tw = d.textlength(text, font=f)
    x1 = W - 88 - tw - 56
    d.rounded_rectangle([(x1, 106), (W - 88, 176)], radius=35, fill=color)
    d.text((x1 + 28, 126), text, font=f, fill=(255, 255, 255))


def card(item, path):
    img = bg()
    d = ImageDraw.Draw(img)
    brand(img, d)

    color = GREEN if item["value"].startswith("−") else RED
    if item["section"] == "该等":
        color = MUTED

    chip(d, item["section"], color if item["section"] != "该等" else (150, 130, 112))

    # 主数字：垂直居中偏上
    f_num = fit(d, item["value"], FONT_BOLD, 430, 920)
    tw = d.textlength(item["value"], font=f_num)
    d.text(((W - tw) / 2, 610), item["value"], font=f_num, fill=color)

    # 口径标签
    fu = ImageFont.truetype(FONT_REG, 40)
    uw = d.textlength(item["unit"], font=fu)
    d.text(((W - uw) / 2, 610 + f_num.size + 40), item["unit"], font=fu, fill=MUTED)

    # 名称 + 品类
    fn = fit(d, item["name"], FONT_BOLD, 100, 900)
    nw = d.textlength(item["name"], font=fn)
    d.text(((W - nw) / 2, 1130), item["name"], font=fn, fill=INK)

    fc = ImageFont.truetype(FONT_REG, 40)
    cw = d.textlength(item["cat"], font=fc)
    d.text(((W - cw) / 2, 1130 + int(fn.size * 1.32)), item["cat"], font=fc, fill=MUTED)

    # 分隔线 + 来源
    d.line([(88, 1600), (W - 88, 1600)], fill=LINE, width=2)
    fs = ImageFont.truetype(FONT_REG, 28)
    d.text((88, 1632), item["src"], font=fs, fill=MUTED)
    d.text((W - 88, 1632), "每周更新", font=fs, fill=MUTED, anchor="ra")

    img.save(path, optimize=True)


def end_card(path):
    img = bg()
    d = ImageDraw.Draw(img)
    brand(img, d)

    d.text((88, 620), "该买的趁现在", font=ImageFont.truetype(FONT_BOLD, 104), fill=INK)
    d.text((88, 760), "该等的别急", font=ImageFont.truetype(FONT_BOLD, 104), fill=RED)

    d.line([(88, 960), (W - 88, 960)], fill=LINE, width=2)

    f = ImageFont.truetype(FONT_REG, 38)
    d.text((88, 1010), "70 个条目，每周日更新", font=f, fill=MUTED)
    d.text((88, 1074), "honestfoxXXX.github.io/price-temperature", font=ImageFont.truetype(FONT_BOLD, 34), fill=INK)

    icon = Image.open(ASSETS / "logo-icon-256.png").convert("RGBA").resize((180, 180), Image.LANCZOS)
    img.paste(icon, ((W - 180) // 2, 1320), icon)

    img.save(path, optimize=True)


def srt(cards):
    def ts(sec):
        h, r = divmod(sec, 3600)
        m, s = divmod(r, 60)
        return "%02d:%02d:%02d,000" % (h, m, s)

    out, t = [], 0
    for i, c in enumerate(cards):
        start = t
        t += c["dur"]
        text = "该买的趁现在，该等的别急" if i == len(cards) - 1 else (
            c["value"] + " " + c["name"])
        out.append("%d\n%s --> %s\n%s\n" % (i + 1, ts(start), ts(t), text))
    return "\n".join(out)


def main():
    day = datetime.date.today().isoformat()
    outdir = ROOT / "output" / day / "视频"
    outdir.mkdir(parents=True, exist_ok=True)

    cards = EPISODE + [END]
    for i, item in enumerate(EPISODE):
        card(item, outdir / ("card-%02d.png" % (i + 1)))
    end_card(outdir / ("card-%02d.png" % len(cards)))

    (outdir / "字幕.srt").write_text(srt(cards), encoding="utf-8")

    total = sum(c["dur"] for c in cards)
    print("[ok] %d 张图卡，总时长 %d 秒" % (len(cards), total))
    print("     %s" % outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
