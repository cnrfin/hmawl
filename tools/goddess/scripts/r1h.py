import sys,numpy as np
sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/pm']
import fit2, composite as C, hairswap as h, preview, raster
M,T,ramp,soft,cb,fl=fit2.setup()
g=h.celia_without_hair(M)
outs=[]
for cull in (1,-1):
    raster.CULL=cull
    P=fit2.flora_fit(fl,cb,dy=-0.03)
    outs.append(h.render(M,g,T,[(P,fl['UV'],fl['tris'],fl['tex'])],angs=(0,0.7,1.57,3.14),W=210,H=250,zoom=2.0,ycen=1.12,label=f'cull {cull}'))
preview.stack(outs).save('dbg_cull.png')
