"""Goddess hair from in-game parts: Kate's centre-parted shell, Samantha's front tuft (x2, enlarged),
Samantha's bun (x2), fitted to the blank head; green recolour"""
import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/pm']
import hairstudy as S, restyle, gd2
G='/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/'
GREEN=np.array([(14,50,30),(28,86,52),(52,128,78),(92,166,106),(150,206,150),(210,238,200)],float)
def ramp(keys=GREEN):
    t=np.linspace(0,1,256); xs=np.linspace(0,1,len(keys)); return np.stack([np.interp(t,xs,keys[:,c]) for c in range(3)],1)
SHIFT={("san",197):0.165,("san",329):0.046}
def part(n, comps, ref_face=True, shift=None):
    if shift is None: shift=SHIFT.get((n,comps[0]),0.0)
    M,T,tris,hb=S.hair2(n); V=M['V'].copy(); UV=M['UV']; comp=np.load(G+f'{n}_comp.npy')
    fv=sorted({i for tid,ts,_ in M['groups'] if tid==2 for pi,_ in ts for i in pi}); Fc=M['V'][fv]
    s=0.43/(Fc[:,0].max()-Fc[:,0].min())
    # align: face width, face top (hairline) and face front
    V=(V-[0,Fc[:,1].max(),Fc[:,2].max()])*s+[0,1.30,0.201]
    sel=[t for t,c in zip(tris,comp) if c in comps]
    tex=T[255].copy(); H,W=tex.shape[:2]
    from PIL import Image, ImageDraw
    from scipy.ndimage import binary_dilation
    m=Image.new('L',(W,H),0); d=ImageDraw.Draw(m)
    for pi,ti in sel: d.polygon([((UV[x][0]%1)*W,(UV[x][1]%1)*H) for x in ti],fill=255)
    mask=binary_dilation(np.array(m)>0,iterations=2)
    L=restyle.lum(tex[...,:3]); lo,hi=np.percentile(L[mask],1),np.percentile(L[mask],99.5)
    tex[mask,:3]=ramp()[(np.clip((L[mask]-lo)/(hi-lo)+shift,0,1)*255).astype(int)]
    P=[];Q=[];F=[]
    for pi,ti in sel:
        F.append([len(P),len(P)+1,len(P)+2])
        for p,x in zip(pi,ti): P.append(V[p]); Q.append((UV[x][0]%1,UV[x][1]%1))
    return np.array(P),np.array(Q),np.array(F)[:,::-1],tex,s

def boxfit(P, src_lo, src_hi, dst_lo, dst_hi):
    return dst_lo + (P - src_lo) / (src_hi - src_lo) * (dst_hi - dst_lo)
def kate_shell():
    P,Q,F,tex,_=part('keit',(873,))
    lo,hi=P.min(0),P.max(0)
    P=boxfit(P,lo,hi,np.array([-0.255,0.975,-0.27]),np.array([0.255,1.37,0.205]))
    return gd2.conform(P,F,margin=0.010,ears=False),Q,F,tex

def placed(mesh, origin, at, scale, rot_y=0.0, rot_z=0.0, mirror=False):
    P,Q,F,tex=mesh[:4]; X=(P-origin)*scale
    a=np.radians(rot_y); Ry=np.array([[np.cos(a),0,np.sin(a)],[0,1,0],[-np.sin(a),0,np.cos(a)]])
    b=np.radians(rot_z); Rz=np.array([[np.cos(b),-np.sin(b),0],[np.sin(b),np.cos(b),0],[0,0,1]])
    X=X@(Rz@Ry).T
    if mirror: X[:,0]*=-1; F=F[:,::-1]
    return X+at,Q,F,tex

def align(mesh, origin, at, scale, up_to, mirror=False):
    """rotate the mesh's +y axis onto direction up_to (Rodrigues), scale, move origin to at"""
    P,Q,F,tex=mesh[:4]; X=(P-origin)*scale
    a=np.array([0,1.0,0]); b=np.array(up_to,float); b/=np.linalg.norm(b); v=np.cross(a,b); c=a@b
    K=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]]); R=np.eye(3)+K+K@K/(1+c)
    X=X@R.T
    if mirror: X[:,0]*=-1; F=F[:,::-1]
    return X+at,Q,F,tex

def rot_a_to_b(a,b):
    a=np.array(a,float)/np.linalg.norm(a); b=np.array(b,float)/np.linalg.norm(b); v=np.cross(a,b); c=a@b
    if np.linalg.norm(v)<1e-9: return np.eye(3) if c>0 else -np.eye(3)
    K=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]]); return np.eye(3)+K+K@K/(1+c)
def bun_place(mesh, center, facing, scale, mirror=False, cen=np.array([0,1.08,-0.01])):
    """move the bun so its own outward axis (from the head centre through the bun) points along 'facing';
    'center' is where the bun's middle goes"""
    P,Q,F,tex=mesh[:4]; c=P.mean(0); ax=c-cen
    R=rot_a_to_b(ax,facing); X=((P-c)*scale)@R.T
    if mirror: X[:,0]*=-1; F=F[:,::-1]
    return X+center,Q,F,tex

def bun_place2(mesh, center, facing, scale, axial, cen=np.array([0,1.08,-0.01])):
    """as bun_place, plus a separate stretch 'axial' along the facing direction (how far it sticks out)"""
    P,Q,F,tex=mesh[:4]; c=P.mean(0); ax=c-cen
    fn=np.array(facing,float); fn/=np.linalg.norm(fn)
    X=((P-c)*scale)@rot_a_to_b(ax,fn).T
    X=X+np.outer(X@fn,fn)*(axial/scale-1)
    return X+center,Q,F,tex

def bun_core(mesh, shrink=0.90, rings=7, segs=12):
    """closed inner ellipsoid filling the bun's coil (fitted to the bun's own shape), same strand texture,
    so the slot in the coil shows hair rather than a hole"""
    P,Q,F,tex=mesh[:4]; c=P.mean(0); X=P-c
    w,V=np.linalg.eigh(np.cov(X.T)); ext=np.array([np.percentile(np.abs(X@V[:,k]),95) for k in range(3)])*shrink
    H,W=tex.shape[:2]; uv=Q[F].reshape(-1,2); u0,v0=uv.min(0); u1,v1=uv.max(0)
    um,vm=(u0+u1)/2,(v0+v1)/2; du,dv=(u1-u0)*0.25,(v1-v0)*0.25
    pts=[];uvs=[]
    for i in range(rings+1):
        th=np.pi*i/rings
        for j in range(segs):
            ph=2*np.pi*j/segs; d=np.array([np.sin(th)*np.cos(ph),np.sin(th)*np.sin(ph),np.cos(th)])
            pts.append(c+V@(d*ext)); uvs.append((um+du*np.cos(ph)*np.sin(th),vm+dv*np.sin(ph)*np.sin(th)))
    pts=np.array(pts); uvs=np.array(uvs); Fc=[]
    for i in range(rings):
        for j in range(segs):
            a=i*segs+j; b=i*segs+(j+1)%segs; cc=a+segs; d_=b+segs
            Fc+=[(a,cc,b),(b,cc,d_)]
    Fc=np.array(Fc)
    # outward winding
    n=np.cross(pts[Fc[:,1]]-pts[Fc[:,0]],pts[Fc[:,2]]-pts[Fc[:,0]]); out=(pts[Fc].mean(1)-c)
    flip=(n*out).sum(1)<0; Fc[flip]=Fc[flip][:,::-1]
    return pts,uvs,Fc,tex
def bun_closed(mesh):
    P,Q,F,tex=mesh[:4]; cp,cq,cf,_=bun_core(mesh)
    return np.vstack([P,cp]),np.vstack([Q,cq]),np.vstack([F,cf+len(P)]),tex

def bun_core2(mesh, shrink=0.92, rings=7, segs=12):
    """closed ellipsoid with single pole vertices (no collapsed triangles)"""
    P,Q,F,tex=mesh[:4]; c=P.mean(0); X=P-c
    w,V=np.linalg.eigh(np.cov(X.T)); ext=np.array([np.percentile(np.abs(X@V[:,k]),95) for k in range(3)])*shrink
    uv=Q[F].reshape(-1,2); u0,v0=uv.min(0); u1,v1=uv.max(0); um,vm=(u0+u1)/2,(v0+v1)/2; du,dv=(u1-u0)*0.25,(v1-v0)*0.25
    pts=[c+V@(np.array([0,0,1.0])*ext)]; uvs=[(um,vm)]
    for i in range(1,rings):
        th=np.pi*i/rings
        for j in range(segs):
            ph=2*np.pi*j/segs; d=np.array([np.sin(th)*np.cos(ph),np.sin(th)*np.sin(ph),np.cos(th)])
            pts.append(c+V@(d*ext)); uvs.append((um+du*np.cos(ph)*np.sin(th),vm+dv*np.sin(ph)*np.sin(th)))
    pts.append(c+V@(np.array([0,0,-1.0])*ext)); uvs.append((um,vm)); bot=len(pts)-1
    ring=lambda i,j: 1+(i-1)*segs+j%segs; Fc=[]
    for j in range(segs): Fc.append((0,ring(1,j),ring(1,j+1)))
    for i in range(1,rings-1):
        for j in range(segs):
            a,b,cc,d_=ring(i,j),ring(i,j+1),ring(i+1,j),ring(i+1,j+1); Fc+=[(a,cc,b),(b,cc,d_)]
    for j in range(segs): Fc.append((bot,ring(rings-1,j+1),ring(rings-1,j)))
    Fc=np.array(Fc); pts=np.array(pts)
    n=np.cross(pts[Fc[:,1]]-pts[Fc[:,0]],pts[Fc[:,2]]-pts[Fc[:,0]]); flip=(n*(pts[Fc].mean(1)-c)).sum(1)<0; Fc[flip]=Fc[flip][:,::-1]
    return pts,np.array(uvs),Fc,tex

def solid_bun(center, facing, length, radius, tex, rings=9, segs=14, twist=0.6, x0=18, x1=54, y0=3, y1=22, base_r=0.85, turns=3.0):
    """closed coiled bun: an egg along 'facing' (base against the head, rounded tip), strands wrapping round
    it in a spiral (Samantha's bun stripes), single pole vertices"""
    H,W=tex.shape[:2]; fn=np.array(facing,float); fn/=np.linalg.norm(fn)
    a=np.cross(fn,[0,1,0]); a/=np.linalg.norm(a); b=np.cross(fn,a)
    def prof(t): return radius*(np.sin(np.pi*t)**0.75)*(base_r+(1-base_r)*min(1,t*2.5))
    def uv(t,ph):
        s=((ph/np.pi+twist*t)%2.0); s=1-abs(s-1)                     # along the strands: round the bun (mirrored, seamless)
        q=(t*turns+ph/(2*np.pi))%2.0; q=1-abs(q-1)                    # across the strands: a spiral climbing the bun
        return ((x0+(x1-x0)*s)/W,(y0+(y1-y0)*q)/H)
    pts=[center-fn*length*0.5]; uvs=[uv(0,0)]
    for i in range(1,rings):
        t=i/rings
        for j in range(segs):
            ph=2*np.pi*j/segs; r=prof(t)
            pts.append(center+fn*length*(t-0.5)+(a*np.cos(ph)+b*np.sin(ph))*r); uvs.append(uv(t,ph))
    pts.append(center+fn*length*0.5); uvs.append(uv(1,0)); tip=len(pts)-1
    ring=lambda i,j: 1+(i-1)*segs+j%segs; F=[]
    for j in range(segs): F.append((0,ring(1,j+1),ring(1,j)))
    for i in range(1,rings-1):
        for j in range(segs):
            p,q,r_,s_=ring(i,j),ring(i,j+1),ring(i+1,j),ring(i+1,j+1); F+=[(p,q,r_),(q,s_,r_)]
    for j in range(segs): F.append((tip,ring(rings-1,j),ring(rings-1,j+1)))
    pts=np.array(pts); F=np.array(F)
    n=np.cross(pts[F[:,1]]-pts[F[:,0]],pts[F[:,2]]-pts[F[:,0]]); flip=(n*(pts[F].mean(1)-center)).sum(1)<0; F[flip]=F[flip][:,::-1]
    return pts,np.array(uvs),F,tex

def coil_texture(src, x0=18, x1=54, y0=3, y1=22, W=32, H=32, seed=3):
    """small seamless (both ways) strand texture from Samantha's bun: her strand profile across v made
    periodic, constant along u apart from slight variation"""
    from PIL import Image
    blk=src[y0:y1,x0:x1,:3]; prof=blk.mean(1)                       # colour across the strands
    n=len(prof); prof=np.concatenate([prof,prof[::-1]],0)          # mirror -> periodic profile
    p=np.array(Image.fromarray(prof[:,None,:].repeat(2,1).astype(np.uint8)).resize((2,H),Image.BICUBIC)).astype(float)[:,0]
    rng=np.random.RandomState(seed); var=np.cumsum(rng.uniform(-1,1,W)); var=(var-np.linspace(var[0],var[-1],W))*0.02
    t=np.zeros((H,W,4)); t[...,3]=255
    for x in range(W): t[:,x,:3]=np.clip(np.roll(p,int(round(var[x]*H)),0),0,255)
    return t
def solid_bun2(center, facing, length, radius, ctex, rings=9, segs=16, turns=2.5, around=2.0, base_r=0.85):
    """same closed egg as solid_bun; texture spirals round the axis with no fold (seamless coil texture)"""
    fn=np.array(facing,float); fn/=np.linalg.norm(fn)
    a=np.cross(fn,[0,1,0]); a/=np.linalg.norm(a); b=np.cross(fn,a)
    prof=lambda t: radius*(np.sin(np.pi*t)**0.75)*(base_r+(1-base_r)*min(1,t*2.5))
    P=[center-fn*length*0.5]; Q=[(0.5,0.5)]; F=[]
    for i in range(1,rings):
        t=i/rings
        for j in range(segs+1):                                       # seam column duplicated (u 0..around)
            ph=2*np.pi*j/segs
            P.append(center+fn*length*(t-0.5)+(a*np.cos(ph)+b*np.sin(ph))*prof(t))
            Q.append((around*j/segs, t*turns+j/segs))
    P.append(center+fn*length*0.5); Q.append((0.5,turns+0.5)); tip=len(P)-1
    ring=lambda i,j: 1+(i-1)*(segs+1)+j
    for j in range(segs): F.append((0,ring(1,j+1),ring(1,j)))
    for i in range(1,rings-1):
        for j in range(segs):
            p,q,r_,s_=ring(i,j),ring(i,j+1),ring(i+1,j),ring(i+1,j+1); F+=[(p,q,r_),(q,s_,r_)]
    for j in range(segs): F.append((tip,ring(rings-1,j),ring(rings-1,j+1)))
    P=np.array(P); F=np.array(F)
    n=np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]); flip=(n*(P[F].mean(1)-center)).sum(1)<0; F[flip]=F[flip][:,::-1]
    return P,np.array(Q),F,ctex

def round_bun(center, facing, length, radius, tex, mode='radial', rings=10, segs=16, roundness=0.45,
              kx=(80,120), ky=(146,176), reps=3, ctex=None, turns=0.5):
    """rounder closed bun. mode 'radial': Kate's own texture sheet, strands running from the base round to the
    tip (like hair gathered into a bun), mirrored side to side 'reps' times round; 'coil': spiral coil texture"""
    fn=np.array(facing,float); fn/=np.linalg.norm(fn)
    a=np.cross(fn,[0,1,0]); a/=np.linalg.norm(a); b=np.cross(fn,a)
    prof=lambda t: radius*np.sin(np.pi*t)**roundness
    H,W=tex.shape[:2]
    def uv(t,j):
        if mode=='coil': return (2.0*j/segs, t*turns+j/segs)
        s=(reps*2*j/segs)%2.0; s=1-abs(s-1)
        return ((kx[0]+(kx[1]-kx[0])*s)/W,(ky[0]+(ky[1]-ky[0])*t)/H)
    P=[center-fn*length*0.5]; Q=[uv(0,0)]; F=[]
    for i in range(1,rings):
        t=i/rings
        for j in range(segs+1):
            ph=2*np.pi*j/segs; P.append(center+fn*length*(t-0.5)+(a*np.cos(ph)+b*np.sin(ph))*prof(t)); Q.append(uv(t,j))
    P.append(center+fn*length*0.5); Q.append(uv(1,0)); tip=len(P)-1
    ring=lambda i,j: 1+(i-1)*(segs+1)+j
    for j in range(segs): F.append((0,ring(1,j+1),ring(1,j)))
    for i in range(1,rings-1):
        for j in range(segs):
            p,q,r_,s_=ring(i,j),ring(i,j+1),ring(i+1,j),ring(i+1,j+1); F+=[(p,q,r_),(q,s_,r_)]
    for j in range(segs): F.append((tip,ring(rings-1,j),ring(rings-1,j+1)))
    P=np.array(P); F=np.array(F); Q=np.array(Q)
    # pole vertices: give each pole triangle its own pole copy with the matching uv (no smeared fan)
    if mode=='radial':
        P=list(P); Q=list(Q); F=[list(f) for f in F]
        for f in F:
            for k in range(3):
                if f[k] in (0,tip):
                    other=[x for x in f if x not in (0,tip)]; u=np.mean([Q[x][0] for x in other])
                    P.append(P[f[k]]); Q.append((u,Q[f[k]][1])); f[k]=len(P)-1
        P=np.array(P); Q=np.array(Q); F=np.array(F)
    n=np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]]); flip=(n*(P[F].mean(1)-center)).sum(1)<0; F[flip]=F[flip][:,::-1]
    return P,Q,F,(ctex if mode=='coil' else tex)

def kate_ramp(tex):
    """colour ramp (dark->light) from the main hair's own strand texels"""
    px=tex[146:176,80:120,:3].reshape(-1,3); L=px@[0.3,0.59,0.11]; o=np.argsort(L); px=px[o]
    idx=np.linspace(0,len(px)-1,256).astype(int); r=np.array([px[max(0,i-20):i+21].mean(0) for i in idx])
    return r
def twist_texture(tex, W=64, H=64, clumps=3, seed=4):
    """seamless (both directions) twisted-strand texture in the main hair's colours: rounded clumps with
    dark grooves, fine strands, a soft highlight along each clump"""
    rng=np.random.RandomState(seed)
    u,v=np.meshgrid(np.arange(W)/W,np.arange(H)/H)
    tp=2*np.pi
    s=v*clumps+0.08*np.sin(tp*u)+0.05*np.sin(tp*2*u+1.0)          # clump coordinate (wavy, periodic)
    t=s%1.0; body=np.sin(np.pi*t)**0.6
    fine=np.zeros_like(u)
    for f,a in ((clumps*4,0.07),(clumps*7,0.05),(clumps*11,0.035)):
        fine+=a*np.sin(tp*(f*v)+0.6*np.sin(tp*(u*rng.randint(1,3))+rng.uniform(0,tp))+rng.uniform(0,tp))
    hi=np.exp(-((t-0.42)/0.12)**2)*(0.6+0.4*np.sin(tp*u*2+rng.uniform(0,tp)))
    L=0.22+0.55*body+fine+0.25*hi
    L=(L-L.min())/(L.max()-L.min())
    r=kate_ramp(tex); out=np.zeros((H,W,4)); out[...,3]=255; out[...,:3]=r[(np.clip(L,0,1)*255).astype(int)]
    return out
