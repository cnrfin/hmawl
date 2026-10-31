import json, base64, io, math, numpy as np
from PIL import Image, ImageDraw, ImageFilter
L=json.load(open('../emotis/parts_lib.json'))
lib={}
for g,ps in L['lib'].items():
    seen={}
    for p in ps:
        n=p['name']
        if n in seen: seen[n]+=1; n=f"{n} {seen[n]}"
        else: seen[n]=1
        lib[(g,n)]=(p,Image.open(io.BytesIO(base64.b64decode(p['png']))).convert('RGBA'))
BASE=Image.open(io.BytesIO(base64.b64decode(L['base']))).convert('RGBA')
def part(g,src,half=None,t=None):
    p,im=lib[(g,src)]; t=t or {}
    layer=Image.new('RGBA',(512,512),(0,0,0,0)); layer.alpha_composite(im,(p['x'],p['y']))
    if half:
        m=Image.new('L',(512,512),0); ImageDraw.Draw(m).rectangle([0,0,255,511] if half=='L' else [256,0,511,511],fill=255)
        a=np.array(layer); a[...,3]=np.minimum(a[...,3],np.array(m)); layer=Image.fromarray(a)
    dx,dy,s,r,f=t.get('dx',0),t.get('dy',0),t.get('s',1),t.get('r',0),t.get('f',False)
    if (dx,dy,s,r,f)!=(0,0,1,0,False):
        x0,x1=p['x'],p['x']+p['w']
        if half=='L': x1=min(x1,256)
        if half=='R': x0=max(x0,256)
        px,py=(x0+x1)/2,p['y']+p['h']/2
        if f: layer=layer.transpose(Image.FLIP_LEFT_RIGHT); px=512-px
        layer=layer.resize((round(512*s),)*2,Image.LANCZOS); px*=s; py*=s
        out=Image.new('RGBA',(512,512),(0,0,0,0)); 
        layer=layer.rotate(-r,center=(px,py),resample=Image.BICUBIC)
        out.alpha_composite(layer,(round(px*0+ (px/s if False else 0)),0)) if False else None
        out=Image.new('RGBA',(1024,1024),(0,0,0,0)); out.alpha_composite(layer,(int(512+(px/s)+dx-px- (px/s - px/s)),0)) if False else None
        canvas=Image.new('RGBA',(512,512),(0,0,0,0))
        ox=round((px/s)+dx-px); oy=round((py/s)+dy-py)
        canvas.paste(layer,(ox,oy),layer); layer=canvas
    return layer
def tear(d,x,y,s,a):
    pts=[]
    for k in range(40):
        th=2*math.pi*k/40; r=9*s
        pts.append((x+r*math.sin(th)*0.9,y+r*(math.cos(th)) if math.cos(th)>0 else y+r*math.cos(th)*1.6))
    d.polygon(pts,fill=(124,195,255,int(255*a)),outline=(47,127,201,int(255*a)))
def face(spec):
    img=BASE.copy(); head=np.array(BASE)[...,3]>128
    over=Image.new('RGBA',(512,512),(0,0,0,0))
    ex=spec.get('extras',{})
    if ex.get('blush'):
        b=Image.new('RGBA',(512,512),(0,0,0,0)); d=ImageDraw.Draw(b)
        for x,y in ((128,270),(384,270)): d.ellipse([x-46,y-30,x+46,y+30],fill=(255,90,90,int(140*ex['blush']/100)))
        over.alpha_composite(b.filter(ImageFilter.GaussianBlur(14)))
    over.alpha_composite(part('mouth',spec['mouth']['src'],None,spec['mouth']))
    for g in ('eyes','brows'):
        for h in ('L','R'): over.alpha_composite(part(g,spec[g][h]['src'],h,spec[g][h]))
    a=np.array(over); a[~head,3]=0; img.alpha_composite(Image.fromarray(a))
    if ex.get('tears'):
        t=Image.new('RGBA',(512,512),(0,0,0,0)); d=ImageDraw.Draw(t); tear(d,176,238,1,ex['tears']/100); tear(d,336,238,1,ex['tears']/100); img.alpha_composite(t)
    return img
def F(b,e,m,x=None,eL=None,eR=None,bL=None,bR=None):
    T=lambda s:{'src':s}
    return {'brows':{'L':T(bL or b),'R':T(bR or b)},'eyes':{'L':T(eL or e),'R':T(eR or e)},'mouth':T(m),'extras':x or {}}
