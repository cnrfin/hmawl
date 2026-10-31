"""Muffy's bald head: her own face shell (face, eyes, mouth, ears) + a closed skull built from her own head
shape (under the face: just inside the face; elsewhere: just inside her hair's inner surface). Same skeleton
as our body, so it goes on at her exact size and position."""
import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/pm']
import awlmodel, hairstudy as S
from skull2 import rays
MP='/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/girls/mumu_0/mumu_0'
C0=np.array([0,1.07,-0.03])
def face_parts(ycut=0.84):
    M=awlmodel.load(MP); V=M['V']; UV=M['UV']
    g={}
    for tid,ts,_ in M['groups']: g.setdefault(tid,[]).extend(ts)
    out={}
    for tid in (2,0,1):
        P=[];Q=[];F=[];key={}
        for pi,ti in g[tid]:
            if V[list(pi)].mean(0)[1]<ycut: continue
            idx=[]
            for p,x in zip(pi,ti):
                k=(p,x)
                if k not in key: key[k]=len(P); P.append(V[p]); Q.append((UV[x][0]%1,UV[x][1]%1) if tid==2 else (UV[x][0],UV[x][1]))
                idx.append(key[k])
            F.append(idx)
        out[tid]=(np.array(P),np.array(Q),np.array(F)[:,::-1])
    return out
def skull(face, rings=14, segs=22, hair_in=0.022, face_in=0.004, ybot=0.86, smooth=30):
    M=awlmodel.load(MP); _,_,ht,_=S.hair2('mumu'); V=M['V']
    htri=np.array([V[list(pi)] for pi,_ in ht])
    ftri=np.vstack([face[t][0][face[t][2]] for t in face])
    P=[];D=[];ring=[]
    for i in range(rings+1):
        ph=np.pi*i/rings
        for j in range(segs):
            th=2*np.pi*j/segs; d=np.array([np.sin(ph)*np.sin(th),np.cos(ph),np.sin(ph)*np.cos(th)]); D.append(d)
    D=np.array(D); O=np.repeat(C0[None],len(D),0)
    rf=rays(O,D,ftri); rh=rays(O,D,htri)
    # hair: innermost hit = hair's inner surface; use the nearest hit along the ray
    r=np.where(np.isfinite(rf),rf-face_in,np.where(np.isfinite(rh),rh-hair_in,np.nan))
    fixed=np.isfinite(rf)
    n=len(D); nb=[set() for _ in range(n)]
    for i in range(rings+1):
        for j in range(segs):
            a=i*segs+j
            for b in (i*segs+(j+1)%segs,(i+1)*segs+j if i<rings else None):
                if b is not None and b<n: nb[a].add(b); nb[b].add(a)
    r=np.where(np.isnan(r),np.nanmedian(r),r)
    for _ in range(smooth):
        m=np.array([r[list(s)].mean() for s in nb]); r=np.where(fixed,r,0.5*r+0.5*m)
        r=np.where(np.isfinite(rf),np.minimum(r,rf-face_in),r)
    P=C0+D*r[:,None]
    P[:,1]=np.maximum(P[:,1],ybot)                      # flat-ish base inside the neck
    F=[]
    for i in range(rings):
        for j in range(segs):
            a=i*segs+j; b=i*segs+(j+1)%segs; c=a+segs; d=b+segs
            if i>0: F.append((a,b,c))
            if i<rings-1: F.append((b,d,c))
    F=np.array(F)
    nrm=np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]); flip=(nrm*(P[F].mean(1)-C0)).sum(1)<0; F[flip]=F[flip][:,::-1]
    A=np.linalg.norm(nrm,axis=1); F=F[A>1e-10]
    return P,F

def head_radius_fn(tris, res=4):
    """radius of a closed-ish head surface along directions from C0 (rays), cached on a direction grid"""
    th=np.radians(np.arange(-180,181,res)); ph=np.radians(np.arange(0,181,res))
    TH,PH=np.meshgrid(th,ph); D=np.stack([np.sin(PH)*np.sin(TH),np.cos(PH),np.sin(PH)*np.cos(TH)],-1).reshape(-1,3)
    r=rays(np.repeat(C0[None],len(D),0),D,tris).reshape(PH.shape)
    r=np.where(np.isfinite(r),r,np.nan)
    for _ in range(50):
        m=np.isnan(r)
        if not m.any(): break
        acc=np.zeros_like(r); cnt=np.zeros_like(r)
        for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
            sh=np.roll(np.roll(r,dy,0),dx,1); ok=~np.isnan(sh); acc[ok]+=sh[ok]; cnt+=ok
        f=m&(cnt>0); r[f]=acc[f]/cnt[f]
    def f(P):
        d=P-C0; rr=np.linalg.norm(d,axis=1); d=d/rr[:,None]
        t=np.degrees(np.arctan2(d[:,0],d[:,2])); p=np.degrees(np.arccos(np.clip(d[:,1],-1,1)))
        x=(t+180)/res; y=p/res; x0=np.clip(np.floor(x).astype(int),0,r.shape[1]-2); y0=np.clip(np.floor(y).astype(int),0,r.shape[0]-2); fx=x-x0; fy=y-y0
        v=r[y0,x0]*(1-fx)*(1-fy)+r[y0,x0+1]*fx*(1-fy)+r[y0+1,x0]*(1-fx)*fy+r[y0+1,x0+1]*fx*fy
        return v,rr,d
    return f
def transfer(P, old_f, new_f, ylo=0.80, yhi=0.92):
    """move points so they keep the same height above the head surface, old head -> new head"""
    ro,rr,d=old_f(P); rn,_,_=new_f(P)
    w=np.clip((P[:,1]-ylo)/(yhi-ylo),0,1)
    return C0+d*(rr+(rn-ro)*w)[:,None]
