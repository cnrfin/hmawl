import numpy as np, trimesh
def fib_dirs(n=300, min_el=-35):
    i=np.arange(n)+0.5; phi=np.arccos(1-2*i/n); th=np.pi*(1+5**0.5)*i
    D=np.stack([np.sin(phi)*np.cos(th),np.cos(phi),np.sin(phi)*np.sin(th)],1)
    return D[np.degrees(np.arcsin(D[:,1]))>=min_el]
def visible(pieces, cand, dirs=None, eps=1e-4):
    """pieces: list of (P,F); cand: dict piece_index -> bool mask of candidate tris. returns dict of visible masks"""
    dirs=fib_dirs() if dirs is None else dirs
    allV=[];allF=[];own=[];o=0
    for k,(P,F) in enumerate(pieces):
        allV.append(P); allF.append(np.asarray(F)+o); own+= [(k,j) for j in range(len(F))]; o+=len(P)
    V=np.vstack(allV); F=np.vstack(allF); mesh=trimesh.Trimesh(V,F,process=False)
    base=np.cumsum([0]+[len(f) for _,f in pieces])
    inter=trimesh.ray.ray_pyembree.RayMeshIntersector(mesh)
    out={}
    for k,m in cand.items():
        P,Fk=pieces[k]; idx=np.where(m)[0]; T=P[np.asarray(Fk)[idx]]
        samples=[T.mean(1)]+[T.mean(1)*0.4+T[:,i]*0.6 for i in range(3)]
        vis=np.zeros(len(idx),bool)
        for S in samples:
            for d in dirs:
                todo=~vis
                if not todo.any(): break
                O=S[todo]+d*3.0; Dd=np.repeat(-d[None],todo.sum(),0)
                tri=inter.intersects_first(O,Dd)
                gid=base[k]+idx[todo]
                vis[np.where(todo)[0][tri==gid]]=True
        out[k]=np.zeros(len(m),bool); out[k][idx[vis]]=True; out[k][~m]=True
    return out
