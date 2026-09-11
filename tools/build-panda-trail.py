"""Blender-authored path to Panda's garden, with a deterministic planting clearance.

The previous woodland GLB is retained as the input so repeated runs are idempotent.
The original editable woodland source is kept separately in the project archive.
"""
from pathlib import Path
import math, shutil, json
import bpy, bmesh

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'worlds/frog/source/assets'
NATIVE=ROOT/'worlds/frog/blender'
NATIVE.mkdir(parents=True,exist_ok=True)
source=NATIVE/'woodland-before-panda.glb'
if not source.exists():shutil.copyfile(ASSETS/'woodland.glb',source)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(source))
removed=0
for obj in list(bpy.data.objects):
    if obj.type!='MESH' or not obj.name.startswith('Vegetation_'):continue
    bm=bmesh.new();bm.from_mesh(obj.data)
    faces=[]
    for face in bm.faces:
        p=obj.matrix_world @ face.calc_center_median()
        if math.hypot(p.x-26,p.y+13)<4.4 and p.z<2.0:faces.append(face)
    removed+=len(faces)
    if faces:
        bmesh.ops.delete(bm,geom=faces,context='FACES');bm.to_mesh(obj.data);obj.data.update()
    bm.free()

def terrain(x,y):
    edge=max(0,(math.hypot(x*.9,y)-27)/9)
    return .12+.16*math.sin(x*.20)*math.cos(y*.16)+.08*math.sin(x*.6+y*.32)+edge*edge*1.8

material=bpy.data.materials.new('Panda garden soft ochre trail')
material.use_nodes=True
shader=next(node for node in material.node_tree.nodes if node.type=='BSDF_PRINCIPLED')
shader.inputs['Base Color'].default_value=(.49,.36,.20,1)
shader.inputs['Roughness'].default_value=.97
points=[(19.4,-11.7),(21,-13.8),(21.8,-16.8),(24,-18.8),(26,-18.8),(26,-17.2)]
vertices=[];faces=[]
for k,(a,b) in enumerate(zip(points,points[1:])):
    dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy);count=max(3,int(length*8))
    start=len(vertices)
    for i in range(count+1):
        t=i/count;x=a[0]+dx*t;y=a[1]+dy*t
        width=.70+.05*math.sin(t*3+k)
        for side in [-1,1]:
            xx=x-dy/length*side*width;yy=y+dx/length*side*width
            vertices.append((xx,yy,terrain(xx,yy)+.025))
    for i in range(count):
        q=start+i*2;faces.append((q,q+1,q+3,q+2))
mesh=bpy.data.meshes.new('PandaTrail');mesh.from_pydata(vertices,[],faces);mesh.update()
obj=bpy.data.objects.new('PandaTrail',mesh);bpy.context.collection.objects.link(obj);obj.data.materials.append(material)
bpy.ops.wm.save_as_mainfile(filepath=str(NATIVE/'panda-garden-integration.blend'))
bpy.ops.export_scene.gltf(filepath=str(ASSETS/'woodland.glb'),export_format='GLB',export_apply=True,export_animations=False,export_lights=False,export_cameras=False)
(NATIVE/'panda-garden-integration.json').write_text(json.dumps({'generator':'Blender','removed_low_plant_faces':removed,'house_position_godot':[26,.25,13],'trail_blender':points,'retained_base':source.name},indent=2)+'\n')
print('PANDA_GARDEN_READY',removed)
