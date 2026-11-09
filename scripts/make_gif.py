"""把 列×行 的精灵图切帧，合成透明 GIF（480 与 240 两个尺寸）和 APNG。

用法：python3 make_gif.py 精灵图.png 列数 行数 输出前缀 [每帧ms] [--bg auto|none|#RRGGBB] [--tol 48]

--bg 处理背景（默认 auto）：
  auto     原图本来就是透明底就不动；不是的话，从画面四周取背景色抠掉——纯色底、
           以及模型画出来的灰白棋盘格「假透明」都能抠
  none     不抠，保留原背景
  #RRGGBB  指定要抠的背景色，比如生图时要的是纯品红底就写 #FF00FF
--tol 颜色容差，抠不干净调大，抠到角色身上调小
"""
import argparse, os
import numpy as np
from PIL import Image

ap = argparse.ArgumentParser(description='精灵图切帧合成透明GIF')
ap.add_argument('src'); ap.add_argument('cols', type=int); ap.add_argument('rows', type=int); ap.add_argument('prefix')
ap.add_argument('ms', type=int, nargs='?', default=180, help='每帧毫秒，默认180')
ap.add_argument('--bg', default='auto'); ap.add_argument('--tol', type=float, default=48)
args = ap.parse_args()


def border_colors(rgb):
    """四周 3px 一圈里占比最高的颜色；第二种颜色也占得多（棋盘格）就一起返回。"""
    ring = np.concatenate([rgb[:3].reshape(-1, 3), rgb[-3:].reshape(-1, 3), rgb[:, :3].reshape(-1, 3), rgb[:, -3:].reshape(-1, 3)]).astype(int)
    q = ring // 16
    keys, inv, cnt = np.unique(q, axis=0, return_inverse=True, return_counts=True)
    order = np.argsort(-cnt)
    out = [ring[inv.ravel() == order[0]].mean(0)]
    if len(order) > 1 and cnt[order[1]] > 0.2 * len(ring):
        out.append(ring[inv.ravel() == order[1]].mean(0))
    return np.array(out)


def connected_to_edge(mask):
    """mask 里和画面边缘连通的部分（背景），不吃掉角色内部同色的地方，比如白眼珠。"""
    try:
        from scipy import ndimage
        lab, _ = ndimage.label(mask)
        edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
        return np.isin(lab, edge[edge > 0])
    except ImportError:  # 没装 scipy：从边缘一圈圈往里扩，慢一点但结果一样
        reach = np.zeros_like(mask)
        reach[0], reach[-1], reach[:, 0], reach[:, -1] = mask[0], mask[-1], mask[:, 0], mask[:, -1]
        while True:
            grow = reach.copy()
            grow[1:] |= reach[:-1]; grow[:-1] |= reach[1:]; grow[:, 1:] |= reach[:, :-1]; grow[:, :-1] |= reach[:, 1:]
            grow &= mask
            if (grow == reach).all():
                return reach
            reach = grow


def remove_bg(im, mode, tol):
    a = np.asarray(im).astype(float)
    if mode == 'none':
        return im, '保留原背景'
    if mode == 'auto' and (a[..., 3] < 16).mean() > 0.02:
        return im, '原图已是透明底'
    rgb = a[..., :3]
    keys = np.array([[int(mode[i:i + 2], 16) for i in (1, 3, 5)]], float) if mode.startswith('#') else border_colors(rgb)
    dist = np.min([np.linalg.norm(rgb - k, axis=-1) for k in keys], axis=0)
    k = keys[0]; hi, lo = k > 128, k <= 128
    vivid = len(keys) == 1 and hi.any() and lo.any() and k[hi].min() - k[lo].max() > 150
    # 绿、品红这类鲜艳底是特意选的角色身上没有的颜色，全图抠（胳膊和身子之间被围住的空隙也要抠）；
    # 白底、棋盘格只抠和边缘连通的部分，不然白眼珠、白衣服也没了
    bg = (dist < tol) if vivid else connected_to_edge(dist < tol)

    # 背景外沿是半透明过渡，颜色＝角色色×α＋背景色×(1−α)，要反推出 α 和原色，去掉绿边/紫边
    def grow(m):
        g = m.copy(); g[1:] |= m[:-1]; g[:-1] |= m[1:]; g[:, 1:] |= m[:, :-1]; g[:, :-1] |= m[:, 1:]; return g
    band = bg.copy()
    for _ in range(8 if vivid else 3):
        band = grow(band)
    band &= ~bg
    alpha = a[..., 3] / 255
    if vivid:  # 绿、品红这类鲜艳底：像素里背景色的成分（溢色）有多少，就透明多少
        span = k[hi].min() - k[lo].max()
        spill = rgb[..., hi].min(-1) - rgb[..., lo].max(-1)
        sa = np.clip(1 - spill / span, 0, 1)
        band |= spill > 0.35 * span  # 离边远、但明显混了背景色的半透明处（光晕、发丝）也算
        alpha = np.where(band, np.minimum(alpha, sa), alpha)
        fg = np.where(band[..., None], (rgb - (1 - sa[..., None]) * k) / np.maximum(sa[..., None], 0.05), rgb)
    else:  # 白底、棋盘格：角色色取紧挨着的内侧像素，按投影反推
        key = keys[np.argmin([np.linalg.norm(rgb - kk, axis=-1) for kk in keys], axis=0)]
        known = ~bg & ~band; f = np.where(known[..., None], rgb, 0.0); n = known.astype(float)
        for _ in range(4):  # 把内侧颜色一圈圈往外推到过渡带上
            s = np.zeros_like(f); c = np.zeros_like(n)
            for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                s += np.roll(f * n[..., None], (dy, dx), (0, 1)); c += np.roll(n, (dy, dx), (0, 1))
            new = band & (n == 0) & (c > 0)
            f[new] = s[new] / c[new][:, None]; n = np.where(new, 1.0, n)
        d = f - key
        pa = np.clip(((rgb - key) * d).sum(-1) / np.maximum((d * d).sum(-1), 1), 0, 1)
        alpha = np.where(band & (n > 0), np.minimum(alpha, pa), alpha)
        fg = np.where((band & (n > 0))[..., None], f, rgb)
    alpha = np.where(bg, 0, alpha)
    out = np.dstack([np.clip(fg, 0, 255), alpha * 255]).astype(np.uint8)
    kind = '棋盘格假透明' if len(keys) > 1 else '纯色背景 #%02X%02X%02X' % tuple(int(v) for v in keys[0])
    msg = f'抠掉了{kind}（背景占 {bg.mean():.0%}）'
    if len(keys) > 1 or keys.min() > 200:
        msg += '\n提醒：白底和棋盘格会把角色的白描边、白字幕一起抠掉。先看一眼帧图，缺了就重出一张纯品红或纯绿底的'
    return Image.fromarray(out, 'RGBA'), msg


im = Image.open(args.src).convert('RGBA')
im, how = remove_bg(im, args.bg, args.tol)
print('背景：', how)
W, H = im.size; cw, ch = W // args.cols, H // args.rows
frames = [im.crop((c * cw, r * ch, (c + 1) * cw, (r + 1) * ch)) for r in range(args.rows) for c in range(args.cols)]
empty = [i + 1 for i, f in enumerate(frames) if f.getbbox() is None]
if empty:
    print('提醒：第', empty, '格是空的，检查列数行数对不对')
    frames = [f for f in frames if f.getbbox() is not None]
# 统一裁到所有帧的并集包围盒，去掉多余透明边，保持帧间对齐
boxes = [f.getbbox() for f in frames]
x0 = min(b[0] for b in boxes); y0 = min(b[1] for b in boxes); x1 = max(b[2] for b in boxes); y1 = max(b[3] for b in boxes)
pad = 8
frames = [f.crop((max(x0 - pad, 0), max(y0 - pad, 0), min(x1 + pad, cw), min(y1 + pad, ch))) for f in frames]


# 按画面下部（字幕、脚、桌子这类静止的东西）对齐：让每帧下 35% 区域的包围盒中心 x 与底边 y 对齐到第 1 帧
def anchor(f):
    al = np.asarray(f)[..., 3]; h = al.shape[0]; ys, xs = np.where(al[int(h * 0.65):] > 128)
    if len(xs) == 0:
        ys, xs = np.where(al > 128); return (xs.min() + xs.max()) / 2, ys.max()
    return (xs.min() + xs.max()) / 2, ys.max() + int(h * 0.65)


ax, ay = anchor(frames[0]); moved = []
for f in frames:
    bx, by = anchor(f); c = Image.new('RGBA', f.size, (0, 0, 0, 0)); c.paste(f, (int(round(ax - bx)), int(round(ay - by))), f); moved.append(c)
frames = moved


def square(f, size):
    s = max(f.size); c = Image.new('RGBA', (s, s), (0, 0, 0, 0)); c.paste(f, ((s - f.size[0]) // 2, (s - f.size[1]) // 2))
    return c.resize((size, size), Image.LANCZOS)


for i, f in enumerate(frames):
    f.save(f'{args.prefix}_帧{i + 1:02d}.png')


def gif(fs, out):
    # GIF 只有 1 bit 透明：alpha<128 当透明
    pal = []
    for f in fs:
        a = f.getchannel('A').point(lambda v: 255 if v >= 128 else 0)
        rgb = Image.new('RGBA', f.size, (255, 255, 255, 0)); rgb.paste(f, mask=a)
        p = rgb.convert('RGB').quantize(255, dither=Image.Dither.NONE)
        p.paste(255, mask=a.point(lambda v: 255 - v))
        pal.append(p)
    pal[0].save(out, save_all=True, append_images=pal[1:], duration=args.ms, loop=0, transparency=255, disposal=2, optimize=False)


big = [square(f, 480) for f in frames]
small = [square(f, 240) for f in frames]
gif(big, f'{args.prefix}_480.gif'); gif(small, f'{args.prefix}_240.gif')
big[0].save(f'{args.prefix}_480.png', save_all=True, append_images=big[1:], duration=args.ms, loop=0, disposal=1)  # APNG，保留半透明边缘
print(len(frames), '帧')
for p in (f'{args.prefix}_480.gif', f'{args.prefix}_240.gif', f'{args.prefix}_480.png'):
    print(p, os.path.getsize(p) // 1024, 'KB')
