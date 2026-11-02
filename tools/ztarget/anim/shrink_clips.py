# Key reduction for our player clips (126-131): sample each clip's bone locals at every frame, keep only the keys that
# slerp / lerp between kept neighbours can't reproduce (Douglas-Peucker on frames), constant tracks as 'const'.
# The mainchapter archive loads at the start of the heap, so every byte here is game heap lost (test 18 crashed
# leaving the house with the full-key clips). Run from the scratchpad goddess/ dir:  shrink_clips.py IN_DIR OUT_DIR
import sys, os
sys.path[:0]=['.','blank','../pm','/home/user/hmawl-goddess/tools/joe/scripts']
import numpy as np, pose, joe_anm
from awlchar import act, world
from anm import parse
from scipy.spatial.transform import Rotation as Rot, Slerp
nodes=act(open('../boy/boy_0/boy_0.act','rb').read()); NN=len(nodes)
TEMPLATE=open('../boy/anm/anm001.bin','rb').read()
TOL_R=np.radians(0.35); TOL_T=0.0006
def err(qa,qb,ta,tb,fa,fb,Q,T,f):
    u=(f-fa)/(fb-fa); q=Slerp([0,1],Rot.from_quat([qa,qb]))([u])[0]
    return max((Rot.from_quat(Q[f])*q.inv()).magnitude()/TOL_R, np.abs(ta+(tb-ta)*u-T[f]).max()/TOL_T)
def reduce(Q,T):
    keep={0,len(Q)-1}; st=[(0,len(Q)-1)]
    while st:
        a,b=st.pop()
        if b-a<2: continue
        e=[(err(Q[a],Q[b],T[a],T[b],a,b,Q,T,f),f) for f in range(a+1,b)]; m,f=max(e)
        if m>1: keep.add(f); st+=[(a,f),(f,b)]
    return sorted(keep)
def shrink(data):
    tr=parse(data); L=int(round(tr[0]['length'])); Ls=[[np.array(m) for m in pose.locals_at(nodes,tr,f)] for f in range(L+1)]
    tracks=[]; nk=0
    for n in range(NN):
        Q=[]; prev=None
        for f in range(L+1):
            q=joe_anm.mat2q(Ls[f][n][:3,:3])
            if prev is not None and np.dot(q,prev)<0: q=-q
            prev=q; Q.append(q)
        Q=np.array(Q); T=np.array([Ls[f][n][:3,3] for f in range(L+1)])
        if np.abs(Q-Q[0]).max()<1e-4 and np.abs(T-T[0]).max()<1e-5: tracks.append((n,'const',(Q[0],T[0]))); continue
        ks=reduce(Q,T); nk+=len(ks); tracks.append((n,'keys',[(f,Q[f],T[f]) for f in ks]))
    out=joe_anm.rebuild(TEMPLATE,float(L),tracks)
    # check against the original at every frame (world positions of all bones)
    t2=parse(out); e=max(np.abs(world(nodes,pose.locals_at(nodes,tr,f))[k][:3,3]-world(nodes,pose.locals_at(nodes,t2,f))[k][:3,3]).max() for f in range(L+1) for k in range(NN))
    return out,nk,e
if __name__=='__main__':
    src,dst=sys.argv[1:3]; os.makedirs(dst,exist_ok=True); tot0=tot1=0
    for k in range(126,132):
        d=open(os.path.join(src,'anm%d.bin'%k),'rb').read(); o,nk,e=shrink(d); open(os.path.join(dst,'anm%d.bin'%k),'wb').write(o)
        tot0+=len(d); tot1+=len(o); print(k,len(d),'->',len(o),'keys',nk,'max bone error %.4f'%e)
    print('total',tot0,'->',tot1)
