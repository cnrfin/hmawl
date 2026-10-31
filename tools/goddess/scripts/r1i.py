import sys,numpy as np
sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/pm']
import fit2, composite as C, hairswap as h, preview, raster
raster.CULL=-1
M,T,ramp,soft,cb,fl=fit2.setup()
g=h.celia_without_hair(M)
sc=fit2.scalp(col=soft[70][:3]); sc=(sc[0],sc[1],[((a,c,b),(a,c,b)) for (a,b,c),_ in sc[2]],sc[3]) if len(sys.argv)>1 else sc
outs=[h.render(M,g,T,[sc],angs=(0,0.7,1.57,3.14),W=230,H=230,zoom=3.4,ycen=1.1,label='scalp cap only')]
for back in (1.0,0.85):
    P=fit2.flora_fit(fl,cb,dy=-0.03,back=back)
    vs=sorted({v for pi,_ in fl['tris'] for v in pi}); top=P[vs][:,1].max()
    ex=[sc,(P,fl['UV'],fl['tris'],fl['tex'])]
    for sx in (1,-1):
        Pb,UV,tr=C.bun(np.array([sx*0.20,top-0.17,-0.20*back]),np.array([0.105,0.11,0.11]),fl['tex']); ex.append((Pb,UV,tr,fl['tex']))
    outs.append(h.render(M,g,T,ex,angs=(0,0.7,1.57,2.4,3.14),W=230,H=230,zoom=3.4,ycen=1.1,label=f'middle height, scalp cap, back {int(back*100)}%'))
preview.stack(outs).save('step1h_close.png')
