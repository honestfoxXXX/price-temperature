#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用火山引擎的音频生成接口做背景音乐。

    set VOLC_KEY=你的key
    python tools/make_bgm.py [日期]

输出 output/<日期>/视频/_bgm.wav（22050Hz 单声道，长度对齐视频）

接口：POST /api/v3/tts/create
关键：X-Api-Resource-Id 必须传 seed-audio-1.0，
      不传的话网关会默认落到 volc.service_type.10074 并报 not granted。
"""

import base64
import json
import os
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
import wave

import imageio_ffmpeg

ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = "https://openspeech.bytedance.com/api/v3/tts/create"
RESOURCE = "seed-audio-1.0"

PROMPT = (
    "轻快的 lo-fi 电子背景音乐，温暖的电钢琴与柔和的鼓刷，"
    "节奏约 100 BPM，无人声，情绪克制、明亮、不焦虑，"
    "适合生活资讯类短视频做背景铺底，全程平稳，不要突然的高潮或转折，"
    "时长约 30 秒。"
)


def generate(key, prompt):
    body = {
        "model": "seed-audio-1.0",
        "text_prompt": prompt,
        "audio_config": {"format": "mp3", "sample_rate": 44100},
    }
    headers = {
        "X-Api-Key": key,
        "X-Api-Resource-Id": RESOURCE,
        "X-Api-Request-Id": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.loads(r.read())
    return base64.b64decode(data["audio"]), data.get("duration", 0)


def main():
    key = os.environ.get("VOLC_KEY")
    if not key:
        print("[x] 先设环境变量 VOLC_KEY")
        return 1
    day = sys.argv[1] if len(sys.argv) > 1 else "2026-10-18"
    vdir = ROOT / "output" / day / "视频"
    vdir.mkdir(parents=True, exist_ok=True)

    print("生成配乐…")
    audio, dur = generate(key, PROMPT)
    mp3 = vdir / "_bgm.mp3"
    mp3.write_bytes(audio)
    print("  模型输出 %.1f 秒 / %d 字节" % (dur, len(audio)))

    wav = vdir / "_bgm.wav"
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
                    "-i", str(mp3), "-ar", "22050", "-ac", "1", "-sample_fmt", "s16",
                    str(wav)], check=True)
    mp3.unlink()

    with wave.open(str(wav)) as w:
        print("  转成 wav %.2f 秒" % (w.getnframes() / w.getframerate()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
