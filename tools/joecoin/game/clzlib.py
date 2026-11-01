import struct
def be(b,o): return struct.unpack_from('>I',b,o)[0]
def clz_decompress(b):
    assert b[:4]==b'CLZ\0'
    size=be(b,4); o=bytearray(); i=0x10
    while len(o)<size:
        f=b[i]; i+=1
        for k in range(8):
            if len(o)>=size: break
            if not (f>>k)&1: o.append(b[i]); i+=1
            else:
                b0,b1=b[i],b[i+1]; i+=2; dist=0x1000-(b0|((b1&0xF0)<<4))
                for _ in range((b1&0xF)+3): o.append(o[-dist])
    return bytes(o)
def clz_compress(b):
    n = len(b); W = 0x1000; MAXL = 18
    heads = {}; cand = [None]*n
    for i in range(n):
        if i + 3 <= n:
            k = b[i:i+3]; lst = heads.setdefault(k, [])
            best = []
            for j in reversed(lst):
                if i - j > W: break
                best.append(j)
                if len(best) >= 64: break
            cand[i] = best; lst.append(i)
    # cost in bits: literal 9, match 17
    INF = 1 << 60; cost = [INF]*(n+1); choice = [None]*(n+1); cost[n] = 0
    for i in range(n-1, -1, -1):
        c = cost[i+1] + 9; ch = (0, 1)
        for j in cand[i] or ():
            L = 0
            while L < MAXL and i+L < n and b[j+L] == b[i+L]: L += 1
            for l in range(3, L+1):
                cc = cost[i+l] + 17
                if cc < c: c = cc; ch = (i-j, l)
        cost[i] = c; choice[i] = ch
    out = bytearray(b'CLZ\0' + struct.pack('>III', n, 0, n))
    i = 0
    while i < n:
        fpos = len(out); out.append(0); f = 0
        for k in range(8):
            if i >= n: break
            d, l = choice[i]
            if d == 0: out.append(b[i]); i += 1
            else:
                v = 0x1000 - d; out.append(v & 0xFF); out.append(((v >> 4) & 0xF0) | (l - 3)); f |= 1 << k; i += l
        out[fpos] = f
    return bytes(out)
