"""Step 1b: Celia without her own hair, with the goddess's hair mesh fitted to her head."""
import sys, numpy as np
sys.path[:0] = ['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess',
                '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/model',
                '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/pm']
import restyle, load315, wally, raster
from PIL import Image, ImageDraw
CEL = restyle.CEL

HEADT = wally.tpl(CEL + '_b0.tpl', 1)
def celia_without_hair(M):
    """drop the triangles textured from Celia's hair block or her cap (body sheet)"""
    body = wally.tpl(CEL + '_b0.tpl', 0); H, W = body.shape[:2]
    B = M['bones']; UV = M['UV']
    head = lambda v: bool(B[v]) and all(b in (6, 7, 8, 9) for b in B[v])
    hb = (40, 114, 81, 186)                                     # hair block (x0, y0, x1, y1) in texels
    groups = []
    for tid, tris, vst in M['groups']:
        keep = []
        for (pi, ti) in tris:
            if tid == 255 and all(head(v) for v in pi):
                u = np.mean([UV[t][0] % 1 for t in ti]) * W; v = np.mean([UV[t][1] % 1 for t in ti]) * H
                if v < 60 or (hb[0] <= u <= hb[2] and hb[1] <= v <= hb[3]): continue
            if all(head(v) for v in pi) and tid == 2:               # scalp tufts: dark hair texels of the head sheet
                ht = HEADT; hh, hw = ht.shape[:2]
                u = np.mean([UV[t][0] % 1 for t in ti]) * hw; v = np.mean([UV[t][1] % 1 for t in ti]) * hh
                c = ht[min(int(v), hh - 1), min(int(u), hw - 1)]
                if c[0] * 0.3 + c[1] * 0.59 + c[2] * 0.11 < 100: continue
            keep.append((pi, ti))
        groups.append((tid, keep, vst))
    return groups

def goddess_hair(scale, offset):
    G = load315.load(); h = [m for m in G if m['mat'] == 'hair_315'][0]
    P = h['P'] * 0.01 * scale + np.array(offset)
    tex = np.array(Image.open(load315.D + 'hair_315_00.png').convert('RGBA'), float)
    tris = [((a, b, c), (a, b, c)) for a, b, c in h['T']]
    UV = np.array([(u, 1 - v) for u, v in h['UV']])
    return P, UV, tris, tex

def render(M, groups, T, extra, angs=(0, 0.6, 1.57, 3.14), W=230, H=330, zoom=1.0, ycen=None, label=''):
    ims = []
    for ang in angs:
        img = np.zeros((H, W, 3)) + [200, 215, 225]; zb = np.full((H, W), -1e9)
        sc = H / 1.75 * zoom; oy = H - 10 if ycen is None else H / 2 + ycen * sc
        wally.draw(img, zb, M['V'], M['UV'], groups, T, raster.rotY(ang), sc, W / 2, oy)
        for P, UV, tris, tex in extra: raster.render(img, zb, P, UV, tris, tex, raster.rotY(ang), sc, W / 2, oy)
        ims.append(Image.fromarray(img.clip(0, 255).astype(np.uint8)))
    out = Image.new('RGB', (W * len(ims), H + 18), 'white')
    for i, im in enumerate(ims): out.paste(im, (W * i, 18))
    ImageDraw.Draw(out).text((4, 3), label, fill=(0, 0, 0))
    return out
