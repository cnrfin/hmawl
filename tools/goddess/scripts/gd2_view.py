import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank']
import view, raster
from PIL import Image, ImageDraw
def rend(body, parts, lab, angs, zoom, yc, W, H):
    BV, BF = body; ims = []
    for ang in angs:
        img = np.zeros((H, W, 3)) + [200, 215, 225]; zb = np.full((H, W), -1e9); sc = H / 1.45 * zoom; oy = H / 2 + yc * sc
        R = raster.rotY(ang); view.smooth_render(img, zb, BV, BF, view.SKIN, R, sc, W / 2, oy)
        for P, UV, T, tex in parts: view.smooth_tex(img, zb, P, np.asarray(T), UV, tex, R, sc, W / 2, oy)
        ims.append(Image.fromarray(img.clip(0, 255).astype(np.uint8)))
    o = Image.new('RGB', (W * len(ims), H + 18), 'white')
    for i, im in enumerate(ims): o.paste(im, (W * i, 18))
    ImageDraw.Draw(o).text((4, 3), lab, fill=(0, 0, 0)); return o
def stack(ims, path):
    O = Image.new('RGB', (max(i.width for i in ims), sum(i.height for i in ims)), 'white'); y = 0
    for i in ims: O.paste(i, (0, y)); y += i.height
    O.save(path)
