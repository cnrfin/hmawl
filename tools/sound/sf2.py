"""SoundFont 2 writer: multi-zone instruments, one preset per instrument."""
import struct, math
def chunk(tag, data):
    if len(data) % 2: data += b'\0'
    return tag + struct.pack('<I', len(data)) + data
def lst(tag, body): return chunk(b'LIST', tag + body)
def name20(s): return s.encode('ascii', 'replace')[:19].ljust(20, b'\0')

def write(path, samples, instruments, bank_name='HMAWL'):
    """samples: [dict(name, pcm, rate, loop=(s,e)|None)]
    instruments: [dict(name, bank, program, zones=[dict(lo, hi, sample, root, vol=0..127, pan=-64..63)])]"""
    smpl = b''; shdr = b''; pos = 0
    for s in samples:
        start, end = pos, pos + len(s['pcm'])
        ls, le = (start + s['loop'][0], start + s['loop'][1]) if s.get('loop') else (start, end)
        shdr += name20(s['name']) + struct.pack('<IIIIIBbHH', start, end, ls, le, s['rate'], 60, 0, 0, 1)
        smpl += struct.pack('<%dh' % len(s['pcm']), *s['pcm']) + bytes(92); pos = end + 46
    shdr += name20('EOS') + bytes(26)
    inst = ibag = igen = phdr = pbag = pgen = b''
    gi = bi = pgi = pbi = 0
    for k, ins in enumerate(instruments):
        inst += name20(ins['name']) + struct.pack('<H', bi)
        for z in ins['zones']:
            ibag += struct.pack('<HH', gi, 0); bi += 1
            s = samples[z['sample']]
            gens = [(43, z['lo'] | (z['hi'] << 8))]
            vol = z.get('vol', 127)
            if vol < 127: gens.append((48, int(min(1440, -200 * math.log10(max(vol, 1) / 127.0)))))  # initialAttenuation cB
            if z.get('pan'): gens.append((17, int(z['pan'] / 64.0 * 500)))
            gens.append((38, 1200 if not s.get('loop') else 600))     # releaseVolEnv ~ 2 s / 1.4 s
            if s.get('loop'): gens.append((54, 1))
            gens.append((58, z['root']))                               # overridingRootKey
            gens.append((53, z['sample']))
            for op, amt in gens: igen += struct.pack('<Hh' if amt < 0 else '<HH', op, amt); gi += 1
        phdr += name20(ins['name']) + struct.pack('<HHHIII', ins['program'], ins['bank'], pbi, 0, 0, 0)
        pbag += struct.pack('<HH', pgi, 0); pbi += 1
        pgen += struct.pack('<HH', 41, k); pgi += 1
    inst += name20('EOI') + struct.pack('<H', bi); ibag += struct.pack('<HH', gi, 0); igen += bytes(4)
    phdr += name20('EOP') + struct.pack('<HHHIII', 0, 0, pbi, 0, 0, 0); pbag += struct.pack('<HH', pgi, 0); pgen += bytes(4)
    info = lst(b'INFO', chunk(b'ifil', struct.pack('<HH', 2, 1)) + chunk(b'isng', b'EMU8000\0') +
               chunk(b'INAM', bank_name.encode() + b'\0'))
    pdta = lst(b'pdta', chunk(b'phdr', phdr) + chunk(b'pbag', pbag) + chunk(b'pmod', bytes(10)) + chunk(b'pgen', pgen) +
               chunk(b'inst', inst) + chunk(b'ibag', ibag) + chunk(b'imod', bytes(10)) + chunk(b'igen', igen) + chunk(b'shdr', shdr))
    body = b'sfbk' + info + lst(b'sdta', chunk(b'smpl', smpl)) + pdta
    open(path, 'wb').write(b'RIFF' + struct.pack('<I', len(body)) + body)
