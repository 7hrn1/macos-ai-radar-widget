#!/usr/bin/env python3
"""Assemble the numbered frames from render.mjs into an optimised GIF (shared palette, no dithering, crossfade between pages).
usage: make_gif.py <frames_dir> <out.gif> [--width 960] [--fps 10] [--colors 128]"""
import glob, os, sys
from PIL import Image

args = sys.argv[1:]
def opt(name, default):
    return type(default)(args[args.index(name) + 1]) if name in args else default
src, out = args[0], args[1]
width, fps, colors = opt('--width', 960), opt('--fps', 10), opt('--colors', 80)

scenes = {}
for f in sorted(glob.glob(os.path.join(src, 's*_*.jpg'))):
    scenes.setdefault(os.path.basename(f).split('_')[0], []).append(f)
order = sorted(scenes)
if not order: sys.exit('no frames found in ' + src)

def load(f):
    im = Image.open(f).convert('RGB')
    return im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)

frames = []
for si, name in enumerate(order):
    imgs = [load(f) for f in scenes[name]]
    if si > 0 and frames and name != order[si - 1]:
        if name == 's3':                              # a different page: crossfade from the last desktop frame
            a, b = frames[-1], imgs[0]
            frames += [Image.blend(a, b, k / 5) for k in range(1, 5)]
    frames += imgs

# one palette for the whole clip (smaller file, no colour flicker)
sample = frames[:: max(1, len(frames) // 24)]
sheet = Image.new('RGB', (frames[0].width, frames[0].height * len(sample)))
for i, im in enumerate(sample): sheet.paste(im, (0, i * im.height))
pal = sheet.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
q = [im.quantize(palette=pal, dither=Image.Dither.NONE) for im in frames]
q[0].save(out, save_all=True, append_images=q[1:], duration=round(1000 / fps), loop=0, optimize=True, disposal=1)
print(f'{out}: {len(q)} frames, {width}px, {os.path.getsize(out) / 1048576:.1f} MB, {len(q) / fps:.1f}s')
