"""goddess hair v3 (AWL style): opaque texture, mostly-transparent triangles dropped, back curved round and
smoothed, back + tendrils given volume"""
import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank']
import gd2
def build(thr=0.5, t_tend=0.025, ytip=None, ytop=1.14, ybot=0.30):
    f=np.load('/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/gd2_princess_full.npz'); P,UV,T=f['P'],f['UV'],f['T']
    tex=gd2.green_hair_tex(); T=T[gd2.coverage(tex,UV,T)>=thr]; otex=gd2.filled(tex)
    cen=P[T].mean(1); th=np.degrees(np.arctan2(cen[:,0],-cen[:,2]))
    back=(np.abs(th)<100)&(cen[:,1]<1.14); tend=(np.abs(th)>=100)&(cen[:,1]<1.10)
    wid,n=gd2.weld(P); vb=np.zeros(n,bool); vo=np.zeros(n,bool)
    for k,t in enumerate(T): (vb if back[k] else vo)[wid[t]]=True
    only_back=(vb&~vo)[wid]
    P=P.copy()
    if ytip is not None:                       # shorten the back hair (Celia's length): compress heights below ytop
        m=only_back&(P[:,1]<ytop); P[m,1]=ytop-(ytop-P[m,1])*(ytop-ytip)/(ytop-ybot)
    PW=gd2.wrap_back(P,T,back,k=1.3,squeeze=0.10)
    side=only_back&(np.abs(PW[:,0])>0.11)&(PW[:,1]<0.9)&(PW[:,1]>0.6)
    PW[:,2]=np.where(side,np.minimum(PW[:,2],-0.08),PW[:,2])
    PW=gd2.taubin(PW,T,back,iters=10); PW=gd2.taubin(PW,T,tend,iters=6)
    PW=gd2.conform(PW,T,margin=0.010,ears=False)
    NP,NUV,NT=gd2.thicken2(PW,UV,T,back,otex)
    NP,NUV,NT=gd2.thicken2(NP,NUV,NT,np.r_[tend,np.zeros(len(NT)-len(T),bool)],otex,t_top=t_tend,t_tip=t_tend*0.7,y_full=1.0,y_start=1.08)
    wid,n=gd2.weld(NP); par=list(range(n))
    def F(x):
        while par[x]!=x: par[x]=par[par[x]]; x=par[x]
        return x
    for a,b,c in NT: par[F(wid[a])]=F(wid[b]); par[F(wid[b])]=F(wid[c])
    comp=np.array([F(wid[t[0]]) for t in NT]); cnt={c:(comp==c).sum() for c in set(comp)}
    NT=NT[np.array([cnt[c]>=4 for c in comp])]
    return NP,NUV,NT,otex
