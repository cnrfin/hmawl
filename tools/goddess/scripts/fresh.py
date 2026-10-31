"""fresh build: Flora's full main hair shell (one connected piece), split back with ribbons, teal"""
import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/pm']
import hairstudy as S, florahair as FH, gd2
def shell(drop_tendrils=False, ycut=1.13):
    M,T,tris,hb=S.hair2('flora'); V=M['V'].copy(); UV=M['UV']; comp=np.load('/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/flora_comp.npy')
    fv=sorted({i for tid,ts,_ in M['groups'] if tid==2 for pi,_ in ts for i in pi}); Fc=M['V'][fv]
    s=0.43/(Fc[:,0].max()-Fc[:,0].min()); V=(V-[0,Fc[:,1].min(),Fc[:,2].max()])*s+[0,0.871,0.201]
    keep=[]
    for t,c in zip(tris,comp):
        if c!=933: continue
        q=V[list(t[0])]; cc=q.mean(0)
        if drop_tendrils and cc[2]>-0.06 and cc[1]<ycut: continue
        keep.append(t)
    P=[];Q=[];F=[]
    for pi,ti in keep:
        F.append([len(P),len(P)+1,len(P)+2])
        for p,x in zip(pi,ti): P.append(V[p]); Q.append((UV[x][0]%1,UV[x][1]%1))
    return np.array(P),np.array(Q),np.array(F)[:,::-1]
def build(drop_tendrils=False):
    P,Q,F=shell(drop_tendrils)
    P1,Q1,F1=gd2.loop_subdiv(P,Q,F[:,::-1],smooth=0.0); F1=F1[:,::-1]
    P2,F2=FH.split_back3(P1,F1,ucup=0.07,outer=0.25,gather=0.6,bulge=0.055)
    back=P1[:,2]<-0.02
    P2=gd2.taubin(P2,F2,(P2[F2].mean(1)[:,2]<-0.02),iters=8)
    P2=gd2.conform(P2,F2,margin=0.008,ears=False)
    _,_,_,tex,_=FH.build(ponytail=True)
    return P2,Q1,F2,tex

def build2(gapw=0.05, cx=0.14, ycen=0.92, lift=0.10):
    P,Q,F=shell(True)
    c=P[F].mean(1)
    # reopen the V: drop the nape hair in the centre below the split
    F=F[~((np.abs(c[:,0])<0.06)&(c[:,1]<ycen)&(c[:,2]<0.0))]
    c=P[F].mean(1); back=P[F][:,:,2].min(1)<0.02            # back + buffer: subdivided (undeformed buffer -> no cracks)
    P1,Q1,Fa=gd2.loop_subdiv(P,Q,F[back][:,::-1],smooth=0.0); Fa=Fa[:,::-1]
    F1=np.vstack([Fa,F[~back]])
    P2,F2=FH.split_back3(P1,F1,ucup=0.07,outer=0.25,gather=0.6,bulge=0.055,gapw=gapw,cx=cx,lift=lift)
    P2=gd2.taubin(P2,F2,(P2[F2].mean(1)[:,2]<-0.02),iters=8)
    P2=gd2.conform(P2,F2,margin=0.008,ears=False)
    _,_,_,tex,_=FH.build(ponytail=True)
    return P2,Q1,F2,tex

def side_pony_shell(side=1, skew=0.10, gather=0.35, y0=1.05, ybot=0.80):
    """Flora's shell (Celia tendrils version) with the back swept towards one side"""
    P,Q,F=shell(True)
    P=P.copy(); y=P[:,1]; w=np.clip((y0-y)/(y0-ybot),0,1); w=w*w*(3-2*w)
    back=P[:,2]<-0.02
    tgt=side*0.16
    P[:,0]=np.where(back,P[:,0]+side*skew*w+(tgt-P[:,0])*gather*w**1.5,P[:,0])
    P=gd2.taubin(P,F,P[F].mean(1)[:,2]<-0.02,iters=6)
    return gd2.conform(P,F,margin=0.008,ears=False),Q,F
def side_pony(side=1, knot=(0.16,0.86,-0.06), turn=150.0, scale=0.9):
    """Flora's bow + full spiral ponytail, knot gathered at the side of the neck, tail brought forward over the shoulder"""
    import blank as BL
    B,Tl,kc,tt=FH.bow_and_tail(tail_from=9.0)
    out=[]
    a=np.radians(turn)*side
    R=np.array([[np.cos(a),0,np.sin(a)],[0,1,0],[-np.sin(a),0,np.cos(a)]])
    for (P,Q,F) in (B,Tl):
        X=((P-kc)*scale)@R.T+np.array(knot)*[side,1,1]
        for _ in range(10):
            g=np.zeros_like(X); e=1e-3
            for k in range(3):
                dd=np.zeros(3); dd[k]=e; g[:,k]=(BL.sdf(X+dd)-BL.sdf(X-dd))/(2*e)
            g/=np.linalg.norm(g,axis=1,keepdims=True)+1e-9
            X+=g*np.maximum(0.015-BL.sdf(X),0)[:,None]
        out.append((X,Q,F))
    return out

def side_pony2(side=1, knot=(0.15,0.93,-0.05), tail_turn=180.0, bow_turn=90.0, tail_scale=0.9, bow_scale=0.55, tilt=15.0):
    import blank as BL
    B,Tl,kc,tt=FH.bow_and_tail(tail_from=9.0)
    def rot(turn,tilt_):
        a=np.radians(turn)*side; Ry=np.array([[np.cos(a),0,np.sin(a)],[0,1,0],[-np.sin(a),0,np.cos(a)]])
        b=np.radians(tilt_)*side; Rz=np.array([[np.cos(b),-np.sin(b),0],[np.sin(b),np.cos(b),0],[0,0,1]])
        return Rz@Ry
    K=np.array(knot)*[side,1,1]; out=[]
    for (P,Q,F),turn,sc,org,tl in ((Tl,tail_turn,tail_scale,tt,tilt),(B,bow_turn,bow_scale,kc,0.0)):
        X=((P-org)*sc)@rot(turn,tl).T+K
        if side<0: pass
        for _ in range(12):
            g=np.zeros_like(X); e=1e-3
            for k in range(3):
                dd=np.zeros(3); dd[k]=e; g[:,k]=(BL.sdf(X+dd)-BL.sdf(X-dd))/(2*e)
            g/=np.linalg.norm(g,axis=1,keepdims=True)+1e-9
            X+=g*np.maximum(0.015-BL.sdf(X),0)[:,None]
        out.append((X,Q,F))
    return out
