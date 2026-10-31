"""render built game files with their own vertex normals (Gouraud), like the game's per-vertex lighting"""
import sys,struct; sys.path[:0]=['.','blank','../pm']
import numpy as np, awlmodel, wally, view, raster
from PIL import Image, ImageDraw
def load(pre):
    M=awlmodel.load(pre); V=M['V']; UV=M['UV']
    g=open(pre+'.gpl','rb').read()[0x1C:]
    pos=struct.unpack_from('>I',g,0)[0]; off,cnt,fmt,comp=struct.unpack_from('>IHBB',g,pos); frac=fmt&0xF
    raw=np.frombuffer(g[off:off+cnt*12],'>i2').reshape(-1,6).astype(float); N=raw[:,3:]/(1<<frac)
    T=wally.textures(pre+'_b0.tpl',pre+'_f0_e.tpl',pre+'_f0_m.tpl')
    parts=[]
    for tid,ts,_ in M['groups']:
        P=np.array([V[list(pi)] for pi,_ in ts]).reshape(-1,3); Nn=np.array([N[list(pi)] for pi,_ in ts]).reshape(-1,3)
        Q=np.array([UV[list(ti)] for _,ti in ts]).reshape(-1,2)
        parts.append((P,Q,np.arange(len(P)).reshape(-1,3),T[tid],Nn))
    return parts
def draw(parts,views,zm,yc,W=230,H=300,lab=''):
    ims=[]
    for ang,tilt in views:
        img=np.zeros((H,W,3))+[200,215,225]; zb=np.full((H,W),-1e9); sc=H/1.6*zm; oy=H/2+yc*sc; R=raster.rotX(tilt)@raster.rotY(ang)
        for P,Q,F,t,Nn in parts: view.smooth_tex(img,zb,P,F,Q,t,R,sc,W/2,oy,normals=Nn,weld_key=False)
        ims.append(Image.fromarray(img.clip(0,255).astype(np.uint8)))
    o=Image.new('RGB',(W*len(ims),H+18),'white')
    for i,im in enumerate(ims): o.paste(im,(W*i,18))
    ImageDraw.Draw(o).text((4,3),lab,fill=(0,0,0)); return o
