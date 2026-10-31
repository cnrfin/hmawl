"""Make the head ONE surface: delete the reshaped original-head triangles that lie under Muffy's face shell,
then zip the head's cut edge onto the face shell's outer edge (shared vertex positions, no overlap, no gap)."""
import sys; sys.path[:0]=['.','blank']
import numpy as np, pickle, heapq
from collections import Counter, defaultdict
import muffyhead as MH
from skull2 import rays
DY=0.04; SH=np.array([0,-DY,0]); C0=MH.C0+SH
def weld(P,F,dec=4):
    key={};idx=np.zeros(len(P),int);U=[]
    for i,p in enumerate(P):
        k=tuple(np.round(p,dec))
        if k not in key: key[k]=len(U); U.append(p)
        idx[i]=key[k]
    return np.array(U),idx[F],idx
def bedges(F):
    e=Counter()
    for t in F:
        for a,b in ((t[0],t[1]),(t[1],t[2]),(t[2],t[0])): e[tuple(sorted((a,b)))]+=1
    return [k for k,v in e.items() if v==1]
def build():
    g=pickle.load(open('goddess_option3_dy40.pkl','rb')); V=g['V'].copy(); Fb=g['Fb'].copy(); Ub=g['Ub']
    mh=pickle.load(open('muffyhead_v1.pkl','rb')); f=mh['face']
    # face shell, shifted, welded
    FP=np.vstack([f[t][0] for t in (2,0,1)])+SH; FF=[];o=0
    for t in (2,0,1): FF.append(f[t][2]+o); o+=len(f[t][0])
    FF=np.vstack(FF); U,W,fidx=weld(FP,FF)
    # ears: small boundary loops that hang off the face outline at one junction vertex
    fb0=bedges(W); ad=defaultdict(list)
    for a,b in fb0: ad[a].append(b); ad[b].append(a)
    earv=np.zeros(len(U),bool); earedges=set()
    for j in [v for v in ad if len(ad[v])==4]:
        for n0 in ad[j]:
            L=[j,n0]
            while L[-1]!=j and len(L)<12:
                nx=[x for x in ad[L[-1]] if x!=L[-2]]
                if len(nx)!=1: break
                L.append(nx[0])
            if L[-1]==j and len(L)<12:
                earv[L[1:-1]]=True; earedges|={tuple(sorted((L[i],L[i+1]))) for i in range(len(L)-1)}
    print('ear verts',earv.sum())
    # close the opening at each ear base (it sits between the ear cup and the head): triangles junction->rim
    # using only rim vertices that lie at the head side (|x| below the ear tips)
    n2=len(f[2][0]); uv2={}
    for k in range(n2): uv2.setdefault(fidx[k],f[2][1][k])
    earpatch=[]
    for j in [v for v in ad if len(ad[v])==4]:
        for n0 in ad[j]:
            L=[j,n0]
            while L[-1]!=j and len(L)<12:
                nx=[x for x in ad[L[-1]] if x!=L[-2]]
                if len(nx)!=1: break
                L.append(nx[0])
            if L[-1]==j and len(L)<12:
                rim=L[1:-1]   # close the whole ear opening/back (fan from the junction over the rim)
                for a,b in zip(rim[:-1],rim[1:]): earpatch.append((j,a,b))
                break
    print('ear patch tris',earpatch)
    ftri=U[W[~earv[W].any(1)]]            # coverage ignores the ear flaps (the head continues behind them)
    # head triangles of the body mesh (above the neck)
    cen=V[Fb].mean(1); head=V[Fb][:,:,1].min(1)>0.80
    # coverage test: vertex is covered if the ray from C0 through it hits the face shell
    hv=np.unique(Fb[head]); d=V[hv]-C0; d/=np.linalg.norm(d,axis=1)[:,None]
    t=rays(np.repeat(C0[None],len(hv),0),d,ftri); r=np.linalg.norm(V[hv]-C0,axis=1)
    hit=np.isfinite(t)&(np.abs(t-r)<0.03); cov=np.zeros(len(V),bool); cov[hv[hit]]=True
    print('covered head verts',hit.sum(),'of',len(hv))
    kill=head&(cov[Fb].sum(1)>=2)
    Fk=Fb[~kill]; Uk=Ub[~kill]
    # head cut boundary = boundary edges of remaining mesh among head verts
    hb=[e for e in bedges(Fk) if V[list(e)][:,1].min()>0.80]
    fb=bedges(W)
    fadj=defaultdict(list)
    fb2=[e for e in fb if tuple(sorted(e)) not in earedges]
    for a,b in fb2: L=np.linalg.norm(U[a]-U[b]); fadj[a].append((b,L)); fadj[b].append((a,L))
    fbv=np.array(sorted(fadj))
    # snap each head boundary vertex onto the nearest face-boundary vertex (keeps vertices shared exactly)
    hbv=sorted(set(np.array(hb).ravel()))
    snap={}
    for v in hbv:
        j=fbv[np.argmin(np.linalg.norm(U[fbv]-V[v],axis=1))]; snap[v]=j
    moved=max(np.linalg.norm(U[snap[v]]-V[v]) for v in hbv)
    for v in hbv: V[v]=U[snap[v]]
    # fill: for each head boundary edge (a,b), walk face boundary shortest path snap[a]->snap[b]; fan from a
    def path(s,t):
        dist={s:0};prev={};pq=[(0,s)]
        while pq:
            dd,u=heapq.heappop(pq)
            if u==t: break
            if dd>dist[u]: continue
            for w,L in fadj[u]:
                if dd+L<dist.get(w,1e9): dist[w]=dd+L; prev[w]=u; heapq.heappush(pq,(dd+L,w))
        if t not in dist: return None
        p=[t]
        while p[-1]!=s: p.append(prev[p[-1]])
        return p[::-1]
    fill=[]; nskip=0
    for a,b in hb:
        p=path(snap[a],snap[b])
        if p is None: nskip+=1; continue
        for i in range(1,len(p)-1):
            fill.append((V[a].copy(),U[p[i]],U[p[i+1]]))
    return dict(earpatch=[(U[list(t)],np.array([(0.3,0.7)]*3)) for t in earpatch],V=V,Fk=Fk,Uk=Uk,kill=kill,fill=fill,moved=moved,nskip=nskip,nhb=len(hb),U=U,W=W,face=f,g=g)
if __name__=='__main__':
    r=build(); print('killed head tris',r['kill'].sum(),'head cut edges',r['nhb'],'max snap move',round(r['moved'],4),'fill tris',len(r['fill']),'unjoined edges',r['nskip'])
    pickle.dump({k:r[k] for k in ('V','Fk','Uk','fill','earpatch')},open('stitched_v1.pkl','wb'))
