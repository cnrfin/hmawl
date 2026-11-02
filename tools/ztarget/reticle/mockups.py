import math
from PIL import Image, ImageDraw
BG=Image.open('bg.png').convert('RGBA'); CX,CY=319,298; HEAD=CY-48; FEET=CY+58
Y=(255,206,46)          # flat yellow
S=3                     # supersample
def ease_out_back(t,o=1.6):
    t=min(max(t,0),1); t-=1; return t*t*((o+1)*t+o)+1
def ease_out(t): t=min(max(t,0),1); return 1-(1-t)**3
def tri(d,cx,cy,ang,size,alpha):     # triangle pointing toward (cx,cy) from angle ang (its tip at radius)
    pass
def layer(): return Image.new('RGBA',(640*S,480*S),(0,0,0,0))
def poly(d,pts,a): d.polygon([(x*S,y*S) for x,y in pts],fill=Y+(a,))
def A_petals(t):                      # 4 triangles closing in, then breathing
    L=layer(); d=ImageDraw.Draw(L); k=ease_out_back(t/0.35); r=70+(24-70)*k
    if t>0.35: r=24+2*math.sin((t-0.35)*2*math.pi/1.2)
    a=int(255*min(1,t/0.15)); s=11
    for ang in (0,90,180,270):
        c,sn=math.cos(math.radians(ang)),math.sin(math.radians(ang))
        tip=(CX+c*r,CY+sn*r); base=(CX+c*(r+s*1.6),CY+sn*(r+s*1.6)); px,py=-sn*s,c*s
        poly(d,[tip,(base[0]+px,base[1]+py),(base[0]-px,base[1]-py)],a)
    return L
def B_brackets(t):                    # 4 corner brackets snapping in
    L=layer(); d=ImageDraw.Draw(L); k=ease_out_back(t/0.3,2.0); h=60+(30-60)*k
    if t>0.3: h=30+1.5*math.sin((t-0.3)*2*math.pi/1.4)
    a=int(255*min(1,t/0.12)); l=12; w=4
    for sx in (-1,1):
        for sy in (-1,1):
            x0,y0=CX+sx*h,CY+sy*h*1.15
            poly(d,[(x0,y0),(x0-sx*l,y0),(x0-sx*l,y0-sy*w),(x0,y0-sy*w)],a)
            poly(d,[(x0,y0),(x0,y0-sy*l),(x0-sx*w,y0-sy*l),(x0-sx*w,y0)],a)
    return L
def C_spinner(t):                     # OoT-like: 4 triangles spinning in, then slow spin
    L=layer(); d=ImageDraw.Draw(L); k=ease_out(t/0.4); r=80+(26-80)*k
    if t>0.4: r=26
    spin=360*(1-k)*1.5+ (t*90)               # fast while closing, then 90 deg/s
    a=int(255*min(1,t/0.15)); s=10
    for i in range(4):
        ang=math.radians(spin+90*i+45); c,sn=math.cos(ang),math.sin(ang)
        tip=(CX+c*r,CY+sn*r); base=(CX+c*(r+s*1.7),CY+sn*(r+s*1.7)); px,py=-sn*s,c*s
        poly(d,[tip,(base[0]+px,base[1]+py),(base[0]-px,base[1]-py)],a)
    return L
def D_arrow(t):                       # chevron dropping onto the head, bobbing; flat ring at the feet
    L=layer(); d=ImageDraw.Draw(L); k=ease_out_back(t/0.4,2.2); y=HEAD-60+(HEAD-14-(HEAD-60))*k
    if t>0.4: y=HEAD-14-4*abs(math.sin((t-0.4)*math.pi/0.7))
    a=int(255*min(1,t/0.15)); w=13
    poly(d,[(CX-w,y-14),(CX+w,y-14),(CX,y+6)],a)
    rk=ease_out(t/0.3); rx,ry=26*rk+6,7*rk+2; a2=int(200*min(1,t/0.2))
    d.ellipse([((CX-rx)*S,(FEET-ry)*S),((CX+rx)*S,(FEET+ry)*S)],fill=Y+(a2,))
    if rx>8 and ry>3: d.ellipse([((CX-rx+6)*S,(FEET-ry+2.2)*S),((CX+rx-6)*S,(FEET+ry-2.2)*S)],fill=(0,0,0,0))
    return L
def frame(fn,t,label):
    L=fn(t).resize((640,480),Image.LANCZOS); im=BG.copy(); im.alpha_composite(L)
    im=im.convert('RGB'); ImageDraw.Draw(im).rectangle([0,0,640,26],fill=(20,20,20)); ImageDraw.Draw(im).text((8,7),label,fill=(255,255,255)); return im
V=[(A_petals,'A  Petals: 4 triangles close in, then breathe'),(B_brackets,'B  Brackets: corner frame snaps in'),
   (C_spinner,'C  Spinner: OoT-style, spins in then slow spin'),(D_arrow,'D  Arrow: drops onto the head + ring at the feet')]
frames=[]
for i in range(0,66,2):
    t=i/30.0; g=Image.new('RGB',(960,720))
    for k,(fn,lab) in enumerate(V): g.paste(frame(fn,t,lab).resize((480,360),Image.LANCZOS),((k%2)*480,(k//2)*360))
    frames.append(g.resize((800,600),Image.LANCZOS).quantize(colors=200,method=Image.Quantize.MEDIANCUT))
frames[0].save('reticles.gif',save_all=True,append_images=frames[1:]+[frames[-1]]*6,duration=66,loop=0,optimize=True)
st=Image.new('RGB',(1280,960))
for k,(fn,lab) in enumerate(V): st.paste(frame(fn,1.3,lab),((k%2)*640,(k//2)*480))
st.save('reticles_still.png'); print('ok')
