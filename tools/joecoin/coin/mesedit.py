"""Small .mes editor: replace whole messages; text in ASCII with \\n, | = <wait>, ^ = <page>."""
import struct
def enc(s):
    out = bytearray(); SPEC = {'.': 0x80C8, '!': 0x80CB, "'": 0x80F2, '+': 0x80C6, '%': 0x80D7, '$': 0x80FD, '-': 0x800A, '?': 0x80CA, ',': 0x8105}
    for ch in s:
        if 'A' <= ch <= 'Z': out += struct.pack('>H', 0x800B + ord(ch) - 65)
        elif 'a' <= ch <= 'z': out += struct.pack('>H', 0x80D8 + ord(ch) - 97)
        elif '0' <= ch <= '9': out += struct.pack('>H', 0x8000 + ord(ch) - 48)
        elif ch == ' ': out.append(0x02)
        elif ch == '\n': out.append(0x01)
        elif ch == '|': out.append(0x30)
        elif ch == '^': out.append(0x31)
        elif ch in SPEC: out += struct.pack('>H', SPEC[ch])
        else: raise ValueError(ch)
    return bytes(out)
def read(d):
    n = struct.unpack_from('>I', d, 4)[0]; offs = list(struct.unpack_from('>%dI' % n, d, 8)) + [len(d)]
    return [d[offs[i]:offs[i + 1]] for i in range(n)]
def write(msgs):
    n = len(msgs); o = 8 + 4 * n; tab = []; body = b''
    for m in msgs: tab.append(o + len(body)); body += m
    return struct.pack('>II', 0xCDC3B0B0, n) + struct.pack('>%dI' % n, *tab) + body
