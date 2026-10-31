"""opaque cape veil (original goddess's veil, AWL-style): from behind the neck/shoulders, down the back,
flaring, hem in three soft points (sides + centre back). Two layers (outer + inner), no gap."""
import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank']
import blank as BL
def prof(y):
    """(half-width, back depth, front edge z) of the cape at height y"""
    rx=np.interp(y,[0.40,0.55,0.68,0.76,0.81,0.84],[0.26,0.23,0.19,0.15,0.13,0.10])
    rz=np.interp(y,[0.40,0.55,0.68,0.76,0.81,0.84],[0.20,0.17,0.14,0.11,0.09,0.07])
    return rx,rz
def build(rings=10, segs=14, th_max=105.0, ytop=0.835, ybot=0.43, pt=0.09, gap=0.012, th_top=None, top_rx=None):
    P=[];U=[]
    for i in range(rings):
        t=i/(rings-1)
        for j in range(segs+1):
            tm=th_max if th_top is None else th_top+(th_max-th_top)*min(1,t/0.45)
            th=np.radians(-tm+2*tm*j/segs)                     # 0 = centre back
            yb=ybot-pt*(np.cos(th*3*np.pi/(2*np.radians(th_max)))**2 if False else 0)
            # hem with points at the centre back and both sides
            ph=abs(th)/np.radians(tm); hem=ybot-pt*(np.exp(-(ph/0.18)**2)+np.exp(-((1-ph)/0.18)**2))
            y=ytop+(hem-ytop)*t
            rx,rz=prof(y)
            if top_rx is not None:
                w=max(0,1-t/0.35); rx=rx+(top_rx-rx)*w; rz=rz+(0.10-rz)*w*(abs(np.cos(th))<0.5)
            P.append((rx*np.sin(th),y,-0.01-rz*np.cos(th)))
            U.append((j/segs,t))
    P=np.array(P); U=np.array(U)
    for _ in range(10):                                      # keep it off the body/arms
        g=np.zeros_like(P); e=1e-3
        for k in range(3):
            dd=np.zeros(3); dd[k]=e; g[:,k]=(BL.sdf(P+dd)-BL.sdf(P-dd))/(2*e)
        g/=np.linalg.norm(g,axis=1,keepdims=True)+1e-9; P=P+g*np.maximum(gap-BL.sdf(P),0)[:,None]
    F=[]
    for i in range(rings-1):
        for j in range(segs):
            a=i*(segs+1)+j; b=a+1; c=a+segs+1; d=c+1; F+=[(a,b,c),(b,d,c)]
    F=np.array(F)
    n=np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]); out=P[F].mean(1)*[1,0,1]-[0,0,-0.01]
    if (n*out).sum()<0: F=F[:,::-1]
    # inner layer: slightly inside, reversed
    N=np.zeros_like(P)
    for k in range(3): np.add.at(N,F[:,k],np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]))
    N/=np.linalg.norm(N,axis=1,keepdims=True)
    Pi=P-N*0.006
    return np.vstack([P,Pi]),np.vstack([U,U]),np.vstack([F,F[:,::-1]+len(P)])
