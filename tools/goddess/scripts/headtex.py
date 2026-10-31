"""Muffy's hairline texture (head sheet: a strip of hair roots fading into skin) recoloured teal and mapped
on the blank head along a hairline that runs under the tendrils"""
import sys,numpy as np; sys.path[:0]=['/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess','/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/pm']
import wally, restyle, hairtex2 as HT
MU='/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/goddess/girls/mumu_0/mumu_0'
CEN=np.array([0,1.08,-0.01])
def sheet():
    t=wally.tpl(MU+'_b0.tpl',1).astype(float); H,W=t.shape[:2]
    rgb=t[...,:3]; hair=(rgb[...,0]-rgb[...,2]>70)&(np.arange(H)[:,None]<20)      # gold roots (skin is pinkish)
    L=restyle.lum(rgb); lo,hi=np.percentile(L[hair],2),np.percentile(L[hair],99)
    teal=HT.ramp()[(np.clip((L-lo)/(hi-lo),0,1)*0.62*255).astype(int)]        # no pale tones at the roots
    # fade into skin over the strip's last rows (as Muffy's strip does), by row not colour
    rows=np.arange(H)[:,None]*np.ones((1,W)); k=np.clip((17.0-rows)/5.0,0,1)
    skin=np.median(rgb[30:50,0:30].reshape(-1,3),0)
    rgb=np.where((rows<20)[...,None],skin,rgb)
    t[...,:3]=rgb*(1-k[...,None])+teal*k[...,None]; t[...,3]=255
    return t
def hairline_y(th):
    """th: degrees from the front (0) round to the back (180)"""
    a=np.abs(th); return np.interp(a,[0,20,45,70,95,130,180],[1.28,1.27,1.21,1.12,1.04,0.97,0.95])
ROW_LINE=15.0; ROW_TOP=2.0; BAND=0.07; U0,U1=4.0,84.0; SKIN=(14.0,44.0)
def head_uv(P, H=64, W=128):
    d=P-CEN; th=np.degrees(np.arctan2(d[:,0],d[:,2]))
    dy=P[:,1]-hairline_y(th)
    row=np.where(dy>0, ROW_LINE-(ROW_LINE-ROW_TOP)*np.clip(dy/BAND,0,1), np.nan)
    u=np.where(dy>0, U0+(U1-U0)*((th+180)/360), SKIN[0]); v=np.where(dy>0,row,SKIN[1])
    near=(dy<=0)&(dy>-0.03)               # just below the line: the strip's skin side (fade)
    v=np.where(near, ROW_LINE+3, v); u=np.where(near, U0+(U1-U0)*((th+180)/360), u)
    return np.c_[u/W, v/H]

def sheet_ramp(r):
    """Muffy's hairline strip recoloured with ramp r (roots darker, fading into skin)"""
    t=wally.tpl(MU+'_b0.tpl',1).astype(float); H,W=t.shape[:2]; rgb=t[...,:3]
    hair=(rgb[...,0]-rgb[...,2]>70)&(np.arange(H)[:,None]<20)
    L=restyle.lum(rgb); lo,hi=np.percentile(L[hair],2),np.percentile(L[hair],99)
    col=r[(np.clip((L-lo)/(hi-lo),0,1)*0.62*255).astype(int)]
    rows=np.arange(H)[:,None]*np.ones((1,W)); k=np.clip((17.0-rows)/5.0,0,1)
    skin=np.median(rgb[30:50,0:30].reshape(-1,3),0)
    base=np.where((rows<20)[...,None],skin,rgb)
    t[...,:3]=base*(1-k[...,None])+col*k[...,None]; t[...,3]=255
    return t
def head_uv_line(P, line, H=64, W=128):
    """like head_uv, with the hairline height given per vertex by line(theta_from_front_deg)"""
    d=P-CEN; th=np.degrees(np.arctan2(d[:,0],d[:,2]))
    dy=P[:,1]-line(th)
    row=np.where(dy>0, ROW_LINE-(ROW_LINE-ROW_TOP)*np.clip(dy/BAND,0,1), SKIN[1])
    u=np.where(dy>0, U0+(U1-U0)*((th+180)/360), SKIN[0])
    near=(dy<=0)&(dy>-0.03); row=np.where(near, ROW_LINE+3, row); u=np.where(near, U0+(U1-U0)*((th+180)/360), u)
    return np.c_[u/W, row/H]
