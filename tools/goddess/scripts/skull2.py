"""closed skull under Muffy's face: our full head kept (no holes), every head vertex moved radially so it sits
just inside the face where the face covers it, smoothly blended elsewhere"""
import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank']
C0=np.array([0,1.07,-0.03])
def rays(O,D,tri):
    """distance along each ray (O[i],D[i]) to the nearest triangle hit, inf if none (Moller-Trumbore)"""
    v0,v1,v2=tri[:,0],tri[:,1],tri[:,2]; e1=v1-v0; e2=v2-v0; out=np.full(len(D),np.inf)
    for i,(o,d) in enumerate(zip(O,D)):
        p=np.cross(d,e2); det=(e1*p).sum(1); ok=np.abs(det)>1e-12; inv=np.where(ok,1/np.where(ok,det,1),0)
        t_=o-v0; u=(t_*p).sum(1)*inv; q=np.cross(t_,e1); v=(d*q).sum(1)*inv; t=(e2*q).sum(1)*inv
        hit=ok&(u>=0)&(v>=0)&(u+v<=1)&(t>0)
        if hit.any(): out[i]=t[hit].min()
    return out
def build(V,F,face_tri,ycut=0.86,inset=0.004,iters=25,sx=1.08,sz=1.02):
    V=V.copy(); head=np.where(V[:,1]>ycut)[0]
    V[head]=C0+(V[head]-C0)*[sx,1.0,sz]
    D=V[head]-C0; r0=np.linalg.norm(D,axis=1); D/=r0[:,None]
    rf=rays(np.repeat(C0[None],len(head),0),D,face_tri)
    hit=np.isfinite(rf); rt=np.where(hit,rf-inset,r0)
    # smooth the radius over the head mesh (hits stay fixed); blend near the neck
    idx={v:i for i,v in enumerate(head)}; nb=[set() for _ in head]
    for f in F:
        for a,b in ((f[0],f[1]),(f[1],f[2]),(f[2],f[0])):
            if a in idx and b in idx: nb[idx[a]].add(idx[b]); nb[idx[b]].add(idx[a])
    r=rt.copy()
    for _ in range(iters):
        m=np.array([r[list(s)].mean() if s else r[i] for i,s in enumerate(nb)])
        r=np.where(hit,rt,0.5*r+0.5*m)
        r=np.where(hit,rt,np.minimum(r,np.where(np.isfinite(rf),rf,9)))
    w=np.clip((V[head,1]-ycut)/0.05,0,1)
    V[head]=C0+D*(r0+(r-r0)*w)[:,None]
    return V,hit.sum()
