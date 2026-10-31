import sys; sys.path[:0]=['.','blank']
import rmh
from rmh import *
st=pickle.load(open(sys.argv[1],'rb')); rmh.V=st['V']; rmh.Fb2=st['Fk']; rmh.Ub2=st['Uk']
mh=pickle.load(open('muffyhead_v1.pkl','rb')); f=mh['face']; SH=np.array([0,-0.04,0])
ht=np.load('muffy_face_skin3.npy'); eye=np.load('muffy_eye_A.npy'); mouth=np.load('muffy_mouth.npy')
fp=[(f[2][0]+SH,)+f[2][1:]+(ht,),(f[0][0]+SH,)+f[0][1:]+(eye,),(f[1][0]+SH,)+f[1][1:]+(mouth,)]
fs=[(p[0],p[1],p[2],solid(c)) for p,c in zip(fp,([240,150,150],[150,150,240],[240,90,90]))]
fl=st['fill']
if fl:
    FP=np.array(fl).reshape(-1,3); fill=[(FP,np.zeros((len(FP),2)),np.arange(len(FP)).reshape(-1,3),solid([60,200,60])),(FP,np.zeros((len(FP),2)),np.arange(len(FP)).reshape(-1,3)[:,::-1],solid([60,200,60]))]
else: fill=[]
ep=st.get('earpatch',[])
if ep:
    EP=np.vstack([p for p,_ in ep]); EQ=np.vstack([q for _,q in ep]); EF=np.arange(len(EP)).reshape(-1,3)
    fp=fp+[(EP,EQ,EF,ht),(EP,EQ,EF[:,::-1],ht)]; fs=fs+[(EP,EQ,EF,solid([60,200,60])),(EP,EQ,EF[:,::-1],solid([60,200,60]))]
vw=((0,0),(0.8,0),(1.57,0),(2.4,0),(3.14,0),(0.4,0.6),(0.3,-0.6))
gv.stack([rend('head (body skin) + face shell pink/blue + fill green',fs+fill,views=vw,zm=2.4,yc=1.0),rend('textured',fp+fill[:1],views=vw,zm=2.4,yc=1.0)],sys.argv[2])
