import numpy as np, pyfqmr, trimesh
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
def weld(P,Q,F,dec=5):
    key={}; idx=np.zeros(len(P),int); U=[]; UV=[]
    for i,(p,q) in enumerate(zip(P,Q)):
        k=tuple(np.round(p,dec))+tuple(np.round(q,dec))
        if k not in key: key[k]=len(U); U.append(p); UV.append(q)
        idx[i]=key[k]
    return np.array(U),np.array(UV),idx[np.asarray(F)]
def decimate(P,Q,F,ratio,min_tris=16,preserve_border=True):
    """UV-aware: split into UV charts (seams become borders), decimate each with fixed borders,
    UVs of the new vertices from the closest point on the original chart"""
    U,UV,W=weld(P,Q,F)
    W=W[(W[:,0]!=W[:,1])&(W[:,1]!=W[:,2])&(W[:,0]!=W[:,2])]
    n=len(W); e=[]
    vt={}
    for t,f in enumerate(W):
        for v in f: vt.setdefault(v,[]).append(t)
    rows=[];cols=[]
    for v,ts in vt.items():
        for a in ts[1:]: rows.append(ts[0]); cols.append(a)
    A=coo_matrix((np.ones(len(rows)),(rows,cols)),shape=(n,n)); nc,lab=connected_components(A,directed=False)
    oP=[];oQ=[];oF=[];o=0
    for c in range(nc):
        Fc=W[lab==c]; vs=np.unique(Fc); remap={v:i for i,v in enumerate(vs)}; Fl=np.vectorize(remap.get)(Fc)
        Vc=U[vs]; Qc=UV[vs]
        tgt=max(min_tris,int(len(Fc)*ratio))
        if len(Fc)<=tgt:
            Vn,Fn,Qn=Vc,Fl,Qc
        else:
            s=pyfqmr.Simplify(); s.setMesh(Vc,Fl); s.simplify_mesh(target_count=tgt,aggressiveness=7,preserve_border=preserve_border,verbose=False)
            Vn,Fn,_=s.getMesh()
            m=trimesh.Trimesh(Vc,Fl,process=False)
            cp,dist,tid=trimesh.proximity.closest_point(m,Vn)
            bc=trimesh.triangles.points_to_barycentric(Vc[Fl[tid]],cp)
            bc=np.nan_to_num(bc,nan=1/3.); Qn=(Qc[Fl[tid]]*bc[:,:,None]).sum(1)
        oP.append(Vn); oQ.append(Qn); oF.append(np.asarray(Fn)+o); o+=len(Vn)
    return np.vstack(oP),np.vstack(oQ),np.vstack(oF)
