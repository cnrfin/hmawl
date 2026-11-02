import sys; sys.path[:0]=['.','blank','../pm']
import numpy as np, awlmodel, wally, raster, pose
from PIL import Image, ImageDraw
from awlchar import act, world, skn
from anm import parse
from scipy.spatial.transform import Rotation as Rot, Slerp
pre='../boy/boy_0/boy_0'
M=awlmodel.load(pre); V=M['V']; T=wally.textures(pre+'_b0.tpl',pre+'_f0_e.tpl',pre+'_f0_m.tpl')
nodes=act(open(pre+'.act','rb').read()); Wb=world(nodes); SKD=open(pre+'.skn','rb').read(); sk=skn(SKD)
NN=len(nodes)
walk=parse(open('../boy/anm/anm001.bin','rb').read()); WL=walk[0]['length']
idle=parse(open('../boy/anm/anm000.bin','rb').read())
ARMS=set(range(22,43))
LEGS={+1:dict(hip=10,knee=11,ank=12,feet=(1,2,3)), -1:dict(hip=15,knee=16,ank=17,feet=(4,5,6))}
def children(n): return [i for i,v in enumerate(nodes) if v['parent']==n]
def subtree(n):
    out=[n]; st=[n]
    while st:
        c=st.pop()
        for k in children(c): out.append(k); st.append(k)
    return out
def rot_between(a,b):
    a=a/np.linalg.norm(a); b=b/np.linalg.norm(b); v=np.cross(a,b); c=np.dot(a,b)
    if np.linalg.norm(v)<1e-9: return np.eye(3)
    vx=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]]); return np.eye(3)+vx+vx@vx*(1/(1+c))
def apply_about(W, ids, R, c):
    for i in ids:
        M_=W[i].copy(); M_[:3,:3]=R@M_[:3,:3]; M_[:3,3]=R@(M_[:3,3]-c)+c; W[i]=M_
def locals_blend(f, arm_calm):
    La=pose.locals_at(nodes,walk,f); Li=pose.locals_at(nodes,idle,0); out=[]
    for i in range(NN):
        A=np.array(La[i]); B=np.array(Li[i])
        if i in ARMS and arm_calm>0:
            r=Slerp([0,1],Rot.from_matrix([A[:3,:3],B[:3,:3]]))([arm_calm]).as_matrix()[0]
            C=A.copy(); C[:3,:3]=r; C[:3,3]=A[:3,3]*(1-arm_calm)+B[:3,3]*arm_calm; out.append(C)
        else: out.append(A)
    return out
def strafe_world(f, side, k=0.65):
    """side +1: step toward +x (his left), -1: toward -x"""
    W=world(nodes, locals_blend(f, 0.6)); Wr=world(nodes, pose.locals_at(nodes,walk,f))
    for s,leg in LEGS.items():
        H=W[leg['hip']][:3,3]; A0=W[leg['feet'][0]][:3,3].copy()
        sw=A0[2]-H[2]                                     # forward/back swing of this foot
        R0=Wb[leg['feet'][0]][:3,3]
        lift=max(A0[1]-R0[1],0)*0.8                          # how high the walk lifts this foot
        A=R0.copy(); A[0]=R0[0]+side*sw*k; A[1]=R0[1]+lift; A[2]=R0[2]+0.02
        for i in leg['feet']:                                 # flat foot, toes forward, moved to A
            W[i]=Wb[i].copy(); W[i][:3,3]+=A-R0
        # 2-bone IK: hip->knee->ankle reaches A, knee bends forward (+z)
        K0=W[leg['knee']][:3,3]; N0=W[leg['ank']][:3,3]
        a=np.linalg.norm(K0-H); b=np.linalg.norm(N0-K0); dv=A-H; dl=min(np.linalg.norm(dv),a+b-1e-4)
        u=dv/np.linalg.norm(dv); pole=np.array([0,0,1.0]); pole=pole-u*np.dot(pole,u); pole/=np.linalg.norm(pole)
        x=(a*a-b*b+dl*dl)/(2*dl); y=np.sqrt(max(a*a-x*x,0)); K=H+u*x+pole*y
        R1=rot_between(K0-H,K-H); apply_about(W, subtree(leg['knee'])+[leg['hip']], R1, H)
        N1=W[leg['ank']][:3,3]; K1=W[leg['knee']][:3,3]; R2=rot_between(N1-K1,A-K1); apply_about(W, subtree(leg['knee']), R2, K1)
    return W
def back_world(f): return world(nodes, pose.locals_at(nodes,walk,(WL-f)%WL))
def fwd_world(f): return world(nodes, pose.locals_at(nodes,walk,f))
def draw(W,ang,lab,W_=240,H_=260):
    Vp=pose.skin_weighted(V,sk,SKD,Wb,W)
    img=np.zeros((H_,W_,3))+[200,215,225]; zb=np.full((H_,W_),-1e9)
    wally.draw(img,zb,Vp,M['UV'],M['groups'],T,raster.rotX(-0.2)@raster.rotY(ang),110,W_/2,H_-25)
    im=Image.fromarray(img.clip(0,255).astype(np.uint8)); ImageDraw.Draw(im).text((5,5),lab,fill=(0,0,0)); return im
if __name__=='__main__':
    frames=[]
    for t in range(0,63):
        f=(t*1.0)%WL
        row=Image.new('RGB',(240*4,260),'white')
        row.paste(draw(fwd_world(f),2.6,'forward (walk)'),(0,0))
        row.paste(draw(back_world(f),2.6,'back (walk reversed)'),(240,0))
        row.paste(draw(strafe_world(f,+1),3.14,'strafe left'),(480,0))
        row.paste(draw(strafe_world(f,-1),3.14,'strafe right'),(720,0))
        frames.append(row)
    frames[0].save('../boy/strafe1.gif',save_all=True,append_images=frames[1:],duration=33,loop=0)
    st=Image.new('RGB',(960,260*4))
    for i,k in enumerate((0,5,10,15)): st.paste(frames[k],(0,260*i))
    st.save('../boy/strafe1.png'); print('ok')
