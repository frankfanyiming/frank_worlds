"""Model/geometry verification, not a browser or device FPS test."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'worlds/doraemon/web/public/models'
OUT=ROOT/'docs/evidence/nobi-rollback27';OUT.mkdir(exist_ok=True)
profile=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'desktop'
bpy.ops.wm.read_factory_settings(use_empty=True)
parts=[('mobile-v27/' if profile=='mobile' else '')+'nobi-home-v27','world-v11',('mobile-v23/' if profile=='mobile' else '')+'bedroom-v12']
for part in parts:bpy.ops.import_scene.gltf(filepath=str(BASE/(part+'.glb')))
# Inspect the actual restored center treads rather than the stale v10 metadata.
obj=bpy.data.objects['home_stairs']
vertices=[obj.matrix_world@v.co for v in obj.data.vertices]
bvh=BVHTree.FromPolygons(vertices,[tuple(p.vertices)for p in obj.data.polygons])
samples=[]
for i in range(16):
 y=1.30+i*.225
 hit=bvh.ray_cast(Vector((-13.05,y,4.4)),Vector((0,0,-1)))
 assert hit[0],('Missing stair tread',i)
 expected=.48+(i+1)*(3.15-.48)/16
 assert abs(hit[0].z-expected)<.007,(i,hit[0].z,expected)
 samples.append({'x':-13.05,'y':round(y,4),'z':round(hit[0].z,5)})
# All kitchen and circulation floor probes must land on the restored ground floor.
floor=bpy.data.objects['home_ground'];bvh=BVHTree.FromPolygons([floor.matrix_world@v.co for v in floor.data.vertices],[tuple(p.vertices)for p in floor.data.polygons])
for x,y in [(-11.5,1.1),(-11.5,1.8),(-12.0,6.5),(-14,2.1),(-12,7.2)]:
 hit=bvh.ray_cast(Vector((x,y,.60)),Vector((0,0,-1)))
 assert hit[0] and abs(hit[0].z-.48)<.007,('Missing floor',x,y,hit[0])
(OUT/(profile+'-geometry.json')).write_text(json.dumps({'profile':profile,'stairTreads':samples,'fiveGroundFloorProbes':True,'renderer':'Blender Cycles; not browser'},indent=2))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
scene.render.resolution_x=1120;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Review daylight');scene.world.use_nodes=True
bg=scene.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.67,.78,.88,1);bg.inputs['Strength'].default_value=.7
scene.view_settings.view_transform='AgX'
bpy.ops.object.light_add(type='SUN',location=(-5,-10,12));sun=bpy.context.object;sun.rotation_euler=(math.radians(32),math.radians(-25),math.radians(-25));sun.data.energy=2;sun.data.angle=math.radians(10)
def area(loc,target,energy,size):
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.data.energy=energy;o.data.shape='DISK';o.data.size=size;o.data.color=(1,.94,.84);o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
area((-10.6,8.3,2.3),(-11.8,5.8,1),120,2);area((-12.5,4.8,2.8),(-10.8,7.6,1),80,3);area((-5,-8,10),(-13,2,2),1800,10)
bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera
for name,loc,target,lens in [('kitchen',(-13.0,4.6,1.92),(-10.7,7.55,1.45),24),('exterior',(-2,-12.8,3),(-12.8,2.1,3.15),39)]:
 camera.location=loc;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.lens=lens;scene.render.filepath=str(OUT/(profile+'-'+name+'.png'));bpy.ops.render.render(write_still=True)
print('NOBI_MODEL_VERIFIED',profile,flush=True)
