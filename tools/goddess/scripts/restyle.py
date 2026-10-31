"""Celia -> Harvest Goddess, texture side. Step 1: hair (and bandana) recoloured to the goddess's green,
shade by shade (luminance -> her hair texture's colour ramp), keeping Celia's painted strands."""
import sys, numpy as np
sys.path[:0] = ['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess',
                '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/pm']
import awlmodel, wally
from PIL import Image, ImageDraw
SRC = '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/model/Harvest Goddess copy/'
CEL = '/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/girls/sepi_0/sepi_0'
lum = lambda c: c[..., 0] * 0.3 + c[..., 1] * 0.59 + c[..., 2] * 0.11

def ramp_from(img_path, sel=None):
    """sorted colours of a texture (opaque, greenish pixels) -> 256-entry luminance ramp"""
    a = np.array(Image.open(img_path).convert('RGBA')).astype(float).reshape(-1, 4)
    a = a[a[:, 3] > 200][:, :3]
    if sel is not None: a = a[sel(a)]
    L = lum(a); o = np.argsort(L); a, L = a[o], L[o]
    ramp = np.zeros((256, 3))
    for i in range(256):
        q = np.searchsorted(L, i * L[-1] / 255.0); q = min(max(q, 0), len(a) - 1)
        lo, hi = max(0, q - 20), min(len(a), q + 20); ramp[i] = a[lo:hi].mean(0)
    return ramp

def recolour(px, ramp, lo_in, hi_in):
    """map pixel luminance (lo_in..hi_in) onto the ramp's full range"""
    L = lum(px[..., :3]); t = np.clip((L - lo_in) / max(hi_in - lo_in, 1), 0, 1)
    out = px.copy(); out[..., :3] = ramp[(t * 255).astype(int)]
    return out

def uv_mask(M, shape, sel_tid, pred):
    H, W = shape; m = Image.new('L', (W, H), 0); dr = ImageDraw.Draw(m)
    for tid, tris, _ in M['groups']:
        if tid != sel_tid: continue
        for (a, b, c), (ta, tb, tc) in tris:
            if all(pred(v) for v in (a, b, c)):
                dr.polygon([(M['UV'][t][0] % 1 * W, M['UV'][t][1] % 1 * H) for t in (ta, tb, tc)], fill=255)
    return np.array(m) > 0

def step1():
    M = awlmodel.load(CEL)
    B = M['bones']
    head = lambda v: bool(B[v]) and all(b in (6, 7, 8, 9) for b in B[v])
    body = wally.tpl(CEL + '_b0.tpl', 0); headt = wally.tpl(CEL + '_b0.tpl', 1)
    hair_ramp = ramp_from(SRC + 'hair_315_00.png', sel=lambda a: (a[:, 1] > a[:, 0] + 10) & (a[:, 1] > a[:, 2]))
    hair_ramp = hair_ramp[np.linspace(60, 255, 256).astype(int)]          # the lighter part: her mint green
    m = uv_mask(M, body.shape[:2], 255, head)
    rgb = body[..., :3]; L = lum(rgb)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    skin = (r > 190) & (g > 150) & (b > 120) & (r > b + 25)                # face/neck skin shares these texels
    orange = (r > g + 40) & (g > b + 15) | (L > 200)                        # bandana cloth (orange, white dots)
    hairpx = m & ~skin & ~orange
    lo, hi = np.percentile(L[hairpx], 2), np.percentile(L[hairpx], 99)
    body2 = body.copy(); body2[hairpx] = recolour(body[hairpx], hair_ramp, lo, hi)
    # bandana: fill with the (recoloured) hair-strand swatch, tiled, so the cap reads as hair
    cap = np.zeros_like(m); cap[:60] = True
    band = m & cap                                                          # the whole cap area (cloth, lace, dots)
    hb = hairpx.copy(); hb[:60] = False                                     # the hair block itself (below the cap's texels)
    ys, xs = np.where(hb)
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    sw = body2[y0:y1 + 1, x0:x1 + 1]
    by, bx = np.where(band)
    body2[by, bx] = sw[(by - by.min()) % sw.shape[0], (bx - bx.min()) % sw.shape[1]]

    # head sheet: the dark hair strip and hairline
    hs = headt[..., :3]; dark = (lum(hs) < 110) & (headt[..., 3] > 0)
    head2 = headt.copy(); head2[dark] = recolour(headt[dark], hair_ramp, 0, 110)
    return M, body2, head2

if __name__ == '__main__':
    M, body2, head2 = step1()
    Image.fromarray(body2.astype(np.uint8), 'RGBA').save('step1_body.png')
    Image.fromarray(head2.astype(np.uint8), 'RGBA').save('step1_head.png')
