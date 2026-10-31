"""tidy cut hair: drop spikes (triangles with 2+ open edges) and tiny pieces, smooth every open edge into a
clean curve that tucks slightly in towards the head (a rounded lock end), then smooth the surface"""
import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank']
import gd2
from collections import defaultdict
def open_edges(wid,F):
    ec=defaultdict(int)
    for f in F:
        for a,b in ((f[0],f[1]),(f[1],f[2]),(f[2],f[0])): ec[tuple(sorted((wid[a],wid[b])))]+=1
    return ec
def clean(P,F,spike_passes=3,min_piece=10,iters=25,tuck=0.012,smooth_iters=6):
    wid,n=gd2.weld(P)
    for _ in range(spike_passes):
        ec=open_edges(wid,F)
        nb=np.array([sum(ec[tuple(sorted((wid[f[i]],wid[f[(i+1)%3]])))]==1 for i in range(3)) for f in F])
        F=F[nb<2]
    par=list(range(n))
    def fd(x):
        while par[x]!=x: par[x]=par[par[x]]; x=par[x]
        return x
    for f in F: par[fd(wid[f[0]])]=fd(wid[f[1]]); par[fd(wid[f[1]])]=fd(wid[f[2]])
    comp=np.array([fd(wid[f[0]]) for f in F]); cnt=defaultdict(int)
    for c in comp: cnt[c]+=1
    F=F[np.array([cnt[c]>=min_piece for c in comp])]
    WP=np.zeros((n,3)); WP[wid]=P
    ec=open_edges(wid,F); bn=defaultdict(set)
    for (a,b),c in ec.items():
        if c==1: bn[a].add(b); bn[b].add(a)
    bv=np.array(sorted(bn)); 
    cen=np.array([0,1.0,-0.02])
    for _ in range(iters):
        NW=WP.copy()
        for v in bv:
            nb=list(bn[v]); NW[v]=0.5*WP[v]+0.5*WP[nb].mean(0)
        WP=NW
    # tuck the edge in towards the head axis (rounded end)
    for v in bv:
        d=WP[v]-cen; d[1]=0; L=np.linalg.norm(d)
        if L>1e-6: WP[v]-=d/L*tuck
    P2=WP[wid]
    P2=gd2.taubin(P2,F,np.ones(len(F),bool),iters=smooth_iters)
    return P2,F

def boundary_loops(wid,F):
    ec=open_edges(wid,F); nxt=defaultdict(list)
    for f in F:
        for a,b in ((f[0],f[1]),(f[1],f[2]),(f[2],f[0])):
            if ec[tuple(sorted((wid[a],wid[b])))]==1: nxt[wid[a]].append(wid[b])
    loops=[]; seen=set()
    for s in list(nxt):
        if s in seen: continue
        lp=[s]; seen.add(s); cur=s
        while True:
            n=[x for x in nxt[cur] if x not in seen]
            if not n: break
            cur=n[0]; lp.append(cur); seen.add(cur)
        loops.append(lp)
    return loops
def fill_holes(P,Q,F,maxlen=0.25,maxn=8):
    """close small holes: fan from the hole's centre (new vertex), UVs from the nearest corner"""
    wid,n=gd2.weld(P); rep={}
    for i,w in enumerate(wid): rep.setdefault(w,i)
    WP=np.zeros((n,3)); WP[wid]=P
    P=list(P); Q=list(Q); newF=[]
    for lp in boundary_loops(wid,F):
        if len(lp)<3 or len(lp)>maxn: continue
        L=sum(np.linalg.norm(WP[lp[i]]-WP[lp[(i+1)%len(lp)]]) for i in range(len(lp)))
        if L>maxlen or WP[lp].mean(0)[2]>-0.1: continue
        c=WP[lp].mean(0); ci=len(P); P.append(c); Q.append(Q[rep[lp[0]]])
        for i in range(len(lp)):
            a=rep[lp[i]]; b=rep[lp[(i+1)%len(lp)]]; newF.append((b,a,ci))
    F2=np.vstack([F,np.array(newF)]) if newF else F
    return np.array(P),np.array(Q),F2,len(newF)
