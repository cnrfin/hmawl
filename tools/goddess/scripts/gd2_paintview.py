import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank']
import hairpaint as hp, gd2, gd2_view as gv
def parts(tex):
    b=np.load('blank/blank_v3.npz')
    d=np.load('gd2_hairB.npz'); f=np.load('gd2_hairF.npz')
    TP,TT,TUV=d['TP'],d['TT'],d['TUV']; cen=TP[TT].mean(1); th=np.degrees(np.arctan2(cen[:,0],-cen[:,2]))
    front=((cen[:,2]>0.03)&(cen[:,1]<1.28))|((np.abs(th)>95)&(cen[:,1]<1.15))
    MP,MT=f['MP'],f['MT']; ptex=gd2.green_hair_tex()
    atlas=np.concatenate([ptex,tex],0); vs=0.5
    st=lambda uv: np.c_[uv[:,0],uv[:,1]*vs]; sb=lambda uv: np.c_[uv[:,0],vs+uv[:,1]*vs*0.999]
    crownT=TT[~front]; frontT=TT[front]
    cr=(TP[crownT].reshape(-1,3), sb(hp.uv(TP[crownT].reshape(-1,3))), np.arange(len(crownT)*3).reshape(-1,3), atlas)
    mu=(MP[MT].reshape(-1,3), sb(hp.uv(MP[MT].reshape(-1,3))), np.arange(len(MT)*3).reshape(-1,3), atlas)
    fr=(TP, st(TUV), frontT, atlas); cap=(d['CP'], sb(hp.uv(d['CP'])), d['CT'], atlas)
    return (b['V'],b['F']), [cap,mu,cr,fr]
