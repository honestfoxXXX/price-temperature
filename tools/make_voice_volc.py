#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
火山引擎（豆包语音合成 2.0）配音生成。

    set VOLC_KEY=你的key
    python tools/make_voice_volc.py <音色ID> [日期]

输出 output/<日期>/视频/_tts5/c01.wav … c13.wav（22050Hz 单声道）

音色说明：
    内置音色（seed-tts-2.0）：
        zh_male_yangguangqingnian_uranus_bigtts    阳光青年 · 有冲劲
        zh_female_gaolengyujie_uranus_bigtts       高冷御姐 · 冷静
        zh_female_shuangkuaisisi_uranus_bigtts     爽快思思 · 口语
    复刻音色（seed-icl-2.0，S_ 开头）：
        需要控制台单独开通「声音复刻」，否则报
        resource_id=volc.seedicl.default not granted
"""

import base64
import json
import os
import pathlib
import subprocess
import sys
import urllib.request
import uuid
import wave

import imageio_ffmpeg

ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
SPEECH_RATE = 20          # [-50,100]，100 = 2 倍速
# 部分复刻音色对 speech_rate 不敏感（实测 20/40/70 时长几乎一样），
# 用 ffmpeg 的 atempo 兜底变速，保持音高不变。
TEMPO = float(os.environ.get("VOLC_TEMPO", "1.0"))
# 若设了目标总长（秒），生成后统一按比值变速，让不同音色的成片长度一致
TARGET = float(os.environ.get("VOLC_TARGET", "22"))

LINES = [
    "你知道有样东西，一个月涨了四成七吗？",
    "存储设备。",
    "就是它，一个月就涨了四成七。",
    "平板跟着涨，两成三。",
    "内存更狠，一年涨了近四倍。",
    "但另一边，叶菜在崩。菠菜，跌了一成。",
    "生菜，九点七。",
    "平菇，七点九。",
    "显卡，先别碰。",
    "视频会员，四年涨了四次。",
    "关注我，每周日更新。",
]


def synth(text, speaker, key):
    resource = "seed-icl-2.0" if speaker.startswith("S_") else "seed-tts-2.0"
    body = {
        "user": {"uid": "price-temperature"},
        "req_params": {
            "text": text,
            "speaker": speaker,
            "audio_params": {"format": "mp3", "sample_rate": 24000,
                             "speech_rate": SPEECH_RATE},
        },
    }
    headers = {
        "X-Api-Key": key,
        "X-Api-Resource-Id": resource,
        "X-Api-Request-Id": str(uuid.uuid4()),
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        raw = r.read()

    audio = bytearray()
    for line in raw.decode("utf-8", "ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("data"):
            audio.extend(base64.b64decode(obj["data"]))
        code = obj.get("code")
        if code not in (0, None, 20000000):
            raise RuntimeError("code=%s %s" % (code, obj.get("message")))
    if not audio:
        raise RuntimeError("没有收到音频数据")
    return bytes(audio)


def to_wav(mp3, wav_path):
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", str(mp3)]
    if abs(TEMPO - 1.0) > 0.01:
        cmd += ["-filter:a", "atempo=%.3f" % TEMPO]
    cmd += ["-ar", "22050", "-ac", "1", "-sample_fmt", "s16", str(wav_path)]
    subprocess.run(cmd, check=True)


def main():
    DEFAULT_VOICE = "S_Dvf6T9yi2"       # 自己的复刻音色
    speaker = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_VOICE
    day = sys.argv[2] if len(sys.argv) > 2 else "2026-10-18"
    key = os.environ.get("VOLC_KEY")
    if not key:
        print("[x] 先设环境变量 VOLC_KEY")
        return 1

    outdir = ROOT / "output" / day / "视频" / "_tts5"
    outdir.mkdir(parents=True, exist_ok=True)
    for old in list(outdir.glob("c*.wav")) + list(outdir.glob("c*.mp3")):
        old.unlink()          # 清掉上一轮的残留，条数变了才不会错位

    total = 0.0
    for i, line in enumerate(LINES, 1):
        mp3 = outdir / ("c%02d.mp3" % i)
        wav = outdir / ("c%02d.wav" % i)
        mp3.write_bytes(synth(line, speaker, key))
        to_wav(mp3, wav)
        mp3.unlink()
        with wave.open(str(wav)) as w:
            d = w.getnframes() / w.getframerate()
        total += d
        print("  c%02d %5.2fs  %s" % (i, d, line[:18]))

    if TARGET > 0 and total > 0:
        ratio = total / TARGET
        if ratio > 1.02:
            for i in range(1, len(LINES) + 1):
                wav = outdir / ("c%02d.wav" % i)
                tmp = outdir / ("c%02d_t.wav" % i)
                subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
                                "-i", str(wav), "-filter:a", "atempo=%.3f" % ratio,
                                "-ar", "22050", "-ac", "1", "-sample_fmt", "s16", str(tmp)],
                               check=True)
                tmp.replace(wav)
            total = sum(wave.open(str(outdir / ("c%02d.wav" % i))).getnframes() /
                        wave.open(str(outdir / ("c%02d.wav" % i))).getframerate()
                        for i in range(1, len(LINES) + 1))
            print("  按目标 %.1fs 变速 %.2fx → 实际 %.2fs" % (TARGET, ratio, total))
    print("合计 %.2fs（%s，atempo %.2f）" % (total, speaker, TEMPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
