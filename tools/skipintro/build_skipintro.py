#!/usr/bin/env python3
"""Build the "Skip Intro? Yes/No" script-data patch (GYWEE9 US).

usage: build_skipintro.py MAIN_DOL CHAPTER1_ARC SYSTEM_MES OUTDIR

Writes OUTDIR/Chapter1.arc, OUTDIR/system.mes and OUTDIR/patch_report.txt.
Reads the inputs only. See notes/findings.md section 7.13.

Script VM (main.dol func_80186208): instruction = op u8, flags u8 (bit 0:
arg += frame base), pad u16, arg s32. Stack at vm+0x20, sp byte vm+0x1B0,
vars at vm+0x1B8. Numbers are fixed point, shift 7 (OPT chunk). Op 0x25
calls script command `arg` (func_8010C604); its argument count is the
first byte of its 0x24-byte entry in lbl_802BDF00.

Patch (opening script = Chapter1.arc entry 1):
  - instruction PROMPT_AT (after the opening warp) jumps to appended code
    that shows system.mes 0x1F9 "Skip the intro?" (choice 0x40, Yes = 1)
    and sets v[SKIPVAR] = (answer == Yes);
  - No: runs the original instruction and continues the original script;
  - Yes: on a black screen, runs the dog choice (takakura.mes 113, v[8] =
    39 or 40) after a new line "Which dog do you want?", and for each
    naming screen a new short line (system.mes 0x1FB-0x1FD; the dog has
    none, it follows its choice), the commands that screen needs
    (0x03, 0x7D, 0x2D, 0x05) and the naming call (0x0E: v[8], 49, 72, 0),
    going back to black after each; then moves the clock on as the intro
    does (13:10, 15:30, 07:40), warps to the field and jumps to the
    "The Beginning" part of the ending (END_AT: 0x27, other.mes 450, 0x27,
    END), skipping line 447 and the morning scene.
Existing instruction indices never move, so every original jump target
stays valid. The interpreter never reads instruction bytes 2-3, so they
are zeroed (the compiler left junk there), which helps the script
compress.

Both outputs are exactly the size of the originals, so they replace the
files in place on a full disc image. In Chapter1.arc the patched entry 1 is
re-encoded with an optimal-parse CLZ, and if it still does not fit, other
entries are re-encoded the same way (largest saving first) until it does.
Re-encoded entries decompress to their original bytes. system.mes frees
space by sharing one duplicate message and is padded back to its length.
"""
import collections, os, struct, sys

SKIPVAR = 150          # unused by every Chapter1.arc script (they use v[0]..v[93])
PROMPT_FILE = 0x33     # system.mes
PROMPT_MSG = 0x1F9     # 0x1F8 is left as a placeholder: the milk-summary Gecko hooks it
LINES = [('Skip the intro?', True),             # 0x1F9
         ('Which dog do you want?', ['Pointy Ears', 'Long Ears']),  # 0x1FA, the dog choice itself
         ("Let's name your cow.", False),      # 0x1FB
         ('Now name your farm.', False),        # 0x1FC
         ('Finally, how should\nI call you?', False)]  # 0x1FD
MSG_DOG, MSG_COW, MSG_FARM, MSG_YOU = 0x1FA, 0x1FB, 0x1FC, 0x1FD
PROMPT_AT = 0x1D       # first statement after the opening warp and SYS 10
SHIFT = 7
MAX_DIST = 0xFE8    # largest back-reference in the original archives; none overlap

PUSHERS = {0x80112B0C, 0x80112B3C, 0x80112B68, 0x80112B94, 0x80112BCC,
           0x80112C08, 0x80112C6C, 0x80112CA8, 0x80112CDC, 0x80112D08}


# ---------------------------------------------------------------- main.dol
class Dol:
    def __init__(self, path):
        self.d = open(path, 'rb').read()
        h = struct.unpack('>54I', self.d[:0xD8])
        self.secs = [(h[i], h[18 + i], h[36 + i]) for i in range(18) if h[36 + i]]

    def off(self, a):
        for o, s, z in self.secs:
            if s <= a < s + z:
                return o + a - s
        raise ValueError(hex(a))

    def u32(self, a):
        return struct.unpack_from('>I', self.d, self.off(a))[0]

    def u8(self, a):
        return self.d[self.off(a)]


def command_effects(dol):
    """nargs and 'pushes a result' for each script command 0..0xDD."""
    nargs = {i: dol.u8(0x802BDF00 + i * 0x24) for i in range(0xDE)}
    table = [dol.u32(0x802C0078 + 4 * i) for i in range(0xDE)]
    starts = sorted(set(table)) + [0x801127C4]
    pushes = {}
    for i, t in enumerate(table):
        end = starts[starts.index(t) + 1]
        p = False
        for a in range(t, end, 4):
            w = dol.u32(a)
            if w >> 26 == 18 and w & 1:                       # bl
                li = w & 0x3FFFFFC
                if li & 0x2000000:
                    li -= 0x4000000
                if (a + li) & 0xFFFFFFFF in PUSHERS:
                    p = True
        pushes[i] = p
    return nargs, pushes


# ------------------------------------------------------------- containers
def clz_decompress(b):
    size = struct.unpack_from('>I', b, 4)[0]
    out = bytearray(); i = 0x10
    while len(out) < size:
        flags = b[i]; i += 1
        for k in range(8):
            if len(out) >= size:
                break
            if not (flags >> k) & 1:
                out.append(b[i]); i += 1
            else:
                b0, b1 = b[i], b[i + 1]; i += 2
                dist = 0x1000 - (b0 | ((b1 & 0xF0) << 4))
                for _ in range((b1 & 0x0F) + 3):
                    out.append(out[-dist])
    return bytes(out)


def clz_compress(data):
    """Optimal-parse LZSS in the game's CLZ format (inverse of clz_decompress).
    Literal = flag bit + 1 byte, reference = flag bit + 2 bytes; a dynamic
    programme picks the cheapest split. References never point before the
    start of the output, never overlap the bytes they produce and stay
    within 0xFE8 bytes, which is what the game's own archives use."""
    n = len(data)
    heads = collections.defaultdict(list); best = [(0, 0)] * n
    for i in range(n):
        if i + 3 <= n:
            key = data[i:i + 3]; bl = 0; bd = 0
            for j in reversed(heads[key]):
                dist = i - j
                if dist > MAX_DIST:
                    break
                l = 3
                while l < 18 and l < dist and i + l < n and data[j + l] == data[i + l]:
                    l += 1
                if l < 3 or l > dist:
                    continue
                if l > bl:
                    bl, bd = l, dist
                    if l == 18:
                        break
            best[i] = (bl, bd); heads[key].append(i)
    cost = [0] * (n + 1); pick = [None] * (n + 1)
    for i in range(n - 1, -1, -1):
        c = cost[i + 1] + 9; ch = (1, 0)
        bl, bd = best[i]
        for l in range(3, bl + 1):
            if cost[i + l] + 17 < c:
                c = cost[i + l] + 17; ch = (l, bd)
        cost[i] = c; pick[i] = ch
    out = bytearray(b'CLZ\0' + struct.pack('>III', n, 0, n)); i = 0
    while i < n:
        fp = len(out); out.append(0); flags = 0
        for k in range(8):
            if i >= n:
                break
            l, dist = pick[i]
            if l >= 3:
                v = 0x1000 - dist
                out += bytes([v & 0xFF, ((v >> 8) << 4) | (l - 3)]); flags |= 1 << k
                i += l
            else:
                out.append(data[i]); i += 1
        out[fp] = flags
    return bytes(out)


def u8_read(b):
    root = struct.unpack_from('>I', b, 4)[0]
    cnt = struct.unpack_from('>I', b, root + 8)[0]
    nodes = [list(struct.unpack_from('>III', b, root + 12 * n)) for n in range(cnt)]
    files = {n: b[nodes[n][1]:nodes[n][1] + nodes[n][2]] for n in range(1, cnt) if not nodes[n][0] >> 24}
    return root, nodes, files


def u8_relayout(orig, nodes, files):
    """Rewrite the data area of a flat U8 with new entry blobs, keeping the
    header and string table, 0x20-aligned entries, and the original total
    size (zero-padded at the end)."""
    root = struct.unpack_from('>I', orig, 4)[0]
    data_off = struct.unpack_from('>I', orig, 0xC)[0]
    head = bytearray(orig[:data_off]); body = bytearray(); pos = data_off
    order = sorted((nd[1], n) for n, nd in enumerate(nodes) if n and not nd[0] >> 24)
    new = [list(nd) for nd in nodes]
    for k, (_, n) in enumerate(order):
        blob = files[n]
        new[n][1] = pos; new[n][2] = len(blob)
        body += blob; pos += len(blob)
        if k != len(order) - 1:
            pad = (-pos) & 0x1F; body += b'\0' * pad; pos += pad
    for n, nd in enumerate(new):
        struct.pack_into('>III', head, root + 12 * n, *nd)
    out = bytes(head + body)
    if len(out) > len(orig):
        return None
    return out + b'\0' * (len(orig) - len(out))


def fit_archive(orig, nodes, files, patched):
    """Replace entry 1, then re-encode other entries (largest saving first)
    until the archive fits its original size. Re-encoded entries decompress
    to exactly their original bytes."""
    files = dict(files); files[1] = patched; redone = []
    out = u8_relayout(orig, nodes, files)
    if out:
        return out, redone
    gains = []
    for n, f in files.items():
        if n == 1:
            continue
        raw = clz_decompress(f); c = clz_compress(raw)
        assert clz_decompress(c) == raw
        if len(c) < len(f):
            gains.append((len(f) - len(c), n, c))
    for _, n, c in sorted(gains, reverse=True):
        files[n] = c; redone.append(n)
        out = u8_relayout(orig, nodes, files)
        if out:
            return out, redone
    raise SystemExit('Chapter1.arc does not fit its original size even after re-encoding')


# ------------------------------------------------------------------- SCR
def scr_parse(b):
    ch = {}; i = 12
    while i + 8 <= len(b):
        cid = b[i:i + 4]; sz = struct.unpack_from('>I', b, i + 4)[0]
        ch[cid] = (i, sz); i += 8 + sz + (sz & 1)
    co, cs = ch[b'CODE']
    n = struct.unpack_from('>I', b, co + 8)[0]
    ins = [list(struct.unpack_from('>BBHi', b, co + 12 + 8 * k)) for k in range(n)]
    return ch, ins


def scr_build(orig, ins):
    ch, _ = scr_parse(orig)
    out = bytearray(b'RIFF\0\0\0\0SCR ')
    for cid, (o, sz) in sorted(ch.items(), key=lambda x: x[1][0]):
        if cid == b'CODE':
            body = struct.pack('>I', len(ins)) + b''.join(struct.pack('>BBHi', *x) for x in ins)
        else:
            body = orig[o + 8:o + 8 + sz]
        out += cid + struct.pack('>I', len(body)) + body
        if len(body) & 1:
            out += b'\0'
    struct.pack_into('>I', out, 4, len(out))
    return bytes(out)


OP_PUSHV, OP_PUSH, OP_CMP, OP_JMP, OP_JZ, OP_JNZ, OP_STORE, OP_SYS = 0x13, 0x17, 0x12, 0x18, 0x1B, 0x1C, 0x01, 0x25


def stack_effect(op, a, nargs, pushes):
    if op in (0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x12):
        return -1
    if op in (0x0E, 0x0F, 0x10, 0x11, 0x18, 0x21, 0x22, 0x23, 0x24):
        return 0
    if op in (0x13, 0x15, 0x17):
        return 1
    if op in (0x14, 0x16) or 0x19 <= op <= 0x1E:
        return -1
    if op == 0x25:
        return -nargs[a] + (1 if pushes[a] else 0)
    raise ValueError('op %02X not handled (call/ret?)' % op)


def depths(ins, nargs, pushes):
    N = len(ins); dep = [None] * N; work = [(0, 0)]
    while work:
        k, dp = work.pop()
        if k >= N:
            continue
        if dep[k] is not None:
            if dep[k] != dp:
                raise ValueError('stack depth mismatch at %04X' % k)
            continue
        dep[k] = dp
        op, f, p, a = ins[k]
        nd = dp + stack_effect(op, a, nargs, pushes)
        if op == 0x24:
            continue
        if op == 0x18:
            work.append((a, nd)); continue
        if 0x19 <= op <= 0x1E:
            work.append((a, nd))
        work.append((k + 1, nd))
    return dep


END_AT = 0x148F        # the opening's last part: 0x27, other.mes 450 ("The Beginning"), 0x27, END


class Asm:
    """Tiny assembler for appended code (labels resolved at the end)."""
    def __init__(self, base):
        self.base = base; self.code = []; self.labels = {}; self.fix = []

    def here(self, name):
        self.labels[name] = self.base + len(self.code)

    def op(self, op, a=0):
        if isinstance(a, str):
            self.fix.append((len(self.code), a)); a = 0
        self.code.append([op, 0, 0, a])

    def num(self, v):                         # push a fixed-point number
        self.op(OP_PUSH, v << SHIFT)

    def sys(self, cmd):
        self.op(OP_SYS, cmd)

    def wait_nonzero(self, push_args, cmd, name):
        """Repeat (yield; args; cmd) until it returns non-zero, like the game's
        own loops: L: SYS 00; PUSH 0; args; SYS cmd; CMP; JZ t; PUSH 0; JMP c;
        t: PUSH 1; c: JNZ L"""
        self.here(name); self.sys(0x00); self.op(OP_PUSH, 0); push_args(); self.sys(cmd)
        self.op(OP_CMP); self.op(OP_JZ, name + '_t'); self.op(OP_PUSH, 0); self.op(OP_JMP, name + '_c')
        self.here(name + '_t'); self.op(OP_PUSH, 1); self.here(name + '_c'); self.op(OP_JNZ, name)

    def done(self):
        for i, name in self.fix:
            self.code[i][3] = self.labels[name]
        return self.code


def patch_script(ins):
    """Prompt at PROMPT_AT; No continues the original script, Yes runs the
    naming sequence only and then jumps to "The Beginning" (END_AT)."""
    N = len(ins); one = 1 << SHIFT
    A = Asm(N)
    # --- prompt: v[SKIPVAR] = (answer == Yes)
    def prompt_args():
        A.op(OP_PUSH, SKIPVAR); A.num(PROMPT_FILE); A.num(PROMPT_MSG); A.op(OP_PUSH, -one)
    A.here('prompt'); A.sys(0x00); A.op(OP_PUSH, 0); prompt_args(); A.sys(0x04); A.op(OP_STORE)
    A.op(OP_CMP); A.op(OP_JZ, 'p_t'); A.op(OP_PUSH, 0); A.op(OP_JMP, 'p_c')
    A.here('p_t'); A.op(OP_PUSH, 1); A.here('p_c'); A.op(OP_JNZ, 'prompt')
    A.op(OP_PUSH, SKIPVAR); A.op(OP_PUSHV, SKIPVAR); A.num(1); A.op(OP_CMP); A.op(0x11)
    A.op(OP_STORE); A.op(0x16)
    A.op(OP_PUSHV, SKIPVAR); A.op(OP_JNZ, 'fast')
    A.code.append(list(ins[PROMPT_AT])); A.op(OP_JMP, PROMPT_AT + 1)      # No: original
    # --- Yes
    def black():                     # instant black, as the script's own setup (0x0002-0x000D)
        for layer in (0, 1, 3):
            A.num(layer); A.num(0); A.num(0); A.sys(0x41)

    def say(msg, name):              # one of the new system.mes lines, until closed
        A.wait_nonzero(lambda: (A.num(PROMPT_FILE), A.num(msg), A.op(OP_PUSH, -one)), 0x04, name)
    A.here('fast')
    # dog choice: system.mes 0x1FA "Which dog do you want?" with the Pointy Ears / Long Ears options
    # (as takakura.mes 113, without Takakura's line); v[2] = choice; v[8] = 39 (first) or 40
    A.here('c113'); A.sys(0x00); A.op(OP_PUSH, 0); A.op(OP_PUSH, 2); A.num(PROMPT_FILE); A.num(MSG_DOG)
    A.op(OP_PUSH, -one); A.sys(0x04); A.op(OP_STORE); A.op(OP_CMP); A.op(OP_JZ, 'c_t')
    A.op(OP_PUSH, 0); A.op(OP_JMP, 'c_c'); A.here('c_t'); A.op(OP_PUSH, 1)
    A.here('c_c'); A.op(OP_JNZ, 'c113')
    A.op(OP_PUSH, 8); A.num(39); A.op(OP_STORE); A.op(0x16)                     # v[8] = 39
    A.op(OP_PUSHV, 2); A.num(1); A.op(OP_CMP); A.op(OP_JZ, 'dog')               # choice 1 -> 39
    A.op(OP_PUSH, 8); A.num(40); A.op(OP_STORE); A.op(0x16)                     # else 40
    A.here('dog')
    A.num(13); A.op(OP_PUSHV, 8); A.sys(0x03); A.op(0x16)                       # as 0x0594
    A.num(75); A.sys(0x7D); A.num(76); A.sys(0x7D)                              # as 0x0598
    A.wait_nonzero(lambda: A.op(OP_PUSHV, 8), 0x0E, 'n_dog')                    # as 0x059C
    black()
    A.num(2); A.num(90); A.num(1); A.num(1); A.sys(0x2D); A.op(0x16)            # as 0x097B
    say(MSG_COW, 'm_cow')                                                       # replaces 122
    A.wait_nonzero(lambda: A.num(49), 0x0E, 'n_cow')                            # as 0x0A69
    A.num(0); A.num(0); A.sys(0x05)                                             # as 0x0A73
    black()
    say(MSG_FARM, 'm_farm')                                                     # replaces 124
    A.wait_nonzero(lambda: A.num(72), 0x0E, 'n_farm')                           # as 0x0B6D
    black()
    say(MSG_YOU, 'm_you')                                                       # replaces 126
    A.wait_nonzero(lambda: A.num(0), 0x0E, 'n_player')                          # as 0x0C4C
    black()
    for h, m in ((13, 10), (15, 30), (7, 40)):                                  # clock, in order
        A.num(h); A.num(m); A.sys(0x43)
    A.num(1); A.sys(0x2C); A.sys(0x00); A.sys(0x10)                             # as 0x127D
    black()
    A.op(OP_JMP, END_AT)
    app = A.done()
    new = [list(x) for x in ins]
    new[PROMPT_AT] = [OP_JMP, 0, 0, A.labels['prompt']]
    for x in new:
        x[2] = 0                            # pad bytes are never read
    return new + app


# ---------------------------------------------------------------- system.mes
GLYPH = {' ': None, '?': 0x80CA, '.': 0x80C8, ',': 0x8105, "'": 0x80F2}
for i in range(26):
    GLYPH[chr(65 + i)] = 0x800B + i
    GLYPH[chr(97 + i)] = 0x80D8 + i


def mes_text(s, choice=False):
    """Encode a message: '\n' = new line (01), ' ' = 02. choice=True: a Yes/No
    prompt, ending 40 00 00; choice=[option, ...]: the game's own option list
    (as takakura.mes 113 / badog.mes 5): 01 41 <count> 00, the options split by
    01, then 00; otherwise a plain line ending 30 00 (wait for A, end)."""
    def glyphs(t):
        out = bytearray()
        for c in t:
            if c == ' ':
                out.append(0x02)
            elif c == '\n':
                out.append(0x01)
            else:
                out += struct.pack('>H', GLYPH[c])
        return out
    out = glyphs(s)
    if isinstance(choice, list):
        out += bytes([0x01, 0x41, len(choice), 0x00]) + b'\x01'.join(glyphs(o) for o in choice) + b'\x00'
    else:
        out += b'\x40\x00\x00' if choice else b'\x30\x00'
    out += b'\0' * ((-len(out)) & 3)
    return bytes(out)


def mes_add(mes, texts):
    """Append messages 0x1F9, 0x1FA, ... (`texts`) plus 0x1F8 sharing 0x1F9's
    text, without growing the file. Space comes from byte-identical
    duplicate messages: a duplicate's offset is pointed at its first copy
    and its bytes are dropped, only as many as needed. The text lookup
    (func_800FB498) is just base + offset[id], with no length or order
    check, so shared and unordered offsets are fine. Returns the new file
    and the list of (duplicate, original) ids that now share text."""
    magic, n = struct.unpack_from('>II', mes, 0)
    assert magic == 0xCDC3B0B0 and n == 0x1F8, 'expected the original system.mes (504 messages)'
    offs = list(struct.unpack_from('>%dI' % n, mes, 8)) + [len(mes)]
    blobs = [mes[offs[i]:offs[i + 1]] for i in range(n)]
    first = {}; dups = []
    for i, b in enumerate(blobs):
        if b in first:
            dups.append((i, first[b]))
        else:
            first[b] = i
    add = 1 + len(texts)
    for k in range(len(dups) + 1):
        share = dict(dups[:k])
        table = 8 + 4 * (n + add); body = bytearray(); new = []
        for i, b in enumerate(blobs):
            if i in share:
                new.append(None); continue
            new.append(table + len(body)); body += b
        new = [new[share[i]] if i in share else o for i, o in enumerate(new)]
        # drop the zero padding the last message carries beyond 4-byte alignment
        while body.endswith(b'\0' * 5):
            body = body[:-4]
        tail = []
        for t in texts:
            tail.append(table + len(body)); body += t
        new += [tail[0]] + tail
        out = struct.pack('>II', magic, n + add) + struct.pack('>%dI' % (n + add), *new) + bytes(body)
        if len(out) <= len(mes):
            return out + b'\0' * (len(mes) - len(out)), dups[:k]
    raise SystemExit('system.mes: the new messages do not fit')


# ---------------------------------------------------------------------- main
def main():
    dol_p, arc_p, mes_p, outdir = sys.argv[1:5]
    dol = Dol(dol_p)
    nargs, pushes = command_effects(dol)
    arc = open(arc_p, 'rb').read()
    root, nodes, files = u8_read(arc)
    scr = clz_decompress(files[1])
    ch, ins = scr_parse(scr)
    assert len(ins) == 0x14A5, 'unexpected opening script'
    dep = depths(ins, nargs, pushes)
    new = patch_script(ins)
    depths(new, nargs, pushes)                     # patched script must still balance
    # the No path must reach every original instruction it reached before
    orig_reach = {k for k, x in enumerate(dep) if x is not None}
    nscr = scr_build(scr, new)
    blob = clz_compress(nscr)
    assert clz_decompress(blob) == nscr
    narc, redone = fit_archive(arc, nodes, files, blob)
    _, nnodes, chk = u8_read(narc)
    for n in chk:
        if n == 1:
            assert clz_decompress(chk[1]) == nscr
        elif n in redone:
            assert clz_decompress(chk[n]) == clz_decompress(files[n])
        else:
            assert chk[n] == files[n]
    assert len(narc) == len(arc)
    mes = open(mes_p, 'rb').read()
    nmes, shared = mes_add(mes, [mes_text(t, choice=c) for t, c in LINES])
    assert len(nmes) == len(mes)
    os.makedirs(outdir, exist_ok=True)
    open(os.path.join(outdir, 'Chapter1.arc'), 'wb').write(narc)
    open(os.path.join(outdir, 'system.mes'), 'wb').write(nmes)
    with open(os.path.join(outdir, 'patch_report.txt'), 'w') as f:
        f.write('opening script: %d instructions, %d reachable\n' % (len(ins), len(orig_reach)))
        f.write('patched script: %d instructions (+%d)\n' % (len(new), len(new) - len(ins)))
        f.write('system.mes: new ids 0x1F8/0x1F9-0x%X; messages now sharing a duplicate: %s\n'
                % (0x1F8 + len(LINES), ', '.join('0x%X=0x%X' % d for d in shared)))
        f.write('Chapter1.arc %d -> %d bytes (entry 1 %d -> %d bytes; re-encoded, same content: %s); '
                'system.mes %d -> %d bytes\n'
                % (len(arc), len(narc), nodes[1][2], len(blob),
                   ', '.join('entry %d %d->%d' % (n, nodes[n][2], nnodes[n][2]) for n in redone) or 'none',
                   len(mes), len(nmes)))
        f.write('prompt hook: instruction %04X -> JMP %04X\n' % (PROMPT_AT, new[PROMPT_AT][3]))
        f.write('instr %04X was %s, now %s\n' % (PROMPT_AT,
                ' '.join('%02X' % x for x in struct.pack('>BBHi', *ins[PROMPT_AT])),
                ' '.join('%02X' % x for x in struct.pack('>BBHi', *new[PROMPT_AT]))))
        f.write('appended %04X-%04X: prompt, then Yes = dog choice, 4 x (line, naming), clock, warp, jmp %04X\n'
                % (len(ins), len(new) - 1, END_AT))
    print(open(os.path.join(outdir, 'patch_report.txt')).read().split('\nregion')[0])


if __name__ == '__main__':
    main()
