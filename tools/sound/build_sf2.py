"""Build a SoundFont from MusyX music groups: each layer object = one instrument (zones = its layers,
root key = 60 - transpose, as the game plays them); bank 1 = every raw sample on its own (root 60)."""
import sys, os, struct; sys.path.insert(0, '.')
from musyx import *; import sf2

def layers(pool):
    offs = struct.unpack_from('>4I', pool, 0); out = []
    if not offs[3]: return out
    o = offs[3]
    while o < len(pool):
        size = be32(pool, o)
        if size in (0, 0xFFFFFFFF): break
        lid = be16(pool, o + 4); body = pool[o + 8:o + size]; n = be32(body, 0)
        out.append((lid, [struct.unpack_from('>HBBbBbbBB', body, 4 + 12 * k) for k in range(n)]))
        o += size
    return out

def macro_sample(pool):
    """macro id -> sample id (its StartSample command, bytes ...xx xx 10 little-endian in the word)"""
    offs = struct.unpack_from('>4I', pool, 0); o = offs[0]; m = {}
    while o < offs[1]:
        size = be32(pool, o)
        if size in (0, 0xFFFFFFFF): break
        mid = be16(pool, o + 4); body = pool[o + 8:o + size]
        for k in range(0, len(body), 8):
            if body[k + 3] == 0x10: m[mid] = be16(body, k + 1); break
        o += size
    return m

samples, instruments = [], []
for g in sys.argv[2:]:
    parts = u8(open(os.environ.get('SND_IN', '../snd_in') + '/%s.arc' % g, 'rb').read()); samp = open(os.environ.get('SND_IN', '../snd_in') + '/%s.samp' % g, 'rb').read()
    pool, sd = parts[0], parts[2]
    idx = {}
    for e in sdir(sd):
        pcm = dsp_decode(samp[e['off']:e['off'] + (e['n'] + 13) // 14 * 8], e['n'], e['coefs'])
        loop = (e['loop_start'], e['loop_start'] + e['loop_len']) if e['loop_len'] else None
        idx[e['id']] = len(samples)
        samples.append(dict(name='%s_%03d' % (g[:6], e['id']), pcm=pcm, rate=e['rate'], loop=loop))
    ms = macro_sample(pool)
    for k, (lid, ls) in enumerate(layers(pool)):
        zones = [dict(lo=lo, hi=hi, sample=idx[ms[mac]], root=max(0, min(127, 60 - tr)), vol=vol, pan=pan - 64)
                 for mac, lo, hi, tr, vol, _, _, pan, _ in ls if mac in ms and ms[mac] in idx]
        drums = all(z['lo'] == z['hi'] for z in zones)
        instruments.append(dict(name='%s %s %02X' % (g[:6], 'kit' if drums else 'inst', lid & 0xFF),
                                bank=128 if drums else 0, program=len([i for i in instruments if i['bank'] == (128 if drums else 0)]),
                                zones=zones))
raw = [dict(name=s['name'], bank=1, program=i % 128, zones=[dict(lo=0, hi=127, sample=i, root=60)])
       for i, s in enumerate(samples)][:128]
sf2.write(sys.argv[1], samples, instruments + raw, 'HM A Wonderful Life (%s)' % ', '.join(sys.argv[2:]))
for i in instruments:
    print(i['bank'], i['program'], i['name'], [(z['lo'], z['hi'], samples[z['sample']]['name'], z['root']) for z in i['zones']])
print(len(samples), 'samples')
