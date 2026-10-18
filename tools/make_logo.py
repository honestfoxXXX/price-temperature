#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
生成品牌头像 / 图标（2048 与 1024 两档）。

    python tools/make_logo.py

橙色渐变 + 白色「价」字，和站点 header 的 mark 完全一致。
"""

import pathlib

from PIL import Image, ImageDraw, ImageFont

S = 2048
CHAR = "价"
FONT = "C:/Windows/Fonts/msyhbd.ttc"
C1, C2 = (0xFF, 0x6A, 0x1A), (0xFF, 0x9A, 0x3D)
OUT = pathlib.Path(__file__).resolve().parent.parent / "assets"


def gradient(size):
    img = Image.new("RGB", (size, size))
    px = img.load()
    span = 2 * size - 2
    for y in range(size):
        for x in range(size):
            t = (x + y) / span
            px[x, y] = (
                int(C1[0] + (C2[0] - C1[0]) * t),
                int(C1[1] + (C2[1] - C1[1]) * t),
                int(C1[2] + (C2[2] - C1[2]) * t),
            )
    return img


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    base = gradient(S)

    d = ImageDraw.Draw(base)
    f = ImageFont.truetype(FONT, int(S * 0.52))
    d.text((S // 2, S // 2 - int(S * 0.02)), CHAR, font=f, fill="#ffffff", anchor="mm")

    # 满版方形（被裁成圆也安全）
    square = base.copy()
    square.save(OUT / "logo-square-2048.png", optimize=True)
    square.resize((1024, 1024), Image.LANCZOS).save(OUT / "logo-square-1024.png", optimize=True)

    # 圆形
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, S - 1, S - 1), fill=255)
    circle = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    circle.paste(square, (0, 0), mask)
    circle.save(OUT / "logo-round-2048.png", optimize=True)
    circle.resize((1024, 1024), Image.LANCZOS).save(OUT / "logo-round-1024.png", optimize=True)

    # 圆角方形
    r = int(S * 0.23)
    mask2 = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask2).rounded_rectangle((0, 0, S - 1, S - 1), radius=r, fill=255)
    rounded = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    rounded.paste(square, (0, 0), mask2)
    rounded.save(OUT / "logo-rounded-2048.png", optimize=True)
    rounded.resize((512, 512), Image.LANCZOS).save(OUT / "logo-512.png", optimize=True)

    for n in sorted(p.name for p in OUT.glob("logo-*.png")):
        print("  %-24s %4.0f KB" % (n, (OUT / n).stat().st_size / 1024))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
