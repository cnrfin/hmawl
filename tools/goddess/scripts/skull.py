import sys,numpy as np,pickle; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank']
from scipy.spatial import cKDTree
import gd2, edgeclean as EC
def build(face_P, face_F, body_V, body_F, body_U, ycut=0.86, sx=1.08, sz=1.02, snap=0.035):
    """skull behind the new face: our head scaled to the face's width, only the part behind the face kept,
    and its edge vertices snapped onto the face's open edges (no cracks)"""
    V=body_V.copy(); head=V[:,1]>ycut
    c=np.array([0,1.08,-0.01]); V[head]=c+(V[head]-c)*[sx,1.0,sz]
    # where is the face? per (y, angle) the face's own radius; drop skull tris in front of / inside it
    fP=face_P; kd=cKDTree(fP)
    C=V[body_F].mean(1); d,i=kd.query(C)
    rf=np.linalg.norm((fP[i]-c)*[1,0,1],axis=1); rc=np.linalg.norm((C-c)*[1,0,1],axis=1)
    covered=(C[:,1]>ycut)&(d<0.045)&(rc<=rf+0.01)
    front=(C[:,1]>ycut)&(C[:,2]>0.02)&(np.abs(C[:,0])<0.2)&(C[:,1]<1.2)
    keep=~(covered|front)
    F=body_F[keep]; U=body_U[keep]
    # snap skull open-edge vertices near the face edge onto the face edge
    wid,n=gd2.weld(fP); ec=EC.open_edges(wid,face_F); WP=np.zeros((n,3)); WP[wid]=fP
    fb=np.array(sorted({v for e,k in ec.items() if k==1 for v in e})); kb=cKDTree(WP[fb])
    swid,sn=gd2.weld(V); sec=EC.open_edges(swid,F[:, :]) if False else None
    used=np.unique(F); hv=used[V[used,1]>ycut]
    dd,ii=kb.query(V[hv]); m=dd<snap; V[hv[m]]=WP[fb[ii[m]]]
    return V,F,U
