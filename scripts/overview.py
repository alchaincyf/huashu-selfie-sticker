# 所有表情同时动的总览 GIF（每行4个，白底）：先用 make_gif.py 把每套输出到 gif/ 下，再运行本脚本
import glob
from PIL import Image
sets = sorted(glob.glob('gif/*_帧01.png'))
rows = (len(sets) + 3) // 4
S = 300
frames = []
for i in range(8):
    c = Image.new('RGB', (S * 4, S * rows), 'white')
    for k, first in enumerate(sets):
        f = Image.open(first.replace('_帧01', f'_帧{i+1:02d}')).convert('RGBA')
        s = max(f.size); sq = Image.new('RGBA', (s, s), (255, 255, 255, 255)); sq.alpha_composite(f, ((s - f.width) // 2, (s - f.height) // 2))
        c.paste(sq.convert('RGB').resize((S, S), Image.LANCZOS), ((k % 4) * S, (k // 4) * S))
    frames.append(c.quantize(255))
frames[0].save('总览.gif', save_all=True, append_images=frames[1:], duration=220, loop=0)
import os; print(os.path.getsize('总览.gif') // 1024, 'KB')
