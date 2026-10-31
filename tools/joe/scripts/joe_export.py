import bpy, bmesh, numpy as np, mathutils, pickle, math
OUT='/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/emotis/'
bpy.ops.wm.open_mainfile(filepath=OUT+"The Emotis.blend")
sc=bpy.context.scene
def tri_data(o, uvname='Model_UV'):
    dg=bpy.context.evaluated_depsgraph_get(); oe=o.evaluated_get(dg); m=oe.to_mesh(); M=oe.matrix_world
    m.calc_loop_triangles(); uv=m.uv_layers[uvname].data if uvname in m.uv_layers else m.uv_layers.active.data
    P=[];Q=[];F=[];MI=[]
    for t in m.loop_triangles:
        F.append([len(P),len(P)+1,len(P)+2]); MI.append(t.material_index)
        for li in t.loops:
            P.append(tuple(M@m.vertices[m.loops[li].vertex_index].co)); Q.append(tuple(uv[li].uv))
    return np.array(P),np.array(Q),np.array(F),np.array(MI)
def dec(o,r):
    for md in o.modifiers:
        if md.type=='SUBSURF': md.show_render=md.show_viewport=False
    d=o.modifiers.new('dec','DECIMATE'); d.ratio=r
    bpy.context.view_layer.objects.active=o
    while o.modifiers.find('dec')>0: bpy.ops.object.modifier_move_up(modifier='dec')
out={}
gl=bpy.data.objects['Emotiguy_16450.Shape.002']; dec(gl,0.045); out['gloves']=tri_data(gl)
sh=bpy.data.objects['EmotiShoes_11630.Shape']; dec(sh,0.03); out['shoes']=tri_data(sh)
out['shoe_mats']=[s.material.name for s in sh.material_slots]
# plain head: skin only, eyes + mouth holes filled and relaxed into the surface
g=bpy.data.objects['Emotiguy_16450.Shape.001']; names=[s.material.name for s in g.material_slots]; sk=names.index('Skin')
dg=bpy.context.evaluated_depsgraph_get(); ge=g.evaluated_get(dg); me=bpy.data.meshes.new_from_object(ge); me.transform(ge.matrix_world)
bm=bmesh.new(); bm.from_mesh(me)
bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=sk],context='FACES')
bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
EYES=[np.array([s_*0.171,-0.186,0.863]) for s_ in (1,-1)]
def region(p):
    if p[1]>-0.02: return False
    if min(np.sqrt(((p[0]-e[0])/0.235)**2+((p[2]-e[2])/0.20)**2) for e in EYES)<1.15: return True
    return abs(p[0])<0.62 and 0.28<p[2]<0.80
cut=[f for f in bm.faces if any(region(np.array(v.co[:])) for v in f.verts)]
bmesh.ops.delete(bm,geom=cut,context='FACES'); bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
bd=[e for e in bm.edges if e.is_boundary]
nf=bmesh.ops.holes_fill(bm,edges=bd,sides=0)['faces']
pk=bmesh.ops.poke(bm,faces=nf); eds={e for f in pk['faces'] for e in f.edges}
bmesh.ops.subdivide_edges(bm,edges=list(eds),cuts=3,use_grid_fill=True)
bmesh.ops.triangulate(bm,faces=bm.faces)
free=[v for v in bm.verts if region(np.array(v.co[:]))]
for it in range(400):
    for v in free:
        nb=[e.other_vert(v).co for e in v.link_edges]; v.co=sum(nb,mathutils.Vector())/len(nb)
bmesh.ops.triangulate(bm,faces=bm.faces)
out['head_hi']=(np.array([v.co[:] for v in bm.verts]),np.array([[v.index for v in f.verts] for f in bm.faces]))
bm.verts.index_update()
out['head_hi']=(np.array([v.co[:] for v in bm.verts]),np.array([[v.index for v in f.verts] for f in bm.faces]))
hm=bpy.data.meshes.new('JoePlain'); bm.to_mesh(hm); ho=bpy.data.objects.new('JoePlain',hm); sc.collection.objects.link(ho)
d=ho.modifiers.new('dec','DECIMATE'); d.ratio=600/len(hm.polygons)
dg=bpy.context.evaluated_depsgraph_get(); m=ho.evaluated_get(dg).to_mesh(); m.calc_loop_triangles()
V=np.array([v.co[:] for v in m.vertices]); F=np.array([t.vertices[:] for t in m.loop_triangles])
out['head']=(V,F)
pickle.dump(out,open(OUT+'joe_pieces.pkl','wb'))
for img in ('EmotiguyDefault.001','ShoesTex'):
    im=bpy.data.images[img]; im.filepath_raw=OUT+f'tex_{img.split(".")[0]}.png'; im.file_format='PNG'; im.save()
print('gloves',len(out['gloves'][2]),'shoes',len(out['shoes'][2]),'head',len(F), out['shoe_mats'])
