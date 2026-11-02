"""Add a new MusyX sound effect to GAME_ALL: a sample from a sound file, a macro copied from an existing
one (pointed at the new sample) and an SFX entry with a new define id (cmd_30 / sound id numbering).
usage: add_sfx.py IN.audio GAME_ALL.arc GAME_ALL.samp OUTDIR [--id 432] [--template 305] [--gain 0.89]
Nothing already in the bank moves in the .samp (the sample is appended); the pool gets the macro at the
end of its macro section, the sdir an entry before its terminator, the proj id lists and SFX table grow."""
import sys, os, struct, subprocess, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs'))   # u8arc.py
from musyx import be16, be32, sdir, dsp_decode
import dspenc, u8arc

def opt(a, k, d, f=int):
    if k in a: i = a.index(k); v = f(a[i + 1]); del a[i:i + 2]; return v
    return d

def main():
    a = sys.argv[1:]
    new_id = opt(a, '--id', 432); tmpl_id = opt(a, '--template', 305); gain = opt(a, '--gain', 0.89, float)
    src, arc_in, samp_in, out = a
    arc = u8arc.read(open(arc_in, 'rb').read()); nm = u8arc.names(arc)
    kpool, kproj, ksdir = sorted(arc['files'])[:3]
    pool = bytearray(arc['files'][kpool]); proj = bytearray(arc['files'][kproj]); sd = bytes(arc['files'][ksdir])
    samp = bytearray(open(samp_in, 'rb').read())

    # proj: SFX table (count at 0x74, 10-byte entries from 0x78) -> template's macro
    n = be16(proj, 0x74); tab = 0x78
    ents = [bytes(proj[tab + 10 * i:tab + 10 * i + 10]) for i in range(n)]
    if any(be16(e, 0) == new_id for e in ents): sys.exit('sound %d already exists' % new_id)
    tmpl = next(e for e in ents if be16(e, 0) == tmpl_id); tmac = be16(tmpl, 2)

    # pool: macros {u32 size, u16 id, u16 0, 8-byte commands} up to 0xFFFFFFFF
    o = be32(pool, 0); macs = {}
    while be32(pool, o) != 0xFFFFFFFF:
        macs[be16(pool, o + 4)] = o; o += be32(pool, o)
    term = o; new_mac = max(macs) + 1
    mo = macs[tmac]; mac = bytearray(pool[mo:mo + be32(pool, mo)])
    struct.pack_into('>H', mac, 4, new_mac)
    ss = [k for k in range(8, len(mac), 8) if mac[k + 3] == 0x10]           # StartSample
    assert len(ss) == 1, ss
    tsamp = be16(mac, ss[0] + 1)

    # sdir: entries 0x20 up to 0xFFFFFFFF, then 0x28-byte infos
    ents_sd = sdir(sd); nsd = len(ents_sd)
    assert be32(sd, nsd * 0x20) == 0xFFFFFFFF
    new_samp = max(e['id'] for e in ents_sd) + 1
    assert new_samp == new_mac, (new_samp, new_mac)                      # id lists are shared below
    struct.pack_into('>H', mac, ss[0] + 1, new_samp)                     # StartSample -> the new sample
    te = next(e for e in ents_sd if e['id'] == tsamp)

    # audio -> mono at the template's rate, normalised, DSP-ADPCM
    rate = te['rate']
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-ac', '1', '-ar', str(rate), '-f', 's16le', '-'],
                         capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.int16).astype(float)
    x *= (32767 * gain) / max(1.0, np.abs(x).max())
    pcm = np.round(x).astype(int)
    co = dspenc.fit_coefs(pcm); enc = dspenc.encode(pcm, co); flat = [v for p in co for v in p]
    dec = np.array(dsp_decode(enc, len(pcm), flat), float)
    snr = 10 * np.log10((x ** 2).sum() / max(1.0, ((x - dec) ** 2).sum()))

    # .samp: append (32-byte aligned)
    samp += bytes((-len(samp)) % 0x20); soff = len(samp); samp += enc; samp += bytes((-len(samp)) % 0x20)

    # sdir: shift infos by one entry, add entry + info
    heads = bytearray(sd[:nsd * 0x20]); infos = bytearray(sd[nsd * 0x20 + 4:])
    for i in range(nsd):
        struct.pack_into('>I', heads, i * 0x20 + 0x1C, be32(heads, i * 0x20 + 0x1C) + 0x20)
    info_off = (nsd + 1) * 0x20 + 4 + len(infos)
    ent = bytearray(heads[ents_sd.index(te) * 0x20:][:0x20])
    struct.pack_into('>HHI', ent, 0, new_samp, be16(ent, 2), soff)
    struct.pack_into('>H', ent, 0xE, rate)
    struct.pack_into('>IIII', ent, 0x10, len(pcm), 0, 0, info_off)
    tinfo = sd[te['info']:te['info'] + 0x28]
    info = bytearray(tinfo); struct.pack_into('>BBhh', info, 2, enc[0], 0, 0, 0); struct.pack_into('>16h', info, 8, *flat)
    sd2 = bytes(heads + ent) + b'\xff\xff\xff\xff' + bytes(infos + info)

    # pool: macro before the terminator, later section offsets move
    pool[term:term] = mac
    for k in range(1, 4):
        v = be32(pool, 4 * k)
        if v and v > term: struct.pack_into('>I', pool, 4 * k, v + len(mac))

    # proj: macro and sample id lists end with a range ... 0x8000|lo, hi: extend hi to the new id
    for lst in (be32(proj, 8), be32(proj, 0xC)):
        o = lst
        while be16(proj, o) != 0xFFFF:
            o += 4 if be16(proj, o) & 0x8000 else 2
        last = o - 2
        assert be16(proj, last) == new_mac - 1 and be16(proj, last - 2) & 0x8000, hex(be16(proj, last))
        struct.pack_into('>H', proj, last, new_mac)
    e = bytearray(tmpl); struct.pack_into('>HH', e, 0, new_id, new_mac)
    end = tab + 10 * n
    assert be32(proj, 0) == end
    proj[end:end] = e; struct.pack_into('>H', proj, 0x74, n + 1); struct.pack_into('>I', proj, 0, end + 10)

    newarc = u8arc.build(arc, {kpool: bytes(pool), kproj: bytes(proj), ksdir: sd2})
    os.makedirs(out, exist_ok=True)
    open(os.path.join(out, os.path.basename(arc_in)), 'wb').write(newarc)
    open(os.path.join(out, os.path.basename(samp_in)), 'wb').write(samp)

    # read back
    chk = u8arc.read(newarc); p2, j2, s2 = (chk['files'][k] for k in sorted(chk['files'])[:3])
    se = sdir(s2); ne = next(x for x in se if x['id'] == new_samp)
    back = dsp_decode(bytes(samp[ne['off']:ne['off'] + (ne['n'] + 13) // 14 * 8]), ne['n'], ne['coefs'])
    assert back == dec.astype(int).tolist()
    for old in ents_sd:                                                   # old samples untouched
        x2 = next(x for x in se if x['id'] == old['id'])
        assert (x2['off'], x2['n'], x2['coefs']) == (old['off'], old['n'], old['coefs'])
    pm = u8arc.read(newarc); pp = pm['files'][sorted(pm['files'])[0]]
    o = be32(pp, 0)
    while be16(pp, o + 4) != new_mac: o += be32(pp, o)
    m2 = pp[o:o + be32(pp, o)]; st = [be16(m2, k + 1) for k in range(8, len(m2), 8) if m2[k + 3] == 0x10]
    assert st == [new_samp], st                                           # the macro plays the new sample
    print('sound %d -> macro %d -> sample %d: %.3f s at %d Hz, %d bytes, SNR %.1f dB; template sound %d (macro %d)'
          % (new_id, new_mac, new_samp, len(pcm) / rate, rate, len(enc), snr, tmpl_id, tmac))

if __name__ == '__main__':
    main()
