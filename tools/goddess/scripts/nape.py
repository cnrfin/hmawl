import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank']
import headtex as HX, goddesshair as GH, gd2_view as gv, gd2, blank as BL
from PIL import Image
CEN=np.array([0,1.08,-0.01])
def lower_back(P, ytop=1.22, rim_old=1.0, rim_new=0.90):
    P=P.copy(); d=P-CEN; th=np.degrees(np.arctan2(d[:,0],d[:,2])); a=np.abs(th)
    w=np.interp(a,[0,70,110,150,180],[0,0,0.5,1,1])                      # back fully, sides partly, front not
    k=1+((ytop-rim_new)/(ytop-rim_old)-1)*w
    m=P[:,1]<ytop; P[m,1]=ytop-(ytop-P[m,1])*k[m]
    for _ in range(10):                                                    # keep off the neck / head
        g=np.zeros_like(P); e=1e-3
        for j in range(3):
            dd=np.zeros(3); dd[j]=e; g[:,j]=(BL.sdf(P+dd)-BL.sdf(P-dd))/(2*e)
        g/=np.linalg.norm(g,axis=1,keepdims=True)+1e-9
        P+=g*np.maximum(0.012-BL.sdf(P),0)[:,None]
    return P
def rim_of(P):
    d=P-CEN; th=np.degrees(np.arctan2(d[:,0],d[:,2])); bins=np.arange(-180,181,10); rim=[]
    for a in bins:
        m=np.abs(((th-a+180)%360)-180)<8; rim.append(P[m,1].min() if m.any() else np.nan)
    rim=np.array(rim); ok=~np.isnan(rim); return bins,np.interp(bins,bins[ok],rim[ok])
def scalp(tex, bins, rim):
    b=np.load('/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank/blank_v3.npz'); BV,BF=b['V'],b['F']
    str_=tex[144:178,78:122,:3]; W,H=128,64
    st=np.array(Image.fromarray(str_.astype(np.uint8)).resize((W//2,32),Image.BICUBIC)).astype(float); st=np.concatenate([st,st[:,::-1]],1)
    skin=np.array([246,214,182.]); sheet=np.zeros((H,W,4)); sheet[...,3]=255; sheet[:32,:,:3]=st
    for r in range(32,56):
        t=(r-32)/23; t=t*t*(3-2*t); sheet[r,:,:3]=st[31-int((r-32)*0.6)%32]*0.85*(1-t)+skin*t
    sheet[56:,:,:3]=skin
    def uv(Pv):
        d=Pv-CEN; th=np.degrees(np.arctan2(d[:,0],d[:,2])); a=np.abs(th)
        line=np.interp(th,bins,rim)-np.interp(a,[0,80,120,180],[0,0,0.01,0.012])
        dy=Pv[:,1]-line; fade=np.interp(a,[0,60,100,180],[0.012,0.02,0.04,0.055])
        row=np.where(dy>0,16,32+np.clip(-dy/fade,0,1)*23); row=np.where(-dy>fade,60,row)
        return np.c_[((th+180)/360*3)%1*0.999,row/H]
    hf=BF[(BV[BF][:,:,1].min(1)>0.80)]; used=np.unique(hf); idx=-np.ones(len(BV),int); idx[used]=np.arange(len(used))
    HP,_,HF=gd2.loop_subdiv(BV[used],np.zeros((len(used),2)),idx[hf],smooth=0.0)
    HP=HP+((HP-CEN)/np.linalg.norm(HP-CEN,axis=1,keepdims=True))*0.0008
    return HP,uv(HP),HF,sheet
def accessories(tuft_y=1.31, tuft_z=0.175):
    Tf=GH.part('san',(197,)); Bn=GH.part('san',(329,))
    tP=Tf[0]; torg=np.array([tP[:,0].mean(),tP[:,1].max(),tP[:,2].mean()])
    bP=Bn[0]; borg=np.array([bP[:,0].mean(),bP[:,1].min(),bP[:,2].mean()]); out=[]
    for s in (1,-1):
        out.append(GH.placed(Tf,torg,np.array([0.06*s,tuft_y,tuft_z]),1.7,rot_z=12*s,mirror=(s>0)))
        out.append(GH.align(Bn,borg,np.array([0.155,1.20,-0.13])*[s,1,1],1.0,(0.75*s,0.35,-0.55)))
    return out

def hug(P, y0=1.17, y1=1.04, tgt_lo=0.014, iters=12):
    """pull the lower back hair in onto the head/neck: below y1 it lies tgt_lo off the body; blends above"""
    P=P.copy(); d=P-CEN; th=np.degrees(np.arctan2(d[:,0],d[:,2])); a=np.abs(th)
    wa=np.interp(a,[0,70,110,150,180],[0,0,0.6,1,1]); wy=np.clip((y0-P[:,1])/(y0-y1),0,1); wy=wy*wy*(3-2*wy); w=wa*wy
    for _ in range(iters):
        g=np.zeros_like(P); e=1e-3
        for j in range(3):
            dd=np.zeros(3); dd[j]=e; g[:,j]=(BL.sdf(P+dd)-BL.sdf(P-dd))/(2*e)
        g/=np.linalg.norm(g,axis=1,keepdims=True)+1e-9
        s=BL.sdf(P); P-=g*((s-tgt_lo)*w*0.5)[:,None]
    return P

def rim_smooth(P, win=3):
    bins,rim=rim_of(P)
    # follow the bottom edge's average (not every point), so the fade lies smoothly under the locks
    r=np.r_[rim[-win-1:-1],rim,rim[1:win+1]]
    k=np.ones(2*win+1)/(2*win+1); rs=np.convolve(r,k,mode='same')[win+1:-win] if False else np.convolve(r,k,mode='valid')
    return bins,rs
def front_hug(P, band=0.05, tgt=0.004):
    """pull the front hair edge down onto the forehead/temples"""
    P=P.copy(); bins,rim=rim_of(P); d=P-CEN; th=np.degrees(np.arctan2(d[:,0],d[:,2])); a=np.abs(th)
    edge=np.interp(th,bins,rim); wa=np.interp(a,[0,60,100,130],[1,1,0.5,0])
    w=wa*np.clip(1-(P[:,1]-edge)/band,0,1)**2
    for _ in range(10):
        g=np.zeros_like(P); e=1e-3
        for j in range(3):
            dd=np.zeros(3); dd[j]=e; g[:,j]=(BL.sdf(P+dd)-BL.sdf(P-dd))/(2*e)
        g/=np.linalg.norm(g,axis=1,keepdims=True)+1e-9
        P-=g*((BL.sdf(P)-tgt)*w*0.5)[:,None]
    return P
def scalp2(tex, bins, rim, fade_front=0.022, fade_back=0.05, up=0.012, up_front=0.012):
    b=np.load('/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank/blank_v3.npz'); BV,BF=b['V'],b['F']
    str_=tex[144:178,78:122,:3]; W,H=128,64
    st=np.array(Image.fromarray(str_.astype(np.uint8)).resize((W//2,32),Image.BICUBIC)).astype(float); st=np.concatenate([st,st[:,::-1]],1)
    skin=np.array([246,214,182.]); sheet=np.zeros((H,W,4)); sheet[...,3]=255; sheet[:32,:,:3]=st
    for r in range(32,56):
        t=(r-32)/23; t=t*t*(3-2*t); sheet[r,:,:3]=st[31-int((r-32)*0.6)%32]*0.85*(1-t)+skin*t
    sheet[56:,:,:3]=skin
    def uv(Pv):
        d=Pv-CEN; th=np.degrees(np.arctan2(d[:,0],d[:,2])); a=np.abs(th)
        line=np.interp(th,bins,rim)+np.interp(a,[0,50,90],[up_front,up_front,up])
        dy=Pv[:,1]-line; fade=np.interp(a,[0,35,60,110,180],[fade_front,fade_front,0.016,0.02,fade_back])+up
        row=np.where(dy>0,16,32+np.clip(-dy/fade,0,1)*23); row=np.where(-dy>fade,60,row)
        return np.c_[((th+180)/360*3)%1*0.999,row/H]
    hf=BF[(BV[BF][:,:,1].min(1)>0.80)]; used=np.unique(hf); idx=-np.ones(len(BV),int); idx[used]=np.arange(len(used))
    HP,_,HF=gd2.loop_subdiv(BV[used],np.zeros((len(used),2)),idx[hf],smooth=0.0)
    HP,_,HF=gd2.loop_subdiv(HP,np.zeros((len(HP),2)),HF,smooth=0.0)
    HP=HP+((HP-CEN)/np.linalg.norm(HP-CEN,axis=1,keepdims=True))*0.0008
    return HP,uv(HP),HF,sheet
