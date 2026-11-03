exec(open('/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/boy/strafe.py').read().split("if __name__")[0])
import sys
IDLE=[np.array(m) for m in pose.locals_at(nodes,idle,0)]
def Ry(a): c,s=np.cos(a),np.sin(a); return np.array([[c,0,s],[0,1,0],[-s,0,c]])
def Rx(a): c,s=np.cos(a),np.sin(a); return np.array([[1,0,0],[0,c,-s],[0,s,c]])
def to_locals(W): return [np.linalg.inv(W[nodes[n]['parent']])@W[n] if nodes[n]['parent']>=0 else W[n].copy() for n in range(NN)]
def sm(x): x=min(max(x,0),1); return x*x*(3-2*x)
EASE={'io':lambda t:t*t*(3-2*t),'out':lambda t:1-(1-t)**3,
      'back':lambda t:1+2.2*(t-1)**3+1.2*(t-1)**2,'in':lambda t:t*t}
R_SH,R_EL,R_WR=33,35,36; L_SH,L_EL,L_WR=22,24,25
SPINE={18:0.40,19:0.35,20:0.25}; HEAD=43   # waist carries most of the twist; HEAD=43
REST_R=(-0.12,-0.24,0.04); REST_L=(0.12,-0.24,0.04)
GUARD_L=(0.06,-0.17,0.16); PULL_L=(0.13,-0.20,-0.06)
PR_DOWN=(-0.6,-0.6,-0.45); PR_UP=(-0.85,0.25,-0.45); PL=(0.6,-0.6,-0.3)
# key: frame, right wrist (shoulder-relative, chest frame; +x his left, +y up, +z forward), right pole, left wrist,
#      twist deg (+ turns his chest to his left), lean deg (+ forward), ease into this key
HITS={
 1:[(0,REST_R,PR_DOWN,REST_L,0,0,'io'),
    (5,(-0.26,0.06,-0.04),PR_DOWN,GUARD_L,-60,-8,'io'),
    (8,(0.0,-0.02,0.28),PR_DOWN,PULL_L,15,12,'back'),
    (11,(0.24,-0.08,0.10),PR_DOWN,PULL_L,62,14,'out'),
    (19,REST_R,PR_DOWN,REST_L,0,0,'io')],
 2:[(0,(0.24,-0.08,0.10),PR_DOWN,PULL_L,62,14,'io'),
    (3,(0.22,0.04,0.12),PR_DOWN,GUARD_L,70,6,'io'),
    (6,(0.0,-0.02,0.28),PR_DOWN,PULL_L,0,12,'back'),
    (9,(-0.26,-0.04,0.06),PR_DOWN,PULL_L,-58,10,'out'),
    (17,REST_R,PR_DOWN,REST_L,0,0,'io')],
 3:[(0,(-0.26,-0.04,0.06),PR_DOWN,PULL_L,-58,10,'io'),
    (10,(-0.08,0.27,-0.02),PR_UP,GUARD_L,-45,-18,'io'),
    (13,(0.0,-0.06,0.27),PR_DOWN,PULL_L,12,26,'back'),
    (17,(0.14,-0.22,0.12),PR_DOWN,PULL_L,35,30,'out'),
    (30,REST_R,PR_DOWN,REST_L,0,0,'io')],
}
CHAIN={1:11,2:9}      # frame of hit k at which hit k+1 may start
# blade direction per key (same frames as HITS; body frame), None = the idle hand's own; the edge leads the swing
BLADE={
 1:[None,(-0.6,0.35,-0.72),(0.45,-0.05,0.89),(0.88,-0.15,-0.45),None],
 2:[(0.88,-0.15,-0.45),(0.8,0.25,-0.55),(-0.4,-0.05,0.91),(-0.9,-0.15,-0.4),None],
 3:[(-0.9,-0.15,-0.4),(-0.12,0.62,-0.78),(0.08,-0.3,0.95),(0.15,-0.6,0.78),None],
}
ATTACH=37                        # the weapon model hangs off the hand bone (handle +y, edge +z)
def cr(p0,p1,p2,p3,u):
    return 0.5*((2*p1)+(-p0+p2)*u+(2*p0-5*p1+4*p2-p3)*u*u+(-p0+3*p1-3*p2+p3)*u**3)
def sample(keys,f):
    f=min(max(f,0),keys[-1][0]); k=0
    while k<len(keys)-2 and f>keys[k+1][0]: k+=1
    f0,f1=keys[k][0],keys[k+1][0]; t=(f-f0)/(f1-f0); u=EASE[keys[k+1][6]](t)
    P=[np.array(x[1],float) for x in keys]; i0=max(k-1,0); i3=min(k+2,len(keys)-1)
    hr=cr(P[i0],P[k],P[k+1],P[i3],u)
    lin=lambda j: np.array(keys[k][j],float)*(1-u)+np.array(keys[k+1][j],float)*u
    return hr,lin(2),lin(3),float(lin(4)),float(lin(5))
def ik(W,sh,el,wr,T,pole):
    S_=W[sh][:3,3]; E=W[el][:3,3]; Wr=W[wr][:3,3]; a=np.linalg.norm(E-S_); b=np.linalg.norm(Wr-E)
    d=T-S_; dl=min(max(np.linalg.norm(d),abs(a-b)+1e-3),a+b-1e-3); u=d/np.linalg.norm(d)
    p=np.array(pole,float); p=p-u*np.dot(p,u); p/=np.linalg.norm(p)
    x=(a*a-b*b+dl*dl)/(2*dl); y=np.sqrt(max(a*a-x*x,0)); Ek=S_+u*x+p*y
    apply_about(W,subtree(sh),rot_between(E-S_,Ek-S_),S_)
    E1=W[el][:3,3]; W1=W[wr][:3,3]; apply_about(W,subtree(el),rot_between(W1-E1,S_+u*dl-E1),E1)
def nrm(v): v=np.asarray(v,float); return v/np.linalg.norm(v)
def slerpv(a,b,u):
    a,b=nrm(a),nrm(b); c=np.clip(a@b,-1,1); th=np.arccos(c)
    if th<1e-4: return nrm(a*(1-u)+b*u)
    return (np.sin((1-u)*th)*a+np.sin(u*th)*b)/np.sin(th)
_IDLE_B=None
def idle_blade():
    global _IDLE_B
    if _IDLE_B is None: _IDLE_B=nrm(world(nodes,IDLE)[ATTACH][:3,:3]@np.array([0,1.0,0]))
    return _IDLE_B
def blade_at(h,f):
    keys=HITS[h]; B=[idle_blade() if b is None else nrm(b) for b in BLADE[h]]
    f=min(max(f,0),keys[-1][0]); k=0
    while k<len(keys)-2 and f>keys[k+1][0]: k+=1
    t=(f-keys[k][0])/(keys[k+1][0]-keys[k][0]); u=EASE[keys[k+1][6]](t)
    return slerpv(B[k],B[k+1],min(max(u,0),1))
def pose_at(keys,f,lag=1.0):
    W=world(nodes,IDLE)
    _,_,_,tw,le=sample(keys,f)                       # body leads
    hr,pr,hl,_,_=sample(keys,f-lag)                  # arms follow a frame behind
    for b,s in SPINE.items():
        c=W[b][:3,3].copy(); apply_about(W,subtree(b),Ry(np.radians(tw*s))@Rx(np.radians(le*s)),c)
    c=W[HEAD][:3,3].copy(); apply_about(W,subtree(HEAD),Ry(np.radians(-0.45*tw))@Rx(np.radians(-0.5*le)),c)
    Rc=Ry(np.radians(tw))@Rx(np.radians(le))              # body axes turned by the twist / lean (bone axes differ)
    ik(W,R_SH,R_EL,R_WR,W[R_SH][:3,3]+Rc@hr,Rc@pr)
    ik(W,L_SH,L_EL,L_WR,W[L_SH][:3,3]+Rc@hl,Rc@np.array(PL))
    h=[k for k,v in HITS.items() if v is keys]
    if h:                                    # aim the weapon: blade along b, edge along the swing
        h=h[0]; b=Rc@blade_at(h,f-lag); b1=Rc@blade_at(h,f-lag+0.6); b0=Rc@blade_at(h,f-lag-0.6)
        e=b1-b0; e=e-b*(e@b)
        if np.linalg.norm(e)<1e-3:           # holds: keep the edge facing forward
            e=np.array([0,0,1.0])-b*b[2]
            if np.linalg.norm(e)<1e-3: e=np.array([1.0,0,0])-b*b[0]
        e=nrm(e); x=np.cross(b,e); Rw=np.stack([x,b,e],1)      # columns: model x, y (blade), z (edge)
        Rd=Rw@W[ATTACH][:3,:3].T; c=W[R_WR][:3,3].copy(); apply_about(W,subtree(R_WR),Rd,c)
    return to_locals(W)
def layered(base,att,w):
    out=[m.copy() for m in base]
    for n in range(18,NN):
        r=Slerp([0,1],Rot.from_matrix([base[n][:3,:3],att[n][:3,:3]]))([w]).as_matrix()[0]
        out[n][:3,:3]=r; out[n][:3,3]=base[n][:3,3]*(1-w)+att[n][:3,3]*w
    return out
def combo_timeline():                                 # all three chained: (global frame -> hit, local frame)
    seq=[];g=0
    for h in (1,2,3):
        n=CHAIN.get(h,HITS[h][-1][0])
        for lf in range(n+(1 if h==3 else 0)): seq.append((h,lf))
    return seq
from PIL import ImageDraw as _ID
def draw_sw(W,ang,lab,W_=240,H_=280):
    im=draw(W,ang,lab,W_=W_,H_=H_); R=raster.rotX(-0.2)@raster.rotY(ang)
    wr=W[R_WR][:3,3]; el=W[R_EL][:3,3]; sh=W[R_SH][:3,3]; d=(wr-sh)+0.6*(wr-el); d/=np.linalg.norm(d)
    a=R@(wr+d*0.03); b=R@(wr+d*0.48); sc=110; P=lambda p:(W_/2+p[0]*sc,H_-25-p[1]*sc)
    g=_ID.Draw(im); g.line([P(a),P(b)],fill=(90,90,100),width=5); g.line([P(a),P(b)],fill=(220,225,235),width=3); return im
#MAIN
if __name__=='__main__':
    seq=combo_timeline(); end=len(seq); frames=[]
    for t in range(end+20):
        row=Image.new('RGB',(240*3,280),'white'); f=t-4
        for c,(nm,ang,mode) in enumerate((('walking',0.55,'walk'),('standing, side',1.57,'idle'),('game camera (behind), strafing',2.75,'strafe'))):
            if mode=='walk': base=[np.array(m) for m in pose.locals_at(nodes,walk,(t*1.0)%WL)]
            elif mode=='idle': base=[m.copy() for m in IDLE]
            else: base=to_locals(strafe_world((t*1.0)%WL,+1))
            if 0<=f<end:
                h,lf=seq[f]; w=sm((f+1)/3)*sm((end-f)/6)
                Lw=layered(base,pose_at(HITS[h],lf),w); lab=nm+'   HIT %d'%h
            else: Lw=base; lab=nm
            row.paste((draw_sw if 0<=f<end else draw)(world(nodes,Lw),ang,lab,W_=240,H_=280),(240*c,0))
        frames.append(row)
    frames[0].save(sys.argv[1],save_all=True,append_images=frames[1:],duration=33,loop=0); print(end)
