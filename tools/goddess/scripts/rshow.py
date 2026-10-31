import sys; sys.path[:0]=['.','blank']
import rmh
from rmh import *
V2=np.load('goddess_reshaped_V.npy'); rmh.V=V2
d=pickle.load(open('outfit_xfer.pkl','rb')); rmh.Fb2=d['Fb']; rmh.Ub2=np.load('final/chestU.npy')
mh=pickle.load(open('muffyhead_v1.pkl','rb')); face=mh['face']
ht=np.load('muffy_face_skin3.npy'); eye=np.load('muffy_eye_A.npy'); mouth=np.load('muffy_mouth.npy')
fp=[face[2]+(ht,),face[0]+(eye,),face[1]+(mouth,)]
hair=[(P_,Q_,F_,t_) for nm,P_,Q_,F_,t_ in pickle.load(open('hair_on_muffyhead.pkl','rb'))]
vw=((0,0),(0.7,0),(1.57,0),(3.14,0),(0.4,0.45))
gv.stack([rend('reshaped head only',[],views=vw,zm=2.2,yc=1.02),rend('+ Muffy face',fp,views=vw,zm=2.2,yc=1.02),rend('+ hair',fp+hair,views=vw,zm=2.2,yc=1.02)],sys.argv[1])
