"""Hair fit v2: Flora hair uniform-scaled + chin aligned, back compressed; Celia's own hair kept as a
green scalp wherever it lies inside Flora's hair (fills gaps), dropped where it sticks out."""
import sys,numpy as np
sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/pm']
import composite as C, hairswap as h, wally, restyle, awlmodel
HB=(40,114,81,186)

def setup():
    M=awlmodel.load(h.CEL)
    T=wally.textures(h.CEL+'_b0.tpl',h.CEL+'_f0_e.tpl',h.CEL+'_f0_m.tpl')
    ramp=C.goddess_ramp(); soft=ramp[np.linspace(90,245,256).astype(int)]
    ht=T[2].copy(); dark=(restyle.lum(ht[...,:3])<110)&(ht[...,3]>0); ht[dark]=restyle.recolour(ht[dark],soft,0,110); T[2]=ht
    cb=C.face_box(M,(6,7)); fl=C.flora_hair(cb,ramp)
    return M,T,ramp,soft,cb,fl

def flora_fit(fl,cb,dy=0.0,back=1.0,side=1.0,cz=0.0):
    F=awlmodel.load(C.G+'flora_0/flora_0'); fmin,fmax=C.face_box(F,(42,)); cmin,cmax=cb
    s=(cmax[0]-cmin[0])/(fmax[0]-fmin[0])
    P=(F['V']-[(fmin[0]+fmax[0])/2,fmin[1],(fmin[2]+fmax[2])/2])*s+[(cmin[0]+cmax[0])/2,cmin[1]+dy,(cmin[2]+cmax[2])/2]
    P=P.copy(); b=P[:,2]<cz; P[b,2]=cz+(P[b,2]-cz)*back; P[:,0]*=side
    return P

def radial_env(P,vs,c,nb=24):
    """max radius of the hair per (azimuth, elevation) bin around c"""
    D=P[vs]-c; r=np.linalg.norm(D,axis=1); az=np.arctan2(D[:,0],D[:,2]); el=np.arcsin(np.clip(D[:,1]/r,-1,1))
    ia=((az+np.pi)/(2*np.pi)*nb).astype(int)%nb; ie=np.clip(((el+np.pi/2)/np.pi*nb).astype(int),0,nb-1)
    E=np.zeros((nb,nb)); np.maximum.at(E,(ia,ie),r)
    for _ in range(3):   # fill empty bins from neighbours
        Z=E==0; N=np.maximum.reduce([np.roll(E,1,0),np.roll(E,-1,0),np.roll(E,1,1),np.roll(E,-1,1)]); E[Z]=N[Z]
    def inside(p,margin=0.97):
        d=p-c; rr=np.linalg.norm(d); a=np.arctan2(d[0],d[2]); e=np.arcsin(np.clip(d[1]/rr,-1,1))
        return rr<=E[int((a+np.pi)/(2*np.pi)*nb)%nb, min(int((e+np.pi/2)/np.pi*nb),nb-1)]*margin
    return inside

def celia_with_scalp(M,T,soft,P,fl,c):
    """Celia minus cap; hair-block triangles kept only inside Flora's hair; hair block texture -> darker green"""
    body=T[255]; H,W=body.shape[:2]; B=M['bones']; UV=M['UV']
    head=lambda v: bool(B[v]) and all(b in (6,7,8,9) for b in B[v])
    vs=sorted({v for pi,_ in fl['tris'] for v in pi}); inside=radial_env(P,vs,c)
    groups=[]; kept=dropped=0
    for tid,tris,vst in M['groups']:
        keep=[]
        for pi,ti in tris:
            if tid==255 and all(head(v) for v in pi):
                u=np.mean([UV[t][0]%1 for t in ti])*W; v=np.mean([UV[t][1]%1 for t in ti])*H
                if v<60: continue
                if HB[0]<=u<=HB[2] and HB[1]<=v<=HB[3]:
                    if all(inside(M['V'][x]) for x in pi): kept+=1
                    else: dropped+=1; continue
            keep.append((pi,ti))
        groups.append((tid,keep,vst))
    T=dict(T); b=T[255].copy(); reg=b[HB[1]:HB[3]+1,HB[0]:HB[2]+1]
    dark=soft[np.linspace(0,150,256).astype(int)]      # scalp: the shadow end of the green
    b[HB[1]:HB[3]+1,HB[0]:HB[2]+1]=restyle.recolour(reg.reshape(-1,reg.shape[-1]),dark,0,255).reshape(reg.shape); T[255]=b
    return groups,T,kept,dropped

def scalp(center=(0,1.06,-0.01),radii=(0.226,0.255,0.215),rings=10,segs=18,zcut=0.0,ytop=1.24,ynape=0.86,col=None):
    """skull cap closing the open back/top of Celia's face shell; flat dark green"""
    c=np.array(center); r=np.array(radii); P=[];UV=[];tris=[]
    for i in range(rings+1):
        th=np.pi*i/rings
        for j in range(segs+1):
            ph=2*np.pi*j/segs
            P.append(c+np.array([np.sin(th)*np.cos(ph),np.cos(th),np.sin(th)*np.sin(ph)])*r); UV.append((0.5,0.5))
    P=np.array(P)
    for i in range(rings):
        for j in range(segs):
            a=i*(segs+1)+j; b=a+1; cc=a+segs+1; d=cc+1
            for t in ((a,cc,b),(b,cc,d)):
                m=P[list(t)].mean(0)
                if (m[2]<zcut or m[1]>ytop) and m[1]>ynape: tris.append((t,t))
    tex=np.zeros((4,4,4)); tex[...]=list(col)+[255] if col is not None else [60,110,70,255]
    return P,np.array(UV),tris,tex
