"""把 cols×rows 透明精灵图切帧，合成透明 GIF（原尺寸与 240 版）和 APNG。用法：python3 make_gif.py 精灵图.png 4 2 输出前缀 [每帧ms]"""
import sys, subprocess
from PIL import Image
src, cols, rows, prefix = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
ms = int(sys.argv[5]) if len(sys.argv) > 5 else 180
im = Image.open(src).convert('RGBA')
W, H = im.size; cw, ch = W // cols, H // rows
frames = [im.crop((c * cw, r * ch, (c + 1) * cw, (r + 1) * ch)) for r in range(rows) for c in range(cols)]
# 统一裁到所有帧的并集包围盒，去掉多余透明边，保持帧间对齐
boxes = [f.getbbox() for f in frames]
x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes); x1 = max(b[2] for b in boxes); y1 = max(b[3] for b in boxes)
pad = 8
frames = [f.crop((max(x0 - pad, 0), max(y0 - pad, 0), min(x1 + pad, cw), min(y1 + pad, ch))) for f in frames]
# 按画面下部（桌子/地面等静止物）对齐：让每帧下 35% 区域的包围盒中心 x 与底边 y 对齐到第 1 帧
import numpy as np
def anchor(f):
    a = np.asarray(f)[..., 3]; h = a.shape[0]; ys, xs = np.where(a[int(h * 0.65):] > 128)
    return (xs.min() + xs.max()) / 2, ys.max() + int(h * 0.65)
ax, ay = anchor(frames[0]); moved = []
for f in frames:
    bx, by = anchor(f); c = Image.new('RGBA', f.size, (0, 0, 0, 0)); c.paste(f, (int(round(ax - bx)), int(round(ay - by))), f); moved.append(c)
frames = moved
def square(f, size):
    s = max(f.size); c = Image.new('RGBA', (s, s), (0, 0, 0, 0)); c.paste(f, ((s - f.size[0]) // 2, (s - f.size[1]) // 2))
    return c.resize((size, size), Image.LANCZOS)
for i, f in enumerate(frames): f.save(f'{prefix}_帧{i+1:02d}.png')
def gif(fs, out):
    # GIF 只有 1 bit 透明：alpha<128 当透明
    pal = []
    for f in fs:
        a = f.getchannel('A').point(lambda v: 255 if v >= 128 else 0)
        rgb = Image.new('RGBA', f.size, (255, 255, 255, 0)); rgb.paste(f, mask=a)
        p = rgb.convert('RGB').quantize(255, dither=Image.Dither.NONE)
        p.paste(255, mask=a.point(lambda v: 255 - v))
        pal.append(p)
    pal[0].save(out, save_all=True, append_images=pal[1:], duration=ms, loop=0, transparency=255, disposal=2, optimize=False)
big = [square(f, 480) for f in frames]
small = [square(f, 240) for f in frames]
gif(big, f'{prefix}_480.gif'); gif(small, f'{prefix}_240.gif')
big[0].save(f'{prefix}_480.png', save_all=True, append_images=big[1:], duration=ms, loop=0, disposal=1)  # APNG，保留半透明边缘
import os
for p in (f'{prefix}_480.gif', f'{prefix}_240.gif', f'{prefix}_480.png'):
    print(p, os.path.getsize(p) // 1024, 'KB')
