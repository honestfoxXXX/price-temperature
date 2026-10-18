#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从品牌图标生成各平台尺寸。

源文件：assets/logo-icon-1024.png（由品牌方提供的总览图裁切而来，圆角透明）

    python tools/make_logo.py
"""

import pathlib

from PIL import Image, ImageDraw

ASSETS = pathlib.Path(__file__).resolve().parent.parent / "assets"
SRC = ASSETS / "logo-icon-1024.png"


def circle(img):
    s = img.size[0]
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, s - 1, s - 1), fill=255)
    out = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def fullbleed(img, zoom=1.09):
    """放大裁回，让四角被渐变填满——给会被裁成方/圆的平台用。"""
    s = img.size[0]
    big = img.resize((int(s * zoom), int(s * zoom)), Image.LANCZOS)
    off = (big.size[0] - s) // 2
    return big.crop((off, off, off + s, off + s))


def main():
    if not SRC.exists():
        print("[x] 缺少 %s" % SRC)
        return 1
    icon = Image.open(SRC).convert("RGBA")

    # 头像：圆形，不透明底
    round_img = circle(icon)
    for size in (1024, 512, 256):
        round_img.resize((size, size), Image.LANCZOS).save(
            ASSETS / ("logo-round-%d.png" % size), optimize=True)

    # 方形满版
    sq = fullbleed(icon)
    for size in (1024, 512):
        sq.resize((size, size), Image.LANCZOS).save(
            ASSETS / ("logo-square-%d.png" % size), optimize=True)

    # 网页用小图标
    for size in (256, 128, 64, 32):
        icon.resize((size, size), Image.LANCZOS).save(
            ASSETS / ("logo-icon-%d.png" % size), optimize=True)

    for p in sorted(ASSETS.glob("logo-*.png")):
        print("  %-24s %4.0f KB" % (p.name, p.stat().st_size / 1024))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
