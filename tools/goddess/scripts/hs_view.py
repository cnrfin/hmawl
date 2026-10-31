import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank']
import view
from PIL import Image
def show(V,F,path,label,col=(120,170,120)):
    b=np.load('/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank/blank_v3.npz')
    a=view.render_smooth([(b['V'],b['F'],view.SKIN),(V,F,col)],angs=(0,0.7,1.57,2.4,3.14),W=200,H=280,zoom=1.15,ycen=0.75,label=label)
    c=view.render_smooth([(b['V'],b['F'],view.SKIN),(V,F,col)],angs=(0.35,1.2,2.8),W=330,H=300,zoom=2.2,ycen=1.0,label='closer')
    o=Image.new('RGB',(max(a.width,c.width),a.height+c.height),'white'); o.paste(a,(0,0)); o.paste(c,(0,a.height)); o.save(path)
