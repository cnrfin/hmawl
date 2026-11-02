import struct, subprocess, wave, numpy as np, sys
def vlq(n):
    b=[n&0x7F]; n>>=7
    while n: b.insert(0,0x80|(n&0x7F)); n>>=7
    return bytes(b)
TPQ=480
def mid(path,bank,prog,notes):
    ev=[(0,bytes([0xB0,0,bank])),(0,bytes([0xC0,prog]))]
    for t,d,k,v in notes:
        ev.append((int(t*TPQ),bytes([0x90,k,v]))); ev.append((int((t+d)*TPQ),bytes([0x80,k,0])))
    ev.sort(key=lambda e:e[0]); out=b''; last=0
    for t,m in ev: out+=vlq(t-last)+m; last=t
    out=b'\x00\xff\x51\x03'+(1000000).to_bytes(3,'big')+out+vlq(TPQ)+b'\xff\x2f\x00'
    open(path,'wb').write(b'MThd'+struct.pack('>IHHH',6,0,1,TPQ)+b'MTrk'+struct.pack('>I',len(out))+out)
def render(name,bank,prog,pat,length):
    mid(name+'.mid',bank,prog,pat)
    subprocess.run(['fluidsynth','-ni','-q','-R','0','-C','0','-F',name+'.wav','-r','44100','-g','1.0','/home/user/hmawl_music.sf2',name+'.mid'],capture_output=True)
    w=wave.open(name+'.wav'); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).reshape(-1,2).mean(1).astype(float)
    a=a[:int(length*44100)]; k=int(0.06*44100); a[-k:]*=np.linspace(1,0,k); return a
def lowpass(a,fc):
    if not fc: return a
    sp=np.fft.rfft(a); f=np.fft.rfftfreq(len(a),1/44100); sp*=1/np.sqrt(1+(f/fc)**4); return np.fft.irfft(sp,len(a))
def cent(a):
    sp=np.abs(np.fft.rfft(a[:16384]*np.hanning(16384))); f=np.fft.rfftfreq(16384,1/44100); return (sp*f).sum()/sp.sum()
ref=np.frombuffer(wave.open('ref.wav').readframes(10**7),np.int16).astype(float); rr=0.55*np.sqrt(np.mean(ref[:int(0.3*44100)]**2))
def norm(a): return np.clip(a*rr/max(np.sqrt(np.mean(a[:int(0.3*44100)]**2)),1),-32767,32767)
def pats(D,G,vel):
    s=vel/100
    ON=[(0.00,0.06,D,int(95*s))]+[(0.05+0.06*i,0.07 if i<3 else 0.30,G,int(v*s)) for i,v in enumerate((100,85,75,68))]
    OFF=[(0.00,0.045,G,int(95*s)),(0.04,0.045,G,int(82*s)),(0.08,0.25,D,int(88*s))]
    return ON,OFF
