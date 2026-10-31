"""Muffy's hair, top and back only (no side curls/front locks, no headband), teal, on the blank model"""
import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/pm']
import hairstudy as S, hairtex2 as HT, restyle, gd2
def build(zc=0.0, yc=1.20, sxz=0.97, dz=-0.016):
    M,T,tris,hb=S.hair2('mumu'); V=M['V'].copy(); UV=M['UV']; H,W=256,128
    keep=[]
    for t in tris:
        u=np.mean([UV[x][0]%1 for x in t[1]])*W; v=np.mean([UV[x][1]%1 for x in t[1]])*H
        if not (u>=75 and v<60): continue                       # strands only (no swirl curls, no headband)
        c=M['V'][list(t[0])].mean(0)
        if c[2]>zc and c[1]<yc: continue                         # front locks beside the face
        keep.append(t)
    V[:,0]*=sxz; V[:,2]=V[:,2]*sxz+dz
    tex=T[255].copy(); blk=tex[0:60,75:128]; L=restyle.lum(blk[...,:3]); lo,hi=np.percentile(L,1),np.percentile(L,99.5)
    blk[...,:3]=HT.ramp()[(np.clip((L-lo)/(hi-lo),0,1)*0.72*255).astype(int)]; tex[0:60,75:128]=blk
    P=[];Q=[];F=[]
    for pi,ti in keep:
        F.append([len(P),len(P)+1,len(P)+2])
        for p,t in zip(pi,ti): P.append(V[p]); Q.append((UV[t][0]%1,UV[t][1]%1))
    P=np.array(P); F=np.array(F)[:,::-1]
    return gd2.conform(P,F,margin=0.008,ears=False),np.array(Q),F,tex
