"""A shared Blender scene for neighborhood relationships; this is not a Godot/Web screenshot."""
import sys,json,bpy,math
from pathlib import Path
from mathutils import Matrix,Vector
sys.path.insert(0,str(Path(__file__).parent));import reference_geometry as g
from reference_geometry import *
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'worlds/conan/blender/reference-2026-09';ASSET=ROOT/'worlds/conan/web-project/assets'
S=init();bpy.ops.import_scene.gltf(filepath=str(ASSET/'street.glb'))
for key in ['mouri','kudo','agasa','street-block']:
 spec=json.loads((ASSET/'buildings'/f'{key}.json').read_text());before=set(bpy.context.scene.objects);bpy.ops.import_scene.gltf(filepath=str(ASSET/'buildings'/f'{key}.glb'));new=set(bpy.context.scene.objects)-before;T=Matrix.Translation(Vector(G(spec['origin'])))@Matrix.Rotation(float(spec.get('yaw',0)),4,'Z')
 for o in new:
  if not o.parent or o.parent not in new:o.matrix_world=T@o.matrix_world
 for o in new:
  if 'Glass' in o.name:o.visible_shadow=False
# Dynamic Tripo characters/cars remain separate runtime assets, intentionally absent from architectural proof.
setup_render();S.cycles.samples=20
views=[{'name':'毛利事务所与连排街面','p':[37,19,-30],'target':[.5,5.2,-4],'lens':37},{'name':'博士宅与工藤邻居关系','p':[82,36,46],'target':[56,3.1,-3],'lens':42},{'name':'博士后塔车库与门廊','p':[87,15,-30],'target':[66,3.0,-8],'lens':38}]
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'beika-reference-study.blend'),compress=True);render_views(views,ROOT/'docs/evidence/conan-architecture/shared-scene');print('SHARED_REFERENCE_STUDY_DONE')
