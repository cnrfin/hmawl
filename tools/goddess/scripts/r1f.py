import sys,numpy as np
sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess']
import fit2, composite as C, hairswap as h, preview
M,T,ramp,soft,cb,fl=fit2.setup()
c=np.array([0,1.08,0.02])
outs=[]
for back,side,lab in ((1.0,1.0,'scalp kept, back as is'),(0.8,0.96,'scalp kept, back 80%'),(0.68,0.93,'scalp kept, back 68%')):
    P=fit2.flora_fit(fl,cb,back=back,side=side)
    g,T2,k,d=fit2.celia_with_scalp(M,T,soft,P,fl,c)
    vs=sorted({v for pi,_ in fl['tris'] for v in pi}); top=P[vs][:,1].max()
    ex=[(P,fl['UV'],fl['tris'],fl['tex'])]
    for sx in (1,-1):
        Pb,UV,tr=C.bun(np.array([sx*0.20,top-0.17,-0.20*back]),np.array([0.105,0.11,0.11]),fl['tex']); ex.append((Pb,UV,tr,fl['tex']))
    print(lab,k,d)
    outs.append(h.render(M,g,T2,ex,angs=(0,0.7,1.57,2.4,3.14),W=210,H=250,zoom=2.0,ycen=1.12,label=lab))
preview.stack(outs).save('step1f_scalp.png')
