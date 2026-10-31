import sys,struct
from collections import defaultdict
d=open(sys.argv[1],'rb').read()
S=64.0
tris=[]
def node(o,seen=set()):
    if o in seen or o==0: return
    seen.add(o)
    bb=struct.unpack('>6h',d[o:o+12]); ch=struct.unpack('>4I',d[o+12:o+28])
    nt,nv,_,to,vo=struct.unpack('>5I',d[o+28:o+48])
    if any(ch):
        for c in ch: node(c)
        return
    V=[struct.unpack('>4h',d[o+vo+8*i:o+vo+8*i+8])[:3] for i in range(nv)]
    for k in range(nt):
        a,i0,i1,i2=struct.unpack('>4H',d[o+to+8*k:o+to+8*k+8])
        p=[V[i] for i in (i0,i1,i2)]
        tris.append((a,[[c/S for c in v] for v in p]))
node(8)
MAP={0:0,1:1,2:3,3:2}
groups=defaultdict(list)
for a,p in tris: groups[a].append(p)
for a,ps in sorted(groups.items()):
    xs=[v[0] for p in ps for v in p]; zs=[v[2] for p in ps for v in p]; ys=[v[1] for p in ps for v in p]
    print('raw attr',a,'-> water type',MAP.get(a,5),'tris',len(ps),'x %.0f..%.0f z %.0f..%.0f y %.1f..%.1f'%(min(xs),max(xs),min(zs),max(zs),min(ys),max(ys)))
if len(sys.argv)>2:
    import pickle; pickle.dump(tris,open(sys.argv[2],'wb'))
