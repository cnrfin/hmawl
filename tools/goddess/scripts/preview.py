"""Render an AWL model (bind pose) from front / 3-4 / side / back with given textures."""
import sys, numpy as np
sys.path[:0] = ['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess',
                '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/pm']
import wally, raster
from PIL import Image, ImageDraw
def views(M, T, label='', angs=(0, 0.6, 1.57, 3.14), W=230, H=360, V=None, zoom=1.0, ycen=None):
    V = M['V'] if V is None else V
    ims = []
    for ang in angs:
        img = np.zeros((H, W, 3)) + [200, 215, 225]; zb = np.full((H, W), -1e9)
        sc = H / 1.6 * zoom
        oy = H - 10 if ycen is None else H / 2 + ycen * sc
        wally.draw(img, zb, V, M['UV'], M['groups'], T, raster.rotY(ang), sc, W / 2, oy)
        ims.append(Image.fromarray(img.clip(0, 255).astype(np.uint8)))
    out = Image.new('RGB', (W * len(ims), H + 18), 'white')
    for i, im in enumerate(ims): out.paste(im, (W * i, 18))
    ImageDraw.Draw(out).text((4, 3), label, fill=(0, 0, 0))
    return out
def stack(imgs):
    W = max(i.width for i in imgs); H = sum(i.height for i in imgs)
    out = Image.new('RGB', (W, H), 'white'); y = 0
    for i in imgs: out.paste(i, (0, y)); y += i.height
    return out
