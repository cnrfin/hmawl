import sys; sys.path[:0]=['.']
from rmh import *
from collections import Counter, defaultdict
def neck(cut=0.84, top=0.95, shrink=0.92):
    k2=V[Fb].mean(1)[:,1]<cut; F=Fb[k2]; U=Ub[k2]
    e=Counter(); uvof={}
    for t,u in zip(F,U):
        for i in range(3): uvof[t[i]]=u[i]
        for a,b_ in ((t[0],t[1]),(t[1],t[2]),(t[2],t[0])): e[tuple(sorted((a,b_)))]+=1
    bd=[k for k,v in e.items() if v==1 and V[list(k)][:,1].min()>0.78]
    adj=defaultdict(list)
    for a,b_ in bd: adj[a].append(b_); adj[b_].append(a)
    loop=[bd[0][0]]; prev=None
    while True:
        n=[x for x in adj[loop[-1]] if x!=prev][0]
        if n==loop[0]: break
        prev=loop[-1]; loop.append(n)
    L=V[loop]; c=L.mean(0)
    Tp=L.copy(); Tp[:,[0,2]]=c[[0,2]]+(L[:,[0,2]]-c[[0,2]])*shrink; Tp[:,1]=top
    P=np.vstack([L,Tp]); n=len(loop); Q=np.array([uvof[v] for v in loop]*2)
    NF=[]
    for i in range(n):
        j=(i+1)%n; NF+=[(i,j,n+j),(i,n+j,n+i)]
    NF=np.array(NF)
    nrm=np.cross(P[NF[:,1]]-P[NF[:,0]],P[NF[:,2]]-P[NF[:,0]]); out=P[NF].mean(1)-np.r_[c[0],0,c[2]]*[1,0,1]-[0,0,0]
    out[:,1]=0; flip=(nrm*out).sum(1)<0; NF[flip]=NF[flip][:,::-1]
    return F,U,(P,Q,NF)

def neck2(cut=0.84, rings=((0.856,0.100,0.000,0.066),(0.88,0.112,-0.018,0.072),(0.95,0.100,-0.03,0.066))):
    """Muffy-proportioned neck: our body's neck-cut loop, widening into her short, wide neck under the jaw"""
    F,U,(P0,Q0,_)=neck(cut)
    n=len(P0)//2; L=P0[:n]; c=L.mean(0); Qr=Q0[:n]
    ang=np.arctan2(L[:,0]-c[0],L[:,2]-c[2])
    R=[L]
    for y,hw,zc,zr in rings:
        R.append(np.stack([hw*np.sin(ang),np.full(n,y),zc+zr*np.cos(ang)],1))
    P=np.vstack(R); Q=np.vstack([Qr]*len(R)); NF=[]
    for k in range(len(R)-1):
        for i in range(n):
            j=(i+1)%n; a,b_,cc,d=k*n+i,k*n+j,(k+1)*n+j,(k+1)*n+i; NF+=[(a,b_,cc),(a,cc,d)]
    NF=np.array(NF)
    nrm=np.cross(P[NF[:,1]]-P[NF[:,0]],P[NF[:,2]]-P[NF[:,0]]); m=P[NF].mean(1); out=m-np.array([0,0,-0.01]); out[:,1]=0
    flip=(nrm*out).sum(1)<0; NF[flip]=NF[flip][:,::-1]
    return F,U,(P,Q,NF)
