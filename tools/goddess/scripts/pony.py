import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/pm']
import florahair as FH, goddesshair as GH, wally, restyle, blank as BL
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation
def flora_pony(kate_tex):
    """Flora's bow (own colours) + full spiral ponytail recoloured with the main hair's colours"""
    B,Tl,kc,tt=FH.bow_and_tail(tail_from=9.0)
    ftex=wally.tpl('/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/girls/flora_0/flora_0_b0.tpl',0).astype(float); H,W=ftex.shape[:2]
    m=Image.new('L',(W,H),0); d=ImageDraw.Draw(m)
    for f in Tl[2]: d.polygon([(Tl[1][i][0]*W,Tl[1][i][1]*H) for i in f],fill=255)
    mask=binary_dilation(np.array(m)>0,iterations=2)&(np.arange(W)[None,:]<64)
    L=restyle.lum(ftex[...,:3]); lo,hi=np.percentile(L[mask],1),np.percentile(L[mask],99.5)
    r=GH.kate_ramp(kate_tex); ftex[mask,:3]=r[(np.clip((L[mask]-lo)/(hi-lo),0,1)*255).astype(int)]
    return (B[0],B[1],B[2],ftex),(Tl[0],Tl[1],Tl[2],ftex),kc
def place(parts, kc, at, scale=1.0, tilt=0.0):
    out=[]; a=np.radians(tilt); R=np.array([[1,0,0],[0,np.cos(a),-np.sin(a)],[0,np.sin(a),np.cos(a)]])
    for P,Q,F,t in parts:
        X=((P-kc)*scale)@R.T+at
        for _ in range(10):
            g=np.zeros_like(X); e=1e-3
            for j in range(3):
                dd=np.zeros(3); dd[j]=e; g[:,j]=(BL.sdf(X+dd)-BL.sdf(X-dd))/(2*e)
            g/=np.linalg.norm(g,axis=1,keepdims=True)+1e-9; X=X+g*np.maximum(0.012-BL.sdf(X),0)[:,None]
        out.append((X,Q,F,t))
    return out
