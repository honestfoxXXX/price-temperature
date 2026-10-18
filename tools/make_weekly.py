#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
每周发布用的素材生成器。

跑完之后 output/<日期>/ 里会有：
    长图.png      整页截图，无损
    长图.jpg      同一张图的 JPG，公众号上传用这个（体积小得多）

用法：
    python tools/build.py          # 先确保 index.html 是最新的
    python tools/make_weekly.py

依赖本机的 Microsoft Edge（无头模式截图）。
"""

import datetime
import pathlib
import re
import subprocess
import sys
import tempfile

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parent.parent
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
WIDTH = 750           # 公众号按 750 显示，1:1 取图，避免缩放糊掉
MAX_H = 20000

PROBE = """
<script>
window.addEventListener("load", function(){
  var h = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
  document.title = "H=" + h;
});
</script>
</body>
"""


def file_url(p):
    return pathlib.Path(p).resolve().as_uri()


def measure_height(html_path):
    """让页面把自己的高度写进 title，再用 --dump-dom 读回来。"""
    src = html_path.read_text(encoding="utf-8")
    tmp = pathlib.Path(tempfile.gettempdir()) / "_measure.html"
    tmp.write_text(src.replace("</body>", PROBE), encoding="utf-8")

    out = subprocess.run(
        [EDGE, "--headless=new", "--disable-gpu", "--dump-dom",
         "--virtual-time-budget=5000", f"--window-size={WIDTH},900",
         "--user-data-dir=" + str(pathlib.Path(tempfile.gettempdir()) / "_edgedata"),
         file_url(tmp)],
        capture_output=True, text=True, encoding="utf-8", errors="ignore", timeout=120,
    ).stdout

    m = re.search(r"<title>H=(\d+)</title>", out)
    return int(m.group(1)) if m else None


def shoot(html_path, out_path, height):
    subprocess.run(
        [EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars",
         "--virtual-time-budget=6000",
         f"--window-size={WIDTH},{height}",
         "--user-data-dir=" + str(pathlib.Path(tempfile.gettempdir()) / "_edgedata"),
         "--screenshot=" + str(out_path),
         file_url(html_path)],
        capture_output=True, timeout=180,
    )


def main():
    html_path = ROOT / "index.html"
    if not html_path.exists():
        print("[x] 没有 index.html，先跑 python tools/build.py")
        return 1

    day = datetime.date.today().isoformat()
    outdir = ROOT / "output" / day
    outdir.mkdir(parents=True, exist_ok=True)

    print("测量页面高度…")
    h = measure_height(html_path)
    if not h:
        print("[x] 没拿到页面高度，Edge 可能没启动成功")
        return 1
    h = min(h + 40, MAX_H)
    print("  高度 %d px，按 %d 宽截图" % (h, WIDTH))

    raw = outdir / "长图.png"
    print("截图…")
    shoot(html_path, raw, h)
    if not raw.exists():
        print("[x] 截图失败")
        return 1

    im = Image.open(raw)
    print("  原始 %dx%d" % im.size)

    # 公众号上传用 JPG，体积小很多，手机加载快
    jpg = outdir / "长图.jpg"
    im.convert("RGB").save(jpg, quality=88, optimize=True, progressive=True)

    for p in (raw, jpg):
        print("  %-10s %6.0f KB  %dx%d" % (p.name, p.stat().st_size / 1024, *Image.open(p).size))
    print("\n输出目录：%s" % outdir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
