"""AWL hair texture recoloured greenish-blue, laid out for the cage hair's column UVs"""
import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/pm']
import awlmodel, wally, restyle
from PIL import Image
G='/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/girls/'
SWATCH={'Celia':('sepi',(39,113,82,186)),'Nami':('nami',(2,1,44,76)),'Flora':('flora',(9,88,62,157)),'Lumina':('rumi',(68,205,88,255))}
TEAL=np.array([(18,52,60),(34,88,92),(58,128,128),(98,168,160),(160,210,198),(214,240,228)],float)
def ramp(keys=TEAL):
    t=np.linspace(0,1,256); xs=np.linspace(0,1,len(keys)); return np.stack([np.interp(t,xs,keys[:,c]) for c in range(3)],1)
def swatch(name):
    n,(x0,y0,x1,y1)=SWATCH[name]; p=G+f'{n}_0/{n}_0'
    t=wally.tpl(p+'_b0.tpl',0)[y0:y1,x0:x1].astype(float)
    if name=='Flora': t=np.rot90(t,1)
    L=restyle.lum(t[...,:3]); lo,hi=np.percentile(L,1),np.percentile(L,99.5)
    r=ramp(); out=t.copy(); out[...,:3]=r[(np.clip((L-lo)/(hi-lo),0,1)*255).astype(int)]; out[...,3]=255
    return out
def tiled(name,W=128,H=128,n=4):
    s=swatch(name); w=W//n
    im=np.array(Image.fromarray(s.astype(np.uint8)).resize((w,H),Image.BICUBIC)).astype(float)
    row=np.concatenate([im if k%2==0 else im[:,::-1] for k in range(n)],1)
    return row
