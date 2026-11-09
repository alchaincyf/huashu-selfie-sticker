# huashu-selfie-sticker

做一整套透明底的动态表情包。可以从一张自拍开始，也可以从任意一张图（宠物、手绘、吉祥物、物品）或者一句话开始。

![demo](assets/demo.gif)

上面这8个表情是用这个 skill 做出来的：一张照片先画成Q版角色设定图，再用设定图当参考，让每个表情画成一张4×2的精灵图（8格是一段连续动作，底下一句同样的字幕），最后用脚本切帧、对齐、合成GIF。

![角色设定图](assets/character-sheet.jpg)

## 它做什么

- **第零步：找生图工具**。先用你的 Agent 自带的生图能力：Codex 的 image_gen、豆包里的生图、WorkBuddy 里的混元生图，都直接用。找不到就给你几条路选：你提供一个图片API、调用你电脑上的其他工具，或者它写好提示词、你拿去豆包或即梦生成再发回来
- **第一步：定角色**。照片里的人画成Q版；宠物、手绘、吉祥物保留它本来的样子；什么图都没有就按你的描述设计一个。产出一张角色设定图，把形象锁住
- **第二步：定表情**。一起定下每个表情的字幕和动作
- **第三步：画精灵图**。用设定图当参考，每个表情一张多格精灵图。网格跟着生图工具支持的比例走，16:9是4×2共8帧，方图是3×3共9帧
- **第四步：切帧合成**。输出每一帧的PNG、480和240两个尺寸的透明GIF、保留半透明边缘的APNG，以及所有表情同时动的总览GIF。生图工具出不了透明底也没关系：让它画纯品红或纯绿底，脚本会自动抠掉

作者实测用的是即梦里的 Seedream 5.5（16:9，2K，背景选「透明背景」），9张图都是一次出的，8套64格字幕没有错字。

## 安装

在支持 skill 的 Agent 里直接说：

```
请帮我安装这个Skill：https://github.com/alchaincyf/huashu-selfie-sticker
```

或者手动把仓库克隆到 Agent 的 skills 目录里，例如：

```bash
git clone https://github.com/alchaincyf/huashu-selfie-sticker.git ~/.claude/skills/huashu-selfie-sticker
```

切帧脚本需要 Python 3、Pillow 和 numpy（装了 scipy 抠背景更快，可选）：

```bash
pip install pillow numpy
```

## 用法

对你的 Agent 说其中一句就行：

- 「用这张照片帮我做一套动态表情包」，把照片给它
- 「把这只猫做成表情包」「把我画的这个小人做成会动的表情」，把图给它
- 「帮我做一套上班摸鱼的柴犬表情包」，什么图都不用给

它会先确认用什么生图，出角色设定图让你确认，再跟你一起定表情和字幕，最后切帧出GIF。

只想用脚本也可以：

```bash
python3 scripts/make_gif.py 精灵图.png 4 2 gif/收到马上改 200   # 4列2行，每帧200毫秒
python3 scripts/make_gif.py 精灵图.png 3 3 gif/在吗 200 --bg "#00FF00"   # 纯绿底的方图
python3 scripts/overview.py   # 把 gif/ 下所有表情拼成一张总览GIF
```

要上架表情平台的话，先去平台查当下的尺寸、大小和帧数要求，这里的240版本不保证合规。

## 经验会越用越多

`经验.md` 记着用过的人踩到的坑和管用的写法，skill 每次开始前会读它，做完会把新发现补进去。

## 关注作者

![关注花叔](https://raw.githubusercontent.com/alchaincyf/alchaincyf/main/assets/follow.svg)

---

## English

Make a full set of animated stickers with transparent backgrounds — from a selfie, from any image (a pet, a drawing, a mascot, an object), or from just a sentence.

0. Find an image generator: use the one built into your agent (Codex image_gen, Doubao, WorkBuddy's Hunyuan, etc.). If there is none, it offers options: an image API you provide, another tool on your computer, or prompts you run yourself in any image app.
1. Lock the character with a character sheet (front, side, back, four expressions). Photos become chibi characters; existing characters keep their own style; text-only requests get a designed character.
2. Decide each sticker's caption and action.
3. One sprite sheet per sticker; the grid follows the generator's aspect ratio (16:9 → 4×2, 1:1 → 3×3).
4. Cut frames into per-frame PNGs, transparent GIFs at 480px and 240px, an APNG, and an overview GIF. If the generator can't output transparency, ask for a solid magenta or green background and the script keys it out.

Install by telling your agent "install this skill: https://github.com/alchaincyf/huashu-selfie-sticker", or clone it into your agent's skills folder, then `pip install pillow numpy`.
