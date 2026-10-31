"""transfer the original goddess model's UV layout onto our garments: (angle round the body, normalised height)"""
import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/model']
import gd2
from PIL import Image
SHEET=gd2.filled(np.array(Image.open('/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/images/124.png').convert('RGBA'),float))   # opaque (AWL clothes have no cut-outs)
SHEET_CUT=np.array(Image.open('/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/images/124.png').convert('RGBA'),float)
_G=None
def src():
    global _G
    if _G is None:
        Ms,J=gd2.goddess(); m=[x for x in Ms if x['mat']=='body_315'][0]
        P=m['P']; UV=np.c_[m['UV'][:,0],1-m['UV'][:,1]]; T=m['T']; u=(UV[T].mean(1))*256
        band=(u[:,0]>34)&(u[:,0]<122)
        R=dict(chest=band&(u[:,1]<76),belt=band&(u[:,1]>=76)&(u[:,1]<90),skirt=band&(u[:,1]>=90)&(u[:,1]<145),gown=(u[:,1]>=145))
        _G=(P,UV,T,R)
    return _G
def params(P,ylo,yhi,cz=0.0):
    a=np.degrees(np.arctan2(P[:,0],P[:,2]-cz)); h=(yhi-P[:,1])/(yhi-ylo)
    return np.c_[a,h*180.0]
def transfer(TP, TF, region, ylo=None, yhi=None, res=2.0, src_cz=1.5, wrap_fix=True):
    """per-corner UVs for target triangles (TP,TF) from the original's 'region' triangles"""
    P,UV,T,R=src(); ST=T[R[region]]; sv=np.unique(ST)
    sy0,sy1=P[sv,1].min(),P[sv,1].max()
    qs=params(P,sy0,sy1,src_cz)
    if ylo is None: ylo,yhi=TP[np.unique(TF),1].min(),TP[np.unique(TF),1].max()
    qt=params(TP,ylo,yhi,0.0)
    nx,ny=int(360/res),int(190/res); grid=-np.ones((ny,nx),int)
    for k,t in enumerate(ST):
        q=qs[t].copy()
        if q[:,0].max()-q[:,0].min()>180: q[q[:,0]<0,0]+=360
        A=np.c_[q,np.ones(3)].T
        if abs(np.linalg.det(A))<1e-9: continue
        Ai=np.linalg.inv(A)
        x0,x1=int(np.floor((q[:,0].min()+180)/res)),int(np.ceil((q[:,0].max()+180)/res))
        y0,y1=int(np.floor(q[:,1].min()/res)),int(np.ceil(q[:,1].max()/res))
        for yy in range(max(y0,0),min(y1+1,ny)):
            for xx in range(x0,x1+1):
                b=Ai@np.array([xx*res-180+res/2,yy*res+res/2,1])
                if (b>=-0.02).all(): grid[yy,xx%nx]=k
    for _ in range(300):
        e=grid<0
        if not e.any(): break
        for dy,dx in ((0,1),(0,-1),(1,0),(-1,0)):
            sh=np.roll(np.roll(grid,dy,0),dx,1); m=e&(sh>=0); grid[m]=sh[m]; e=grid<0
    out=np.zeros((len(TF),3,2))
    for i,f in enumerate(TF):
        qf=qt[f].copy()
        if qf[:,0].max()-qf[:,0].min()>180: qf[qf[:,0]<0,0]+=360          # target triangle across the back seam
        c=qf.mean(0); xx=int(((c[0]+180)/res)%nx); yy=int(np.clip(c[1]/res,0,ny-1))
        k=grid[yy,xx]; q=qs[ST[k]].copy()
        if q[:,0].max()-q[:,0].min()>180: q[q[:,0]<0,0]+=360
        Ai=np.linalg.inv(np.c_[q,np.ones(3)].T)
        for j,v in enumerate(f):
            p=qf[j].copy()
            while p[0]<q[:,0].min()-180: p[0]+=360
            while p[0]>q[:,0].max()+180: p[0]-=360
            out[i,j]=UV[ST[k]].T@(Ai@np.array([p[0],p[1],1]))
    return out

def add_veil_region():
    P,UV,T,R=src(); u=UV[T].mean(1)*256
    R['veil']=(u[:,0]>=150)&(u[:,1]<145)&~((u[:,0]<200)&(u[:,1]<75))
