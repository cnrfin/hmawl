import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank']
import gd2
from scipy.spatial import cKDTree
def reference(ytip=0.60, ytop=1.14, ybot=0.30):
    f=np.load('/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/gd2_princess_full.npz'); P,UV,T=f['P'].copy(),f['UV'],f['T']
    tex=gd2.green_hair_tex(); T=T[gd2.coverage(tex,UV,T)>=0.6]
    m=P[:,1]<ytop; P[m,1]=ytop-(ytop-P[m,1])*(ytop-ytip)/(ytop-ybot)
    return P,UV,T,gd2.filled(tex)
def project(V,F,ref):
    P,UV,T,tex=ref
    # dense samples on reference triangles -> owning triangle
    bs=np.array([(a,b,1-a-b) for a in np.linspace(0,1,5) for b in np.linspace(0,1,5) if a+b<=1])
    S=np.einsum('sk,tkd->tsd',bs,P[T]).reshape(-1,3); own=np.repeat(np.arange(len(T)),len(bs))
    kd=cKDTree(S)
    cen=V[F].mean(1); _,idx=kd.query(cen); tri=own[idx]
    out=np.zeros((len(F),3,2))
    for k,(f,t) in enumerate(zip(F,tri)):
        A=P[T[t]]; e1=A[1]-A[0]; e2=A[2]-A[0]; n=np.cross(e1,e2); n/=np.linalg.norm(n)
        M=np.array([e1,e2,n]).T; Mi=np.linalg.inv(M)
        for i in range(3):
            l=Mi@(V[f[i]]-A[0]); out[k,i]=UV[T[t][0]]+(UV[T[t][1]]-UV[T[t][0]])*l[0]+(UV[T[t][2]]-UV[T[t][0]])*l[1]
    return out,tex
