"""Chris's hair (top and back only: her bangs removed) on the blank model, recoloured teal"""
import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/pm']
import hairstudy as S, hairtex2 as HT, restyle, gd2
from PIL import Image, ImageDraw
def build(zc=0.05, sxz=0.92, dy=0.03):
    M,T,tris,hb=S.hair2('kuri'); V=M['V'].copy(); UV=M['UV']; comp=np.load('/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/kuri_comp.npy')
    main=[t for t,c in zip(tris,comp) if c==1104 and M['V'][list(t[0])][:,2].mean()<zc and not (M['V'][list(t[0])][:,1].min()>1.25 and M['V'][list(t[0])][:,2].max()>0.0)]
    V[:,0]*=sxz; V[:,2]=0.01+(V[:,2]-0.01)*sxz; V[:,1]+=dy
    tex=T[255].copy(); H,W=tex.shape[:2]
    m=Image.new('L',(W,H),0); d=ImageDraw.Draw(m)
    for pi,ti in main: d.polygon([((UV[t][0]%1)*W,(UV[t][1]%1)*H) for t in ti],fill=255,outline=255)
    mask=np.array(m)>0
    from scipy.ndimage import binary_dilation; mask=binary_dilation(mask,iterations=2)
    L=restyle.lum(tex[...,:3]); lo,hi=np.percentile(L[mask],1),np.percentile(L[mask],99.5)
    tex[mask,:3]=HT.ramp()[(np.clip((L[mask]-lo)/(hi-lo),0,1)*255).astype(int)]
    P=[];Q=[];F=[]
    for pi,ti in main:
        F.append([len(P),len(P)+1,len(P)+2])
        for p,t in zip(pi,ti): P.append(V[p]); Q.append((UV[t][0]%1,UV[t][1]%1))
    P=np.array(P); F=np.array(F)[:,::-1]
    P=gd2.conform(P,F,margin=0.008,ears=False)
    return P,np.array(Q),F,tex
