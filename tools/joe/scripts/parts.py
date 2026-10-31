import bpy, math, pickle, numpy as np
OUT='/tmp/claude-0/-home-user/93ad7071-c0f2-50fe-8edf-5fd70c4d5f13/scratchpad/emotis/'
bpy.ops.wm.open_mainfile(filepath=OUT+"The Emotis.blend")
sc=bpy.context.scene
g=bpy.data.objects['Emotiguy_16450.Shape.001']
for o in bpy.data.objects:
    if o.type in ('MESH','CURVE','EMPTY'): o.hide_render = o.name!=g.name
c=pickle.load(open(OUT+'face_cam.pkl','rb'))
cm=bpy.data.objects['Camera']; cm.data.type='ORTHO'; cm.data.ortho_scale=c['span']; cm.location=(c['cx'],-3,c['cz']); cm.rotation_euler=(math.radians(90),0,0)
sc.render.engine='BLENDER_WORKBENCH'; sh=sc.display.shading
sc.render.resolution_x=512; sc.render.resolution_y=512; sc.render.film_transparent=True; sc.view_settings.view_transform='Standard'
orig=[s.material for s in g.material_slots]; names=[m.name for m in orig]
key=bpy.data.materials.new('KEY'); key.diffuse_color=(0,1,0,1)
GROUPS={'brows':{'Eyebrow'},'eyes':{'Eyeball','Pupil'},'mouth':{'InnerMouth','Teeth','Gums','Tongue'}}
KEYS=['','head__Angry','head__BaringTeeth','head__Confused','head__Crying','head__Disappointed','head__DontTell','head__Hot','head__IDontKnow','head__Nerd',
 'head__Open-Mouthed','head__Sad','head__Sarcastic','head__Sick','head__Sleepy','head__Smirk','head__Surprise','head__TongueOut','head__PurseLips','head__PuckerLips',
 'head__Grin','head__Smile','head__MouthF','head__MouthO','head__StretchLips','head__MouthSpeak','head__MouthYell','head__EyesWide','head__EyesAfraid',
 'head__Wink L','head__Wink R','head__Blink_l,head__Blink_r','head__Brows-UpDown_l,head__Brows-UpDown_r','head__Brows-Together','head__Angel',
 'head__Blink_l=0.5,head__Blink_r=0.5','head__Blink_l=0.8,head__Blink_r=0.8','head__Sleepy=0.5','head__Wink L=0.5','head__Wink R=0.5','head__Smile=0.5','head__MouthSpeak=0.5','head__Sad=0.5','head__Angry=0.5','Smile','Frown','Crying2','Disp[leased','Pleading','ZAMN','Worried Eyes','Angry Eyes','Heart Pupils','Aoooga Eyes','Fangs','Bunny Teeth','Buck Teeth']
kb=g.data.shape_keys.key_blocks
def render(fn): sc.render.filepath=OUT+'parts2/'+fn; bpy.ops.render.render(write_still=True)
for i,k in enumerate(KEYS):
    for x in kb: x.value=0
    for n in [n for n in k.split(',') if n]:
        nm,_,v=n.partition('='); kb[nm].value=float(v or 1)
    tag='%02d'%i
    sh.light='FLAT'; sh.color_type='TEXTURE'; sh.show_cavity=False; sh.show_shadows=False; sh.show_specular_highlight=False
    for grp,mats in GROUPS.items():
        for si,s in enumerate(g.material_slots): s.material=orig[si] if names[si] in mats else key
        render(f'{tag}_{grp}.png')
    for si,s in enumerate(g.material_slots): s.material=orig[si]
    sh.light='STUDIO'; sh.color_type='SINGLE'; sh.single_color=(0.8,0.8,0.8); sh.show_cavity=True; sh.cavity_type='BOTH'
    render(f'{tag}_lit.png')
open(OUT+'parts2/keys.txt','w').write('\n'.join(KEYS))
