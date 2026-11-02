"""Muffy recolour: pink cotton-candy hair, black dress, white bodice ('breast plate'), pantyhose legs.
Each texel of the body texture is classified by the 3D triangles that use it (texture regions are shared
by several parts), then recoloured keeping its original shading."""
import sys; sys.path[:0]=['.','blank','../pm']
import numpy as np, awlmodel, wally, colorsys
PRE='girls/mumu_0/mumu_0'
def hsv(c):
    c=np.asarray(c,float)/255.; mx=c.max(-1); mn=c.min(-1); d=mx-mn
    h=np.zeros_like(mx); m=d>1e-6
    r,g,b=c[...,0],c[...,1],c[...,2]
    h=np.where(m&(mx==r),((g-b)/np.where(m,d,1))%6,h); h=np.where(m&(mx==g),(b-r)/np.where(m,d,1)+2,h); h=np.where(m&(mx==b),(r-g)/np.where(m,d,1)+4,h)
    return h*60, np.where(mx>0,d/np.maximum(mx,1e-6),0), mx
def ramp(L, stops):
    xs=np.array([s[0] for s in stops]); cs=np.array([s[1] for s in stops],float)
    return np.stack([np.interp(L,xs,cs[:,k]) for k in range(3)],-1)
def label_map(M, tex, chest_y=0.655):
    """per texel: votes for 'chest', 'legs', 'other' from the triangles that cover it"""
    V,UV=M['V'],M['UV']; H,W=tex.shape[:2]; votes=np.zeros((H,W,5))
    for tid,ts,_ in M['groups']:
        if tid!=255: continue
        for pi,ti in ts:
            P=V[list(pi)]; c=P.mean(0); q=UV[list(ti)]%1.0
            uvm=q.mean(0); tc=tex[int(uvm[1]*H)%H,int(uvm[0]*W)%W,:3]; th_,ts_,tv_=hsv(tc)
            hemred=(th_<25 or th_>330) and ts_>0.25
            cls=0 if (c[1]>chest_y and c[2]>0.02 and abs(c[0])<0.13) else (3 if c[1]<0.13 else (4 if (c[1]<0.42 and hemred) else (1 if c[1]<0.40 else 2)))
            x=q[:,0]*W; y=q[:,1]*H
            x0,x1=int(max(0,np.floor(x.min()))),int(min(W-1,np.ceil(x.max()))); y0,y1=int(max(0,np.floor(y.min()))),int(min(H-1,np.ceil(y.max())))
            X,Y=np.meshgrid(np.arange(x0,x1+1)+0.5,np.arange(y0,y1+1)+0.5)
            (xa,ya),(xb,yb),(xc,yc)=zip(x,y)
            den=(yb-yc)*(xa-xc)+(xc-xb)*(ya-yc)
            if abs(den)<1e-9: continue
            w0=((yb-yc)*(X-xc)+(xc-xb)*(Y-yc))/den; w1=((yc-ya)*(X-xc)+(xa-xc)*(Y-yc))/den; w2=1-w0-w1
            m=(w0>=-0.15)&(w1>=-0.15)&(w2>=-0.15)
            votes[y0:y1+1,x0:x1+1,cls]+=m
    return votes
def recolor(M, T):
    t=T[255].copy(); rgb=t[...,:3]; h,s,v=hsv(rgb); L=rgb.mean(-1)/255.
    votes=label_map(M,t); lab=np.argmax(votes,-1); used=votes.sum(-1)>0
    yellow=(h>30)&(h<70)&(s>0.35)&(v>0.25)
    red=((h<20)|(h>335))&(s>0.45)&(v>0.08)
    skin=((h<40)|(h>340))&(s>0.08)&(s<0.45)&(v>0.6)
    out=rgb.copy()
    out[yellow]=ramp(L[yellow],[(0.15,(150,60,105)),(0.45,(240,130,185)),(0.7,(255,182,215)),(0.95,(255,228,240))])
    chest=red&(lab==0)&used; dress=red&~chest&~((lab==3)&used)      # shoes keep their red
    out[dress]=ramp(L[dress],[(0.10,(8,8,12)),(0.30,(28,28,34)),(0.50,(70,70,80)),(0.75,(130,130,142))])
    out[chest]=ramp(L[chest],[(0.15,(150,150,160)),(0.35,(215,215,222)),(0.55,(245,245,248)),(0.8,(255,255,255))])
    shoe=red&(lab==3)&used                                   # shoe details: red -> white
    out[shoe]=ramp(L[shoe],[(0.10,(140,140,148)),(0.30,(210,210,216)),(0.5,(245,245,248)),(0.7,(255,255,255))])
    hem=(lab==4)&used&~red
    out[hem]=ramp(L[hem],[(0.10,(8,8,12)),(0.30,(28,28,34)),(0.50,(70,70,80)),(0.75,(130,130,142))])
    legs=skin&((votes[...,1]+votes[...,3])>0)&((votes[...,1]+votes[...,3])>=votes[...,2])&~hem
    hose=np.array([178,132,108.]); out[legs]=rgb[legs]*0.2+hose*(rgb[legs].mean(-1,keepdims=True)/215.)*0.8
    t[...,:3]=out.clip(0,255)
    h2=T[2].copy(); r2=h2[...,:3]; hh,ss,vv=hsv(r2); L2=r2.mean(-1)/255.
    y2=(hh>30)&(hh<70)&(ss>0.35)&(vv>0.25)
    r2[y2]=ramp(L2[y2],[(0.15,(150,60,105)),(0.45,(240,130,185)),(0.7,(255,182,215)),(0.95,(255,228,240))]); h2[...,:3]=r2
    return t,h2,dict(chest=int(chest.sum()),dress=int(dress.sum()),legs=int(legs.sum()),hair=int(yellow.sum()))

def orange_eyes(img, stops=None):
    """green iris -> bright orange, keeping its shading (works on every eye frame)"""
    out=img.copy(); rgb=out[...,:3]; h,s,v=hsv(rgb)
    g=(h>60)&(h<225)&(s>0.07)&(v>0.12)
    L=v[g]
    rgb[g]=ramp(L,stops or [(0.15,(110,35,0)),(0.40,(225,95,5)),(0.65,(255,150,20)),(0.9,(255,215,110))])
    out[...,:3]=rgb; return out

SOFT_ORANGE=[(0.15,(95,45,20)),(0.40,(185,100,45)),(0.65,(220,145,85)),(0.9,(245,205,150))]      # muted amber
SOFTER_ORANGE=[(0.15,(90,55,35)),(0.40,(165,105,65)),(0.65,(205,150,105)),(0.9,(235,205,170))]  # warm hazel-amber
