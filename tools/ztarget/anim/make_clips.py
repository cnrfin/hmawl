exec(open('../boy/strafe.py').read().split("if __name__")[0])
sys.path.insert(0,'/home/user/hmawl-goddess/tools/joe/scripts')
import joe_anm
TEMPLATE=open('../boy/anm/anm001.bin','rb').read()
def clip_from_worlds(Wf):           # list of world-matrix lists, one per frame 0..L (last = loop of first)
    keys={n:[] for n in range(NN)}
    for f,W in enumerate(Wf):
        for n in range(NN):
            p=nodes[n]['parent']; L=np.linalg.inv(W[p])@W[n] if p>=0 else W[n]
            keys[n].append((f,L))
    tracks=[]
    for n in range(NN):
        ks=keys[n]
        if all(np.allclose(ks[0][1],k[1],atol=1e-5) for k in ks):
            tracks.append((n,'const',(joe_anm.mat2q(ks[0][1][:3,:3]),ks[0][1][:3,3])))
        else:
            out=[]; prev=None
            for f,M_ in ks:
                q=joe_anm.mat2q(M_[:3,:3])
                if prev is not None and np.dot(q,prev)<0: q=-q
                prev=q; out.append((f,q,M_[:3,3]))
            tracks.append((n,'keys',out))
    return joe_anm.rebuild(TEMPLATE, float(len(Wf)-1), tracks)
L=int(WL)
clips={126:clip_from_worlds([strafe_world(f%L,+1) for f in range(L+1)]),
       127:clip_from_worlds([strafe_world(f%L,-1) for f in range(L+1)]),
       128:clip_from_worlds([back_world(f%L) for f in range(L+1)])}
import os; os.makedirs('../boy/clips',exist_ok=True)
for k,v in clips.items(): open('../boy/clips/anm%03d.bin'%k,'wb').write(v); print(k,len(v),parse(v)[0]['length'],len(parse(v)))
# read back and render a strip
st=Image.new('RGB',(240*6,260*3))
for r,k in enumerate((126,127,128)):
    tr=parse(clips[k])
    for c,f in enumerate((0,4,7,11,14,18)):
        W=world(nodes,pose.locals_at(nodes,tr,f)); st.paste(draw(W,0.35,'clip %d f%d'%(k,f)),(240*c,260*r))
st.save('../boy/clips_readback.png')
