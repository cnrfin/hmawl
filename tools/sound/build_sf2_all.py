"""SoundFont from every MusyX music group given: bank = song index, program = the song's own program
number (project page table); each program's layer object -> zones (key range, sample, root 60 - transpose,
volume, pan). Drum-style layers (single-key zones) are also listed in bank 128. Samples shared between
songs are stored once. usage: build_sf2_all.py OUT.sf2 OUT.txt GROUP..."""
import sys, os, struct, hashlib; sys.path.insert(0, '.')
from musyx import *; import sf2

def objects(pool):
    """layer objects: id -> [(macro, lo, hi, transpose, vol, prio, span, pan)]"""
    offs = struct.unpack_from('>4I', pool, 0); out = {}
    o = offs[3]
    while o and o + 8 <= len(pool):
        size = be32(pool, o)
        if size in (0, 0xFFFFFFFF) or o + size > len(pool): break
        lid = be16(pool, o + 4); body = pool[o + 8:o + size]; n = be32(body, 0)
        out[lid] = [struct.unpack_from('>HBBbBbbBB', body, 4 + 12 * k) for k in range(n)]
        o += size
    return out

def macro_samples(pool):
    offs = struct.unpack_from('>4I', pool, 0); o = offs[0]; m = {}
    while o < offs[1]:
        size = be32(pool, o)
        if size in (0, 0xFFFFFFFF): break
        mid = be16(pool, o + 4); body = pool[o + 8:o + size]
        for k in range(0, len(body) - 7, 8):
            if body[k + 3] == 0x10: m[mid] = be16(body, k + 1); break
        o += size
    return m

def programs(proj):
    """[(object id, program)] from each group's normal page table"""
    out = []; o = 0
    while o + 0x28 <= len(proj) and be32(proj, o) != 0xFFFFFFFF:
        end = be32(proj, o); typ = be16(proj, o + 6); h = struct.unpack_from('>8I', proj, o + 8)
        if typ == 0 and h[5]:
            p = o + h[5]
            while p + 6 <= len(proj) and be16(proj, p) != 0xFFFF:
                oid, _, _, prog, _ = struct.unpack_from('>HBBBB', proj, p); out.append((oid, prog)); p += 6
        if not end or end <= o: break
        o = end
    return out

samples, shash, insts, report = [], {}, [], []
for bank, g in enumerate(sys.argv[3:]):
    try:
        parts = u8(open(os.environ.get('SND_IN', '../snd_in') + '/%s.arc' % g, 'rb').read()); samp = open(os.environ.get('SND_IN', '../snd_in') + '/%s.samp' % g, 'rb').read()
        pool, proj, sd = parts[0], parts[1], parts[2]
        ents = {e['id']: e for e in sdir(sd)}; objs = objects(pool); ms = macro_samples(pool); progs = programs(proj)
    except Exception as ex:
        report.append('%-10s skipped (%s)' % (g, ex)); continue
    local = {}
    def sample_index(sid):
        if sid in local: return local[sid]
        e = ents[sid]
        pcm = dsp_decode(samp[e['off']:e['off'] + (e['n'] + 13) // 14 * 8], e['n'], e['coefs'])
        loop = (e['loop_start'], e['loop_start'] + e['loop_len']) if e['loop_len'] else None
        h = hashlib.sha1(struct.pack('<%dh' % len(pcm), *pcm) + struct.pack('<III', e['rate'], *(loop or (0, 0)))).hexdigest()
        if h not in shash:
            shash[h] = len(samples); samples.append(dict(name='%s_%03d' % (g[:8], sid), pcm=pcm, rate=e['rate'], loop=loop))
        local[sid] = shash[h]; return local[sid]
    seen = set()
    for oid, prog in progs:
        if (oid, prog) in seen or oid not in objs: continue
        seen.add((oid, prog))
        zones = [dict(lo=lo, hi=hi, sample=sample_index(ms[mac]), root=max(0, min(127, 60 - tr)), vol=vol, pan=pan - 64)
                 for mac, lo, hi, tr, vol, _, _, pan, _ in objs[oid] if mac in ms and ms[mac] in ents]
        if not zones: continue
        kit = all(z['lo'] == z['hi'] for z in zones)
        name = '%s p%d%s' % (g[:10], prog, ' kit' if kit else '')
        insts.append(dict(name=name, bank=bank, program=prog, zones=zones))
        if kit:
            insts.append(dict(name=name, bank=128, program=len([i for i in insts if i['bank'] == 128]), zones=zones))
        lo = min(z['lo'] for z in zones); hi = max(z['hi'] for z in zones)
        report.append('bank %2d prog %d  %-18s %2d zones, keys %3d-%3d%s' % (bank, prog, name, len(zones), lo, hi,
                      '  (also bank 128 prog %d)' % insts[-1]['program'] if kit else ''))
sf2.write(sys.argv[1], samples, insts, 'HM A Wonderful Life music instruments')
open(sys.argv[2], 'w').write('\n'.join(report) + '\n%d presets, %d samples\n' % (len(insts), len(samples)))
print('\n'.join(report[-5:])); print(len(insts), 'presets', len(samples), 'samples')
