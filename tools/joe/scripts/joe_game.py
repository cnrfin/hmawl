"""Joe (EmotiGuy) as AWL character files on Van's skeleton (ban_0, 50 nodes) with Van's animations.
usage: joe_game.py NAME OUTDIR"""
import sys, os, ast, struct, pickle, json, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); SP=os.path.join(HERE,'..')
sys.path[:0]=[os.path.join(SP,'pm'),os.path.join(SP,'joeexpr'),os.path.join(SP,'goddess')]
from awlchar import act, world
from PIL import Image
import trimesh
NAME,OUT=sys.argv[1],sys.argv[2]; os.makedirs(OUT,exist_ok=True)
FRAC=13; al=lambda b,a:b+bytes((-len(b))%a)
VAN=os.path.join(SP,'goddess','girls','ban_0')+'/'; W_=os.path.join(SP,'wally')+'/'
src=open(os.path.join(SP,'pkg_blank','postman_npc','src','build_blank.py')).read()
for node in ast.parse(src).body:
    if isinstance(node,ast.FunctionDef) and node.name in {'strips','dl','check_strips','build_skn','c565','un565','cmpr','tpl','u8'}:
        exec(compile(ast.Module([node],[]),'b','exec'),globals())
nodes=act(open(VAN+'ban_0.act','rb').read())
S=1.07; DZ=-0.066
def G(P): P=np.asarray(P,float); return np.stack([P[:,0]*S,(P[:,2]+0.412)*S,-P[:,1]*S+DZ],1)
E=os.path.join(SP,'emotis')+'/'
d=pickle.load(open(E+'joe_pieces.pkl','rb')); cam=pickle.load(open(E+'face_cam.pkl','rb')); span=cam['span']*1.12
pieces=[]   # (name, P game, UV in its own texture 0..1, F, texkey, node)
# head: regular lat-long sphere shrunk onto the plain head (no fans -> smooth shading)
HV,HF=d['head_hi']; hm=trimesh.Trimesh(HV,HF,process=False); hint=trimesh.ray.ray_pyembree.RayMeshIntersector(hm)
C=(HV.min(0)+HV.max(0))/2; RINGS,SEGS=16,26
dirs=[[0,0,1.0]]+[[np.sin(np.pi*i/RINGS)*np.sin(2*np.pi*j/SEGS),-np.sin(np.pi*i/RINGS)*np.cos(2*np.pi*j/SEGS),np.cos(np.pi*i/RINGS)] for i in range(1,RINGS) for j in range(SEGS)]+[[0,0,-1.0]]
dirs=np.array(dirs); loc,ri,_=hint.intersects_location(np.repeat(C[None],len(dirs),0),dirs,multiple_hits=False)
r=np.full(len(dirs),np.nan)
for k,l in zip(ri,loc): r[k]=np.linalg.norm(l-C)
r=np.where(np.isnan(r),np.nanmedian(r),r)
# front = mirror of the back (a clean dome; the front had dips where the 3D eyes and mouth were)
mir=dirs*np.array([1,-1,1.0]); lm,rm,_=hint.intersects_location(np.repeat(C[None],len(mir),0),mir,multiple_hits=False)
rb=np.full(len(dirs),np.nan)
for k,l in zip(rm,lm): rb[k]=np.linalg.norm(l-C)
front=dirs[:,1]<0; r=np.where(front&~np.isnan(rb),rb,r); SV=C+dirs*r[:,None]
idx=lambda i,j: 0 if i==0 else (len(dirs)-1 if i==RINGS else 1+(i-1)*SEGS+j%SEGS)
SF=[]
for i in range(RINGS):
    for j in range(SEGS):
        A,B_,C_,D_=idx(i,j),idx(i,j+1),idx(i+1,j),idx(i+1,j+1)
        if i==0: SF.append((A,C_,D_))
        elif i==RINGS-1: SF.append((A,C_,B_))
        else: SF+= [(A,C_,D_),(A,D_,B_)]
SF=np.array(SF); cen=SV[SF].mean(1)-C; n=np.cross(SV[SF[:,1]]-SV[SF[:,0]],SV[SF[:,2]]-SV[SF[:,0]]); fl=(n*cen).sum(1)<0; SF[fl]=SF[fl][:,::-1]
VN=np.zeros_like(SV); n=np.cross(SV[SF[:,1]]-SV[SF[:,0]],SV[SF[:,2]]-SV[SF[:,0]])
for k in range(3): np.add.at(VN,SF[:,k],n)
VN/=np.linalg.norm(VN,axis=1,keepdims=True)
smooth_head=trimesh.Trimesh(SV,SF,process=False)
def canvas_uv(P):
    return np.stack([(P[:,0]-cam['cx'])/span+0.5,(P[:,2]-cam['cz'])/span*-1+0.5],1)
P=SV[SF].reshape(-1,3); NH=VN[SF].reshape(-1,3)
pieces.append(('head',G(P),canvas_uv(P),np.arange(len(P)).reshape(-1,3),'head',13))
NORMALS={'head':NH}
import frames as FR
sint=trimesh.ray.ray_pyembree.RayMeshIntersector(smooth_head)
def gnorm(N): return np.stack([N[:,0],N[:,2],-N[:,1]],1)
def patch(box,nx,ny,lift):
    x0,y0,x1,y1=box; G_=np.full((ny+1,nx+1,3),np.nan); uv=[];nn=[]
    for j in range(ny+1):
        for i in range(nx+1):
            px,py=x0+i/nx*(x1-x0),y0+j/ny*(y1-y0)
            if py<120: py=120-(120-py)*0.72      # brows sit on the rim of his disc-shaped head: bring them onto the face
            wx=cam['cx']+(px/512-0.5)*span; wz=cam['cz']-(py/512-0.5)*span
            loc,_,_=sint.intersects_location([[wx,-3,wz]],[[0,1,0]])
            G_[j,i]=[wx,loc[:,1].min() if len(loc) else np.nan,wz]
    for i in range(nx+1):                       # misses (past the head's outline): keep the patch flat there
        col=G_[:,i,1]; ok=~np.isnan(col)
        if not ok.any(): col[:]=np.nanmin(G_[:,:,1])
        else: col[~ok]=np.interp(np.where(~ok)[0],np.where(ok)[0],col[ok])
    pts=[]
    for j in range(ny+1):
        for i in range(nx+1):
            p=G_[j,i]; d_=p-C; d_/=np.linalg.norm(d_); pts.append(p+d_*lift); uv.append([i/nx,j/ny])
            vi=np.argmin(np.linalg.norm(SV-p,axis=1)); nn.append(VN[vi])
    F=[]
    for j in range(ny):
        for i in range(nx):
            a=j*(nx+1)+i; F+=[[a,a+1,a+nx+2],[a,a+nx+2,a+nx+1]]
    pts=np.array(pts); F=np.array(F); nn=np.array(nn)
    c2=pts[F].mean(1)-C; n2=np.cross(pts[F[:,1]]-pts[F[:,0]],pts[F[:,2]]-pts[F[:,0]]); fl=(n2*c2).sum(1)<0; F[fl]=F[fl][:,::-1]
    return pts,np.array(uv),F,nn
eP,eU,eF,eN=patch(FR.EYE_BOX,10,9,0.010); mP,mU,mF,mN=patch(FR.MOUTH_BOX,10,7,0.006)
pieces.append(('eyes',G(eP),eU,eF,'eyeframe',13)); pieces.append(('mouth',G(mP),mU,mF,'mouthframe',13))
NORMALS['eyes']=eN; NORMALS['mouth']=mN
# gloves and shoes
for key,nodeL,nodeR,tex in (('gloves',18,39,'emoti'),('shoes',8,48,'shoes')):
    P,Q,F,MI=d[key][:4] if len(d[key])==4 else d[key]
    tri=P[F]; side=np.sign(tri.mean(1)[:,0])
    for sd,nd in ((1,nodeL),(-1,nodeR)):
        m=side==sd; FF=F[m].copy()
        # consistent outward winding (the decimated Blender meshes have flipped parts -> holes / black in game)
        tm=trimesh.Trimesh(P,FF,process=False); tm.merge_vertices(); tm.fix_normals()
        tri=P[FF]; n_=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]); n_/=np.maximum(np.linalg.norm(n_,axis=1)[:,None],1e-12)
        flip=(n_*tm.face_normals).sum(1)<0
        cen=tri.reshape(-1,3).mean(0); vol_out=((tri.mean(1)-cen)*tm.face_normals).sum(1).mean()>0
        if not vol_out: flip=~flip
        FF[flip]=FF[flip][:,::-1]
        print(key,sd,'flipped',int(flip.sum()),'of',len(FF))
        PP=P[FF].reshape(-1,3); QQ=Q[FF].reshape(-1,2); QQ=np.stack([QQ[:,0],1-QQ[:,1]],1)
        pieces.append((f'{key}{"L" if sd>0 else "R"}',G(PP),QQ,np.arange(len(PP)).reshape(-1,3),tex,nd))
# textures -> body atlas (gloves crop + shoes), head atlas (skin)
emo=Image.open(E+'tex_EmotiguyDefault.png').convert('RGBA'); sho=Image.open(E+'tex_ShoesTex.png').convert('RGBA')
gq=np.vstack([p[2] for p in pieces if p[0].startswith('gloves')]); u0,v0=gq.min(0); u1,v1=gq.max(0)
gcrop=emo.crop((int(u0*1024)-2,int(v0*1024)-2,int(u1*1024)+2,int(v1*1024)+2)).resize((128,128),Image.LANCZOS)
gbox=(int(u0*1024)-2,int(v0*1024)-2,int(u1*1024)+2,int(v1*1024)+2)
body=Image.new('RGBA',(256,128),(255,255,255,255)); body.paste(gcrop,(0,0)); body.paste(sho.resize((128,128),Image.LANCZOS),(128,0))
head=FR.BASE.resize((128,128),Image.LANCZOS); hb=Image.new('RGBA',(128,128)); 
hd=np.array(head); a=hd[...,3]>0; col=np.median(hd[...,:3][a],0); hd[~a,:3]=col; hd[...,3]=255; head=Image.fromarray(hd)
def atlas_uv(p):
    n,P,Q,F,t,nd=p
    if t=='emoti':
        u=(Q[:,0]*1024-gbox[0])/(gbox[2]-gbox[0]); v=(Q[:,1]*1024-gbox[1])/(gbox[3]-gbox[1]); return np.stack([np.clip(u,0,1)*0.5,np.clip(v,0,1)],1),1
    if t=='shoes': return np.stack([0.5+np.clip(Q[:,0]%1,0,1)*0.5,np.clip(Q[:,1]%1,0,1)],1),1
    if t=='head': return np.clip(Q,0,1),3
    if t=='eyeframe': return Q,0
    if t=='mouthframe': return Q,2
# vertices / skin groups (as the goddess builder)
verts=[];vkey={};uvs=[];ukey={};tris={0:[],1:[],2:[],3:[]}
def nrm(P,F):
    key={};wid=np.array([key.setdefault(tuple(np.round(p,4)),len(key)) for p in P]);acc=np.zeros((len(key),3))
    n=np.cross(P[F[:,1]]-P[F[:,0]],P[F[:,2]]-P[F[:,0]])
    for k in range(3): np.add.at(acc,wid[F[:,k]],n)
    nn=acc[wid]; return nn/np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-12)
vn=[]
for p in pieces:
    n,P,Q,F,t,nd=p; UV,mat=atlas_uv(p); Nn=nrm(P,F); idx=[];uix=[]
    if n in NORMALS: Nn=gnorm(NORMALS[n])
    for i in range(len(P)):
        k=(tuple(np.round(P[i],4)),nd,tuple(np.round(Nn[i],1)),t)
        if k not in vkey: vkey[k]=len(verts); verts.append((P[i],nd)); vn.append(Nn[i])
        idx.append(vkey[k]); uk=(round(UV[i][0]*16384),round(UV[i][1]*16384))
        if uk not in ukey: ukey[uk]=len(uvs); uvs.append(tuple(UV[i]))
        uix.append(ukey[uk])
    for a,b,c in F:
        if len({idx[a],idx[b],idx[c]})<3: continue
        tris[mat].append(((idx[a],idx[b],idx[c]),(uix[a],uix[b],uix[c])))   # same winding as the vanilla models (checked against Muffy)
P=np.array([v[0] for v in verts]); B=np.array([v[1] for v in verts]); N=np.array(vn)
order=[];groups=[];slot=0
for b in sorted(set(B)):
    ix=[i for i in range(len(P)) if B[i]==b]
    for c in range(0,len(ix),128):
        ch=ix[c:c+128]
        if groups:
            pb,ps,pc=groups[-1];need=((ps+pc)*12+0x1F)&~0x1F
            while (slot*12)&~0x1F<need: slot+=1
        n_=max(len(ch),2); groups.append((b,slot,n_))
        for k,i in enumerate(ch): order.append((slot+k,i))
        slot+=n_
nbuf=slot; lb,ls_,lc=groups[-1]; a0=(ls_*12)&~0x1F; nbuf=max(nbuf,-(-(a0+((lc*12+ls_*12%32+0x1F)&~0x1F))//12))
pos_of={i:s_ for s_,i in order}; P2=np.zeros((nbuf,3)); N2=np.zeros((nbuf,3)); N2[:,1]=1
for s_,i in order: P2[s_]=P[i]; N2[s_]=N[i]
filled=set(s_ for s_,i in order)
for s_ in range(nbuf):
    if s_ not in filled: P2[s_]=P2[s_-1]; N2[s_]=N2[s_-1]
for g in tris: tris[g]=[(tuple(pos_of[i] for i in pi),ti) for pi,ti in tris[g]]
q=lambda x:int(np.clip(np.round(x*(1<<FRAC)),-32768,32767)); assert np.abs(P2).max()*(1<<FRAC)<32767
vbuf=b''.join(struct.pack('>6h',*[q(c) for c in P2[i]],*[q(c) for c in N2[i]]) for i in range(len(P2)))
def build_gpl():
    tg=open(W_+'sua_0.gpl','rb').read()[0x1C:]; m=bytearray(0x24)
    m[0x1C:0x24]=struct.pack('>IHBB',0x24,len(P2),0x30|FRAC,6); m+=vbuf; m=bytearray(al(bytes(m),4))
    col=len(m); ch=bytearray(tg[0x3c44:0x3c50]); struct.pack_into('>I',ch,0,col+8); m+=ch
    uvo=len(m); m+=bytes(0x10); uvd=len(m)
    m+=b''.join(struct.pack('>hh',int(np.clip(round(u*16384),-32768,32767)),int(np.clip(round(v*16384),-32768,32767))) for u,v in uvs); m=bytearray(al(bytes(m),4))
    nro=len(m); m+=struct.pack('>IHBBI',0x24+6,len(P2),0x30|FRAC,6,0x41C80000)
    mo=len(m); nc=6; m+=bytes(0xC+0x10*nc)
    while (len(m)+0x1C)%0x20: m+=b'\0'
    offs={}
    for k in (0,1,2,3): o=len(m); dd=dl(tris[k]); m+=dd; offs[k]=(o,len(dd))
    struct.pack_into('>III',m,mo,offs[0][0],mo+0xC,nc<<16)
    cmds=[struct.pack('>IIII',0x01000000,0x11110000,0,0),struct.pack('>IIII',0x03000000,1,0,0),struct.pack('>IIII',0x02000000,0xC3C,*offs[0]),
          struct.pack('>IIII',0x01FF0000,0x11110001,*offs[1]),struct.pack('>IIII',0x01010000,0x11110002,*offs[2]),struct.pack('>IIII',0x01020000,0x11110003,*offs[3])]
    for k,c in enumerate(cmds): m[mo+0xC+0x10*k:mo+0x1C+0x10*k]=c
    tail=len(m); m+=(NAME+'.tpl').encode()+b'\0\0\0'+(NAME[0].upper()+NAME[1:]+'_L:Layer1').encode()+b'\0'
    struct.pack_into('>IHBBII',m,uvo,uvd,len(uvs),0x3E,2,tail,0); struct.pack_into('>5I',m,0,0x1C,col,uvo,nro,mo); struct.pack_into('>II',m,0x14,0x01FF0000,0)
    return struct.pack('>7I',0x005BBC61,0,0,1,0x14,0x1C,len(m))+bytes(m)
def frames_tpl(fr,n):
    ims=[fr.get(i,fr[0]) for i in range(n)]          # every slot filled: unknown expressions show the normal face
    blobs=[];ref=[]
    for im in ims:
        bb=cmpr(im); k=next((j for j,(b2,s2) in enumerate(blobs) if b2==bb and s2==im.size),None)
        if k is None: blobs.append((bb,im.size)); k=len(blobs)-1
        ref.append(k)
    out=bytearray(struct.pack('>III',0x0020AF30,n,0xC))
    for k in range(n): out+=struct.pack('>II',0xC+8*n+0x24*k,0)
    pos=(0xC+8*n+0x24*n+0x1F)&~0x1F; dp=[]
    for bb,_ in blobs: dp.append(pos); pos=(pos+len(bb)+0x1F)&~0x1F
    for im,k in zip(ims,ref): out+=struct.pack('>HHIIIIIIBBBB',im.height,im.width,14,dp[k],1,1,1,1,0,0,0,0)[:0x24].ljust(0x24,b'\0')
    out=bytearray(al(bytes(out),0x20))
    for bb,_ in blobs: out+=al(bb,0x20)
    return bytes(out)
def build_act():
    dd=bytearray(open(VAN+'ban_0.act','rb').read()); i=dd.find(b'ban_0.gpl'); dd[i:i+9]=(NAME+'.gpl').encode()[:9]; return bytes(dd)
if __name__=='__main__':
    for g in tris: check_strips(tris[g])
    gpl,skn,actb=build_gpl(),build_skn(),build_act()
    b0=tpl([body,head]); f0e=frames_tpl(FR.eye_frames(),58); f0m=frames_tpl(FR.mouth_frames(),36)
    arc=u8([(NAME+'.act',actb),(NAME+'.gpl',gpl),(NAME+'.skn',skn),(NAME+'_b0.tpl',b0),(NAME+'_f0_e.tpl',f0e),(NAME+'_f0_m.tpl',f0m),('_tmp.txt',b'')])
    anims=[open(VAN+'anm%02d.bin'%a,'rb').read() for a in range(22)]
    anm=u8([('@',x) for x in anims])
    open(os.path.join(OUT,NAME+'.arc'),'wb').write(arc); open(os.path.join(OUT,NAME+'.anm.arc'),'wb').write(anm)
    for n_,dd in (('act',actb),('gpl',gpl),('skn',skn)): open(os.path.join(OUT,NAME+'.'+n_),'wb').write(dd)
    open(os.path.join(OUT,NAME+'_b0.tpl'),'wb').write(b0); open(os.path.join(OUT,NAME+'_f0_e.tpl'),'wb').write(f0e); open(os.path.join(OUT,NAME+'_f0_m.tpl'),'wb').write(f0m)
    print('tris',{k:len(v) for k,v in tris.items()},'total',sum(len(v) for v in tris.values()),'verts',len(P))
    print(NAME+'.arc',len(arc),'anm',len(anm),'parts',{k:len(v) for k,v in (('gpl',gpl),('skn',skn),('b0',b0),('f0e',f0e),('f0m',f0m))})
