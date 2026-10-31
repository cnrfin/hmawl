"""Option 3: keep the original goddess model (body, neck, shoulders untouched); reshape only its head
vertices radially onto Muffy's head shape, then lay Muffy's face meshes on top."""
import sys; sys.path[:0]=['.','blank']
import numpy as np, pickle, muffyhead as MH
b=np.load('blank/blank_v3.npz'); V=b['V'].copy(); BF=b['F']
mh=pickle.load(open('muffyhead_v1.pkl','rb')); face=mh['face']; sP,sF=mh['skullP'],mh['skullF']
def reshape(ylo=0.835, yhi=0.865, inset=0.006, neck=(0.0,0.10,0.065), dy=0.0):
    oldtri=V[BF[(V[BF][:,:,1].min(1)>0.82)]]
    sh=np.array([0,-dy,0]); newtri=np.vstack([sP[sF]+sh]+[face[t][0][face[t][2]]+sh for t in face])
    old_f=MH.head_radius_fn(oldtri); new_f=MH.head_radius_fn(newtri)
    m=V[:,1]>0.835; P=V[m]
    ro,rr,d=old_f(P); rn,_,_=new_f(P)
    w=np.clip((P[:,1]-ylo)/(yhi-ylo),0,1); w=w*w*(3-2*w)
    zc,hw,zr=neck; e=np.sqrt((P[:,0]/hw)**2+((P[:,2]-zc)/zr)**2)
    w=np.maximum(w,np.clip((e-1.0)/0.3,0,1))       # jaw underside (outside the neck tube) follows the new head fully
    tgt=rr*(rn-inset)/ro
    R=rr+(tgt-rr)*w
    V2=V.copy(); V2[m]=MH.C0+d*R[:,None]
    return V2, old_f, new_f
if __name__=='__main__':
    dy=float(sys.argv[1]) if len(sys.argv)>1 else 0.0
    V2,_,_=reshape(dy=dy); np.save(f'goddess_reshaped_V_dy{int(round(dy*1000))}.npy',V2)
