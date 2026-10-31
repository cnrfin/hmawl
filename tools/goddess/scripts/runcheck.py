import sys; sys.path[:0]=['.','blank','../pm','/home/user/hmawl/tools/logs']
import numpy as np, awlmodel, u8arc, struct, trimesh
from awlchar import act, world, skn
from anm import parse
import pose
def load(pre, anmarc):
    M=awlmodel.load(pre); V=M['V']
    nodes=act(open(pre+'.act','rb').read()); Wb=world(nodes); sk=skn(open(pre+'.skn','rb').read())
    a=u8arc.read(open(anmarc,'rb').read()); files=a['files']; files=files if isinstance(files,list) else list(files.values())
    return M,V,nodes,Wb,sk,[parse(f) for f in files]
def check(pre, anmarc, ai=5, nf=24):
    M,V,nodes,Wb,sk,anims=load(pre,anmarc)
    tr=anims[ai]; L=tr[0]['length']
    # which vertices: legs/feet = nodes 36-41,43-48 ; skirt = nodes 32,33,34 and 3 below hips
    vb=np.zeros(len(V),int)
    for g in sk['g1']:
        i0=(g['dst']+g['al'])//12; vb[i0:i0+g['cnt']]=g['bone']
    legs=np.isin(vb,[36,37,38,39,40,41,43,44,45,46,47,48])
    # skirt triangles: tris whose verts are skirt-node
    tris=[]
    for tid,ts,_ in M['groups']:
        for pi,_ in ts:
            if all(vb[i] in (32,33,34,3) for i in pi) and V[list(pi)][:,1].mean()<0.66*1.1: tris.append(pi)
    tris=np.array(tris)
    worst=[]
    for f in np.linspace(0,L,nf):
        Wp=world(nodes,pose.locals_at(nodes,tr,f)); Vp=pose.skin_rigid_from_skn(V,sk,Wb,Wp)
        mesh=trimesh.Trimesh(Vp,tris,process=False)
        # a leg vertex pokes out if a ray from the body axis (hips x,z at its height) to it crosses the skirt an odd number... simpler: ray from vertex outward horizontally away from the axis hits no skirt
        hip=Wp[3][:3,3]; P=Vp[legs]; d=P-np.array([hip[0],0,hip[2]]); d[:,1]=0; d/=np.linalg.norm(d,axis=1,keepdims=True)+1e-9
        hit=trimesh.ray.ray_pyembree.RayMeshIntersector(mesh).intersects_any(P+d*1e-4,d)
        out=(~hit)&(P[:,1]<0.62*1.1)&(P[:,1]>0.05)
        worst.append((round(f,1),int(out.sum())))
    return worst
if __name__=='__main__':
    for ai,nm in ((1,'walk'),(5,'run')):
        print(nm,check(sys.argv[1],sys.argv[2],ai))
