import bpy, math, json, sys, shutil
from pathlib import Path
from mathutils import Vector, Quaternion
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT
OUT=REPO/'worlds/doraemon/web/public/community-models'
OUT.mkdir(parents=True,exist_ok=True)
def clear():
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 for datablocks in [bpy.data.meshes,bpy.data.materials,bpy.data.images,bpy.data.armatures,bpy.data.actions]:
  for d in list(datablocks):
   if d.users==0:datablocks.remove(d)
def mat(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 bsdf=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) or m.node_tree.nodes.new('ShaderNodeBsdfPrincipled')
 output=next((n for n in m.node_tree.nodes if n.type=='OUTPUT_MATERIAL'),None) or m.node_tree.nodes.new('ShaderNodeOutputMaterial')
 m.node_tree.links.new(bsdf.outputs['BSDF'],output.inputs['Surface']);bsdf.inputs['Base Color'].default_value=(*color,1);bsdf.inputs['Roughness'].default_value=.77;return m
clear()
M={k:mat(k,c) for k,c in {'wood':(.38,.23,.12),'lightwood':(.62,.42,.23),'cream':(.85,.77,.55),'green':(.32,.45,.23),'leaf':(.21,.36,.16),'dark':(.12,.17,.13),'pink':(.79,.43,.42),'stone':(.46,.48,.39),'sand':(.70,.61,.43),'glass':(.96,.74,.35),'white':(.96,.92,.77)}.items()}
def cube(n,loc,scale,m,bevel=.04):
 bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=n;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 o.data.materials.append(M[m])
 if bevel:mod=o.modifiers.new('Soft edges','BEVEL');mod.width=bevel;mod.segments=3;o.modifiers.new('Normals','WEIGHTED_NORMAL')
 return o
def cyl(n,loc,r,depth,m,vertices=16):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=loc);o=bpy.context.object;o.name=n;o.data.materials.append(M[m]);mod=o.modifiers.new('Rim','BEVEL');mod.width=.02;mod.segments=2;o.modifiers.new('Normals','WEIGHTED_NORMAL');return o
def sphere(n,loc,scale,m):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=loc);o=bpy.context.object;o.name=n;o.scale=scale;o.data.materials.append(M[m]);return o
def export(name):
 bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=str(OUT/(name+'.glb')),export_format='GLB',export_animations=False,export_apply=True)
 for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
for name in ['tent','chair','table','lamp','sign','planter','rock','stump','flowers','fence','crate','mat','tile-grass','tile-sand']:
 if name=='tent':
  verts=[(-.8,-.8,0),(.8,-.8,0),(0,-.8,1.15),(-.8,.8,0),(.8,.8,0),(0,.8,1.15)]
  mesh=bpy.data.meshes.new('Canvas');mesh.from_pydata(verts,[],[(0,3,5,2),(1,2,5,4),(3,4,5)]);mesh.update();o=bpy.data.objects.new('Canvas',mesh);bpy.context.collection.objects.link(o);o.data.materials.append(M['cream']);mod=o.modifiers.new('Fabric thickness','SOLIDIFY');mod.thickness=.025
  cube('Groundsheet',(0,0,.025),(1.5,1.6,.05),'green');cyl('Front pole',(0,-.82,.57),.025,1.14,'wood');cyl('Back pole',(0,.82,.57),.025,1.14,'wood')
 elif name in ['chair','table']:
  w=.57 if name=='chair' else 1.35;d=.56 if name=='chair' else .85;h=.46 if name=='chair' else .62
  for x in [-w*.37,w*.37]:
   for y in [-d*.37,d*.37]:cube('Leg',(x,y,h/2),(.07,.07,h),'wood')
  for y in [-d/3,0,d/3]:cube('Plank',(0,y,h),(w,d/3-.012,.07),'lightwood')
  if name=='chair':
   for x in [-.23,.23]:cube('Back upright',(x,.22,.67),(.07,.07,.5),'wood')
   cube('Backrest',(0,.22,.85),(.55,.08,.19),'lightwood')
 elif name=='lamp':
  cyl('Base',(0,0,.05),.19,.1,'dark');cyl('Post',(0,0,.61),.035,1.12,'dark');cube('Warm glass',(0,0,1.21),(.3,.3,.33),'glass');cube('Top',(0,0,1.4),(.4,.4,.07),'dark');
  for x in [-.15,.15]:
   for y in [-.15,.15]:cube('Frame',(x,y,1.21),(.03,.03,.38),'dark')
 elif name=='sign':
  cube('Post',(0,0,.49),(.09,.09,.98),'wood');cube('Board',(0,0,.91),(.9,.1,.33),'lightwood');cube('Inset',(0,-.06,.91),(.76,.015,.2),'cream')
 elif name=='planter':
  cyl('Pot',(0,0,.18),.29,.36,'pink');cyl('Soil',(0,0,.37),.26,.025,'wood')
  for x,y in [(-.15,0),(.12,.08),(0,-.1)]:sphere('Leaf',(x,y,.55),(.20,.18,.3),'leaf')
 elif name=='rock':
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=.5,location=(0,0,.23));o=bpy.context.object;o.scale=(1,.72,.65);o.data.materials.append(M['stone'])
 elif name=='stump':
  cyl('Bark',(0,0,.2),.35,.4,'wood');cyl('Cut',(0,0,.405),.315,.018,'lightwood');cyl('Ring',(0,0,.418),.21,.008,'cream');cyl('Core',(0,0,.426),.18,.006,'lightwood')
 elif name=='flowers':
  for x,y,h in [(-.18,0,.36),(.16,.12,.44),(0,-.16,.30)]:
   cyl('Stem',(x,y,h/2),.018,h,'leaf');sphere('Center',(x,y,h),(.047,.047,.04),'glass')
   for i in range(6):a=i*math.tau/6;sphere('Petal',(x+math.cos(a)*.067,y+math.sin(a)*.067,h),(.055,.05,.028),'white')
 elif name=='fence':
  for x in [-.65,0,.65]:cube('Picket',(x,0,.42),(.13,.12,.84),'lightwood')
  for z in [.25,.6]:cube('Rail',(0,.05,z),(1.5,.1,.09),'wood')
 elif name=='crate':
  for z in [.10,.27,.44]:
   for y in [-.3,.3]:cube('Side slat',(0,y,z),(.68,.055,.14),'lightwood')
   for x in [-.32,.32]:cube('End slat',(x,0,z),(.055,.6,.14),'wood')
  cube('Bottom',(0,0,.035),(.65,.65,.07),'wood')
 elif name=='mat':
  cube('Picnic blanket',(0,0,.018),(1.35,1,.036),'cream',.02)
  for x in [-.5,0,.5]:cube('Stripe',(x,0,.039),(.12,.98,.003),'pink',0)
 else:
  cube('Island',(0,0,-.24),(8,8,.48),'wood',.12);cube('Ground',(0,0,-.035),(7.98,7.98,.08),'green' if name=='tile-grass' else 'sand',.08)
  cube('North south path',(0,0,.018),(1.1,8,.04),'sand',.03);cube('East west path',(0,0,.019),(8,1.1,.04),'sand',.03)
 export(name)
print('COMMUNITY_PROPS_READY',flush=True)
