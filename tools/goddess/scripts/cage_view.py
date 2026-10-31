import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank']
import view
from PIL import Image
def show(V,F,path,label,col=(120,170,120),wire=True):
    b=np.load('/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank/blank_v3.npz')
    A=(0,0.7,1.57,2.4,3.14)
    ims=[view.render_smooth([(b['V'],b['F'],view.SKIN),(V,F,col)],angs=A,W=200,H=280,zoom=1.15,ycen=0.75,label=label),
         view.render_smooth([(b['V'],b['F'],view.SKIN),(V,F,col)],angs=(0,0.5,1.2,2.6,3.14),W=200,H=240,zoom=2.4,ycen=1.12,label='closer')]
    if wire: ims.append(view.render([view.mesh_extra(V,F[:,::-1],col)],angs=(0,0.7,1.57,3.14),W=250,H=300,zoom=1.6,ycen=0.9,cull=1,wire=True,label='wireframe'))
    o=Image.new('RGB',(max(i.width for i in ims),sum(i.height for i in ims)),'white'); y=0
    for i in ims: o.paste(i,(0,y)); y+=i.height
    o.save(path)
