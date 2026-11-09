"""所有表情同时动的总览 GIF（白底）。先用 make_gif.py 把每套输出到同一个目录，再运行：
python3 overview.py [目录，默认 gif] [每行几个，默认 4]
每套帧数可以不一样（比如 8 帧和 6 帧混着），短的会循环播放。"""
import glob, os, sys
from PIL import Image
d = sys.argv[1] if len(sys.argv) > 1 else 'gif'
per_row = int(sys.argv[2]) if len(sys.argv) > 2 else 4
sets = [sorted(glob.glob(f.replace('_帧01.png', '_帧[0-9][0-9].png'))) for f in sorted(glob.glob(os.path.join(d, '*_帧01.png')))]
if not sets:
    sys.exit(f'{d}/ 下没找到 *_帧01.png，先用 make_gif.py 输出到这个目录')
rows = (len(sets) + per_row - 1) // per_row
S = 300
n = max(len(s) for s in sets)
frames = []
for i in range(n):
    c = Image.new('RGB', (S * min(per_row, len(sets)), S * rows), 'white')
    for k, fs in enumerate(sets):
        f = Image.open(fs[i % len(fs)]).convert('RGBA')
        s = max(f.size); sq = Image.new('RGBA', (s, s), (255, 255, 255, 255)); sq.alpha_composite(f, ((s - f.width) // 2, (s - f.height) // 2))
        c.paste(sq.convert('RGB').resize((S, S), Image.LANCZOS), ((k % per_row) * S, (k // per_row) * S))
    frames.append(c.quantize(255))
out = os.path.join(d, '总览.gif')
frames[0].save(out, save_all=True, append_images=frames[1:], duration=220, loop=0)
print(out, os.path.getsize(out) // 1024, 'KB')
