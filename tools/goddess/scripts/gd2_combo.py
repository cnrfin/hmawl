import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank']
import gd2
def princess_hair():
    Ms,J=gd2.princess(); h=[m for m in Ms if m['mat']=='hair_205'][0]
    UV0=np.c_[h['UV'][:,0],1-h['UV'][:,1]]
    P0=gd2.conform(gd2.fit(h['P']),h['T'],ears=False)
    P1,UV1,T1=gd2.loop_subdiv(P0,UV0,h['T']); P1=gd2.conform(P1,T1,ears=False)
    P2=gd2.conform(gd2.plump(P1,T1),T1,margin=0.010,ears=False)
    return P2,UV1,T1
def build(swirls, tendrils, cut=1.10, mcut=1.16):
    tex=gd2.green_hair_tex(); P2,UV1,T1=princess_hair(); cen=P2[T1].mean(1)
    keep=(cen[:,1]>cut) | ((cen[:,2]>0.06)&(cen[:,1]>0.98)) | (tendrils & (cen[:,2]>0.0) & (np.abs(cen[:,0])>0.12))
    MP,MUV,MT,mtex=gd2.muffy_hair(keep=lambda c: c[1]<mcut, swirls=swirls)
    MT=MT[:,::-1]; MP=MP*[0.97,1,0.97]+[0,0,-0.016]; MP=gd2.conform(MP,MT,margin=0.008,ears=False)
    d=np.load('/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/gd2_hair.npz')
    return dict(cap=(d['CP'],d['CUV'],d['CT'],tex), muffy=(MP,MUV,MT,mtex), top=(P2,UV1,T1[keep],tex))
