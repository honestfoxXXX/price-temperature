#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
榜单版成片：一屏一张榜，讲到哪条哪条高亮。

    python tools/make_video_board.py [日期]

设计要点
- 一屏只放一张榜单，所有条目同屏可见
- 配音念到哪条，白卡片滑到哪条，其余行压暗
- 行高按条数自适应，3 条和 4 条都撑满版面
"""

import math
import pathlib
import subprocess
import sys
import wave

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
FB = "C:/Windows/Fonts/msyhbd.ttc"
FR = "C:/Windows/Fonts/msyh.ttc"
FE = "C:/Windows/Fonts/seguiemj.ttf"

W, H, FPS, SR = 1080, 1920, 30, 22050
INK = (36, 26, 18)
MUTED = (166, 141, 123)
GREEN = (15, 138, 61)
RED = (211, 59, 47)
TAUPE = (150, 130, 112)
ORANGE = (255, 90, 31)
BG1, BG2 = (255, 246, 236), (255, 233, 219)
LINE = (240, 226, 214)

ROW_X, ROW_W = 54, 972
LIST_TOP, LIST_AREA = 620, 1010
DIM_ALPHA = 0.46
GAP, SLIDE = 0.18, 0.12

BOARDS = [
    {"title": "跌得最狠", "note": "本周 · 农业农村部", "color": GREEN, "caption": "叶菜整体在跌",
     "items": [
         ("🥬", "菠菜", "果蔬", "−10.5%"),
         ("🥗", "生菜", "果蔬", "−9.7%"),
         ("🍄", "平菇", "果蔬", "−7.9%"),
     ]},
    {"title": "涨得最狠", "note": "CPI · 2026 年 9 月", "color": RED, "caption": "存储涨价在往整机传",
     "items": [
         ("💻", "数据存储设备", "数码", "+46.7%"),
         ("📱", "平板电脑", "数码", "+23.6%"),
         ("🍼", "婴幼儿奶粉", "母婴教育", "+30%"),
         ("💾", "DDR5 内存条", "数码", "+380%"),
     ]},
    {"title": "先别碰", "note": "位置高，还在涨", "color": TAUPE, "caption": "",
     "items": [
         ("🎮", "显卡", "数码", "+60%"),
         ("🧥", "羽绒服", "衣着", "+12%"),
     ]},
]

SCRIPT = [
    ("intro", None), ("board", 0),
    ("item", (0, 0)), ("item", (0, 1)), ("item", (0, 2)),
    ("board", 1),
    ("item", (1, 0)), ("item", (1, 1)), ("item", (1, 2)), ("item", (1, 3)),
    ("board", 2),
    ("end", None), ("end", None),
]

_SHADOWS = {}


def lerp(a, b, t):
    return a + (b - a) * t


def ease(t):
    return 1 - (1 - t) ** 3


def bg_image():
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=(
            int(lerp(BG1[0], BG2[0], t)), int(lerp(BG1[1], BG2[1], t)),
            int(lerp(BG1[2], BG2[2], t))))
    ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    for r in (420, 560, 700):
        rd.ellipse([W // 2 - r, 1080 - r, W // 2 + r, 1080 + r], outline=(255, 178, 138, 40), width=3)
    return Image.alpha_composite(img.convert("RGBA"), ring)


def brand_layer():
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    icon = Image.open(ASSETS / "logo-icon-256.png").convert("RGBA").resize((84, 84), Image.LANCZOS)
    layer.paste(icon, (88, 84), icon)
    d = ImageDraw.Draw(layer)
    d.text((190, 96), "今天贵不贵", font=ImageFont.truetype(FB, 46), fill=INK)
    d.text((190, 150), "什么该买，什么该等", font=ImageFont.truetype(FR, 25), fill=MUTED)
    return layer


def shadow_for(h):
    if h not in _SHADOWS:
        pad = 90                                  # 留够余量，模糊才不会被画布边缘切出硬边
        s = Image.new("RGBA", (ROW_W + pad * 2, h + pad * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(s)
        d.rounded_rectangle([(pad, pad), (pad + ROW_W, pad + h)], radius=34, fill=(120, 70, 40, 54))
        _SHADOWS[h] = s.filter(ImageFilter.GaussianBlur(22))
    return _SHADOWS[h]


def row_layer(icon, name, cat, value, color, height, pop=1.0):
    s = max(1.0, min(1.32, height / 210))          # 行高越大，字越大
    im = Image.new("RGBA", (ROW_W, height), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cy = height // 2
    d.text((44, cy - 22 * s), icon, font=ImageFont.truetype(FE, int(54 * s)),
           anchor="lm", embedded_color=True)
    d.text((158, cy - 40 * s), name, font=ImageFont.truetype(FB, int(46 * s)), fill=INK)
    d.text((158, cy + 12 * s), cat, font=ImageFont.truetype(FR, int(24 * s)), fill=MUTED)
    d.text((ROW_W - 44, cy), value, font=ImageFont.truetype(FB, int(60 * s * pop)), fill=color, anchor="rm")
    return im


def draw_board(img, board, active, slide_from, slide_p, elapsed):
    n = len(board["items"])
    rh = min(340 if n <= 2 else 270, max(196, LIST_AREA // n))
    top = LIST_TOP + (LIST_AREA - n * rh) // 2

    d = ImageDraw.Draw(img)
    a = int(255 * max(0.0, min(1.0, elapsed / 0.26)))
    d.text((54, 400), board["title"], font=ImageFont.truetype(FB, 76), fill=board["color"] + (a,))
    d.text((56, 500), board["note"], font=ImageFont.truetype(FR, 27), fill=MUTED + (a,))
    if board["caption"]:
        d.text((W - 54, 518), board["caption"], font=ImageFont.truetype(FR, 25),
               fill=MUTED + (a,), anchor="ra")

    y = active if (slide_from is None or slide_p >= 1) else lerp(slide_from, active, ease(slide_p))
    card_y = int(top + y * rh)

    img.alpha_composite(shadow_for(rh), (ROW_X - 90, card_y - 90))
    ImageDraw.Draw(img).rounded_rectangle(
        [(ROW_X, card_y), (ROW_X + ROW_W, card_y + rh)], radius=34,
        fill=(255, 255, 255, a))

    for i, (icon, name, cat, value) in enumerate(board["items"]):
        # 逐行错开入场：每行晚 60ms，从左侧滑入
        ra = max(0.0, min(1.0, (elapsed - 0.06 * i) / 0.24))
        if ra <= 0.01:
            continue
        pop = 1.0
        if i == active and slide_p < 1:
            pop = 1.0 + 0.12 * math.sin(math.pi * min(1.0, slide_p))
        layer = row_layer(icon, name, cat, value, board["color"], rh, pop)
        alpha = ra * (1.0 if i == active else DIM_ALPHA)
        layer.putalpha(layer.getchannel("A").point(lambda x: int(x * alpha)))
        dx = int((1 - ease(ra)) * 46)
        img.alpha_composite(layer, (ROW_X + dx, top + i * rh))


def _num_layer(text, color, size):
    f = ImageFont.truetype(FB, size)
    probe = ImageDraw.Draw(Image.new("RGB", (10, 10)))
    w = int(probe.textlength(text, font=f)) + 20
    im = Image.new("RGBA", (w, int(size * 1.5)), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((0, 0), text, font=f, fill=color)
    return im


def _stamp(img, layer, xy, scale, alpha):
    if alpha <= 0.01:
        return
    w = max(1, int(layer.width * scale))
    h = max(1, int(layer.height * scale))
    im = layer.resize((w, h), Image.LANCZOS)
    if alpha < 1:
        im.putalpha(im.getchannel("A").point(lambda v: int(v * alpha)))
    img.alpha_composite(im, (int(xy[0]), int(xy[1])))


_INTRO_CACHE = {}


def intro_screen(img, t):
    """开场：两个极端数字依次砸进来，先把人钉住。"""
    if not _INTRO_CACHE:
        _INTRO_CACHE["up"] = _num_layer("+46.7%", RED, 190)
        _INTRO_CACHE["down"] = _num_layer("−10.5%", GREEN, 190)

    d = ImageDraw.Draw(img)
    d.text((54, 360), "涨疯了", font=ImageFont.truetype(FB, 42), fill=RED)

    p1 = min(1.0, t / 0.42)
    _stamp(img, _INTRO_CACHE["up"], (54, 400),
           1.30 - 0.30 * ease(p1), p1)

    p2 = min(1.0, max(0.0, (t - 0.55) / 0.42))
    if p2 > 0:
        d.text((54, 736), "跌得狠", font=ImageFont.truetype(FB, 42), fill=GREEN)
        _stamp(img, _INTRO_CACHE["down"], (54, 776),
               1.30 - 0.30 * ease(p2), p2)

    if t > 1.4:
        a = int(255 * min(1.0, (t - 1.4) / 0.3))
        d.line([(54, 1090), (W - 54, 1090)], fill=LINE + (a,), width=3)
        d.text((54, 1126), "2026 年 10 月 · 第 42 周", font=ImageFont.truetype(FR, 30),
               fill=MUTED + (a,))


def end_screen(img):
    d = ImageDraw.Draw(img)
    d.text((54, 590), "该买的趁现在", font=ImageFont.truetype(FB, 92), fill=INK)
    d.text((54, 710), "该等的别急", font=ImageFont.truetype(FB, 92), fill=RED)
    d.line([(54, 870), (W - 54, 870)], fill=LINE, width=3)

    d.text((54, 920), "每周日更新", font=ImageFont.truetype(FB, 50), fill=INK)
    d.text((54, 992), "一周只讲一次，讲清楚哪几样值得买、哪几样先别碰",
           font=ImageFont.truetype(FR, 30), fill=MUTED)

    bx0, by0, bx1, by1 = 54, 1100, 614, 1224
    d.rounded_rectangle([(bx0, by0), (bx1, by1)], radius=62, fill=ORANGE)
    d.text(((bx0 + bx1) / 2, (by0 + by1) / 2), "点个关注，不吃亏",
           font=ImageFont.truetype(FB, 44), fill=(255, 255, 255), anchor="mm")

    d.text((54, 1270), "下期见", font=ImageFont.truetype(FR, 30), fill=(190, 170, 156))


def build_audio(wavs, starts, total, out_path):
    buf = np.zeros(int(total * SR) + SR, dtype=np.float32)
    for p, t0 in zip(wavs, starts):
        with wave.open(str(p)) as w:
            clip = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
        i = int((t0 + 0.12) * SR)
        buf[i:i + len(clip)] += clip.astype(np.float32) / 32768.0
    for t0 in starts[2:]:
        n = int(0.05 * SR)
        i = int(t0 * SR)
        if i + n < len(buf):
            tt = np.arange(n) / SR
            buf[i:i + n] += (np.sin(2 * np.pi * 1500 * tt) * np.exp(-tt * 70) * 0.16).astype(np.float32)
    # 统一响度：不同音色的原始电平差很多，这里一律拉到接近满刻度
    peak = float(np.max(np.abs(buf))) or 1.0
    if peak > 0.02:
        buf *= min(4.0, 0.92 / peak)
    with wave.open(str(out_path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((buf * 32767).astype(np.int16).tobytes())


def main():
    day = sys.argv[1] if len(sys.argv) > 1 else "2026-10-18"
    vdir = ROOT / "output" / day / "视频"
    wavs = sorted((vdir / "_tts5").glob("c*.wav"))
    if len(wavs) != len(SCRIPT):
        print("[x] 配音 %d 条 / 脚本 %d 条，对不上" % (len(wavs), len(SCRIPT)))
        return 1

    durs = []
    for p in wavs:
        with wave.open(str(p)) as w:
            durs.append(w.getnframes() / w.getframerate())

    starts, t = [], 0.35
    for d in durs:
        starts.append(t)
        t += d + GAP
    total = t + 1.0
    print("总时长 %.2fs" % total)

    audio = vdir / "_audio_board.wav"
    build_audio(wavs, starts, total, audio)

    events, cur_idx, prev_idx = [], -1, -1
    for (kind, arg), st in zip(SCRIPT, starts):
        if kind == "intro":
            events.append((st, "intro", 0, 0))
        elif kind == "board":
            events.append((st, arg, 0, 0)); cur_idx, prev_idx = 0, 0
        elif kind == "item":
            b, i = arg
            prev_idx, cur_idx = cur_idx, i
            events.append((st, b, i, prev_idx))
        else:
            events.append((st, "end", 0, 0))

    base = bg_image()
    brand = brand_layer()

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    out = vdir / "今天贵不贵-榜单版.mp4"
    proc = subprocess.Popen([
        ffmpeg, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
        "-i", str(audio),
        "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)

    n = int(total * FPS)
    for f in range(n):
        now = f / FPS
        ev = events[0]
        for e in events:
            if e[0] <= now:
                ev = e
            else:
                break
        t0, state, active, prev = ev

        img = base.copy()
        img.alpha_composite(brand)

        if state == "intro":
            intro_screen(img, now)
        elif state == "end":
            end_screen(img)
        else:
            sp = min(1.0, (now - t0) / SLIDE) if prev != active else 1.0
            draw_board(img, BOARDS[state], active,
                       prev if prev != active else None, sp, now - t0)

        d = ImageDraw.Draw(img)
        y = H - 30
        d.rounded_rectangle([(54, y), (W - 54, y + 6)], radius=3, fill=(234, 224, 215))
        d.rounded_rectangle([(54, y), (54 + int((W - 108) * now / total), y + 6)], radius=3, fill=ORANGE)

        proc.stdin.write(img.convert("RGB").tobytes())

    proc.stdin.close()
    proc.wait()
    if out.exists():
        print("[ok] %s  %.1f MB" % (out.name, out.stat().st_size / 1024 / 1024))
        return 0
    print("[x] 失败")
    return 1


if __name__ == "__main__":
    sys.exit(main())
