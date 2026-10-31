"""Celia's own hair mesh on the blank body: bandana re-textured as hair (strands from the crown), hair block
recoloured to the teal ramp, plus the goddess buns"""
import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/pm']
import hairstudy as S, hairtex2 as HT, restyle, cagehair as CH
HB=(39,113,82,186)
def build(sx=0.95, top_v=(116,140), bandana=True, flat=0.034, y0f=0.93, y1f=1.17):
    M,T,tris,hb=S.hair2('sepi'); UV=M['UV']; V=M['V'].copy(); H,W=256,128
    V[:,0]*=sx; V[:,2]=0.01+(V[:,2]-0.01)*sx
    if flat:      # no bandana underneath: the hair lies flat on the skull at the top, blending to Celia's shape below
        cen0=np.array([0,1.08,-0.01]); hv0=sorted({i for pi,_ in tris for i in pi})
        for i in hv0:
            d=V[i]-cen0; r=np.linalg.norm(d); d/=r; sr=np.linalg.norm(CH.surf(d)-cen0); off=r-sr
            w=np.clip((V[i][1]-y0f)/(y1f-y0f),0,1); w=w*w*(3-2*w)
            if off>flat: V[i]=cen0+d*(sr+off+(flat-off)*w)
        # no bandana: the back hair continues up over the crown (its top edge stretched up to the crown)
        el_b=np.radians(118.0); el_e=np.radians(98.0)
        for i in hv0:
            d=V[i]-cen0
            if d[2]>-0.02: continue
            r=np.linalg.norm(d); el=np.arccos(np.clip(d[1]/r,-1,1)); az=np.arctan2(d[0],-d[2])
            if el>=el_b: continue
            el2=el_b-(el_b-el)*el_b/(el_b-el_e)*0.92
            el2=max(el2,np.radians(8))
            dd=np.array([np.sin(el2)*np.sin(az),np.cos(el2),-np.sin(el2)*np.cos(az)])
            sr=np.linalg.norm(CH.surf(dd)-cen0); sr0=np.linalg.norm(CH.surf(d/r)-cen0)
            V[i]=cen0+dd*(sr+(r-sr0))
    tex=T[255].copy(); x0,y0,x1,y1=HB
    blk=tex[y0:y1,x0:x1]; L=restyle.lum(blk[...,:3]); lo,hi=np.percentile(L,1),np.percentile(L,99.5)
    r=HT.ramp(); blk[...,:3]=r[(np.clip((L-lo)/(hi-lo),0,1)*255).astype(int)]; tex[y0:y1,x0:x1]=blk
    P=[];Q=[];F=[]
    cen=np.array([0,1.08,-0.01])
    # bandana -> hair shell: each bandana vertex moved onto the skull + an offset that meets the hair at its rim
    bandv=set(); hairv=set()
    for pi,ti in tris:
        v_=np.mean([UV[t][1]%1 for t in ti])*H
        (bandv if v_<60 else hairv).update(pi)
    bandv=sorted(bandv); hv=np.array(sorted(hairv-set(bandv)))
    import gd2
    for i in bandv:
        d=V[i]-cen; d/=np.linalg.norm(d); sp=CH.surf(d)
        hd=np.linalg.norm(V[hv]-V[i],axis=1); k=hd.argmin()
        rim_off=np.dot(V[hv[k]]-CH.surf((V[hv[k]]-cen)/np.linalg.norm(V[hv[k]]-cen)),d)
        w=np.clip(1-hd[k]/0.08,0,1)
        V[i]=sp+d*(0.032*(1-w)+max(rim_off,0.02)*w)
    for pi,ti in tris:
        u=np.mean([UV[t][0]%1 for t in ti])*W; v=np.mean([UV[t][1]%1 for t in ti])*H
        band=v<60; hair=x0-2<=u<=x1+2 and y0-2<=v<=y1+2
        if not (band or hair) or (band and not bandana): continue
        tri=[]
        for p,t in zip(pi,ti):
            if band:
                q=V[p]-cen; th=np.arctan2(q[0],-q[2]); el=np.degrees(np.arctan2(np.hypot(q[0],q[2]),q[1]))
                uu=(x0+2+(x1-x0-4)*((th/(2*np.pi))%1))/W; vv=(top_v[0]+(top_v[1]-top_v[0])*np.clip(el/90,0,1))/H
            else: uu,vv=UV[t][0]%1,UV[t][1]%1
            P.append(V[p]); Q.append((uu,vv)); tri.append(len(P)-1)
        if band:   # keep a bandana triangle from straddling the wrap seam
            us=[Q[i][0] for i in tri]
            if max(us)-min(us)>0.15:
                for i in tri:
                    if Q[i][0]<(x0+x1)/2/W: Q[i]=(Q[i][0]+(x1-x0-4)/W,Q[i][1])
        F.append(tri)
    return np.array(P),np.array(Q),np.array(F),tex
def buns():
    m=CH.Mesh(); CH.add_buns(m); return np.array(m.V),np.array(m.UV),np.array(m.F),HT.tiled('Celia')

def crown(ycut=1.0):
    """cage crown cap (strands from the crown, centre-parted arched hairline) to replace the bandana"""
    CH.FRONT_END = ([80, 92.5, 105, 117.5, 130, 142.5, 155, 167.5, 180], [None, 1.085, 1.07, 1.06, 1.06, 1.08, 1.12, 1.18, 1.215])
    c = dict(CH.C); c.update(back_extra=0.0, crown_off=0.026)
    M, cols, G = CH.build(c)
    V = np.array(M.V); F = np.array(M.F); part = np.array(M.part); UV = np.array(M.UV)
    keep = np.isin(part, ['crown', 'lip']) & (V[F][:, :, 1].min(1) > ycut)
    F = F[keep]; CU = UV[F].copy(); span = CU[:, :, 0].max(1) - CU[:, :, 0].min(1); fix = span > 0.5
    CU[fix, :, 0] = np.where(CU[fix, :, 0] < 0.5, CU[fix, :, 0] + 1, CU[fix, :, 0])
    return V[F].reshape(-1, 3), CU.reshape(-1, 2), np.arange(len(F) * 3).reshape(-1, 3), HT.tiled('Celia')
