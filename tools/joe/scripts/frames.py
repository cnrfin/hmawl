import sys, os, json, numpy as np
sys.path.insert(0,'.')
from compose import *
from PIL import Image, ImageFilter
S=json.load(open('final_set.json'))
EYE_BOX=(104,30,412,298); MOUTH_BOX=(72,222,504,508)
EYE_SIZE=(112,96); MOUTH_SIZE=(112,72)
TEX=float(os.environ.get('JOE_TEX','1'))          # 0.5: face frames at half size (memory: 314 KB of textures vs a villager's ~33 KB)
if TEX!=1: EYE_SIZE=(int(112*TEX)//8*8,int(96*TEX)//8*8); MOUTH_SIZE=(int(112*TEX)//4*4,int(72*TEX)//4*4)
FTEX=float(os.environ.get('JOE_FACETEX',str(TEX)))   # jm2: the face frames' own scale (the body atlas keeps JOE_TEX)
if FTEX!=TEX:
    q=4 if os.environ.get('JOE_SOFTEYES')=='1' else 8                 # RGB5A3 tiles are 4x4, CMPR 8x8
    EYE_SIZE=(int(112*FTEX)//q*q,int(96*FTEX)//q*q); MOUTH_SIZE=(int(112*FTEX)//4*4,int(72*FTEX)//4*4)
def layers_eyes(spec):
    out=Image.new('RGBA',(512,512),(0,0,0,0)); ex=spec.get('extras',{})
    if ex.get('blush'):
        b=Image.new('RGBA',(512,512),(0,0,0,0)); d=ImageDraw.Draw(b)
        for x,y in ((128,270),(384,270)): d.ellipse([x-46,y-30,x+46,y+30],fill=(255,90,90,int(140*ex['blush']/100)))
        out.alpha_composite(b.filter(ImageFilter.GaussianBlur(14)))
    for g in ('eyes','brows'):
        for h in 'LR': out.alpha_composite(part(g,spec[g][h]['src'],h,spec[g][h]))
    if ex.get('tears'):
        d=ImageDraw.Draw(out); tear(d,176,238,1,ex['tears']/100); tear(d,336,238,1,ex['tears']/100)
    return out
def frame(layer,box,size,soft=False):
    la=np.array(layer); hm=np.array(Image.fromarray(((np.array(BASE)[...,3]>128)*255).astype(np.uint8)).filter(ImageFilter.MinFilter(15)))>0
    la[~hm,3]=0; layer=Image.fromarray(la)
    img=BASE.copy(); img.alpha_composite(layer)
    a=np.array(layer)[...,3]>6
    m=Image.fromarray((a*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))
    # cleaner eyes: whites lifted towards white, pupils solid
    arr=np.array(img).astype(float); rgb=arr[...,:3]; mx=rgb.max(-1); mn=rgb.min(-1); sat=(mx-mn)/np.maximum(mx,1)
    feat=np.array(layer)[...,3]>128
    white=feat&(sat<0.18)&(mx>110); rgb[white]=np.clip(rgb[white]*1.18+18,0,250)
    pupil=feat&(mx<45); rgb[pupil]=(10,8,8); arr[...,:3]=rgb; img=Image.fromarray(arr.astype(np.uint8))
    c=img.crop(box).resize(size,Image.LANCZOS); mk=np.array(m.crop(box).resize(size,Image.BILINEAR))>60
    c=np.array(c)
    if soft:                                   # anti-aliased edge: the hard mask blurred at full size, area-averaged down
        sm=m.filter(ImageFilter.GaussianBlur(1.5))     # same shape as the hard mask (creases stay opaque), smooth edge
        c[...,3]=np.array(sm.crop(box).resize(size,Image.BOX)); return Image.fromarray(c)
    c[...,3]=np.where(mk,255,0); return Image.fromarray(c)
def blush_variant(spec,eyes):
    s=json.loads(json.dumps(spec)); s['eyes']['L']['src']=s['eyes']['R']['src']=eyes; return s
E=dict(S['eyes'])
EYE_MAP={0:'Normal · open',1:'Normal · half',2:'Normal · closed',6:'Angry · open',7:'Angry · half',8:'Angry · closed',
 9:'Happy (eyes shut)',10:'Happy (eyes shut)',11:'Happy (eyes shut)',12:'Blushing',13:('Blushing','Blink half'),14:('Blushing','Blink (closed)'),
 18:'Sad · open',19:'Sad · half',20:'Crying (tears)',30:'Sleeping',54:'Surprised · open',55:'Surprised · half',56:'Surprised · closed',57:'Wink'}
MOUTH_MAP={0:'Neutral · closed',1:'Neutral · talking',2:'Surprised · open',4:'Smile · closed',5:'Smile · talking',7:'Angry · closed',8:'Angry · shouting',9:'Sad · closed',10:'Sad · talking'}
M=dict(S['mouth'])
def eye_frames():
    out={}
    for i,k in EYE_MAP.items():
        spec=blush_variant(E[k[0]],k[1]) if isinstance(k,tuple) else E[k]
        if SOFT_EYES and i not in EYES_USED: continue      # never shown: the slot shows frame 0 (smaller file)
        out[i]=frame(layers_eyes(spec),EYE_BOX,EYE_SIZE,SOFT_EYES)
    return out
SOFT_MOUTH=os.environ.get('JOE_SOFTMOUTH')=='1'
SOFT_EYES=os.environ.get('JOE_SOFTEYES')=='1'    # soft eyes: only the blink frames Joe shows (normal 0-2, angry 6-8, sad 18-20), RGB5A3
EYES_USED={0,1,2,6,7,8,18,19,20}   # soft edges (stored uncompressed, see joe_game.py)
def mouth_frames():
    return {i:frame(part('mouth',M[k]),MOUTH_BOX,MOUTH_SIZE,SOFT_MOUTH) for i,k in MOUTH_MAP.items()}
if __name__=='__main__':
    ef=eye_frames(); mf=mouth_frames()
    o=Image.new('RGBA',(70*len(ef),130),(200,215,225,255))
    for j,(i,im) in enumerate(sorted(ef.items())): o.alpha_composite(im.resize((64,56)),(70*j,0))
    for j,(i,im) in enumerate(sorted(mf.items())): o.alpha_composite(im,(70*j,70))
    o.resize((o.width*2,o.height*2),Image.NEAREST).save('frames_check.png')
