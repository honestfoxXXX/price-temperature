#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
动效版成片：数字滚动 + 逐层入场 + 音效，逐帧程序化绘制。

    python tools/make_video_motion.py [日期]

和 make_video.py 的区别：那个是把静态图卡拼起来，这个每一帧都是现画的，
所以数字会真的滚动起来。

输出：output/<日期>/视频/今天贵不贵-动效版.mp4
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

W, H, FPS = 1080, 1920, 30
INK = (36, 26, 18)
MUTED = (166, 141, 123)
GREEN = (15, 138, 61)
RED = (211, 59, 47)
ORANGE = (255, 90, 31)
BG1, BG2 = (255, 246, 236), (255, 233, 219)
GAP = 0.42
SR = 22050

EPISODE = [
    ("本周", "+46.7%", "环比", "数据存储设备", "数码", "国家统计局 CPI · 2026 年 9 月"),
    ("跌了", "−10.5%", "环比", "菠菜", "果蔬", "农业农村部 · 第 40 周"),
    ("跌了", "−9.7%", "环比", "生菜", "果蔬", "农业农村部 · 第 40 周"),
    ("跌了", "−7.9%", "环比", "平菇", "果蔬", "农业农村部 · 第 40 周"),
    ("涨了", "+23.6%", "环比", "平板电脑", "数码", "国家统计局 CPI · 2026 年 9 月"),
    ("涨了", "+30%", "同比", "婴幼儿奶粉", "母婴教育", "杭州网 · 2026 年 3 月"),
    ("涨了", "+380%", "同比", "DDR5 内存条", "数码", "证券时报 · 2026 年 10 月"),
    ("该等", "+60%", "同比", "显卡", "数码", "17173 · 2026 年 10 月"),
    ("该等", "+12%", "同比", "羽绒服", "衣着", "市场调研估算"),
]
END_CARD = True


def ease_out(t):
    return 1 - (1 - t) ** 3


def parse_value(s):
    sign = -1 if s.startswith("−") or s.startswith("-") else 1
    body = s.lstrip("−-+").rstrip("%")
    v = float(body) * sign
    dec = 1 if "." in body else 0
    return v, dec


def bg_image():
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=(
            int(BG1[0] + (BG2[0] - BG1[0]) * t),
            int(BG1[1] + (BG2[1] - BG1[1]) * t),
            int(BG1[2] + (BG2[2] - BG1[2]) * t)))
    # 背景同心环，呼应雷达图标
    ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    cx, cy = W // 2, 880
    for r in (300, 430, 560):
        rd.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 180, 140, 46), width=3)
    return Image.blend(img, Image.alpha_composite(img.convert("RGBA"), ring).convert("RGB"), 1.0)


def brand_layer():
    """顶部品牌区，每帧都一样，预渲染一次。"""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    icon = Image.open(ASSETS / "logo-icon-256.png").convert("RGBA").resize((96, 96), Image.LANCZOS)
    layer.paste(icon, (88, 96), icon)
    d = ImageDraw.Draw(layer)
    d.text((204, 108), "今天贵不贵", font=ImageFont.truetype(FB, 52), fill=INK)
    d.text((204, 168), "什么该买，什么该等", font=ImageFont.truetype(FR, 28), fill=MUTED)
    return layer


def chip(d, text, color):
    f = ImageFont.truetype(FB, 34)
    tw = d.textlength(text, font=f)
    x1 = W - 88 - tw - 56
    d.rounded_rectangle([(x1, 106), (W - 88, 176)], radius=35, fill=color)
    d.text((x1 + 28, 126), text, font=f, fill=(255, 255, 255))


def fit(d, text, path, start, max_w):
    size = start
    while size > 24:
        f = ImageFont.truetype(path, size)
        if d.textlength(text, font=f) <= max_w:
            return f
        size -= 6
    return ImageFont.truetype(path, 24)


def draw_card(base, brand, item, p, appear):
    """p: 0→1 卡片内进度；appear: 0→1 入场透明度"""
    img = base.copy()
    img.alpha_composite(brand)

    if item is None:                      # 结尾卡
        d = ImageDraw.Draw(img)
        a = int(255 * appear)
        d.text((88, 640), "该买的趁现在", font=ImageFont.truetype(FB, 104), fill=INK + (a,))
        d.text((88, 780), "该等的别急", font=ImageFont.truetype(FB, 104), fill=RED + (a,))
        d.text((88, 1010), "70 个条目，每周日更新", font=ImageFont.truetype(FR, 36), fill=MUTED + (a,))
        d.text((88, 1074), "honestfoxXXX.github.io/price-temperature",
               font=ImageFont.truetype(FB, 32), fill=INK + (a,))
        icon = Image.open(ASSETS / "logo-icon-256.png").convert("RGBA").resize((180, 180), Image.LANCZOS)
        icon.putalpha(icon.getchannel("A").point(lambda x: int(x * appear)))
        img.alpha_composite(icon, ((W - 180) // 2, 1300))
        return img

    section, value, unit, name, cat, src = item
    d = ImageDraw.Draw(img)

    color = GREEN if value.startswith("−") else RED
    if section == "该等":
        color = (150, 130, 112)

    chip(d, section, color if section != "该等" else (150, 130, 112))

    target, dec = parse_value(value)

    # 数字滚动：前 0.9 秒从 0 数到目标，之后停住
    span = 0.9
    k = ease_out(min(1.0, p * DRAW_TIME / span))
    cur = target * k
    txt = ("−" if cur < -0.05 else "+") + ("%.*f" % (dec, abs(cur))) + "%"

    f_num = fit(d, "+%.*f%%" % (dec, abs(target)), FB, 430, 900)
    tw = d.textlength(txt, font=f_num)
    d.text(((W - tw) / 2, 610), txt, font=f_num, fill=color)

    # 单位与名称：数字停稳后才淡入
    a2 = max(0.0, min(1.0, (p * DRAW_TIME - span) / 0.35))
    if a2 > 0:
        al = int(255 * a2)
        fu = ImageFont.truetype(FR, 40)
        uw = d.textlength(unit, font=fu)
        d.text(((W - uw) / 2, 610 + f_num.size + 40), unit, font=fu, fill=MUTED + (al,))

        fn = fit(d, name, FB, 100, 900)
        nw = d.textlength(name, font=fn)
        d.text(((W - nw) / 2, 1130), name, font=fn, fill=INK + (al,))

        fc = ImageFont.truetype(FR, 40)
        cw = d.textlength(cat, font=fc)
        d.text(((W - cw) / 2, 1130 + int(fn.size * 1.32)), cat, font=fc, fill=MUTED + (al,))

        fs = ImageFont.truetype(FR, 26)
        d.line([(88, 1600), (W - 88, 1600)], fill=(243, 227, 219) + (al,), width=2)
        d.text((88, 1632), src, font=fs, fill=MUTED + (al,))
        d.text((W - 88, 1632), "每周更新", font=fs, fill=MUTED + (al,), anchor="ra")

    return img


DRAW_TIME = 2.6      # 每张卡的有效动作时长（秒），用来算动效进度


def build_audio(wavs, durations, out_path):
    clips = []
    for p in wavs:
        with wave.open(str(p)) as w:
            clips.append(np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16))

    total = int(round(sum(durations) * SR))
    buf = np.zeros(total, dtype=np.float32)
    t = 0.0
    lands = []
    for clip, d in zip(clips, durations):
        start = int(round((t + 0.14) * SR))
        buf[start:start + len(clip)] += clip.astype(np.float32) / 32768.0
        lands.append(t + min(DRAW_TIME, d) * 0.42)
        t += d

    def tick(at, amp=0.28):
        n = int(0.06 * SR)
        i = int(at * SR)
        if i + n >= len(buf):
            return
        tt = np.arange(n) / SR
        sig = np.sin(2 * np.pi * 1800 * tt) * np.exp(-tt * 55) * amp
        buf[i:i + n] += sig.astype(np.float32)

    def whoosh(at, amp=0.10):
        n = int(0.34 * SR)
        i = int(at * SR)
        if i + n >= len(buf):
            return
        rng = np.random.default_rng(7)
        noise = rng.normal(0, 1, n)
        env = np.hanning(n) ** 1.5
        buf[i:i + n] += (noise * env * amp).astype(np.float32)

    for at in lands:
        tick(at)
    t = 0.0
    for d in durations[:-1]:
        t += d
        whoosh(t - 0.16)

    peak = float(np.max(np.abs(buf))) or 1.0
    if peak > 0.98:
        buf *= 0.98 / peak

    with wave.open(str(out_path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((buf * 32767).astype(np.int16).tobytes())


def main():
    day = sys.argv[1] if len(sys.argv) > 1 else "2026-10-18"
    vdir = ROOT / "output" / day / "视频"
    wavs = sorted((vdir / "_tts").glob("wav-*.wav"))
    if not wavs:
        print("[x] 找不到配音 wav")
        return 1

    durs = []
    for p in wavs:
        with wave.open(str(p)) as w:
            durs.append(max(2.2, w.getnframes() / w.getframerate() + GAP))

    audio_path = vdir / "_audio_motion.wav"
    build_audio(wavs, durs, audio_path)

    base = bg_image().convert("RGBA")
    brand = brand_layer()

    spans, t = [], 0.0
    for d in durs:
        spans.append((t, d))
        t += d
    total = t

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    out = vdir / "今天贵不贵-动效版.mp4"
    proc = subprocess.Popen([
        ffmpeg, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
        "-i", str(audio_path),
        "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart",
        str(out)], stdin=subprocess.PIPE)

    n = int(total * FPS)
    print("渲染 %d 帧 · %.2fs" % (n, total))
    bar_layer = None
    for f in range(n):
        now = f / FPS
        idx = 0
        for i, (s, d) in enumerate(spans):
            if s <= now < s + d:
                idx = i
                break
        else:
            idx = len(spans) - 1

        s, d = spans[idx]
        p = (now - s) / DRAW_TIME
        appear = min(1.0, (now - s) / 0.22)
        item = EPISODE[idx] if idx < len(EPISODE) else None
        frame = draw_card(base, brand, item, p, appear)

        d2 = ImageDraw.Draw(frame)
        x0, x1, y = 44, W - 44, H - 34
        d2.rounded_rectangle([(x0, y), (x1, y + 6)], radius=3, fill=(232, 222, 213))
        d2.rounded_rectangle([(x0, y), (x0 + int((x1 - x0) * now / total), y + 6)], radius=3, fill=ORANGE)

        proc.stdin.write(frame.convert("RGB").tobytes())

    proc.stdin.close()
    proc.wait()
    if out.exists():
        print("[ok] %s  %.1f MB" % (out.name, out.stat().st_size / 1024 / 1024))
        return 0
    print("[x] 失败")
    return 1


if __name__ == "__main__":
    sys.exit(main())
