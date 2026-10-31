import bpy, numpy as np, bmesh, math, mathutils, pickle, sys
from collections import defaultdict
OUT='/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/emotis/'
bpy.ops.wm.open_mainfile(filepath=OUT+"The Emotis.blend")
sc=bpy.context.scene
DEPTH=float(sys.argv[-1]) if sys.argv[-1].replace('.','').isdigit() else 0.02
g=bpy.data.objects['Emotiguy_16450.Shape.001']; names=[s.material.name for s in g.material_slots]
skm=bpy.data.materials['Skin']; nt_=skm.node_tree
ti=nt_.nodes.new('ShaderNodeTexImage'); ti.image=bpy.data.images['EmotiguyDefault.001']
uvn=nt_.nodes.new('ShaderNodeUVMap'); uvn.uv_map='Model_UV'; nt_.links.new(uvn.outputs['UV'],ti.inputs['Vector'])
nt_.links.new(ti.outputs['Color'],nt_.nodes['Principled BSDF'].inputs['Base Color']); nt_.nodes.active=ti
cam0=pickle.load(open(OUT+'face_cam.pkl','rb'))
for o in bpy.data.objects:
    if o.type in ('MESH','CURVE','EMPTY'): o.hide_render = o.name!=g.name
cm0=bpy.data.objects['Camera']; cm0.data.type='ORTHO'; cm0.data.ortho_scale=cam0['span']
sc.render.engine='BLENDER_WORKBENCH'; sh0=sc.display.shading; sh0.light='FLAT'; sh0.color_type='TEXTURE'
sh0.show_shadows=False; sh0.show_cavity=False; sh0.show_specular_highlight=False
sc.render.resolution_x=512; sc.render.resolution_y=512; sc.render.film_transparent=True; sc.view_settings.view_transform='Standard'
for side,(y,rz) in (('front',(-3,0)),('back',(3,math.pi))):
    cm0.location=(cam0['cx'],y,cam0['cz']); cm0.rotation_euler=(math.radians(90),0,rz)
    sc.render.filepath=OUT+f'albedo_{side}.png'; bpy.ops.render.render(write_still=True)
import os
EXPR=os.environ.get('EXPR','')
for kv in [x for x in EXPR.split(',') if x]:
    k,v=(kv.split('=')+['1'])[:2]; g.data.shape_keys.key_blocks[k].value=float(v)
bpy.context.view_layer.update()
dg=bpy.context.evaluated_depsgraph_get(); ge=g.evaluated_get(dg)
me=bpy.data.meshes.new_from_object(ge); me.transform(ge.matrix_world)
bm=bmesh.new(); bm.from_mesh(me)
# drop eyes and brows (they become texture)
bmesh.ops.delete(bm,geom=[f for f in bm.faces if names[f.material_index] in ('Eyeball','Pupil','Eyebrow')],context='FACES')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
sk=names.index('Skin')
EYES=[np.array([s_*0.171,-0.186,0.863]) for s_ in (1,-1)]
def eyed(p):
    if p[1]>-0.02: return 9.0          # front of the head only
    return min(np.sqrt(((p[0]-e[0])/0.235)**2+((p[2]-e[2])/0.20)**2) for e in EYES)
# 1. cut out the whole eye area (sockets and lids) of the skin
cut=[f for f in bm.faces if f.material_index==sk and any(eyed(np.array(v.co[:]))<1.08 for v in f.verts)]
bmesh.ops.delete(bm,geom=cut,context='FACES')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
# 2. fill with new faces and give them vertices inside
sset={f for f in bm.faces if f.material_index==sk}
bd=[e for e in bm.edges if e.is_boundary and all(v.co.z>0.6 for v in e.verts)]
res=bmesh.ops.holes_fill(bm,edges=bd,sides=0); nf=res['faces']
for f in nf: f.material_index=sk
pk=bmesh.ops.poke(bm,faces=nf); patch=set(pk['faces'])
eds={e for f in patch for e in f.edges}
r2=bmesh.ops.subdivide_edges(bm,edges=list(eds),cuts=2,use_grid_fill=True)
bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>3])
# 3. relax the eye area into the head's own surface (Laplacian, everything else fixed), then a light dip
SV=[v for v in bm.verts if any(f.material_index==sk for f in v.link_faces)]
free=[v for v in SV if eyed(np.array(v.co[:]))<1.15]
fs=set(free)
for it in range(300):
    for v in free:
        nb=[e.other_vert(v).co for e in v.link_edges]
        v.co=sum(nb,mathutils.Vector())/len(nb)
bm.normal_update()
cen=mathutils.Vector((0,0.06,0.72))
for v in free:
    d=eyed(np.array(v.co[:])); w=max(0.0,1-(d/1.0)**2)
    n=(v.co-cen).normalized()
    v.co=v.co-n*DEPTH*w
bmesh.ops.triangulate(bm,faces=bm.faces)
head=bpy.data.meshes.new('JoeHead'); bm.to_mesh(head); ho=bpy.data.objects.new('JoeHead',head); sc.collection.objects.link(ho)
for i,mn in enumerate(names): ho.data.materials.append(g.material_slots[i].material)
# face texture: eyes + brows painted (front planar projection), skin elsewhere
from PIL import Image
cam=cam0
def panel(fn):
    A=np.array(Image.open(OUT+fn).convert('RGBA'),float); m=A[...,3]>128
    edge=np.median(A[...,:3][m],0); A[~m,:3]=edge; A[...,3]=255; return A
F=np.concatenate([panel('albedo_front.png'),panel('albedo_back.png')],1)
img=bpy.data.images.new('JoeFace',1024,512,alpha=True); img.pixels=(np.flipud(F)/255.).ravel().tolist()
img.filepath_raw=OUT+'joe_face_flat.png'; img.file_format='PNG'; img.save()
mat=bpy.data.materials.new('JoeSkin'); mat.use_nodes=True; nt=mat.node_tree
tn=nt.nodes.new('ShaderNodeTexImage'); tn.image=img; nt.links.new(tn.outputs['Color'],nt.nodes['Principled BSDF'].inputs['Base Color'])
ho.data.materials[sk]=mat
uv=ho.data.uv_layers.new(name='face'); ho.data.uv_layers.active=uv; uv.active_render=True
for p in ho.data.polygons:
    for li in p.loop_indices:
        co=ho.data.vertices[ho.data.loops[li].vertex_index].co
        if p.material_index!=sk: continue
        u=(co.x-cam['cx'])/cam['span']+0.5; v=(co.z-cam['cz'])/cam['span']+0.5
        uv.data[li].uv=(u*0.5,v) if p.center.y<0.03 else (0.5+(1-u)*0.5,v)
# decimate: skin, mouth parts separately via vertex groups is complex -> one modifier, then report
def dec(o,ratio):
    d=o.modifiers.new('dec','DECIMATE'); d.ratio=ratio
INT=float(os.environ.get('INTR','0.0'))
if INT>0:
    INSIDE={i for i,mn in enumerate(names) if mn in ('Teeth','Gums','Tongue','InnerMouth')}
    mo=ho.copy(); mo.data=ho.data.copy(); mo.name='JoeMouthInside'; sc.collection.objects.link(mo)
    for ob,drop in ((ho,lambda f:f.material_index in INSIDE),(mo,lambda f:f.material_index not in INSIDE)):
        b2=bmesh.new(); b2.from_mesh(ob.data); bmesh.ops.delete(b2,geom=[f for f in b2.faces if drop(f)],context='FACES')
        bmesh.ops.delete(b2,geom=[v for v in b2.verts if not v.link_faces],context='VERTS'); b2.to_mesh(ob.data); b2.free()
    dec(ho,float(os.environ.get('SKINR','0.16'))); dec(mo,INT)
else:
    dec(ho,float(os.environ.get('HEADR','0.14')))
gl=bpy.data.objects['Emotiguy_16450.Shape.002']; shoes=bpy.data.objects['EmotiShoes_11630.Shape']
for o in (gl,shoes):
    for m in o.modifiers:
        if m.type=='SUBSURF': m.show_render=False; m.show_viewport=False
dec(gl,0.09); dec(shoes,0.06)
for o in bpy.data.objects:
    if o.type in ('MESH','CURVE','EMPTY'): o.hide_render = o.name not in ('JoeHead','JoeMouthInside',gl.name,shoes.name)
def tris(o):
    dg=bpy.context.evaluated_depsgraph_get(); m=o.evaluated_get(dg).to_mesh(); return sum(len(p.vertices)-2 for p in m.polygons)
counts={'head skin+lips':tris(ho),'mouth inside':tris(bpy.data.objects['JoeMouthInside']) if 'JoeMouthInside' in bpy.data.objects else 0,'gloves':tris(gl),'shoes':tris(shoes)}; print('TRIS',counts,'total',sum(counts.values()))
pts=[]
for o in (ho,gl,shoes): pts+=[o.matrix_world@mathutils.Vector(c) for c in o.bound_box]
P=np.array(pts); lo,hi=P.min(0),P.max(0); c=(lo+hi)/2; size=(hi-lo).max()
cm=bpy.data.objects['Camera']; cm.data.type='ORTHO'; cm.data.ortho_scale=size*1.12
sc.render.engine='BLENDER_WORKBENCH'; sh=sc.display.shading; sh.color_type='TEXTURE'; sh.light='STUDIO'; sh.show_cavity=False
sc.render.film_transparent=False; sc.world.color=(0.75,0.8,0.86); sh.background_type='VIEWPORT'; sh.background_color=(0.78,0.83,0.88)
sc.render.resolution_x=400; sc.render.resolution_y=380; sc.view_settings.view_transform='Standard'
for i,ang in enumerate((0,40,90,180)):
    a=math.radians(ang); d=size*3
    cm.location=(c[0]+d*math.sin(a), c[1]-d*math.cos(a), c[2]); cm.rotation_euler=(math.radians(90),0,a)
    sc.render.filepath=OUT+f'joe2_{i}.png'; bpy.ops.render.render(write_still=True)
# close-up of the face
cm.data.ortho_scale=1.6; cm.location=(0,-3,0.72); cm.rotation_euler=(math.radians(90),0,0)
sc.render.filepath=OUT+os.environ.get('FACEOUT','joe2_face.png'); bpy.ops.render.render(write_still=True)
cm.location=(3*math.sin(math.radians(35)),-3*math.cos(math.radians(35)),0.72); cm.rotation_euler=(math.radians(90),0,math.radians(35))
sc.render.filepath=OUT+'joe2_face34.png'; bpy.ops.render.render(write_still=True)
