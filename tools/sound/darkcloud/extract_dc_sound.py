#!/usr/bin/env python3
"""Pull Dark Cloud (PS2) sound files out of your own disc's DATA.DAT, using its DATA.HD2 index.
DATA.HD2: 32-byte little-endian records {u32 name offset, u32 x3, u32 byte offset in DATA.DAT, u32 size,
u32 index, u32 flag}, the names (backslash paths, NUL-terminated) after the records.
usage: extract_dc_sound.py DATA.HD2 DATA.DAT OUT_DIR [prefix ...]
default prefixes: sound\\battle sound\\tbl   (about 5 MB); 'sound' takes every sound file (~99 MB).
The extracted audio is for your own build only: keep it out of the repository."""
import sys, os, struct, zipfile
def main():
    if len(sys.argv) < 4: sys.exit(__doc__)
    hd, dat, out = sys.argv[1:4]
    pre = [p.replace('/', '\\').lower() for p in (sys.argv[4:] or ['sound\\battle', 'sound\\tbl'])]
    d = open(hd, 'rb').read()
    first = struct.unpack_from('<I', d, 0)[0]; n = first // 32
    recs = []
    for k in range(n):
        no, _, _, _, off, size, _, _ = struct.unpack_from('<8I', d, 32 * k)
        recs.append((d[no:d.index(b'\0', no)].decode('latin1'), off, size))
    pick = [r for r in recs if any(r[0].lower().startswith(p) for p in pre)]
    os.makedirs(out, exist_ok=True); total = 0
    with open(dat, 'rb') as f:
        for name, off, size in pick:
            f.seek(off); data = f.read(size); assert len(data) == size, name
            p = os.path.join(out, *name.split('\\')); os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, 'wb').write(data); total += size
    z = out.rstrip('/\\') + '.zip'
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, _, _ in pick: zf.write(os.path.join(out, *name.split('\\')), name.replace('\\', '/'))
    print('%d files, %.1f MB -> %s and %s (%.1f MB)' % (len(pick), total / 1e6, out, z, os.path.getsize(z) / 1e6))
if __name__ == '__main__': main()
