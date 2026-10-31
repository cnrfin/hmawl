"""ponytail bow made from the outfit's own pieces: red sash ribbon (loops + tails) and a cluster of the
cream flowers, opaque solid geometry (AWL: no cut-outs)"""
import numpy as np
def strip(C, Wd, Nd, w, th, u0, u1, v0, v1, point=False):
    """closed ribbon along centreline C with width dir Wd and normal Nd (per point); uv: across u0..u1, along v0..v1"""
    n=len(C); P=[];U=[]
    for i in range(n):
        ww=w*(0.0 if (point and i==n-1) else 1.0)
        t=i/(n-1)
        for a,b in ((-1,-1),(1,-1),(1,1),(-1,1)):
            P.append(C[i]+Wd[i]*a*ww/2+Nd[i]*b*th/2); U.append((u0+(u1-u0)*(a+1)/2, v0+(v1-v0)*t))
    F=[]
    for i in range(n-1):
        for k in range(4):
            a=i*4+k; b=i*4+(k+1)%4; c=a+4; d=b+4; F+=[(a,b,d),(a,d,c)]
    F+=[(0,2,1),(0,3,2),((n-1)*4,(n-1)*4+1,(n-1)*4+2),((n-1)*4,(n-1)*4+2,(n-1)*4+3)]
    P=np.array(P); F=np.array(F); c=P.mean(0)
    nrm=np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]])
    # orient each face away from the local centreline point
    cl=np.repeat(np.arange(n),4)[F].mean(1).round().astype(int).clip(0,n-1)
    flip=(nrm*(P[F].mean(1)-C[cl])).sum(1)<0; F[flip]=F[flip][:,::-1]
    return P,np.array(U),F
def flower(c, n, r=0.034, lobes=5, segs=20, cup=0.008, uc=(132/256,57.5/256), ur=8/256, petal=(142/256,57/256)):
    a_=np.cross(n,[0,1,0]); a_/=np.linalg.norm(a_); b_=np.cross(n,a_)
    P=[c+n*0.004]; U=[(131/256,57/256)]
    for j in range(segs):
        ph=2*np.pi*j/segs; rr=r*(0.62+0.38*abs(np.cos(lobes*ph/2)))
        P.append(c+(a_*np.cos(ph)+b_*np.sin(ph))*rr-n*cup); U.append((petal[0]+np.cos(ph)*1.5/256,petal[1]+np.sin(ph)*1.5/256))
    back=len(P); P.append(c-n*0.006); U.append(uc)
    F=[]
    for j in range(segs):
        k=1+j; l=1+(j+1)%segs; F.append((0,k,l)); F.append((back,l,k))
    P=np.array(P); F=np.array(F)
    nr=np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]); want=np.where(np.arange(len(F))%2==0,1,-1)
    flip=(nr@n)*want<0; F[flip]=F[flip][:,::-1]
    return P,np.array(U),F
RED=(4/256,30/256,4/256,140/256)
def build(knot, out=np.array([0,0,-1.0]), scale=1.0):
    k=np.array(knot); o=out/np.linalg.norm(out); up=np.array([0,1.0,0]); side=np.cross(up,o); side/=np.linalg.norm(side)
    s=scale; parts=[]
    for sd in (1,-1):                                       # two loops
        t=np.linspace(0,1,9); ang=2*np.pi*t
        C=np.array([k+side*sd*(0.055*s*(1-np.cos(ang)))+up*(0.028*s*np.sin(ang))+o*0.006 for ang in ang])
        T=np.gradient(C,axis=0); T/=np.linalg.norm(T,axis=1,keepdims=True)
        Wd=np.array([o for _ in C]); Nd=np.cross(T,Wd); Nd/=np.linalg.norm(Nd,axis=1,keepdims=True)
        parts.append(strip(C,Wd,Nd,0.03*s,0.006*s,*RED))
    for sd,sp in ((1,0.22),(-1,-0.18)):                     # two tails, splayed, pointed ends
        t=np.linspace(0,1,6); d=np.array([sp,-1.0,0]); d/=np.linalg.norm(d)
        C=np.array([k+d*0.21*s*x+o*(0.01+0.012*np.sin(np.pi*x)) for x in t])
        Wd=np.array([side for _ in C]); Nd=np.array([o for _ in C])
        parts.append(strip(C,Wd,Nd,0.032*s,0.005*s,*RED,point=True))
    for dx,dy in ((0,0.004),(0.028,-0.012),(-0.028,-0.010)):  # flower cluster over the knot
        parts.append(flower(k+side*dx*s+up*dy*s+o*0.02*s,o,r=0.034*s))
    return parts

def lobe(c, ax, up, o, L, H, D, segs=12, rings=6, uv=RED):
    """flattened ribbon loop (closed ellipsoid lobe), long axis ax"""
    P=[];U=[]
    for i in range(rings+1):
        t=i/rings; z=np.cos(np.pi*t); r=np.sin(np.pi*t)
        for j in range(segs):
            ph=2*np.pi*j/segs
            P.append(c+ax*L*0.5*z+up*H*0.5*r*np.cos(ph)+o*D*0.5*r*np.sin(ph)); U.append((uv[0]+(uv[1]-uv[0])*j/segs,uv[2]+(uv[3]-uv[2])*t))
    F=[]
    for i in range(rings):
        for j in range(segs):
            a=i*segs+j; b=i*segs+(j+1)%segs; cc=a+segs; d=b+segs; F+=[(a,cc,b),(b,cc,d)]
    P=np.array(P); F=np.array(F); n=np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]])
    flip=(n*(P[F].mean(1)-c)).sum(1)<0; F[flip]=F[flip][:,::-1]
    # drop degenerate pole tris
    A=np.linalg.norm(n,axis=1); return P,np.array(U),F[A>1e-12]
def build2(knot, out=np.array([0,0,-1.0]), scale=1.0, fr=0.044):
    k=np.array(knot); o=out/np.linalg.norm(out); up=np.array([0,1.0,0]); side=np.cross(up,o); side/=np.linalg.norm(side); s=scale
    parts=[]
    for sd in (1,-1):
        ax=side*sd*np.cos(np.radians(15))+up*np.sin(np.radians(15)); ax/=np.linalg.norm(ax)
        upl=np.cross(o,ax); upl*=np.sign(upl@up)
        parts.append(lobe(k+ax*0.058*s+o*0.004,ax,upl,o,0.11*s,0.055*s,0.03*s))
    for sd,sp in ((1,0.22),(-1,-0.18)):
        t=np.linspace(0,1,6); d=np.array([sp,-1.0,0]); d/=np.linalg.norm(d)
        C=np.array([k+d*0.22*s*x+o*(0.012+0.012*np.sin(np.pi*x)) for x in t])
        Wd=np.array([side for _ in C]); Nd=np.array([o for _ in C])
        parts.append(strip(C,Wd,Nd,0.034*s,0.005*s,*RED,point=True))
    for dx,dy in ((0,0.006),(0.034,-0.014),(-0.034,-0.012)):
        parts.append(flower(k+side*dx*s+up*dy*s+o*0.026*s,o,r=fr*s))
    return parts

def front_sash(knot, scale=1.0, length=0.30, surf=None):
    """front of the belt: flower cluster + two long sash tails down the skirt (as the original)"""
    k=np.array(knot); o=np.array([0,0,1.0]); up=np.array([0,1.0,0]); side=np.array([1.0,0,0]); s=scale; parts=[]
    for sd,sp in ((1,0.10),(-1,-0.06)):
        t=np.linspace(0,1,7); d=np.array([sp,-1.0,0]); d/=np.linalg.norm(d)
        C=np.array([k+d*length*x+side*sd*0.012 for x in t])
        if surf is not None: C[:,2]=np.maximum(C[:,2],[surf(c[0],c[1])+0.008 for c in C])
        Wd=np.array([side for _ in C]); Nd=np.array([o for _ in C])
        parts.append(strip(C,Wd,Nd,0.034*s,0.005*s,*RED,point=True))
    for dx,dy in ((0,0.006),(0.034,-0.012),(-0.034,-0.010)):
        parts.append(flower(k+side*dx*s+up*dy*s+o*0.026*s,o,r=0.044*s))
    return parts
