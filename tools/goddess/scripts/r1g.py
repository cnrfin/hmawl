import sys,numpy as np
sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess']
import fit2, composite as C, hairswap as h, preview
M,T,ramp,soft,cb,fl=fit2.setup()
g=h.celia_without_hair(M)
col=soft[70][:3]
sc=fit2.scalp(col=col)
outs=[h.render(M,g,T,[sc],angs=(0,1.57,2.4,3.14),W=210,H=250,zoom=2.0,ycen=1.12,label='new scalp cap only')]
for back,side,lab in ((0.85,0.97,'scalp cap + hair, back 85%'),(0.72,0.94,'scalp cap + hair, back 72%')):
    P=fit2.flora_fit(fl,cb,back=back,side=side)
    vs=sorted({v for pi,_ in fl['tris'] for v in pi}); top=P[vs][:,1].max()
    ex=[sc,(P,fl['UV'],fl['tris'],fl['tex'])]
    for sx in (1,-1):
        Pb,UV,tr=C.bun(np.array([sx*0.20,top-0.17,-0.20*back]),np.array([0.105,0.11,0.11]),fl['tex']); ex.append((Pb,UV,tr,fl['tex']))
    outs.append(h.render(M,g,T,ex,angs=(0,0.7,1.57,2.4,3.14),W=210,H=250,zoom=2.0,ycen=1.12,label=lab))
preview.stack(outs).save('step1g_scalp.png')
