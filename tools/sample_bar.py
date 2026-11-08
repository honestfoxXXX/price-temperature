"""样片：横向条形图 + 数字滚动 + 镜头推近 + 卡片入场（5 秒，无声）。"""
import math, pathlib, subprocess
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS = 1080, 1920, 30
DUR = 5.0
SAFE = 104
RIGHT = W - SAFE
FB = 'C:/Windows/Fonts/msyhbd.ttc'
FR = 'C:/Windows/Fonts/msyh.ttc'
FE = 'C:/Windows/Fonts/seguiemj.ttf'
INK = (43, 33, 27)
MUTED = (128, 107, 93)
RED = (207, 59, 49)
ORANGE = (255, 90, 31)
BG1, BG2 = (255, 246, 236), (255, 233, 219)

ROWS = [
    ('💾', '数据存储设备', 46.7),
    ('📱', '平板电脑', 23.6),
    ('💻', '计算机', 21.8),
    ('📞', '移动电话机', 14.9),
]
MAXV = 46.7
ROW_TOP, ROW_H = 540, 268
OUT = pathlib.Path(__file__).resolve().parents[1] / 'output' / '2026-11-08'


def font(size, bold=True, emoji=False):
    return ImageFont.truetype(FE if emoji else (FB if bold else FR), size)


def ease(t):
    return 1 - (1 - t) ** 3


def bg():
    img = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / (H - 1)
        d.line([(0, y), (W, y)], fill=(255,
                                       int(BG1[1] + (BG2[1] - BG1[1]) * t),
                                       int(BG1[2] + (BG2[2] - BG1[2]) * t)))
    return img.convert('RGBA')


def bar_gradient(width):
    """横向渐变条，带圆角由调用方处理。"""
    w = max(1, int(width))
    g = Image.new('RGBA', (w, 26), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    for x in range(w):
        t = x / max(1, w - 1)
        d.line([(x, 0), (x, 25)], fill=(int(255 - 48 * t), int(138 - 79 * t), int(76 - 27 * t), 255))
    return g


def frame(t):
    img = bg()
    d = ImageDraw.Draw(img)
    art = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    a = ImageDraw.Draw(art)

    # 品牌
    icon = Image.open(pathlib.Path(__file__).resolve().parents[1] / 'assets/logo-icon-128.png')
    icon = icon.convert('RGBA').resize((78, 78), Image.LANCZOS)
    art.paste(icon, (SAFE, 96), icon)
    a.text((SAFE + 98, 104), '今天贵不贵', font=font(44), fill=INK)
    a.text((SAFE + 98, 160), '什么该买，什么该等', font=font(24, False), fill=MUTED)

    # 标题（0–0.3s 入场）
    p = min(1.0, t / 0.32)
    a.text((SAFE, 330 + int((1 - ease(p)) * 26)), '这些，比一年前贵多少',
           font=font(68), fill=INK + (int(255 * p),))

    # 强调线
    a.rounded_rectangle((SAFE, 430, SAFE + int(120 * ease(p)), 436), radius=3, fill=ORANGE + (int(255 * p),))

    for i, (ic, name, v) in enumerate(ROWS):
        t0 = 0.30 + i * 0.13
        rp = min(1.0, max(0.0, (t - t0) / 0.30))
        if rp <= 0:
            continue
        y = ROW_TOP + i * ROW_H + int((1 - ease(rp)) * 46)
        alpha = int(255 * ease(rp))

        a.text((SAFE, y + 4), ic, font=font(50, emoji=True), embedded_color=True)
        a.text((SAFE + 68, y), name, font=font(46), fill=INK + (alpha,))

        # 数字滚动
        bp = min(1.0, max(0.0, (t - t0 - 0.06) / 0.95))
        cur = v * ease(bp)
        txt = '+%.1f%%' % cur
        a.text((RIGHT, y - 6), txt, font=font(64), fill=RED + (alpha,), anchor='ra')

        # 条形：轨道 + 渐变填充
        ty = y + 118
        a.rounded_rectangle((SAFE, ty, RIGHT, ty + 26), radius=13, fill=(240, 226, 214, alpha))
        blen = int((RIGHT - SAFE) * (v / MAXV) * ease(bp))
        if blen > 8:
            g = bar_gradient(blen)
            mask = Image.new('L', (blen, 26), 0)
            ImageDraw.Draw(mask).rounded_rectangle((0, 0, blen - 1, 25), radius=13, fill=255)
            if alpha < 255:
                mask = mask.point(lambda x: int(x * alpha / 255))
            art.paste(g, (SAFE, ty), mask)

    # 底部一行结论
    cp = min(1.0, max(0.0, (t - 2.4) / 0.5))
    if cp > 0:
        a.text((SAFE, 1640 + int((1 - ease(cp)) * 20)), '同一条链：存储涨，整机跟着涨',
               font=font(40), fill=MUTED + (int(255 * ease(cp)),), )

    img.alpha_composite(art)

    # 镜头：缓慢推近
    z = 1.0 + 0.035 * (t / DUR)
    nw, nh = int(W * z), int(H * z)
    cam = img.convert('RGB').resize((nw, nh), Image.LANCZOS)
    left, top = (nw - W) // 2, (nh - H) // 2
    return cam.crop((left, top, left + W, top + H))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    dst = OUT / '样片-条形图.mp4'
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    proc = subprocess.Popen([ff, '-y', '-loglevel', 'error',
                             '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '%dx%d' % (W, H),
                             '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'medium',
                             '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(dst)],
                            stdin=subprocess.PIPE)
    n = int(DUR * FPS)
    for f in range(n):
        proc.stdin.write(frame(f / FPS).tobytes())
    proc.stdin.close()
    proc.wait()
    for at in (0.9, 2.0, 3.4, 4.8):
        frame(at).save(OUT / ('样片帧-%0.1fs.png' % at))
    print('sample:', dst, round(dst.stat().st_size / 1024 / 1024, 2), 'MB')


if __name__ == '__main__':
    main()
