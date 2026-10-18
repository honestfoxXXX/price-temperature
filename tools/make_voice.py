#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
用微软 Edge 的在线神经语音生成配音（免费，无需 key）。

    python tools/make_voice.py [日期]

输出 output/<日期>/视频/_tts4/c01.wav … c13.wav（22050Hz 单声道）

想换音色改 VOICE：
    zh-CN-YunyangNeural  男 · 资讯播报（默认，念数字最稳）
    zh-CN-YunxiNeural    男 · 温柔叙事
    zh-CN-XiaoxiaoNeural 女 · 通用
    zh-CN-YunjianNeural  男 · 体育/激昂
"""

import asyncio
import pathlib
import subprocess
import sys
import wave

import edge_tts
import imageio_ffmpeg

ROOT = pathlib.Path(__file__).resolve().parent.parent
VOICE = "zh-CN-YunyangNeural"
RATE = "+18%"

LINES = [
    "这周物价，涨的涨疯了，跌的跌得狠。",
    "先看跌的。",
    "菠菜，跌了一成。",
    "生菜，百分之九点七。",
    "平菇，百分之七点九。",
    "再看涨的。",
    "存储设备，一周涨了四成七。",
    "平板，二十三点六。",
    "奶粉，三十。",
    "内存，一年涨了近四倍。",
    "这两样先别碰。",
    "该买的趁现在，该等的别急。",
    "关注我，每周日更新。",
]


async def synth(text, mp3_path):
    await edge_tts.Communicate(text, VOICE, rate=RATE).save(str(mp3_path))


def to_wav(mp3, wav_path):
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
                    "-i", str(mp3), "-ar", "22050", "-ac", "1", "-sample_fmt", "s16",
                    str(wav_path)], check=True)


def main():
    day = sys.argv[1] if len(sys.argv) > 1 else "2026-10-18"
    outdir = ROOT / "output" / day / "视频" / "_tts4"
    outdir.mkdir(parents=True, exist_ok=True)

    total = 0.0
    for i, line in enumerate(LINES, 1):
        mp3 = outdir / ("c%02d.mp3" % i)
        wav = outdir / ("c%02d.wav" % i)
        asyncio.run(synth(line, mp3))
        to_wav(mp3, wav)
        mp3.unlink()
        with wave.open(str(wav)) as w:
            d = w.getnframes() / w.getframerate()
        total += d
        print("  c%02d %5.2fs  %s" % (i, d, line[:18]))

    print("合计 %.2fs（%s，语速 %s）" % (total, VOICE, RATE))
    return 0


if __name__ == "__main__":
    sys.exit(main())
