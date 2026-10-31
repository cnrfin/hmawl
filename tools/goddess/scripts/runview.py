import sys; sys.path[:0]=['.','blank','../pm','/home/user/hmawl/tools/logs']
import numpy as np, awlmodel, wally, raster
from PIL import Image, ImageDraw
from runcheck import load
import pose
from awlchar import world
def run_sheet(pre, anmarc, out, ai=5, frames=(0,6,12,18,24,30), views=(3.14,1.57), lab=''):
    M,V,nodes,Wb,sk,anims=load(pre,anmarc); T=wally.textures(pre+'_b0.tpl',pre+'_f0_e.tpl',pre+'_f0_m.tpl')
    tr=anims[ai]; rows=[]
    for ang in views:
        ims=[]
        for f in frames:
            Wp=world(nodes,pose.locals_at(nodes,tr,f)); Vp=pose.skin_rigid_from_skn(V,sk,Wb,Wp)
            W_,H_=170,230; img=np.zeros((H_,W_,3))+[200,215,225]; zb=np.full((H_,W_),-1e9); sc=H_/0.9; oy=H_/2+0.33*sc
            wally.draw(img,zb,Vp,M['UV'],M['groups'],T,raster.rotY(ang),sc,W_/2,oy); ims.append(Image.fromarray(img.clip(0,255).astype(np.uint8)))
        o=Image.new('RGB',(170*len(ims),248),'white')
        for i,im in enumerate(ims): o.paste(im,(170*i,18))
        ImageDraw.Draw(o).text((4,3),f'{lab} anim {ai} frames {frames}, view {ang}',fill=(0,0,0)); rows.append(o)
    H=sum(r.height for r in rows); O=Image.new('RGB',(rows[0].width,H),'white'); y=0
    for r in rows: O.paste(r,(0,y)); y+=r.height
    O.save(out)
if __name__=='__main__': run_sheet(sys.argv[1],sys.argv[2],sys.argv[3])
