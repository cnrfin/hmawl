"""Full AWL .skn skinning (added to scratchpad pm/pose.py; the preview scripts call pose.skin_weighted)."""
import numpy as np
def skin_weighted(V, sk, skd, Wbind, Wpose):
    """Full skinning: g1 rigid; g2 two bones with u16 weights (/65536, first bone); g3 accumulated
    influences (u16 vertex indices at 'wt', u16 weights at 'idx', normalised per vertex)."""
    import struct
    out = V.copy()
    Minv = [np.linalg.inv(w) for w in Wbind]
    def xf(b, p): M = Wpose[b] @ Minv[b]; return (M[:3, :3] @ p.T).T + M[:3, 3]
    for g in sk['g1']:
        i0 = (g['dst'] + g['al']) // 12; idx = np.arange(i0, i0 + g['cnt']); out[idx] = xf(g['bone'], V[idx])
    for g in sk['g2']:
        i0 = (g['dst'] + g['al']) // 12; idx = np.arange(i0, i0 + g['cnt'])
        w = np.array(struct.unpack_from('>%dH' % g['cnt'], skd, g['wt']), float)[:, None] / 65536.0
        out[idx] = w * xf(g['b'][0], V[idx]) + (1 - w) * xf(g['b'][1], V[idx])
    acc = {}; wsum = {}
    for g in sk['g3']:
        vi = np.array(struct.unpack_from('>%dH' % g['cnt'], skd, g['wt']))
        w = np.array(struct.unpack_from('>%dH' % g['cnt'], skd, g['idx']), float) / 65536.0
        P = xf(g['bone'], V[vi])
        for k, v in enumerate(vi):
            acc[v] = acc.get(v, 0) + w[k] * P[k]; wsum[v] = wsum.get(v, 0) + w[k]
    for v in acc:
        if wsum[v] > 1e-6: out[v] = acc[v] / wsum[v]
    return out
