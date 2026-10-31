"""goddess braid: chain of alternating lobes along a path (behind her right ear, over the shoulder, down the
front to the thigh), twist texture along each lobe, a tie with small yellow flowers and a short tuft at the end"""
import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank']
import blank as BL
PATH=np.array([(-0.17,1.06,-0.10),(-0.20,0.96,-0.06),(-0.205,0.87,0.00),(-0.19,0.78,0.06),(-0.175,0.66,0.085),(-0.165,0.52,0.085),(-0.16,0.40,0.075),(-0.155,0.31,0.065)])
def spline(pts,n):
    from scipy.interpolate import CubicSpline
    d=np.r_[0,np.cumsum(np.linalg.norm(np.diff(pts,axis=0),axis=1))]
    cs=CubicSpline(d,pts); s=np.linspace(0,d[-1],n); return cs(s),cs(s,1)
def ellipsoid(c, ax, side, nrm, L, W, D, segs=6, rings=4, tile=1.0):
    P=[];Q=[]
    for i in range(1,rings):
        t=i/rings; z=np.cos(np.pi*t); r=np.sin(np.pi*t)
        for j in range(segs+1):
            ph=2*np.pi*j/segs
            P.append(c+ax*L*0.5*z+side*W*0.5*r*np.cos(ph)+nrm*D*0.5*r*np.sin(ph)); Q.append((t*tile,j/segs))
    top=len(P); P.append(c+ax*L*0.5); Q.append((0,0.5)); bot=len(P); P.append(c-ax*L*0.5); Q.append((tile,0.5))
    ring=lambda i,j: (i-1)*(segs+1)+j; F=[]
    for j in range(segs): F.append((top,ring(1,j),ring(1,j+1))); F.append((bot,ring(rings-1,j+1),ring(rings-1,j)))
    for i in range(1,rings-1):
        for j in range(segs):
            a,b,c_,d=ring(i,j),ring(i,j+1),ring(i+1,j),ring(i+1,j+1); F+=[(a,c_,b),(b,c_,d)]
    P=np.array(P); F=np.array(F); n=np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]])
    flip=(n*(P[F].mean(1)-c)).sum(1)<0; F[flip]=F[flip][:,::-1]
    return P,np.array(Q),F
def build(n_lobes=17, w0=0.075, w1=0.05, tilt=32.0, ttex=None):
    pts,tan=spline(PATH,n_lobes+1); allP=[];allQ=[];allF=[];off=0
    L=np.linalg.norm(np.diff(pts,axis=0),axis=1).mean()
    for k in range(n_lobes):
        c=(pts[k]+pts[k+1])/2; t=tan[k]/np.linalg.norm(tan[k])
        out=c-np.array([0,c[1],-0.02]); out[1]=0; nrm=out-t*(out@t); nrm/=np.linalg.norm(nrm)  # faces away from the body
        side=np.cross(t,nrm); side/=np.linalg.norm(side)
        a=np.radians(tilt)*(1 if k%2 else -1)
        ax=t*np.cos(a)+side*np.sin(a); sd=np.cross(nrm,ax); sd/=np.linalg.norm(sd)
        f=k/(n_lobes-1); w=w0+(w1-w0)*f
        P,Q,F=ellipsoid(c,-ax,sd,nrm,L*1.9,w*0.8,w*0.62)
        allP.append(P); allQ.append(Q); allF.append(F+off); off+=len(P)
    P=np.vstack(allP); Q=np.vstack(allQ); F=np.vstack(allF)
    # keep it off the body
    for _ in range(10):
        g=np.zeros_like(P); e=1e-3
        for j in range(3):
            dd=np.zeros(3); dd[j]=e; g[:,j]=(BL.sdf(P+dd)-BL.sdf(P-dd))/(2*e)
        g/=np.linalg.norm(g,axis=1,keepdims=True)+1e-9; P=P+g*np.maximum(0.012-BL.sdf(P),0)[:,None]
    return P,Q,F,ttex,pts,tan
def tie_and_flowers(end, tan, nrm, w=0.05):
    t=tan/np.linalg.norm(tan); side=np.cross(t,nrm); side/=np.linalg.norm(side)
    band=ellipsoid(end,t,side,nrm,0.025,w*0.75,w*0.65,segs=8,rings=3)
    fl=[]
    for k,(dx,dy) in enumerate(((0,0),(0.022,0.008),(-0.022,0.006),(0.01,-0.018),(-0.012,-0.016))):
        c=end+side*dx+t*dy+nrm*0.028
        fl.append(ellipsoid(c,nrm,side,t,0.012,0.026,0.026,segs=6,rings=3))
    return band,fl
def flat_tex(rgb):
    t=np.zeros((2,2,4)); t[...,:3]=rgb; t[...,3]=255; return t
