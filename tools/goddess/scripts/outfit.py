"""goddess outfit on the blank body, textured from her original body_315 texture:
bandeau top, red belt, lavender wrap skirt, long white gown, gold armbands, gold pendant"""
import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank']
import blank as BL
from PIL import Image
TEX=np.array(Image.open('/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/model/Harvest Goddess copy/body_315_00.png').convert('RGBA'),float)
def px(x,y): return (x/256.0,y/256.0)
def vnormals(V,F):
    N=np.zeros_like(V)
    for k in range(3): np.add.at(N,F[:,k],np.cross(V[F[:,1]]-V[F[:,0]],V[F[:,2]]-V[F[:,0]]))
    return N/np.maximum(np.linalg.norm(N,axis=1,keepdims=True),1e-9)
def shell(V,F,sel,off,uvf):
    """offset copy of the selected body faces; per-corner uvs from uvf(points)"""
    N=vnormals(V,F); Fs=F[sel]; used=np.unique(Fs); idx=-np.ones(len(V),int); idx[used]=np.arange(len(used))
    P=V[used]+N[used]*off
    T=idx[Fs]; C=P[T].reshape(-1,3); U=uvf(C)
    # duplicate corners so per-face seams (mirror) are clean
    return C,U,np.arange(len(C)).reshape(-1,3)
def ang(P,cz=0.0): return np.degrees(np.arctan2(P[:,0],P[:,2]-cz))      # 0 front, +-180 back
def mirror_u(a,x0,x1): return x0+(x1-x0)*np.abs(a)/180.0
def tube(prof, y0, y1, n_r, segs, uvf, cz=0.0, wave=None):
    """closed-side tube (open top/bottom) with elliptical rings; prof(y)->(rx,rz)"""
    P=[];U=[];F=[]
    ys=np.linspace(y0,y1,n_r)
    for i,y in enumerate(ys):
        rx,rz=prof(y)
        for j in range(segs+1):
            a=2*np.pi*j/segs; yy=y
            if wave is not None and i==n_r-1: yy=y+wave(a)
            p=np.array([rx*np.sin(a),yy,cz+rz*np.cos(a)]); P.append(p)
    P=np.array(P); A=np.degrees(np.arctan2(P[:,0],P[:,2]-cz))
    U=uvf(P,A,np.repeat(np.arange(n_r),segs+1)/(n_r-1))
    for i in range(n_r-1):
        for j in range(segs):
            a=i*(segs+1)+j; b=a+1; c=a+segs+1; d=c+1; F+=[(a,c,b),(b,c,d)]
    F=np.array(F); n=np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]])
    out=P[F].mean(1)-np.c_[np.zeros(len(F)),P[F].mean(1)[:,1],np.full(len(F),cz)]
    flip=(n*out).sum(1)<0; F[flip]=F[flip][:,::-1]
    return P,U,F
def build(body):
    V,F=body; C=V[F].mean(1); torso=np.abs(C[:,0])<0.15
    out={}
    # bandeau top
    sel=torso&(C[:,1]>0.683)&(C[:,1]<0.772)
    out['top']=shell(V,F,sel,0.006,lambda P: np.c_[mirror_u(ang(P),40,113)/256,(14+(0.772-P[:,1])/0.089*30)/256])
    # gown: from under the belt to the floor, flaring, wavy hem
    def gprof(y):
        t=np.clip((0.60-y)/0.58,0,1); return 0.128+0.17*t**1.6, 0.098+0.13*t**1.6
    out['gown']=tube(gprof,0.60,0.015,9,20,lambda P,A,t: np.c_[(4+np.abs(A)/180*140)/256,(150+t*70)/256],
                     cz=0.0,wave=lambda a: 0.012*np.sin(5*a))
    # lavender wrap skirt over the gown: belt to mid thigh, a little wider than the gown
    def sprof(y):
        rx,rz=gprof(y); return rx+0.014, rz+0.014
    out['skirt']=tube(sprof,0.60,0.36,4,20,lambda P,A,t: np.c_[mirror_u(A,40,120)/256,(90+t*48)/256])
    # red belt
    def bprof(y): rx,rz=gprof(0.60); return rx+0.02, rz+0.02
    out['belt']=tube(bprof,0.625,0.595,2,20,lambda P,A,t: np.c_[mirror_u(A,40,120)/256,(78+t*10)/256])
    # gold armbands on the forearms, near the wrist
    bands=[]
    for s in (1,-1):
        P=[];U=[];Fb=[];segs=10
        for i,x in enumerate((0.31,0.365)):
            for j in range(segs+1):
                a=2*np.pi*j/segs; r=0.034
                P.append((s*x,0.79+r*np.sin(a),r*np.cos(a))); U.append(((154+40*j/segs)/256,(4+i*64)/256))
        for j in range(segs):
            a=j; b=j+1; c=j+segs+1; d=c+1; Fb+=[(a,c,b),(b,c,d)]
        P=np.array(P); Fb=np.array(Fb); n=np.cross(P[Fb[:,1]]-P[Fb[:,0]],P[Fb[:,2]]-P[Fb[:,0]])
        o=P[Fb].mean(1)-np.c_[P[Fb].mean(1)[:,0],np.full(len(Fb),0.79),np.zeros(len(Fb))]
        flip=(n*o).sum(1)<0; Fb[flip]=Fb[flip][:,::-1]; bands.append((P,np.array(U),Fb))
    out['bands']=bands
    # gold pendant hanging from the belt front (double-sided card, cut-out)
    rx,rz=bprof(0.6); z=rz+0.006
    P=np.array([(-0.03,0.598,z),(0.03,0.598,z),(0.03,0.50,z+0.01),(-0.03,0.50,z+0.01)])
    U=np.array([px(124,80),px(166,80),px(166,128),px(124,128)])
    out['pendant']=(P,U,np.array([(0,2,1),(0,3,2),(0,1,2),(0,2,3)]))
    return out

def desat(T,k=0.82):
    t=T.copy(); L=(t[...,:3]*[0.3,0.59,0.11]).sum(-1,keepdims=True); t[...,:3]=L+(t[...,:3]-L)*k; return t
def ring_tube(rings, segs, uvf, scallop=None):
    """AWL-style skirt shell: list of rings (y, rx, rz, cz); single-sided, open top/bottom; optional scalloped
    last ring (n, dy, dr)"""
    P=[]; n_r=len(rings)
    for i,(y,rx,rz,cz) in enumerate(rings):
        for j in range(segs+1):
            a=2*np.pi*j/segs; yy=y; f=1.0
            if scallop and i==n_r-1:
                n,dy,dr=scallop; w=0.5-0.5*np.cos(n*a); yy=y+dy*w; f=1+dr*(1-w)
            P.append((rx*f*np.sin(a),yy,cz+rz*f*np.cos(a)))
    P=np.array(P); A=np.repeat(np.arange(n_r),segs+1); J=np.tile(np.arange(segs+1),n_r)
    U=uvf(J/segs,A/(n_r-1)); F=[]
    for i in range(n_r-1):
        for j in range(segs):
            a=i*(segs+1)+j; b=a+1; c=a+segs+1; d=c+1; F+=[(a,c,b),(b,c,d)]
    F=np.array(F); cz=np.array([r[3] for r in rings]).mean()
    n=np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]); m=P[F].mean(1); out=m-np.c_[np.zeros(len(F)),m[:,1],np.full(len(F),cz)]
    flip=(n*out).sum(1)<0; F[flip]=F[flip][:,::-1]
    return P,U,F
def mir(s): return 1-np.abs(2*s-1)          # 0 at back seam, 1 at front: mirrored texture round the body
def build2(body):
    V,F=body; C=V[F].mean(1); torso=np.abs(C[:,0])<0.15; out={}
    sel=torso&(C[:,1]>0.683)&(C[:,1]<0.772)
    out['top']=shell(V,F,sel,0.006,lambda P: np.c_[mirror_u(ang(P),40,113)/256,(14+(0.772-P[:,1])/0.089*30)/256])
    # gown: oval, centred a little forward (like Celia's), bell flare to the floor, Muffy-style scalloped hem
    G=[(0.612,0.084,0.066,0.0),(0.55,0.124,0.090,-0.004),(0.48,0.140,0.098,0.0),(0.36,0.160,0.118,0.012),
       (0.22,0.196,0.155,0.025),(0.10,0.235,0.190,0.035),(0.025,0.270,0.222,0.04)]
    out['gown']=ring_tube(G,16,lambda s,t: np.c_[(4+mir(s)*140)/256,(150+t*68)/256],scallop=(8,0.03,0.06))
    # lavender wrap skirt: overlay panel (like an apron layer), hem dips to a point at the front
    S=[(0.605,0.090,0.071,0.0),(0.55,0.132,0.098,-0.004),(0.47,0.150,0.110,0.004),(0.36,0.172,0.132,0.014)]
    P,U,Fs=ring_tube(S,16,lambda s,t: np.c_[(40+mir(s)*80)/256,(90+t*48)/256])
    a=np.arctan2(P[:,0],P[:,2]-0.016); last=np.arange(len(P))>=3*17
    P[last,1]-=0.07*np.clip(np.cos(a[last]),0,1)**2                     # point at the front
    out['skirt']=(P,U,Fs)
    out['belt']=ring_tube([(0.632,0.087,0.068,0.0),(0.598,0.093,0.074,0.0)],16,lambda s,t: np.c_[(40+mir(s)*80)/256,(78+t*10)/256])
    o=build(body); out['bands']=o['bands']
    z=0.074+0.004
    P=np.array([(-0.03,0.60,z),(0.03,0.60,z),(0.03,0.50,z+0.012),(-0.03,0.50,z+0.012)])
    out['pendant']=(P,np.array([px(124,80),px(166,80),px(166,128),px(124,128)]),np.array([(0,2,1),(0,3,2),(0,1,2),(0,2,3)]))
    return out
def hide_legs(body, ycut=0.60):
    """AWL practice: body parts fully hidden under clothes are not modelled. Drop legs/hips under the gown"""
    V,F=body; C=V[F].mean(1); keep=~((C[:,1]<ycut)&(C[:,1]>0.06)); return V,F[keep]

FACE_TEX='/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/model/Harvest Goddess copy/face_315_00.png'
Y0,Y1=0.655,0.845
BOT=0.688
def bandeau_edge(u): return 0.768-0.014*np.exp(-((1-u)/0.09)**2)        # sweetheart dip at the front centre
def chest_texture(W=64,H=96,shadow=0.38,cleav=0.55):
    """Muffy-style single block: bandeau + upper chest skin, painted shading (neckline shadow, cleavage)"""
    T=desat(TEX); face=np.array(Image.open(FACE_TEX).convert('RGB'),float)
    skin=np.array([246,214,182.])            # exactly the body's skin colour (no tone step at the edges)
    out=np.zeros((H,W,4)); out[...,3]=255
    for r in range(H):
        y=Y1-(r+0.5)/H*(Y1-Y0)
        for c in range(W):
            u=(c+0.5)/W; e=bandeau_edge(u)
            if BOT<=y<e:
                t=(e-y)/(e-BOT); x=int(40+u*72); yy=int(14+t*30); col=T[yy,x,:3].copy()
                if e-y<0.004 or y-BOT<0.003: col*=0.75                    # trim lines along both edges
                out[r,c,:3]=col
            elif y<BOT:
                out[r,c,:3]=skin
            else:
                d=y-e; col=skin.copy()
                cv=np.exp(-((1-u)/0.06)**2)*np.clip(1-d/0.07,0,1)**0.7       # cleavage line between the breasts
                col*=1-cleav*cv
                out[r,c,:3]=col
    return out
def chest_piece(body, W=64, H=96):
    V,F=body; C=V[F].mean(1); hv=V[F][:,:,1].max(1); sel=(np.abs(C[:,0])<0.15)&(C[:,1]>Y0)&(hv<Y1+0.02)&(C[:,1]<Y1)
    import gd2
    N=vnormals(V,F); Fs=F[sel]; used=np.unique(Fs); idx=-np.ones(len(V),int); idx[used]=np.arange(len(used))
    Pv,_,Ft=gd2.loop_subdiv(V[used],np.zeros((len(used),2)),idx[Fs],smooth=0.0)      # finer, for the painted shading
    Nv,_,_=gd2.loop_subdiv(N[used],np.zeros((len(used),2)),idx[Fs],smooth=0.0)
    for _ in range(4):                                                              # put the new points on the body surface
        d=BL.sdf(Pv); g=np.zeros_like(Pv); e_=1e-3
        for j in range(3):
            dd=np.zeros(3); dd[j]=e_; g[:,j]=(BL.sdf(Pv+dd)-BL.sdf(Pv-dd))/(2*e_)
        Pv-=g*(d/np.maximum((g*g).sum(1),1e-9))[:,None]
    Nv/=np.linalg.norm(Nv,axis=1,keepdims=True)
    Cc=Pv[Ft].reshape(-1,3); Nc=Nv[Ft].reshape(-1,3)
    a=ang(Cc); u=1-np.abs(a)/180.0; v=(Y1-Cc[:,1])/(Y1-Y0)
    # bandeau stands a little off the skin, skin part stays on the body
    e=bandeau_edge(u); lift=np.where((Cc[:,1]<e)&(Cc[:,1]>=BOT),0.006,0.0006); P=Cc+Nc*lift[:,None]
    return (P,np.c_[u,v],np.arange(len(P)).reshape(-1,3)),sel

SKIN=np.array([246,214,182.])
CLV=(0.10,0.70,0.835)        # half-width, bottom, top of the painted chest area (planar, front)
def body_texture(W=64,H=64,cleav=0.5):
    """the body's own skin texture: plain skin, with the cleavage painted in the chest area (rows/cols = CLV box)"""
    out=np.zeros((H,W,4)); out[...,:3]=SKIN; out[...,3]=255
    hw,y0,y1=CLV
    for r in range(H):
        y=y1-(r+0.5)/H*(y1-y0)
        for c in range(W):
            x=-hw+(c+0.5)/W*2*hw; e=bandeau_edge(1-abs(x)/0.5)
            d=y-e
            if d<0: continue
            cv=np.exp(-(x/0.012)**2)*np.clip(1-d/0.05,0,1)**0.8
            out[r,c,:3]=SKIN*(1-cleav*cv)
    return out
def body_uvs(V,F):
    """per-corner UVs: front chest faces planar-mapped into the painted box, everything else on plain skin"""
    hw,y0,y1=CLV; C=V[F].mean(1)
    sel=(np.abs(C[:,0])<hw*0.9)&(C[:,1]>y0)&(C[:,1]<y1)&(C[:,2]>0.0)
    U=np.full((len(F),3,2),0.02)
    P=V[F[sel]]; U[sel,:,0]=np.clip((P[:,:,0]+hw)/(2*hw),0.01,0.99); U[sel,:,1]=np.clip((y1-P[:,:,1])/(y1-y0),0.01,0.99)
    return U
