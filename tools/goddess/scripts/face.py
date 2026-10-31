"""Chris's eyes + mouth on the goddess head: her eye/mouth mesh patches fitted to our head, eye texture frames
recoloured blue -> lavender"""
import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/pm']
import awlmodel, wally, gd2
import colorsys
KP='/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/girls/kuri_0/kuri_0'
def lavender(img, hue=268/360., sat_scale=0.75, lo=170/360., hi=255/360.):
    out=img.copy(); H,W=img.shape[:2]
    for y in range(H):
        for x in range(W):
            r,g,b=img[y,x,:3]/255.
            h,s,v=colorsys.rgb_to_hsv(r,g,b)
            if lo<=h<=hi and s>0.18:
                r2,g2,b2=colorsys.hsv_to_rgb(hue,s*sat_scale,v); out[y,x,:3]=np.array([r2,g2,b2])*255
    return out
def patches():
    M=awlmodel.load(KP); V=M['V']; UV=M['UV']
    face=[t for tid,ts,_ in M['groups'] if tid==2 for t in ts]
    fv=sorted({i for pi,_ in face for i in pi}); Fc=V[fv]
    s=0.43/(Fc[:,0].max()-Fc[:,0].min())
    def fit(P): return (P-[0,Fc[:,1].min(),Fc[:,2].max()])*s+[0,0.871,0.201]
    out={}
    for tid in (0,1):
        ts=[t for g,tt,_ in M['groups'] if g==tid for t in tt]
        P=[];Q=[];F=[]
        for pi,ti in ts:
            F.append([len(P),len(P)+1,len(P)+2])
            for p,x in zip(pi,ti): P.append(fit(V[p])); Q.append((UV[x][0],UV[x][1]))
        P=np.array(P); F=np.array(F)[:,::-1]
        # project onto our head surface, just above it
        cen=np.array([0,1.08,0.0])
        for _ in range(20):
            d=gd2.head_sdf(P,ears=False); g=gd2.head_grad(P,ears=False); P=P-g*(d-0.0025)[:,None]
        out[tid]=(P,np.array(Q),F)
    return out

def match_skin(img, target):
    """the face-part textures carry Chris's skin around the features: tint them to our body skin"""
    px=img[...,:3].reshape(-1,3); src=np.median(px,0)                   # the dominant (skin) colour
    ratio=np.array(target,float)/src
    out=img.copy()
    d=np.abs(img[...,:3]-src).sum(-1); w=np.clip(1-d/120,0,1)[...,None]      # near-skin pixels fully, features less
    out[...,:3]=img[...,:3]*(ratio*w+(1-w)*(1+(ratio-1)*0.6))
    return out.clip(0,255)
def body_skin(S):
    return S[62,60,:3]

# AWL layout (measured on Muffy, Nami, Flora, Samantha; fractions of chin->skull-top height H and head width W):
# eyes: centre 0.49 H above the chin, patch height 0.50 H, each eye patch from x 0.04 to 0.76 (half-width units)
# mouth: centre 0.20 H, height 0.31 H, width 0.62 W
LAYOUT=dict(eye_c=0.49,eye_h=0.50,eye_x=(0.04,0.76),mouth_c=0.20,mouth_h=0.31,mouth_w=0.62)
def patches2(chin=0.868, top=1.328, W=0.462, L=LAYOUT, lift=0.0025):
    M=awlmodel.load(KP); V=M['V']; UV=M['UV']; H=top-chin; out={}
    for tid in (0,1):
        ts=[t for g,tt,_ in M['groups'] if g==tid for t in tt]
        idx=sorted({i for pi,_ in ts for i in pi}); S=V[idx]
        P=[];Q=[];F=[]
        for pi,ti in ts:
            F.append([len(P),len(P)+1,len(P)+2])
            for p,x in zip(pi,ti): P.append(V[p].copy()); Q.append((UV[x][0],UV[x][1]))
        P=np.array(P); F=np.array(F)[:,::-1]
        y0,y1=S[:,1].min(),S[:,1].max()
        if tid==0:
            ax=np.abs(S[:,0]); a0,a1=ax.min(),ax.max()
            sgn=np.sign(P[:,0]); t=(np.abs(P[:,0])-a0)/(a1-a0)
            P[:,0]=sgn*(L['eye_x'][0]+t*(L['eye_x'][1]-L['eye_x'][0]))*W/2
            yc,hh=L['eye_c'],L['eye_h']
        else:
            x0,x1=S[:,0].min(),S[:,0].max(); P[:,0]=(P[:,0]-(x0+x1)/2)/(x1-x0)*L['mouth_w']*W
            yc,hh=L['mouth_c'],L['mouth_h']
        P[:,1]=chin+(yc+((P[:,1]-y0)/(y1-y0)-0.5)*hh)*H
        P[:,2]=0.3
        for _ in range(30):                                        # drop straight back onto the head
            d=gd2.head_sdf(P,ears=False); P[:,2]-=np.maximum(d-lift,-0.05)*0.8
        out[tid]=(P,np.array(Q),F)
    return out

def chris_face(chin=0.868, top=1.328, W=0.462, lift=0.0015):
    """the game's technique: the face mesh has holes where the eyes and mouth go, and the eye/mouth triangles
    fill them (sharing the edge vertices), UVs spanning the whole eye/mouth texture. Take Chris's face mesh
    (skin + eyes + mouth, one connected surface), fit it to our head: per-axis box fit (chin, skull top,
    width), then drop each vertex straight back onto our head's surface"""
    M=awlmodel.load(KP); V=M['V']; UV=M['UV']
    g={}
    for tid,ts,_ in M['groups']: g.setdefault(tid,[]).extend(ts)
    face=V[sorted({i for pi,_ in g[2] for i in pi})]
    cen=face[(np.abs(face[:,0])<0.04)&(face[:,2]>0.05)]
    # Chris's real chin (front, below the mouth) and skull top
    mo=V[sorted({i for pi,_ in g[1] for i in pi})]
    c_chin=cen[cen[:,1]<mo[:,1].min()][:,1].max() if False else cen[(cen[:,1]<mo[:,1].min())][:,1].min()
    c_top=face[:,1].max(); c_W=2*np.abs(face[(face[:,1]>c_chin+0.1)&(face[:,1]<c_chin+0.3),0]).max()
    out={}
    for tid in (2,0,1):
        ts=[t for t in g[tid] if V[list(t[0])].mean(0)[1]>c_chin-0.02 and V[list(t[0])].mean(0)[2]>-0.02]
        P=[];Q=[];F=[];key={}
        for pi,ti in ts:
            idx=[]
            for p,x in zip(pi,ti):
                k=(p,x)
                if k not in key: key[k]=len(P); P.append(V[p].copy()); Q.append((UV[x][0]%1 if tid==2 else UV[x][0],UV[x][1]%1 if tid==2 else UV[x][1]))
                idx.append(key[k])
            F.append(idx)
        P=np.array(P); F=np.array(F)[:,::-1]
        P[:,0]=P[:,0]/c_W*W
        P[:,1]=chin+(P[:,1]-c_chin)/(c_top-c_chin)*(top-chin)
        z0=P[:,2].copy(); P[:,2]=0.35
        for _ in range(40):
            d=gd2.head_sdf(P,ears=False); P[:,2]-=np.maximum(d-lift,-0.05)*0.8
        out[tid]=(P,np.array(Q),F)
    return out,(c_chin,c_top,c_W)

def chris_face2(chin=0.868, top=1.328, W=0.462, L=LAYOUT, lift=0.0015, path=None):
    """as chris_face, but anchored on the AWL layout: Chris's eye centre -> 0.49 H, mouth centre -> 0.20 H,
    eye outer edge -> 0.76 of the half-width; only the face itself is kept (no neck, ears or hairline)"""
    M=awlmodel.load(path or KP); V=M['V']; UV=M['UV']; H=top-chin
    g={}
    for tid,ts,_ in M['groups']: g.setdefault(tid,[]).extend(ts)
    E=V[sorted({i for pi,_ in g[0] for i in pi})]; Mo=V[sorted({i for pi,_ in g[1] for i in pi})]
    ey,my=E[:,1].mean(),Mo[:,1].mean(); ex=np.abs(E[:,0]).max()
    ty_e,ty_m=chin+L['eye_c']*H,chin+L['mouth_c']*H
    sx=(L['eye_x'][1]*W/2)/ex; sy=sx                                 # uniform: keep Chris's own proportions
    ty_m=ty_e-(ey-my)*sy
    out={}
    for tid in (2,0,1):
        P=[];Q=[];F=[];key={}
        for pi,ti in g[tid]:
            c=V[list(pi)].mean(0); my_=ty_m+(c[1]-my)*sy; mx=c[0]*sx
            if tid==2 and (my_<chin-0.004 or my_>top-0.07 or abs(mx)>W/2*0.93 or c[2]<0.02): continue
            idx=[]
            for p,x in zip(pi,ti):
                k=(p,x)
                if k not in key:
                    key[k]=len(P); q=V[p].copy(); q[0]*=sx; q[1]=ty_m+(q[1]-my)*sy; P.append(q)
                    Q.append((UV[x][0]%1,UV[x][1]%1) if tid==2 else (UV[x][0],UV[x][1]))
                idx.append(key[k])
            F.append(idx)
        P=np.array(P); F=np.array(F)[:,::-1]; P[:,2]=0.35
        for _ in range(40):
            d=gd2.head_sdf(P,ears=False); P[:,2]-=np.maximum(d-lift,-0.05)*0.8
        out[tid]=(P,np.array(Q),F)
    return out

def brows_to(img, rgb_dark, rows=14, lo=10/360., hi=55/360.):
    """eyebrows (brown/gold strokes in the top rows of the eye texture) -> the hair's dark green"""
    out=img.copy(); dk=np.array(rgb_dark,float)
    for y in range(min(rows,img.shape[0])):
        for x in range(img.shape[1]):
            r,g,b=img[y,x,:3]/255.; h,s,v=colorsys.rgb_to_hsv(r,g,b)
            if lo<=h<=hi and s>0.35 and v<0.85:
                out[y,x,:3]=dk*(0.6+0.6*v)
    return out.clip(0,255)

def native_face(path, chin=0.868, top=1.328, W=0.462, lift=0.0015, scale=None):
    """Muffy's face at her own proportions: one uniform scale (our head width / hers), her chin on ours"""
    M=awlmodel.load(path); V=M['V']; UV=M['UV']
    g={}
    for tid,ts,_ in M['groups']: g.setdefault(tid,[]).extend(ts)
    face=V[sorted({i for pi,_ in g[2] for i in pi})]
    cen=face[(np.abs(face[:,0])<0.04)&(face[:,2]>0.05)]; mchin=cen[:,1].min()
    mW=2*np.abs(face[(face[:,1]>mchin+0.12)&(face[:,1]<mchin+0.25),0]).max()
    s=scale or W/mW; out={}
    for tid in (2,0,1):
        P=[];Q=[];F=[];key={}
        for pi,ti in g[tid]:
            c=V[list(pi)].mean(0); yy=chin+(c[1]-mchin)*s
            if tid==2 and (yy<chin-0.004 or yy>top-0.07 or abs(c[0]*s)>W/2*0.93 or c[2]<0.02): continue
            idx=[]
            for p,x in zip(pi,ti):
                k=(p,x)
                if k not in key:
                    key[k]=len(P); q=V[p].copy(); q[0]*=s; q[1]=chin+(q[1]-mchin)*s; P.append(q)
                    Q.append((UV[x][0]%1,UV[x][1]%1) if tid==2 else (UV[x][0],UV[x][1]))
                idx.append(key[k])
            F.append(idx)
        P=np.array(P); F=np.array(F)[:,::-1]; P[:,2]=0.35
        for _ in range(40):
            d=gd2.head_sdf(P,ears=False); P[:,2]-=np.maximum(d-lift,-0.05)*0.8
        out[tid]=(P,np.array(Q),F)
    return out,s

def native_face2(path, sx, sy, chin=0.868, top_cut=1.30, lift=0.0015):
    """Muffy's whole face (incl. her hairline band), scaled sx/sy about her chin"""
    M=awlmodel.load(path); V=M['V']; UV=M['UV']
    g={}
    for tid,ts,_ in M['groups']: g.setdefault(tid,[]).extend(ts)
    face=V[sorted({i for pi,_ in g[2] for i in pi})]
    cen=face[(np.abs(face[:,0])<0.04)&(face[:,2]>0.05)]; mchin=cen[:,1].min(); out={}
    for tid in (2,0,1):
        P=[];Q=[];F=[];key={}
        for pi,ti in g[tid]:
            c=V[list(pi)].mean(0); yy=chin+(c[1]-mchin)*sy
            if tid==2 and (yy<chin-0.004 or yy>top_cut or abs(c[0]*sx)>0.215 or c[2]<0.02): continue
            idx=[]
            for p,x in zip(pi,ti):
                k=(p,x)
                if k not in key:
                    key[k]=len(P); q=V[p].copy(); q[0]*=sx; q[1]=chin+(q[1]-mchin)*sy; P.append(q)
                    Q.append((UV[x][0]%1,UV[x][1]%1) if tid==2 else (UV[x][0],UV[x][1]))
                idx.append(key[k])
            F.append(idx)
        P=np.array(P); F=np.array(F)[:,::-1]; P[:,2]=0.35
        for _ in range(40):
            d=gd2.head_sdf(P,ears=False); P[:,2]-=np.maximum(d-lift,-0.05)*0.8
        out[tid]=(P,np.array(Q),F)
    return out

def native_face3(path, sx, sy, hair_ours=1.265, hair_muffy=1.19, chin=0.868, lift=0.0015):
    """anchored at the hairline (Muffy's painted hairline -> our hair edge), scaled down from there;
    whatever falls below our chin is dropped"""
    M=awlmodel.load(path); V=M['V']; UV=M['UV']
    g={}
    for tid,ts,_ in M['groups']: g.setdefault(tid,[]).extend(ts)
    out={}
    for tid in (2,0,1):
        P=[];Q=[];F=[];key={}
        for pi,ti in g[tid]:
            c=V[list(pi)].mean(0); yy=hair_ours+(c[1]-hair_muffy)*sy
            if tid==2 and (yy<chin-0.002 or yy>1.30 or abs(c[0]*sx)>0.215 or c[2]<0.02): continue
            idx=[]
            for p,x in zip(pi,ti):
                k=(p,x)
                if k not in key:
                    key[k]=len(P); q=V[p].copy(); q[0]*=sx; q[1]=hair_ours+(q[1]-hair_muffy)*sy; P.append(q)
                    Q.append((UV[x][0]%1,UV[x][1]%1) if tid==2 else (UV[x][0],UV[x][1]))
                idx.append(key[k])
            F.append(idx)
        P=np.array(P); F=np.array(F)[:,::-1]; P[:,2]=0.35
        for _ in range(40):
            d=gd2.head_sdf(P,ears=False); P[:,2]-=np.maximum(d-lift,-0.05)*0.8
        out[tid]=(P,np.array(Q),F)
    return out
