import sys,numpy as np,pickle; sys.path[:0]=['.','blank']
import view, raster, gd2_view as gv
from PIL import Image, ImageDraw
b=np.load('blank/blank_v3.npz'); V=b['V']
d=pickle.load(open('outfit_xfer.pkl','rb')); Fb=d['Fb']; Ub=np.load('final/chestU.npy'); C=V[Fb].mean(1); keep=C[:,1]<0.88; Fb2=Fb[keep]; Ub2=Ub[keep]
S=np.load('final/body_sheet_filled.npy')
def solid(c):
    s=np.zeros((2,2,4)); s[...,:3]=c; s[...,3]=255; return s
def rend(lab,parts,yc=1.06,zm=2.6,body=True,views=((0,0),(0.7,0),(1.57,0),(2.4,0),(3.14,0),(0.5,-0.5))):
    ims=[]
    for ang,tilt in views:
        W,H=200,240; img=np.zeros((H,W,3))+[200,215,225]; zb=np.full((H,W),-1e9); sc=H/1.45*zm; oy=H/2+yc*sc; R=raster.rotX(tilt)@raster.rotY(ang)
        if body:
            Qb=V[Fb2].reshape(-1,3); view.smooth_tex(img,zb,Qb,np.arange(len(Qb)).reshape(-1,3),Ub2.reshape(-1,2),S,R,sc,W/2,oy)
        for P_,Q_,F_,t_ in parts: view.smooth_tex(img,zb,P_,np.asarray(F_),Q_,t_,R,sc,W/2,oy)
        ims.append(Image.fromarray(img.clip(0,255).astype(np.uint8)))
    o_=Image.new('RGB',(200*len(ims),258),'white')
    for i,im in enumerate(ims): o_.paste(im,(200*i,18))
    ImageDraw.Draw(o_).text((4,3),lab,fill=(0,0,0)); return o_
