# Encode the combo (combo.py) as boy_0.anm.arc clips 129 / 130 / 131 (hit 1 / 2 / 3). Run from the scratchpad goddess/ dir
# like strafe.py. Only bones 18+ are used in game (zt.c layers them over the walk); bones below keep the idle pose.
import sys
exec(open(sys.argv[1] if len(sys.argv) > 1 else 'combo.py').read().split('#MAIN')[0])
sys.path.insert(0,'/home/user/hmawl-goddess/tools/joe/scripts')
import joe_anm, os
TEMPLATE=open('../boy/anm/anm001.bin','rb').read()
def clip_from_locals(Lf):
    tracks=[]
    for n in range(NN):
        ks=[(f,L[n]) for f,L in enumerate(Lf)]
        if all(np.allclose(ks[0][1],k[1],atol=1e-5) for k in ks):
            tracks.append((n,'const',(joe_anm.mat2q(ks[0][1][:3,:3]),ks[0][1][:3,3])))
        else:
            out=[]; prev=None
            for f,M_ in ks:
                q=joe_anm.mat2q(M_[:3,:3])
                if prev is not None and np.dot(q,prev)<0: q=-q
                prev=q; out.append((f,q,M_[:3,3]))
            tracks.append((n,'keys',out))
    return joe_anm.rebuild(TEMPLATE, float(len(Lf)-1), tracks)
out=os.path.dirname(os.path.abspath(sys.argv[2])) if len(sys.argv) > 2 else '.'
for h,clip in ((1,129),(2,130),(3,131)):
    n=HITS[h][-1][0]; b=clip_from_locals([pose_at(HITS[h],f) for f in range(n+1)])
    p=os.path.join(out,'anm%d.bin'%clip); open(p,'wb').write(b)
    tr=parse(b); W0=world(nodes,pose_at(HITS[h],8)); W1=world(nodes,pose.locals_at(nodes,tr,8))
    print(clip,len(b),'frames',tr[0]['length'],'readback err %.5f'%max(np.abs(W0[k][:3,3]-W1[k][:3,3]).max() for k in range(18,NN)))
