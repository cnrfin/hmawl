"""Celia's hands (her own mesh, nodes and painted-finger texture, tinted to our skin) in place of ours;
the gold bracelets moved to the wrist to cover the join."""
import sys; sys.path[:0]=['.','blank','../pm']
import numpy as np, awlmodel, wally, face as FC
C='../celia/sepi_0'
def celia_hands(skin):
    M=awlmodel.load(C); CV=M['V']; UV=M['UV']; vb=M['bones']
    T=wally.textures(C+'_b0.tpl',C+'_f0_e.tpl',C+'_f0_m.tpl'); t=T[0xFF]; h,w=t.shape[:2]
    ts=[x for tid,tt,_ in M['groups'] if tid==255 for x in tt]
    out=[]
    for sd in (1,-1):
        P=[];Q=[];F=[];N=[]
        for pi,ti in ts:
            X=CV[list(pi)]
            if (X[:,0]*sd).min()<=0.37: continue
            uv=UV[list(ti)].mean(0); col=t[int((uv[1]%1)*h)%h,int((uv[0]%1)*w)%w,:3]
            if not (col[0]>col[1]+8 and col[0]>150): continue
            F.append([len(P),len(P)+1,len(P)+2])
            for p,x in zip(pi,ti): P.append(CV[p]); Q.append(UV[x]); N.append(vb[p][0] if len(vb[p]) and vb[p][0] not in (9,) else (17 if sd>0 else 28))
        out.append(dict(P=np.array(P),Q=np.array(Q),F=np.array(F)[:,::-1],node=np.array(N)))
    # texture: her body texture tinted to our skin (only the hand region is used)
    src=np.array([246,218,189.])                      # her hand skin
    tex=t.copy(); r=np.array(skin,float)/src
    d=np.abs(t[...,:3]-src).sum(-1); wgt=np.clip(1-d/120,0,1)[...,None]
    tex[...,:3]=(t[...,:3]*(r*wgt+(1-wgt)*(1+(r-1)*0.6))).clip(0,255)
    return out,tex
