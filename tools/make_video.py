#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
把图卡 + 配音合成为成片 MP4。

    python tools/make_video.py [日期]

前置：先跑 tools/make_video_cards.py 生成图卡，
      并把配音 wav 放在 output/<日期>/视频/_tts/ 下（wav-01..10）。

输出：output/<日期>/视频/今天贵不贵.mp4  （1080×1920 / 30fps / 35 秒左右）
"""

import pathlib
import subprocess
import sys
import wave

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

ROOT = pathlib.Path(__file__).resolve().parent.parent
W, H = 1080, 1920
FPS = 30
DIP = 0.14            # 每张卡出入的「落到背景色」时长（秒）
GAP = 0.42            # 每张卡的余量
ZOOM_STEPS = 12
ZOOM_MAX = 1.035

BAR_H = 6
BAR_INSET = 44


def load_audio(paths):
    clips, sr = [], None
    for p in paths:
        with wave.open(str(p)) as w:
            assert w.getnchannels() == 1 and w.getsampwidth() == 2, "只支持 16bit 单声道"
            sr = sr or w.getframerate()
            assert w.getframerate() == sr
            clips.append(np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16))
    return clips, sr


def build_audio(clips, sr, durations, out_path):
    total = int(round(sum(durations) * sr))
    buf = np.zeros(total, dtype=np.int16)
    t = 0.0
    for clip, d in zip(clips, durations):
        start = int(round((t + 0.14) * sr))
        end = min(start + len(clip), total)
        buf[start:end] = clip[:end - start]
        t += d
    with wave.open(str(out_path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(buf.tobytes())
    return total / sr


def zoom_cache(path):
    """预生成一组由 1.0 到 ZOOM_MAX 的缩放帧，避免逐帧重采样。"""
    im = Image.open(path).convert("RGB")
    out = []
    for i in range(ZOOM_STEPS):
        z = 1.0 + (ZOOM_MAX - 1.0) * i / (ZOOM_STEPS - 1)
        nw, nh = int(W * z), int(H * z)
        big = im.resize((nw, nh), Image.LANCZOS)
        left, top = (nw - W) // 2, (nh - H) // 2
        out.append(big.crop((left, top, left + W, top + H)))
    return out


def main():
    day = sys.argv[1] if len(sys.argv) > 1 else None
    if not day:
        dirs = sorted((ROOT / "output").glob("*"), reverse=True)
        if not dirs:
            print("[x] output/ 下没有日期目录")
            return 1
        day = dirs[0].name

    vdir = ROOT / "output" / day / "视频"
    cards = sorted(vdir.glob("card-*.png"))
    wavs = sorted((vdir / "_tts").glob("wav-*.wav"))
    if len(cards) != len(wavs):
        print("[x] 图卡 %d 张，配音 %d 条，数量不一致" % (len(cards), len(wavs)))
        return 1

    clips, sr = load_audio(wavs)
    durations = [max(2.2, len(c) / sr + GAP) for c in clips]
    audio_path = vdir / "_audio.wav"
    total = build_audio(clips, sr, durations, audio_path)
    print("音频 %.2fs · 视频 %.2fs · %d 帧" % (len(np.concatenate(clips)) / sr, total, int(total * FPS)))

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    out_path = vdir / "今天贵不贵.mp4"
    cmd = [
        ffmpeg, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-r", str(FPS), "-i", "-",
        "-i", str(audio_path),
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart",
        str(out_path),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    n_frames = int(total * FPS)
    spans, t = [], 0.0
    for d in durations:
        spans.append((t, d))
        t += d

    cur = -1
    cache = None
    BG = Image.new("RGB", (W, H), (255, 246, 238))
    for f in range(n_frames):
        now = f / FPS
        idx = 0
        for i, (s, d) in enumerate(spans):
            if s <= now < s + d:
                idx = i
                break
        else:
            idx = len(spans) - 1
        if idx != cur:
            cur, cache = idx, zoom_cache(cards[idx])

        local = (now - spans[idx][0]) / spans[idx][1]
        step = min(ZOOM_STEPS - 1, int(local * ZOOM_STEPS))
        frame = cache[step]

        # 出入画：短暂落到背景色再起来，避免两张卡文字重影
        el = now - spans[idx][0]
        rem = spans[idx][1] - el
        if el < DIP:
            frame = Image.blend(BG, frame, el / DIP)
        elif rem < DIP:
            frame = Image.blend(BG, frame, max(0.0, rem / DIP))

        frame = frame.copy()
        d = ImageDraw.Draw(frame)
        x0, x1 = BAR_INSET, W - BAR_INSET
        y = H - 34
        d.rounded_rectangle([(x0, y), (x1, y + BAR_H)], radius=3, fill=(232, 222, 213))
        p = (now / total)
        d.rounded_rectangle([(x0, y), (x0 + int((x1 - x0) * p), y + BAR_H)], radius=3, fill=(255, 90, 31))

        proc.stdin.write(frame.tobytes())

    proc.stdin.close()
    proc.wait()

    if out_path.exists():
        print("[ok] %s  %.1f MB" % (out_path.name, out_path.stat().st_size / 1024 / 1024))
        return 0
    print("[x] 编码失败")
    return 1


if __name__ == "__main__":
    sys.exit(main())
