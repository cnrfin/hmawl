import sys, json, numpy as np
sys.path.insert(0,'.')
from compose import *
from PIL import Image, ImageFilter
S=json.load(open('final_set.json'))
EYE_BOX=(104,30,412,298); MOUTH_BOX=(72,222,504,508)
EYE_SIZE=(80,64); MOUTH_SIZE=(80,56)
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
def frame(layer,box,size):
    la=np.array(layer); hm=np.array(Image.fromarray(((np.array(BASE)[...,3]>128)*255).astype(np.uint8)).filter(ImageFilter.MinFilter(15)))>0
    la[~hm,3]=0; layer=Image.fromarray(la)
    img=BASE.copy(); img.alpha_composite(layer)
    a=np.array(layer)[...,3]>6
    m=Image.fromarray((a*255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))
    c=img.crop(box).resize(size,Image.LANCZOS); mk=np.array(m.crop(box).resize(size,Image.BILINEAR))>60
    c=np.array(c); c[...,3]=np.where(mk,255,0); return Image.fromarray(c)
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
        out[i]=frame(layers_eyes(spec),EYE_BOX,EYE_SIZE)
    return out
def mouth_frames():
    return {i:frame(part('mouth',M[k]),MOUTH_BOX,MOUTH_SIZE) for i,k in MOUTH_MAP.items()}
if __name__=='__main__':
    ef=eye_frames(); mf=mouth_frames()
    o=Image.new('RGBA',(70*len(ef),130),(200,215,225,255))
    for j,(i,im) in enumerate(sorted(ef.items())): o.alpha_composite(im.resize((64,56)),(70*j,0))
    for j,(i,im) in enumerate(sorted(mf.items())): o.alpha_composite(im,(70*j,70))
    o.resize((o.width*2,o.height*2),Image.NEAREST).save('frames_check.png')
