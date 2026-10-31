import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/model']
import gd2, outfit as O, goddesshair as GH, gd2_view as gv, pickle, view, raster
from PIL import Image, ImageDraw
def run(path, prev, out):
    raw=np.array(Image.open(path).convert('RGBA'),float)
    old=np.array(Image.open(prev).convert('RGBA'),float)
    dd=np.abs(raw-old).sum(2); ys,xs=np.where(dd>30); print('changed px',len(ys),(xs.min(),xs.max(),ys.min(),ys.max()) if len(ys) else '')
    S=gd2.filled(raw); np.save('sheet_latest.npy',S)
    b=np.load('blank/blank_v3.npz'); V=b['V']; d=pickle.load(open('outfit_xfer.pkl','rb')); Fb=d['Fb']
    o=pickle.load(open('outfit_v3.pkl','rb')); T=O.desat(O.TEX)
    k=np.load('gh_hair_v9.npz'); P,Q,F,tex=k['P'],k['Q'],k['F'],np.load('gh_kate_tex.npy')
    s=np.load('gh_scalp_v15.npz'); sheet2=np.load('gh_scalp_sheet2.npy'); loose=pickle.load(open('gh_loose_final.pkl','rb'))
    buns=pickle.load(open('gh_buns_twist_4.pkl','rb')); pony=pickle.load(open('gh_pony2_A.pkl','rb'))
    Tf=GH.part('san',(197,)); tP=Tf[0]; torg=np.array([tP[:,0].mean(),tP[:,1].max(),tP[:,2].mean()])
    hair=[(s['P'],s['Q'],s['F'],sheet2),(P,Q,F,tex)]+loose+buns+pony
    for sd in (1,-1): hair.append(GH.placed(Tf,torg,np.array([0.06*sd,1.285,0.187]),1.7,rot_z=12*sd,mirror=(sd>0)))
    parts=[d['gown']+(S,),d['skirt']+(S,),(o['belt'][0],o['belt'][1],o['belt'][2],T),o['pendant']+(raw,)]+[bd+(T,) for bd in o['bands']]+hair
    ims=[]
    for lab,txt in (('A','A: top 1.2 cm lower'),('B','B: top 2.2 cm lower')):
        U=np.load(f'chestU_{lab}.npy'); imr=[]
        for ang in (0,0.6,1.57):
            W,H=260,300; img=np.zeros((H,W,3))+[200,215,225]; zb=np.full((H,W),-1e9); sc=H/1.45*2.2; oy=H/2+0.72*sc; R=raster.rotY(ang)
            Qb=V[Fb].reshape(-1,3); view.smooth_tex(img,zb,Qb,np.arange(len(Qb)).reshape(-1,3),U.reshape(-1,2),S,R,sc,W/2,oy)
            for P_,Q_,F_,t_ in parts: view.smooth_tex(img,zb,P_,np.asarray(F_),Q_,t_,R,sc,W/2,oy)
            imr.append(Image.fromarray(img.clip(0,255).astype(np.uint8)))
        o_=Image.new('RGB',(780,318),'white')
        for i,im in enumerate(imr): o_.paste(im,(260*i,18))
        ImageDraw.Draw(o_).text((4,3),txt+', your latest sheet',fill=(0,0,0)); ims.append(o_)
    gv.stack(ims,out)
