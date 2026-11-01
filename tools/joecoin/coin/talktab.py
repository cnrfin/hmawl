import sys,struct
sys.path.insert(0,'/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad')
from clz import clz_decompress
from mesloose import dump
MES='/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/joecoin/mes/mes files US/'
GROUPS={}
def groups():
    d=open('/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/bin/main.dol','rb').read()
    offs=struct.unpack_from('>18I',d,0); addrs=struct.unpack_from('>18I',d,0x48); sizes=struct.unpack_from('>18I',d,0x90)
    def at(a):
        for o,ad,s in zip(offs,addrs,sizes):
            if s and ad<=a<ad+s: return o+a-ad
    for i in range(67):
        o=at(0x802517E0+8*i); a,b=struct.unpack_from('>II',d,o)
        if b: GROUPS[i]=d[at(b):d.index(b'\0',at(b))].decode()
groups()
_mes={}
def line(g,m):
    if g not in GROUPS: return '?'
    f=GROUPS[g]
    if f not in _mes:
        try: _mes[f]=dump(MES+f)
        except Exception: _mes[f]=[]
    L=_mes[f]; return L[m] if m<len(L) else '?'
def load(arc):
    A=open(arc,'rb').read(); root=0x20; n=struct.unpack_from('>I',A,root+8)[0]
    mem=[struct.unpack_from('>II',A,root+12*k+4) for k in range(1,n)]
    return [clz_decompress(A[o:o+s]) for o,s in mem]
def rec(u,i):
    r=u[i*78:(i+1)*78]
    pages=[[struct.unpack_from('>HH',r,p*20+4*j) for j in range(4)]+[struct.unpack_from('>I',r,p*20+16)[0]] for p in range(3)]
    tri=[struct.unpack_from('>HHH',r,60+6*j) for j in range(3)]
    return pages,tri
