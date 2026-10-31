"""Basic sandals: straps painted onto the feet (side-projected UVs into a small sandal texture) + a thin sole."""
import numpy as np
from scipy.spatial import ConvexHull
Z0,Z1,Y0,Y1=-0.06,0.16,0.0,0.09
LEATHER=np.array([178,120,66.]); DARK=np.array([120,78,44.]); SOLE=np.array([110,72,42.])
def texture(skin, n=64):
    T=np.zeros((n,n,4)); T[...,3]=255; T[...,:3]=skin
    zz=Z0+(np.arange(n)+0.5)/n*(Z1-Z0); yy=Y0+(np.arange(n)+0.5)/n*(Y1-Y0)
    Zg,Yg=np.meshgrid(zz,yy)            # rows = y (v), cols = z (u)
    straps=[(Zg>0.100)&(Zg<0.122),                     # toe strap
            (Zg>0.050)&(Zg<0.072),                     # instep strap
            (Yg>0.050)&(Yg<0.062),                     # ankle strap
            (Zg<-0.018)&(Yg<0.062)]                    # heel strap
    m=np.zeros_like(Zg,bool)
    for s in straps: m|=s
    m|=Yg<0.010                                        # sole edge on the foot
    T[m,:3]=LEATHER
    # darker stitched edge: strap pixels next to skin
    e=m&~(np.roll(m,1,0)&np.roll(m,-1,0)&np.roll(m,1,1)&np.roll(m,-1,1)); T[e,:3]=LEATHER*0.8
    T[Yg<0.010,:3]=SOLE
    return T
def foot_uv(P):
    return np.stack([(P[...,2]-Z0)/(Z1-Z0),(P[...,1]-Y0)/(Y1-Y0)],-1).clip(0.001,0.999)
def soles(footP, pad=0.006, top=0.012):
    out=[]
    for sd in (1,-1):
        Q=footP[(np.sign(footP[:,0])==sd)&(footP[:,1]<0.03)][:,[0,2]]
        h=Q[ConvexHull(Q).vertices]; c=h.mean(0); d=h-c; h=c+d*(1+pad/np.linalg.norm(d,axis=1))[:,None]
        n=len(h); P=np.vstack([np.c_[h[:,0],np.full(n,top),h[:,1]],np.c_[h[:,0],np.zeros(n),h[:,1]],[[c[0],top,c[1]],[c[0],0,c[1]]]])
        F=[]
        for i in range(n):
            j=(i+1)%n; F+=[(i,j,n+j),(i,n+j,n+i),(2*n,j,i),(2*n+1,n+i,n+j)]
        F=np.array(F)
        nrm=np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]); cen=P[F].mean(1)-[c[0],top/2,c[1]]
        fl=(nrm*cen).sum(1)<0; F[fl]=F[fl][:,::-1]
        out.append((P,np.full((len(P),2),0.5),F))
    return out
