import sys; sys.path[:0]=['.','blank','../pm']
import numpy as np, awlmodel, wally, raster, pose
from PIL import Image, ImageDraw
from awlchar import act, world, skn
from anm import parse
pre='../boy/boy_0/boy_0'
M=awlmodel.load(pre); V=M['V']; T=wally.textures(pre+'_b0.tpl',pre+'_f0_e.tpl',pre+'_f0_m.tpl')
nodes=act(open(pre+'.act','rb').read()); Wb=world(nodes); SKD=open(pre+'.skn','rb').read(); sk=skn(SKD)
def draw(tr,f,ang=0.9,W_=180,H_=220):
    Wp=world(nodes,pose.locals_at(nodes,tr,f)); Vp=pose.skin_weighted(V,sk,SKD,Wb,Wp)
    img=np.zeros((H_,W_,3))+[200,215,225]; zb=np.full((H_,W_),-1e9)
    wally.draw(img,zb,Vp,M['UV'],M['groups'],T,raster.rotX(-0.15)@raster.rotY(ang),90,W_/2,H_-20)
    return Image.fromarray(img.clip(0,255).astype(np.uint8))
if __name__=='__main__':
    ids=[int(x) for x in sys.argv[1].split(',')]
    cols=6; out=Image.new('RGB',(180*cols,220*len(ids)))
    for r,i in enumerate(ids):
        tr=parse(open('../boy/anm/anm%03d.bin'%i,'rb').read()); L=tr[0]['length']
        for c in range(cols):
            im=draw(tr,L*c/cols); ImageDraw.Draw(im).text((4,4),'%d L%d'%(i,L),fill=(0,0,0)); out.paste(im,(180*c,220*r))
    out.save(sys.argv[2])
