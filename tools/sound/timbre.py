import struct, subprocess, wave, numpy as np, os
def vlq(n):
    b=[n&0x7F]; n>>=7
    while n: b.insert(0,0x80|(n&0x7F)); n>>=7
    return bytes(b)
def one_note_mid(path, bank, prog, key, ch=0, dur=480):
    ev=b''
    if bank>=128 and ch!=9: ch=9
    ev+=vlq(0)+bytes([0xB0|ch,0,bank if bank<128 else 0])+vlq(0)+bytes([0xC0|ch,prog])
    ev+=vlq(0)+bytes([0x90|ch,key,100])+vlq(dur)+bytes([0x80|ch,key,0])+vlq(480)+b'\xff\x2f\x00'
    open(path,'wb').write(b'MThd'+struct.pack('>IHHH',6,0,1,480)+b'MTrk'+struct.pack('>I',len(ev))+ev)
def render(sf, mid, wav):
    subprocess.run(['fluidsynth','-ni','-q','-F',wav,'-r','32000','-g','1.0',sf,mid],capture_output=True)
    w=wave.open(wav); a=np.frombuffer(w.readframes(w.getnframes()),np.int16).reshape(-1,2).mean(1); return a
def features(a, sr=32000):
    a=a.astype(float)
    if np.abs(a).max()<50: return None
    env=np.array([np.sqrt(np.mean(a[i:i+320]**2)) for i in range(0,len(a)-320,320)])+1e-6
    pk=env.argmax(); attack=pk*0.01
    dec=np.log(env[min(len(env)-1,pk+50)]/env[pk])      # level 0.5 s after the peak
    seg=a[pk*320:pk*320+8192]
    if len(seg)<8192: seg=np.pad(seg,(0,8192-len(seg)))
    sp=np.abs(np.fft.rfft(seg*np.hanning(8192)))+1e-9; fr=np.fft.rfftfreq(8192,1/sr)
    edges=np.geomspace(60,12000,25); bands=np.array([sp[(fr>=edges[i])&(fr<edges[i+1])].mean() for i in range(24)])
    bands=np.log(bands/bands.max())
    return np.concatenate([bands/3.0,[attack*10, dec, ]])
