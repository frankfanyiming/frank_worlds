"""Blender-native, metre-scaled Beika reference geometry. Author points are Godot Y-up."""
import bpy,bmesh,math,json,random
from pathlib import Path
from mathutils import Vector
from math import sin,cos,pi,tau
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'worlds/conan/blender/reference-2026-09';OUT.mkdir(parents=True,exist_ok=True)
G=lambda p:(p[0],-p[2],p[1])
random.seed(91228)
GROUP='Structure';COLL=[];MATS={};OBJECTS=[]
def init():
 bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.scale_length=1
 return s

def rgba(h):
 def f(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
 return (*[f(int(h[i:i+2],16)/255) for i in [0,2,4]],1)
def mat(n,h,rough=.8,metal=0,alpha=1):
 m=bpy.data.materials.new(n);m.diffuse_color=rgba(h);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=rgba(h);p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
 if alpha<1:p.inputs['Alpha'].default_value=alpha;m.surface_render_method='DITHERED'
 MATS[n]=m;return m

def mark(o,m,collision=False,group=None):
 if m:o.data.materials.append(m)
 o['group']=group or GROUP;o['collision']=collision;OBJECTS.append(o)
 if m and 'Glass' in m.name:o.visible_shadow=False;o['cast_shadow']=False
 return o

def uv(o,scale=1):
 if o.type!='MESH':return
 layer=o.data.uv_layers.new(name='UVMap')
 for f in o.data.polygons:
  axis=max(range(3),key=lambda i:abs(f.normal[i]));axes=[i for i in range(3) if i!=axis]
  for li in f.loop_indices:
   v=o.data.vertices[o.data.loops[li].vertex_index].co;layer.data[li].uv=(v[axes[0]]/scale,v[axes[1]]/scale)

def mesh(n,vs,fs,m,collision=False,smooth=False,group=None,recalc=False):
 me=bpy.data.meshes.new(n);me.from_pydata([G(v) for v in vs],[],fs);me.update();o=bpy.data.objects.new(n,me);bpy.context.scene.collection.objects.link(o);mark(o,m,collision,group)
 if recalc:
  bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 uv(o)
 for f in me.polygons:f.use_smooth=smooth
 return o

def box(n,p,s,m,bevel=.012,collision=False,group=None,angle=0):
 vs=[(x*s[0]/2,y*s[1]/2,z*s[2]/2) for x,y,z in [(-1,-1,-1),(1,-1,-1),(1,-1,1),(-1,-1,1),(-1,1,-1),(1,1,-1),(1,1,1),(-1,1,1)]]
 o=mesh(n,vs,[(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],m,collision,group=group,recalc=True);o.location=G(p);o.rotation_euler.z=angle
 if bevel:b=o.modifiers.new('Soft manufactured edges','BEVEL');b.width=bevel;b.segments=2;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
 return o

def cyl(n,p,r,h,m,vertices=32,collision=False,group=None):
 me=bpy.data.meshes.new(n);bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=vertices,radius1=r,radius2=r,depth=h);bm.to_mesh(me);bm.free();o=bpy.data.objects.new(n,me);bpy.context.scene.collection.objects.link(o);o.location=G(p);mark(o,m,collision,group);uv(o)
 for f in o.data.polygons:f.use_smooth=len(f.vertices)==4
 b=o.modifiers.new('Turned edge','BEVEL');b.width=.007;b.segments=2;o.modifiers.new('Weighted normals','WEIGHTED_NORMAL');return o

def ell(n,p,s,m,group=None):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=1,location=G(p));o=bpy.context.object;o.name=n;o.scale=(s[0],s[2],s[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);mark(o,m,False,group)
 for f in o.data.polygons:f.use_smooth=True
 return o

def rod(n,a,b,r,m,group=None):
 va,vb=Vector(G(a)),Vector(G(b));o=cyl(n,((a[0]+b[0])/2,(a[1]+b[1])/2,(a[2]+b[2])/2),r,(vb-va).length,m,12,False,group);o.modifiers.clear();o.rotation_euler=(vb-va).to_track_quat('Z','Y').to_euler()
 for f in o.data.polygons:f.use_smooth=True
 return o

def line(n,pts,r,m,group=None,closed=False):
 cu=bpy.data.curves.new(n,'CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=r;cu.bevel_resolution=2;sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
 for p,v in zip(sp.points,pts):p.co=(*G(v),1)
 sp.use_cyclic_u=closed;o=bpy.data.objects.new(n,cu);bpy.context.scene.collection.objects.link(o);return mark(o,m,False,group)

def label(txt,p,size,m,angle=0,group=None):
 cu=bpy.data.curves.new('Sign '+txt,'FONT');cu.body=txt;cu.align_x='CENTER';cu.align_y='CENTER';cu.size=size;cu.extrude=.001
 path='/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc'
 if Path(path).exists():cu.font=bpy.data.fonts.load(path)
 o=bpy.data.objects.new('Sign '+txt,cu);bpy.context.scene.collection.objects.link(o);o.location=G(p);o.rotation_euler=(pi/2,0,angle);return mark(o,m,False,group)

def prism(n,polygon,low,high,m,collision=False,group=None):
 count=len(polygon);v=[(x,y,z) for y in [low,high] for x,z in polygon];f=[tuple(reversed(range(count))),tuple(range(count,2*count))]+[(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
 return mesh(n,v,f,m,collision,False,group,True)

def ring(n,c,r0,r1,low,high,m,a0=0,a1=tau,segments=64,collision=False,group=None):
 vs=[]
 for y in [low,high]:
  for r in [r0,r1]:
   for i in range(segments+1):a=a0+(a1-a0)*i/segments;vs.append((c[0]+r*cos(a),y,c[1]+r*sin(a)))
 N=segments+1;f=[]
 for i in range(segments):f.extend([(i,i+1,N+i+1,N+i),(2*N+i,3*N+i,3*N+i+1,2*N+i+1),(i,2*N+i,2*N+i+1,i+1),(N+i,N+i+1,3*N+i+1,3*N+i)])
 f.extend([(0,N,3*N,2*N),(N-1,3*N-1,4*N-1,2*N-1)])
 return mesh(n,vs,f,m,collision,False,group,True)

def boolean_hole(o,center,r,height=20):
 bpy.ops.mesh.primitive_cylinder_add(vertices=80,radius=r,depth=height,location=G(center));cut=bpy.context.object;mod=o.modifiers.new('Real stair opening','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cut;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(cut,do_unlink=True)

def export_asset(name,objects=None):
 objects=objects or OBJECTS;deps=bpy.context.evaluated_depsgraph_get();groups={};exp=[]
 for o in objects:
  if o.type not in ['MESH','CURVE','FONT']:continue
  key=o.get('group','Detail')+('_Collision' if o.get('collision') else '')
  for ma in o.data.materials:
   if ma and 'Glass' in ma.name:key+='_Glass';break
  groups.setdefault(key,[]).append(o)
 for key,obs in groups.items():
  vs=[];fs=[];uvs=[];mis=[];mats=[];smooth=[]
  for o in obs:
   eo=o.evaluated_get(deps);me=eo.to_mesh(preserve_all_data_layers=True,depsgraph=deps);me.transform(o.matrix_world);base=len(vs);vs.extend(tuple(v.co) for v in me.vertices);mapping=[]
   for ma in me.materials:
    if ma not in mats:mats.append(ma)
    mapping.append(mats.index(ma))
   u=me.uv_layers.active
   for p in me.polygons:fs.append(tuple(base+i for i in p.vertices));mis.append(mapping[p.material_index] if mapping else 0);smooth.append(p.use_smooth);uvs.extend(tuple(u.data[i].uv) if u else (0,0) for i in p.loop_indices)
   eo.to_mesh_clear()
  me=bpy.data.meshes.new(key);me.from_pydata(vs,[],fs);me.update()
  for ma in mats:me.materials.append(ma)
  u=me.uv_layers.new();u.data.foreach_set('uv',[c for p in uvs for c in p])
  for f,mi,sm in zip(me.polygons,mis,smooth):f.material_index=mi;f.use_smooth=sm
  o=bpy.data.objects.new(key,me);bpy.context.scene.collection.objects.link(o);o['source']='Blender authored';exp.append(o)
 bpy.ops.object.select_all(action='DESELECT')
 for o in exp:o.select_set(True)
 bpy.context.view_layer.objects.active=exp[0]
 bpy.ops.export_scene.gltf(filepath=str(OUT/(name+'.glb')),export_format='GLB',use_selection=True,export_extras=True,export_apply=True,export_cameras=False,export_lights=False)
 result={'file':name+'.glb','triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in exp),'meshes':len(exp),'source_objects':len(objects)}
 for o in exp:bpy.data.objects.remove(o,do_unlink=True)
 return result

def setup_render():
 s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True;s.render.resolution_x=1200;s.render.resolution_y=850;s.render.resolution_percentage=100
 if not s.world:s.world=bpy.data.worlds.new('Reference daylight')
 s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.68,.76,.88,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.35
 d=bpy.data.lights.new('Sun','SUN');d.energy=2.4;d.angle=.10;o=bpy.data.objects.new('Sun',d);s.collection.objects.link(o);o.rotation_euler=(.55,-.5,-.8)
 s.view_settings.view_transform='AgX'
 return s

def render_views(views,out,grey=False):
 out=Path(out);out.mkdir(parents=True,exist_ok=True);s=bpy.context.scene
 if grey:
  gm=mat('Review clay material','aeb5b5');s.view_layers[0].material_override=gm
 for i,v in enumerate(views):
  d=bpy.data.cameras.new(v['name']);o=bpy.data.objects.new(v['name'],d);s.collection.objects.link(o);o.location=G(v['p']);o.rotation_euler=(Vector(G(v['target']))-o.location).to_track_quat('-Z','Y').to_euler();d.lens=v.get('lens',36);s.camera=o;s.render.filepath=str(out/(f'{i+1:02}-'+v['name']+'.png'));bpy.ops.render.render(write_still=True)
 s.view_layers[0].material_override=None
