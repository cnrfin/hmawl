"""Read/write one model of real.gpl (the hand-held tool models).
Layout (offsets inside a model):
 0x00 0x1C | 0x04 colour hdr | 0x08 uv hdr | 0x0C normal hdr | 0x10 material | 0x14 01FF0000 | 0x18 0
 pos hdr @0x1C: u32 data, u16 count, u8 fmt(0x16 = s8, 6 frac bits), u8 3 ; data
 colour hdr: u32 data, u16 count, u8 fmt, u8 comps ; data (rgb), pad 4
 uv hdr: u32 data, u16 count, u8 fmt(0x07 = u8, 7 frac bits), u8 2, u32 off of 'real.tpl' name, u32 0 ; data
 normal hdr: u32 data, u16 count, u8 0x16, u8 3, 4 bytes (41C80000) ; data
 material: u32 A(=dl-0xC), u32 B(=mat+0xC), 00030000, [B:] 01000000, 1111 00 tex, 0,0, 03000000, 00000001, 0,0,
           02000000, 00000828, u32 A, u32 dl size ; zeros up to dl ; display list (prims 0x80/0x90/0x98, u16 count,
           3 u8 idx per vertex: pos, normal, uv) ; zeros ; 'real.tpl' + pad, model padded to 0x20."""
import struct
def parse(m):
    g=lambda o: struct.unpack_from('>I',m,o)[0]
    co,uo,no,mo=g(4),g(8),g(0xC),g(0x10)
    po=g(0x1C); pc=struct.unpack_from('>H',m,0x20)[0]
    P=[struct.unpack_from('>3b',m,po+3*k) for k in range(pc)]
    cd=g(co); cc=struct.unpack_from('>H',m,co+4)[0]; C=m[co+4:co+8]; Cd=m[cd:uo]
    ud=g(uo); uc=struct.unpack_from('>H',m,uo+4)[0]; UV=[tuple(m[ud+2*k:ud+2*k+2]) for k in range(uc)]
    nd=g(no); nc=struct.unpack_from('>H',m,no+4)[0]; N=[struct.unpack_from('>3b',m,nd+3*k) for k in range(nc)]
    tex=m[mo+0x13]; dls=g(mo+0x38); dlo=g(mo)
    prims=[]; i=dlo
    while i<len(m) and m[i] in (0x80,0x90,0x98,0xA0):
        k=struct.unpack_from('>H',m,i+1)[0]; prims.append((m[i],[tuple(m[i+3+3*q:i+6+3*q]) for q in range(k)])); i+=3+3*k
    return dict(P=P,N=N,UV=UV,prims=prims,tex=tex,col=(C,Cd),nhdr=m[no+8:no+12])
def al(b,a):
    return b+bytes((-len(b))%a)
def build(md, base=0xC, tail=b'real.tpl\0\0\0\0'):
    # base = file offset of the model modulo 0x20 (the display list must be 0x20-aligned in the file)
    P,N,UV,prims,tex=md['P'],md['N'],md['UV'],md['prims'],md['tex']
    out=bytearray(0x24)
    pos=b''.join(struct.pack('>3b',*p) for p in P)
    out+=pos; out=bytearray(al(bytes(out),4))
    co=len(out); C,Cd=md['col']; out+=struct.pack('>I',co+8)+C+Cd
    out=bytearray(al(bytes(out),4))
    uo=len(out); out+=b'\0'*16; ud=len(out)
    out+=b''.join(bytes(u) for u in UV); out=bytearray(al(bytes(out),4))
    no=len(out); out+=struct.pack('>IHBB',no+12,len(N),0x16,3)+md['nhdr']
    out+=b''.join(struct.pack('>3b',*n) for n in N); out=bytearray(al(bytes(out),4))
    mo=len(out)
    dl=b''.join(bytes([c])+struct.pack('>H',len(v))+b''.join(bytes(x) for x in v) for c,v in prims)
    mat=bytearray(0x3C)
    dlo=mo+0x64  # placeholder, fixed below
    out+=mat
    # pad so the display list starts 0x20-aligned with at least the original gap
    while (base+len(out))%0x20: out+=b'\0'
    A=len(out); dlo=A
    body=dl
    total=dlo+len(body)
    total=total+len(tail)
    while total%0x20: total+=1
    namepos=total-len(tail)
    out+=body+b'\0'*(namepos-dlo-len(body))+tail
    dls=namepos-dlo
    struct.pack_into('>IIIIIII',out,0,0x1C,co,uo,no,mo,0x01FF0000,0)
    struct.pack_into('>IHBB',out,0x1C,0x24,len(P),0x16,3)
    struct.pack_into('>IHBBII',out,uo,ud,len(UV),0x07,2,namepos,0)
    struct.pack_into('>III',out,mo,A,mo+0xC,0x00030000)
    struct.pack_into('>IIIII',out,mo+0xC,0x01000000,0x11110000|tex,0,0,0x03000000)
    struct.pack_into('>IIIIIII',out,mo+0x20,1,0,0,0x02000000,0x828,A,dls)
    return bytes(out)
