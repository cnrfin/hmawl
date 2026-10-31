import sys; sys.path[:0]=['.','blank']
import rmh
from rmh import *
import outfit as O, view
st=pickle.load(open('stitched_v1.pkl','rb')); Vh=st['V']; Fk=st['Fk']; Uk=st['Uk']
mh=pickle.load(open('muffyhead_v1.pkl','rb')); f=mh['face']; SH=np.array([0,-0.04,0])
ht=np.load('muffy_face_skin3.npy'); eye=np.load('muffy_eye_A.npy'); mouth=np.load('muffy_mouth.npy')
EP=np.vstack([p for p,_ in st['earpatch']]); EQ=np.vstack([q for _,q in st['earpatch']]); EF=np.arange(len(EP)).reshape(-1,3)
FL=np.array(st['fill']).reshape(-1,3) if st['fill'] else np.zeros((0,3))
headpieces=[(Vh[Fk].reshape(-1,3),Uk.reshape(-1,2),np.arange(len(Fk)*3).reshape(-1,3),S),
            (f[2][0]+SH,f[2][1],f[2][2],ht),(f[0][0]+SH,f[0][1],f[0][2],eye),(f[1][0]+SH,f[1][1],f[1][2],mouth),
            (EP,EQ,EF,ht)]
if len(FL): headpieces.append((FL,np.full((len(FL),2),0.5),np.arange(len(FL)).reshape(-1,3),S))
# unified smooth normals over the whole head surface (shared positions -> one normal), like a single mesh
key={}; acc=[]
def k_(p): return tuple(np.round(p,4))
for P,Q,F,t in headpieces[:-1] if len(FL) else headpieces:
    n=np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]])
    for tri,nn in zip(F,n):
        for v in tri:
            kk=k_(P[v])
            if kk not in key: key[kk]=len(acc); acc.append(np.zeros(3))
            acc[key[kk]]+=nn
acc=np.array(acc)
def normals(P):
    return np.array([acc[key[k_(p)]] if k_(p) in key else np.array([0,1.,0]) for p in P])
o=pickle.load(open('outfit_v4.pkl','rb')); x2=pickle.load(open('outfit_xfer2.pkl','rb')); T=O.desat(O.TEX)
veil=pickle.load(open('veil_A.pkl','rb'))+(S,)
sb=pickle.load(open('sashbow_v3.pkl','rb')); sash=[p+(S,) for p in sb['sash']]
hair=[(P_+SH,Q_,F_,t_) for nm,P_,Q_,F_,t_ in pickle.load(open('hair_on_muffyhead.pkl','rb'))]
outfit=[x2['gown']+(S,),x2['skirt']+(S,),(o['belt'][0],o['belt'][1],o['belt'][2],T),veil]+sash+[bd+(T,) for bd in o['bands']]
# body below the head stays the original body mesh (non-head triangles of Fk are drawn as part of headpieces[0])
pickle.dump(dict(Vbody=Vh,Fk=Fk,Uk=Uk,headpieces=headpieces,outfit=outfit,hair=hair),open('goddess_option3_stitched.pkl','wb'))
def draw(lab,parts_head,parts_other,views,zm,yc,W=200,H=240):
    ims=[]
    for ang,tilt in views:
        img=np.zeros((H,W,3))+[200,215,225]; zb=np.full((H,W),-1e9); sc=H/1.45*zm; oy=H/2+yc*sc; R=raster.rotX(tilt)@raster.rotY(ang)
        for P,Q,F,t in parts_head: view.smooth_tex(img,zb,P,np.asarray(F),Q,t,R,sc,W/2,oy,normals=normals(P))
        for P,Q,F,t in parts_head[4:5]: view.smooth_tex(img,zb,P,np.asarray(F)[:,::-1],Q,t,R,sc,W/2,oy,normals=-normals(P))
        for P,Q,F,t in parts_other: view.smooth_tex(img,zb,P,np.asarray(F),Q,t,R,sc,W/2,oy)
        ims.append(Image.fromarray(img.clip(0,255).astype(np.uint8)))
    o_=Image.new('RGB',(W*len(ims),H+18),'white')
    for i,im in enumerate(ims): o_.paste(im,(W*i,18))
    ImageDraw.Draw(o_).text((4,3),lab,fill=(0,0,0)); return o_
vw=((0,0),(0.7,0),(1.57,0),(3.14,0),(0.4,0.5))
cols=[[235,205,175],[240,150,150],[150,150,240],[240,90,90],[60,200,60],[60,200,60]]
diag=[(P,Q,F,solid(c)) for (P,Q,F,t),c in zip(headpieces,cols)]
rows=[draw('ONE head surface: original head mesh reshaped (skin) joined edge-to-edge with Muffy face (pink/blue/red), ear backs closed (green)',diag,[],vw,2.4,1.0),
      draw('bald, textured',headpieces,[],vw,2.4,1.0),
      draw('with hair',headpieces,hair,vw,2.4,1.0),
      draw('full',headpieces,outfit+hair,vw,0.95,0.68)]
gv.stack(rows,'goddess_option3_stitched.png')
