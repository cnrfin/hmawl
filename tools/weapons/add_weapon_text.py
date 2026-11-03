#!/usr/bin/env python3
"""Weapon names and descriptions (weapons phase 1). Edits the disc's own Message.arc (item.mes = names, index =
item id) and itemdoc03.mes (descriptions, index = id - 0x3ED), keeping every other message byte for byte, so it
works on top of earlier edits ($JOE coin, Lumber, Joe).
usage: add_weapon_text.py Message.arc itemdoc03.mes OUT_DIR"""
import sys, os, struct, hashlib
WEAPONS = {  # id: (name, description lines)
    0x4E3: ("Stick", "A sturdy stick.\nBetter than nothing!"),
    0x4E4: ("Wooden Sword", "A wooden practice\nsword. Light and quick."),
    0x4EA: ("Farmer's Sword", "An iron sword, made\nto protect the farm."),
    0x4EB: ("H.M Murasama", "A legendary blade.\nIt hums with power..."),
}
SPEC = {'.': 0x80C8, '!': 0x80CB, "'": 0x80F2, '+': 0x80C6, '%': 0x80D7, '$': 0x80FD, '-': 0x800A, '?': 0x80CA, ',': 0x8105}
def enc(s):
    out = bytearray()
    for ch in s:
        if 'A' <= ch <= 'Z': out += struct.pack('>H', 0x800B + ord(ch) - 65)
        elif 'a' <= ch <= 'z': out += struct.pack('>H', 0x80D8 + ord(ch) - 97)
        elif '0' <= ch <= '9': out += struct.pack('>H', 0x8000 + ord(ch) - 48)
        elif ch == ' ': out.append(0x02)
        elif ch == '\n': out.append(0x01)
        elif ch in SPEC: out += struct.pack('>H', SPEC[ch])
        else: raise ValueError(ch)
    return bytes(out)
def mes_read(d):
    assert d[:4] == b'\xCD\xC3\xB0\xB0'
    n = struct.unpack_from('>I', d, 4)[0]; offs = list(struct.unpack_from('>%dI' % n, d, 8))
    ends = sorted(set(offs + [len(d)]))                  # a few messages are stored out of order
    return [d[o:ends[ends.index(o) + 1]] for o in offs]
def mes_write(msgs):
    n = len(msgs); o = 8 + 4 * n; tab = []; body = b''
    for m in msgs: tab.append(o + len(body)); body += m
    return struct.pack('>II', 0xCDC3B0B0, n) + struct.pack('>%dI' % n, *tab) + body
def u8_replace(d, name, data):
    """rebuild a flat U8 archive with one file's data replaced (node order kept, data 0x20-aligned)"""
    assert d[:4] == b'U\xaa8-'
    root, hs, ds = struct.unpack_from('>III', d, 4); n = struct.unpack_from('>I', d, root + 8)[0]
    nodes = [list(struct.unpack_from('>III', d, root + 12 * k)) for k in range(n)]; st = root + 12 * n
    nm = lambda k: d[st + (nodes[k][0] & 0xFFFFFF):].split(b'\0')[0].decode()
    files = [k for k in range(n) if not nodes[k][0] >> 24]
    out = bytearray(d[:ds]); found = False
    for k in sorted(files, key=lambda k: nodes[k][1]):
        blob = d[nodes[k][1]:nodes[k][1] + nodes[k][2]]
        if nm(k) == name: blob = data; found = True
        out += bytes((-len(out)) % 0x20); nodes[k][1] = len(out); nodes[k][2] = len(blob); out += blob
    assert found, name
    for k, w in enumerate(nodes): struct.pack_into('>III', out, root + 12 * k, *w)
    return bytes(out)
def u8_get(d, name):
    root, hs, ds = struct.unpack_from('>III', d, 4); n = struct.unpack_from('>I', d, root + 8)[0]; st = root + 12 * n
    for k in range(n):
        w0, o, s = struct.unpack_from('>III', d, root + 12 * k)
        if not w0 >> 24 and d[st + (w0 & 0xFFFFFF):].split(b'\0')[0].decode() == name: return d[o:o + s]
    raise KeyError(name)
def main():
    if len(sys.argv) != 4: sys.exit(__doc__)
    arc = open(sys.argv[1], 'rb').read(); doc = open(sys.argv[2], 'rb').read(); out = sys.argv[3]
    names = mes_read(u8_get(arc, 'item.mes')); docs = mes_read(doc)
    for i, (name, desc) in WEAPONS.items():
        old = names[i]; z = len(old) - len(old.rstrip(b'\0'))
        names[i] = enc(name) + b'\0' * max(z, 1)
        m = docs[i - 0x3ED]; assert m[0] == 0x13 and m[1] == 0x25 and m[5] == 0x17, hex(i)   # <hl><25:id>\n</hl>
        docs[i - 0x3ED] = m[:6] + enc(desc) + b'\x30\x00'
    os.makedirs(out, exist_ok=True)
    a2 = u8_replace(arc, 'item.mes', mes_write(names)); d2 = mes_write(docs)
    assert mes_read(u8_get(a2, 'item.mes')) == names and mes_read(d2) == docs
    open(os.path.join(out, 'Message.arc'), 'wb').write(a2); open(os.path.join(out, 'itemdoc03.mes'), 'wb').write(d2)
    for f, b in (('Message.arc', a2), ('itemdoc03.mes', d2)): print(f, len(b), hashlib.sha1(b).hexdigest()[:8])
if __name__ == '__main__': main()
