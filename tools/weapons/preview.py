import sys; sys.path[:0]=['/home/user/hmawl-goddess/tools/weapons','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/pm']
import numpy as np, weapon_models as W, tpltool, view, raster, struct
from PIL import Image, ImageDraw
def tex_of(style,w,h):
    img=W.texture(style,w,h); data=W.enc_cmpr(img)
    t=dict(w=w,h=h,fmt=14,data=0); return tpltool.decode(data,t)
def tris(m):
    V=[];UV=[];F=[]
    for f in m.faces:
        for k in range(1,len(f)-1):
            for v in (f[0],f[k],f[k+1]):
                V.append(np.array(m.P[v[0]])/64.0); UV.append(np.array(m.UV[v[2]])/128.0); 
            F.append([len(V)-3,len(V)-2,len(V)-1])
    return np.array(V),np.array(F),np.array(UV)
cols=[]
for wid,nm,f,style,rt,st in W.WEAPONS:
    w,h=(16,32) if wid in (0x4E3,0x4E4) else (32,16)
    T=tex_of(style,w,h).astype(float)
    V,F,UV=tris(f()); ims=[]
    for ang in (0.0,1.2,1.57):
        Wd,Hd=170,300; img=np.zeros((Hd,Wd,3))+[232,234,238]; zb=np.full((Hd,Wd),-1e9)
        R=raster.rotX(-0.25)@raster.rotY(ang); sc=170
        view.smooth_tex(img,zb,V,F,UV,T,R,sc,Wd/2,Hd*0.72,cull=0)
        ims.append(Image.fromarray(img.clip(0,255).astype(np.uint8)))
    col=Image.new('RGB',(170*3,330),'white'); [col.paste(im,(170*i,24)) for i,im in enumerate(ims)]
    ImageDraw.Draw(col).text((6,6),'%s (%X)'%(nm,wid),fill=(0,0,0))
    big=Image.fromarray(np.kron(tex_of(style,w,h)[...,:3],np.ones((4,4,1),np.uint8))); col.paste(big,(510-big.size[0]-4,30))
    cols.append(col)
out=Image.new('RGB',(510*2,330*2),'white')
for i,c in enumerate(cols): out.paste(c,(510*(i%2),330*(i//2)))
out.save(sys.argv[1])
