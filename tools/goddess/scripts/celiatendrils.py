"""Celia's front tendrils (her own mesh: from the parting, over the forehead corners, down beside the face),
on the blank model, teal"""
import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/blank','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/pm']
import hairstudy as S, hairtex2 as HT, restyle
HB=(39,113,82,186)
def build(sx=0.95, zc=0.0):
    M,T,tris,hb=S.hair2('sepi'); V=M['V'].copy(); UV=M['UV']; comp=np.load('/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/celia_comp.npy')
    V[:,0]*=sx; V[:,2]=0.01+(V[:,2]-0.01)*sx
    tex=T[255].copy(); x0,y0,x1,y1=HB; blk=tex[y0:y1,x0:x1]; L=restyle.lum(blk[...,:3]); lo,hi=np.percentile(L,1),np.percentile(L,99.5)
    blk[...,:3]=HT.ramp()[(np.clip((L-lo)/(hi-lo),0,1)*255).astype(int)]; tex[y0:y1,x0:x1]=blk
    sel=[t for t,c in zip(tris,comp) if c==comp.max() or True]
    sel=[t for t,c in zip(tris,comp) if c!=comp.min() and M['V'][list(t[0])][:,2].mean()>zc and np.mean([UV[x][1]%1 for x in t[1]])*256>100]
    P=[];Q=[];F=[]
    for pi,ti in sel:
        F.append([len(P),len(P)+1,len(P)+2])
        for p,t in zip(pi,ti): P.append(V[p]); Q.append((UV[t][0]%1,UV[t][1]%1))
    return np.array(P),np.array(Q),np.array(F)[:,::-1],tex

def wave(P, amp=0.028, waves=2.0, y0=1.12, ramp=0.10, zamp=0.010):
    """Flora-like sideways S-wave down the hanging part (none over the forehead), whole lock moves together"""
    P = P.copy(); y = P[:, 1]; ytip = y.min()
    t = np.clip((y0 - y) / (y0 - ytip), 0, 1)
    w = np.clip((y0 - y) / ramp, 0, 1); w = w * w * (3 - 2 * w)
    s = np.sign(P[:, 0])
    P[:, 0] += s * amp * np.sin(t * waves * 2 * np.pi) * w
    P[:, 2] += zamp * np.sin(t * waves * 2 * np.pi + np.pi / 2) * w
    return P
