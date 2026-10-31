"""new head: Muffy's face surface (face+eyes+mouth, the AWL face shape) as the front of the head, our skull behind"""
import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/pm']
import awlmodel
MP='/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/girls/mumu_0/mumu_0'
def muffy_xf(s=0.956, chin=0.868, dz=-0.03):
    M=awlmodel.load(MP); V=M['V']
    g={}
    for tid,ts,_ in M['groups']: g.setdefault(tid,[]).extend(ts)
    face=V[sorted({i for pi,_ in g[2] for i in pi})]
    mchin=face[(np.abs(face[:,0])<0.04)&(face[:,2]>0.05)][:,1].min()
    def xf(P): P=np.array(P,float); return np.c_[P[:,0]*s, chin+(P[:,1]-mchin)*s, P[:,2]*s+dz]
    return M,g,xf,mchin
def build(s=0.956, chin=0.868, dz=-0.03, neck_cut=0.84):
    M,g,xf,mchin=muffy_xf(s,chin,dz); V=M['V']; UV=M['UV']; out={}
    for tid in (2,0,1):
        P=[];Q=[];F=[];key={}
        for pi,ti in g[tid]:
            c=xf(V[list(pi)]).mean(0)
            if c[1]<neck_cut: continue
            idx=[]
            for p,x in zip(pi,ti):
                k=(p,x)
                if k not in key: key[k]=len(P); P.append(xf([V[p]])[0]); Q.append((UV[x][0]%1,UV[x][1]%1) if tid==2 else (UV[x][0],UV[x][1]))
                idx.append(key[k])
            F.append(idx)
        out[tid]=(np.array(P),np.array(Q),np.array(F)[:,::-1])
    # back edge of the new face by height (to keep only the skull behind it)
    A=np.vstack([out[t][0] for t in out]); ys=np.linspace(0.84,1.35,30); zb=[]
    for y in ys:
        m=np.abs(A[:,1]-y)<0.02; zb.append(A[m,2].min() if m.any() else 0.09)
    return out,(ys,np.array(zb))
