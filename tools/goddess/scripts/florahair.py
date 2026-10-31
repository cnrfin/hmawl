"""back of Flora's hair (no bow), fitted to the blank head, teal"""
import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/pm']
import hairstudy as S, hairtex2 as HT, restyle, gd2
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation
def build(zc=-0.05, ponytail=False, dark=0.72):
    M,T,tris,hb=S.hair2('flora'); V=M['V'].copy(); UV=M['UV']; comp=np.load('/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/flora_comp.npy')
    tex=T[255].copy(); H,W=tex.shape[:2]
    def col(t):
        u=np.mean([UV[x][0]%1 for x in t[1]])*W; v=np.mean([UV[x][1]%1 for x in t[1]])*H
        return tex[min(int(v),H-1),min(int(u),W-1),:3]
    keep=[]
    for t,c in zip(tris,comp):
        if c in (481,508,837): continue                                   # bow sides, glasses-level piece
        r,g,b=col(t)
        if not (g>r*0.62 and g>b+40): continue                           # bow (orange), hair tie (purple)
        if c==395 and not ponytail: continue
        if c==933 and M['V'][list(t[0])][:,2].mean()>=zc: continue
        keep.append(t)
    # fit: Flora face box -> blank head (uniform scale on width, chin and front aligned)
    fv=sorted({i for tid,ts,_ in M['groups'] if tid==2 for pi,_ in ts for i in pi}); Fc=M['V'][fv]
    s=0.43/(Fc[:,0].max()-Fc[:,0].min())
    V=(V-[0,Fc[:,1].min(),Fc[:,2].max()])*s+[0,0.871,0.201]
    m=Image.new('L',(W,H),0); d=ImageDraw.Draw(m)
    for pi,ti in keep: d.polygon([((UV[x][0]%1)*W,(UV[x][1]%1)*H) for x in ti],fill=255)
    mask=binary_dilation(np.array(m)>0,iterations=2)
    L=restyle.lum(tex[...,:3]); lo,hi=np.percentile(L[mask],1),np.percentile(L[mask],99.5)
    tex[mask,:3]=HT.ramp()[(np.clip((L[mask]-lo)/(hi-lo),0,1)*dark*255).astype(int)]
    P=[];Q=[];F=[]
    for pi,ti in keep:
        F.append([len(P),len(P)+1,len(P)+2])
        for p,x in zip(pi,ti): P.append(V[p]); Q.append((UV[x][0]%1,UV[x][1]%1))
    P=np.array(P); F=np.array(F)[:,::-1]
    return gd2.conform(P,F,margin=0.008,ears=False),np.array(Q),F,tex,s

def pony_parts():
    """Flora's bow (both loops + knot) and spiral ponytail, in blank-model coordinates (same fit as the shell),
    and the bow knot centre"""
    M,T,tris,hb=S.hair2('flora'); V=M['V'].copy(); UV=M['UV']; comp=np.load('/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/flora_comp.npy')
    tex=T[255]; H,W=tex.shape[:2]
    fv=sorted({i for tid,ts,_ in M['groups'] if tid==2 for pi,_ in ts for i in pi}); Fc=M['V'][fv]
    s=0.43/(Fc[:,0].max()-Fc[:,0].min()); V=(V-[0,Fc[:,1].min(),Fc[:,2].max()])*s+[0,0.871,0.201]
    sel=[t for t,c in zip(tris,comp) if c in (395,481,508)]
    knot=[]
    for t in sel:
        u=np.mean([UV[x][0]%1 for x in t[1]])*W
        if u>=64: knot+= [V[p] for p in t[0]]
    P=[];Q=[];F=[]
    for pi,ti in sel:
        F.append([len(P),len(P)+1,len(P)+2])
        for p,x in zip(pi,ti): P.append(V[p]); Q.append((UV[x][0]%1,UV[x][1]%1))
    K=np.array(knot); kc=K[np.abs(K[:,0])<0.06].mean(0) if (np.abs(K[:,0])<0.06).any() else K.mean(0)
    return np.array(P),np.array(Q),np.array(F)[:,::-1],kc
def twin(P,F,kc,side,at,scale=0.6,splay=12.0):
    """small copy of the bow + ponytail, knot moved to 'at'; left copy mirrored; tail splayed outward"""
    Q=(P-kc)*scale
    if side<0: Q[:,0]*=-1; F=F[:,::-1]
    a=np.radians(splay)*side
    R=np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]])
    return Q@R.T+at,F

def split_back(P,F,y0=0.99,ybot=0.81,gather=0.6,lift=0.10,drop=0.06,cx=0.115,gapw=0.035):
    """back hair splits below y0 into two rounded lumps (upside-down V between them), each gathered
    towards x=+-cx at the bottom"""
    c=P[F].mean(1); F=F[~((np.abs(c[:,0])<gapw)&(c[:,1]<y0-0.04)&(c[:,2]<-0.05))]      # open the split
    Q=P.copy(); y=P[:,1]; w=np.clip((y0-y)/(y0-ybot),0,1); w=w*w*(3-2*w)
    back=P[:,2]<-0.02
    sx=np.sign(P[:,0]+1e-9)
    Q[:,0]=np.where(back,P[:,0]+(sx*cx-P[:,0])*gather*w**1.5,P[:,0])
    Q[:,1]=np.where(back,y-drop*w+lift*w*np.exp(-(P[:,0]/0.07)**2),y)
    return Q,F
def bow_and_tail(tail_from=0.66):
    """Flora's bow (loops + knot) and the end segment of her spiral ponytail, separately, with the knot centre"""
    M,T,tris,hb=S.hair2('flora'); V=M['V'].copy(); UV=M['UV']; comp=np.load('/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/flora_comp.npy')
    tex=T[255]; H,W=tex.shape[:2]
    fv=sorted({i for tid,ts,_ in M['groups'] if tid==2 for pi,_ in ts for i in pi}); Fc=M['V'][fv]
    s=0.43/(Fc[:,0].max()-Fc[:,0].min()); V=(V-[0,Fc[:,1].min(),Fc[:,2].max()])*s+[0,0.871,0.201]
    bow=[];tail=[]
    for t,c in zip(tris,comp):
        if c not in (395,481,508): continue
        u=np.mean([UV[x][0]%1 for x in t[1]])*W
        if c in (481,508) or u>=64: bow.append(t)
        elif V[list(t[0])][:,1].max()<tail_from: tail.append(t)
    def mesh(sel):
        P=[];Q=[];F=[]
        for pi,ti in sel:
            F.append([len(P),len(P)+1,len(P)+2])
            for p,x in zip(pi,ti): P.append(V[p]); Q.append((UV[x][0]%1,UV[x][1]%1))
        return np.array(P),np.array(Q),np.array(F)[:,::-1]
    B=mesh(bow); Tl=mesh(tail)
    kn=B[0][np.abs(B[0][:,0])<0.05]; kc=kn.mean(0)
    tt=Tl[0][Tl[0][:,1]>Tl[0][:,1].max()-0.03].mean(0)          # top of the tail segment
    return B,Tl,kc,tt
def place(mesh,origin,at,scale,side):
    P,Q,F=mesh; X=(P-origin)*scale
    if side<0: X[:,0]*=-1; F=F[:,::-1]
    return X+at,Q,F

def split_back2(P,F,y0=1.0,ybot=0.81,cx=0.12,zc=-0.13,lift=0.10,drop=0.10,bulge=0.035,gather=0.75,gapw=0.035):
    """two rounder, fuller lumps: each lump swells out round its own axis (x=+-cx, z=zc) in the middle,
    and only closes in to a rounded bottom near the end"""
    c=P[F].mean(1); F=F[~((np.abs(c[:,0])<gapw)&(c[:,1]<y0-0.04)&(c[:,2]<-0.05))]
    Q=P.copy(); y=P[:,1]; w=np.clip((y0-y)/(y0-ybot),0,1)
    back=P[:,2]<-0.02; sx=np.sign(P[:,0]+1e-9)
    ax=np.c_[sx*cx,np.zeros(len(P)),np.full(len(P),zc)]
    rad=P-ax; rad[:,1]=0; rl=np.linalg.norm(rad,axis=1,keepdims=True)+1e-9; rad/=rl
    swell=bulge*np.sin(np.pi*np.clip(w*1.15,0,1))                       # fullest in the middle of the lump
    close=gather*np.clip((w-0.6)/0.4,0,1)**1.5                          # rounds off only at the bottom
    newxz=ax+rad*(rl*(1-close[:,None])+swell[:,None])
    Q[:,0]=np.where(back,newxz[:,0],P[:,0]); Q[:,2]=np.where(back,newxz[:,2],P[:,2])
    Q[:,1]=np.where(back,y-drop*w**1.3+lift*w*np.exp(-(P[:,0]/0.07)**2),y)
    return Q,F

def split_back3(P,F,y0=1.0,ybot=0.81,cx=0.12,zc=-0.13,lift=0.10,drop=0.15,bulge=0.05,gather=0.6,gapw=0.035,ucup=0.06,outer=0.45):
    """as split_back2, plus: U-shaped (cupped) bottom on each lump, and the outer sides kept full"""
    c=P[F].mean(1); F=F[~((np.abs(c[:,0])<gapw)&(c[:,1]<y0-0.04)&(c[:,2]<-0.05))]
    Q=P.copy(); y=P[:,1]; w=np.clip((y0-y)/(y0-ybot),0,1)
    back=P[:,2]<-0.02; sx=np.sign(P[:,0]+1e-9)
    ax=np.c_[sx*cx,np.zeros(len(P)),np.full(len(P),zc)]
    rad=P-ax; rad[:,1]=0; rl=np.linalg.norm(rad,axis=1,keepdims=True)+1e-9; rad/=rl
    swell=bulge*np.sin(np.pi*np.clip(w*1.0,0,1)*0.85)
    close=gather*np.clip((w-0.55)/0.45,0,1)**1.3
    outside=(np.abs(P[:,0])>cx)
    close=np.where(outside,close*outer,close)                        # outer edge keeps its fullness
    newxz=ax+rad*(rl*(1-close[:,None])+swell[:,None])
    Q[:,0]=np.where(back,newxz[:,0],P[:,0]); Q[:,2]=np.where(back,newxz[:,2],P[:,2])
    ny=y-drop*w**1.3+lift*w*np.exp(-(P[:,0]/0.07)**2)
    # U-cup: towards the bottom, points away from the lump's centre line rise -> rounded lower edge
    dxl=np.abs(Q[:,0]-sx*cx)/0.13; wb=np.clip((w-0.5)/0.5,0,1)
    ny+=ucup*np.clip(dxl,0,1.3)**2*wb
    Q[:,1]=np.where(back,ny,y)
    return Q,F
