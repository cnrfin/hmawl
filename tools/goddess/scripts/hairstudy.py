import sys,numpy as np
sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/pm']
import awlmodel, wally
from collections import defaultdict
G='/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/girls/'
NAMES={'sepi':'Celia','mumu':'Muffy','nami':'Nami','rumi':'Lumina','flora':'Flora','kuri':'Chris','keit':'Karen?','san':'Sabrina?','roma':'Romana','besu':'Vesta','nina':'Nina','ru':'Ruby'}
def hair(n):
    p=G+f'{n}_0/{n}_0'; M=awlmodel.load(p); T=wally.textures(p+'_b0.tpl',p+'_f0_e.tpl',p+'_f0_m.tpl')
    B=M['bones']; V=M['V']
    cen=defaultdict(list)
    for i,b in enumerate(B):
        for x in b: cen[x].append(V[i][1])
    headb={b for b,ys in cen.items() if np.mean(ys)>0.93 and len(ys)>3}
    # face sheet bbox (tid 2) to separate face from hair
    tris=[]
    for tid,ts,_ in M['groups']:
        if tid!=255: continue
        for pi,ti in ts:
            if all(B[v] and set(B[v])<=headb for v in pi): tris.append((pi,ti))
    return M,T,tris,headb
def stats(M,tris):
    V=M['V']; ec=defaultdict(int)
    for pi,_ in tris:
        for a,b in ((pi[0],pi[1]),(pi[1],pi[2]),(pi[2],pi[0])): ec[tuple(sorted((a,b)))]+=1
    # weld by position for edge stats
    key={}; w=[key.setdefault(tuple(np.round(V[i],3)),len(key)) for i in range(len(V))]
    ew=defaultdict(int)
    for pi,_ in tris:
        q=[w[i] for i in pi]
        for a,b in ((q[0],q[1]),(q[1],q[2]),(q[2],q[0])): ew[tuple(sorted((a,b)))]+=1
    vs=sorted({i for pi,_ in tris for i in pi}); Q=V[vs]
    return dict(tris=len(tris),verts=len({w[i] for i in vs}),open_edges=sum(1 for c in ew.values() if c==1),edges=len(ew),
                ymin=Q[:,1].min(),ymax=Q[:,1].max(),zmin=Q[:,2].min(),xw=Q[:,0].max()-Q[:,0].min())

def hair2(n):
    p=G+f'{n}_0/{n}_0'; M=awlmodel.load(p); T=wally.textures(p+'_b0.tpl',p+'_f0_e.tpl',p+'_f0_m.tpl')
    B=M['bones']; V=M['V']; nodes=M['nodes']
    cen=defaultdict(list)
    for i,b in enumerate(B):
        for x in b: cen[x].append(V[i][1])
    head=max((b for b,ys in cen.items() if len(ys)>50), key=lambda b: np.mean(cen[b]))
    def under(b):
        while b>=0:
            if b==head: return True
            b=nodes[b]['parent']
        return False
    hb={b for b in range(len(nodes)) if under(b)}
    face=set()
    tris=[]
    for tid,ts,_ in M['groups']:
        if tid!=255: continue
        for pi,ti in ts:
            if all(B[v] and set(B[v])<=hb for v in pi): tris.append((pi,ti))
    return M,T,tris,hb
