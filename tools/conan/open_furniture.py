"""Adapt downloaded Poly Haven CC0 furniture to the authored room coordinates.

Files, authors, licenses and source checksums: open-assets-manifest.json.
The source project retains editable imported meshes, not a flattened billboard.
"""
import bpy,math,json,sys
from pathlib import Path
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).parent))
import reference_geometry as g
ROOT=Path(__file__).resolve().parents[2]
ASSETS=ROOT/'work/open-assets-r22'
def fit(asset,point,width=None,height=None,depth=None,yaw=0):
 before=set(bpy.data.objects)
 bpy.ops.import_scene.gltf(filepath=str(ASSETS/asset/(asset+'_1k.gltf')))
 imported=set(bpy.data.objects)-before;meshes=[o for o in imported if o.type=='MESH']
 deps=bpy.context.evaluated_depsgraph_get()
 # Freeze only the imported furniture rig. World actors and their rigs are never touched.
 for o in meshes:
  matrix=o.matrix_world.copy();evaluated=o.evaluated_get(deps)
  o.data=bpy.data.meshes.new_from_object(evaluated,preserve_all_data_layers=True,depsgraph=deps)
  o.modifiers.clear();o.parent=None;o.matrix_world=matrix
 for o in imported-set(meshes):bpy.data.objects.remove(o,do_unlink=True)
 points=[o.matrix_world@Vector(v) for o in meshes for v in o.bound_box]
 low=Vector([min(p[i] for p in points) for i in range(3)]);high=Vector([max(p[i] for p in points) for i in range(3)]);size=high-low
 factor=width/size.x if width else height/size.z if height else 1
 scale=Vector((width/size.x if width else factor,depth/size.y if depth else factor,height/size.z if height else factor))
 matrix=Matrix.Translation(g.G(point))@Matrix.Rotation(yaw,4,'Z')@Matrix.Diagonal((*scale,1))@Matrix.Translation(Vector((-(low.x+high.x)/2,-(low.y+high.y)/2,-low.z)))
 for o in meshes:
  o.matrix_world=matrix@o.matrix_world;o.name='CC0_'+asset+'_'+o.name;o['group']=g.GROUP;o['collision']=False;o['license']='CC0-1.0';o['source_url']='https://polyhaven.com/a/'+asset;g.OBJECTS.append(o)
  # Books and dial panels have many unseen faces. Retain bevel silhouettes while
  # reducing small details for the phone's Compatibility renderer.
  if len(o.data.polygons)>3000:
   dec=o.modifiers.new('Web furniture surface budget','DECIMATE');dec.ratio=.48 if asset=='book_encyclopedia_set_01' else .72
 return meshes

def agasa(room):
 remove=[]
 for o in g.OBJECTS:
  workbench=o.name.startswith('Research workbench') and abs(o.location.x-4.6)<.05
  legs=o.name.startswith('Research desk steel leg') and abs(o.location.y-5.5)<.05
  garage=o.name.startswith('Garage tool workbench')
  if workbench or legs or garage:remove.append(o)
 for o in remove:g.OBJECTS.remove(o);bpy.data.objects.remove(o,do_unlink=True)
 base=-3.12;g.GROUP='AgasaReference_CC0_Workshop'
 for x in [3.72,5.48]:fit('metal_office_desk',(x,base,-5.50),width=1.73,height=.88,depth=.77)
 fit('desk_lamp_arm_01',(6.08,base+.855,-5.30),height=.67,yaw=math.pi)
 fit('vintage_radio_transceiver',(4.0,base+.89,-5.50),width=.56)
 fit('metal_office_desk',(13.64,0,-3.60),width=2.8,height=.92,depth=.74,yaw=-math.pi/2)
 fit('desk_lamp_arm_01',(13.90,.89,-4.55),height=.68,yaw=math.pi/2)
 fit('vintage_radio_transceiver',(13.59,.925,-3.72),width=.57,yaw=-math.pi/2)
 # Colliders preserve the two existing workbench footprints, plus real pedestal volumes.
 for x in [3.72,5.48]:
  room['colliders'].append({'p':[x,base+.84,-5.5],'s':[1.73,.08,.77]})
 room['colliders'].append({'p':[13.64,.88,-3.6],'s':[.74,.08,2.8]})
 g.GROUP='AgasaReference_CC0_Living'
 fit('modern_wooden_cabinet',(4.42,.062,4.48),width=2.35,height=.68,depth=.50,yaw=-math.pi*.8)
 fit('book_encyclopedia_set_01',(4.45,.744,4.45),width=.55,yaw=-math.pi*.8)
 # Keep collision inside the angled console, clear of the front circulation lane.
 room['colliders'].append({'p':[4.42,.40,4.48],'s':[2.35,.68,.50],'r':-math.pi*.8})
 room['notes']['open_furniture22']=['Poly Haven metal_office_desk','desk_lamp_arm_01','vintage_radio_transceiver','modern_wooden_cabinet','book_encyclopedia_set_01']

def other_homes():
 import shutil
 for key in ['mouri','kudo']:
  g.init();g.OBJECTS.clear();g.GROUP=key.title()+'CC0Furniture'
  if key=='mouri':
   fit('book_encyclopedia_set_01',(-1.38,4.122,-1.80),width=.50)
  else:
   fit('book_encyclopedia_set_01',(8.31,.80,-.77),width=.48)
  name=key+'-open-furniture';g.export_asset(name)
  bpy.ops.wm.save_as_mainfile(filepath=str(g.OUT/(name+'.blend')))
  for variant in ['source','web-project']:
   dest=ROOT/f'worlds/conan/{variant}/assets/buildings';shutil.copy2(g.OUT/(name+'.glb'),dest/(name+'.glb'))
   p=dest/(key+'.json');d=json.loads(p.read_text());d['detail_assets']=list(dict.fromkeys(d.get('detail_assets',[])+[name]));p.write_text(json.dumps(d,ensure_ascii=False,indent=2))

if __name__=='__main__':other_homes()
