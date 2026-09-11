"""Recolor the existing Blender rock shell, preserving its doors and window bores.

First run: blender --background --python this-file -- /path/to/original-world.blend
Later runs can use the saved, isolated frog-stone-shell.blend in this repository.
"""
from pathlib import Path
import sys
import bpy
import numpy as np

root = Path(__file__).resolve().parents[1]
native = root/'worlds/frog/blender/frog-stone-shell.blend'
args = sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
bpy.ops.wm.open_mainfile(filepath=str(Path(args[0]) if args else native))
selected = [o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('Rock shelter solid wall','Individual arch stone','Arch jamb stone'))]
assert selected, 'The editable Blender stone shell was not found'
for obj in list(bpy.data.objects):
    if obj not in selected: bpy.data.objects.remove(obj,do_unlink=True)

mat = bpy.data.materials.new('Natural grey limestone exterior')
mat.use_nodes=True
bs = mat.node_tree.nodes.get('Principled BSDF')
bs.inputs['Base Color'].default_value=(.30,.335,.345,1)
bs.inputs['Roughness'].default_value=.98
mat.diffuse_color=(.30,.335,.345,1)
# Deterministic, baked mineral variation is exported as a regular GLB texture.
n=512
rng=np.random.default_rng(911)
yy,xx=np.mgrid[0:n,0:n]/n
field=np.zeros((n,n))
for grid,weight in [(4,.48),(11,.28),(31,.16),(91,.08)]:
    values=rng.random((grid+1,grid+1));gx=xx*grid;gy=yy*grid
    ix=gx.astype(int);iy=gy.astype(int);u=gx-ix;v=gy-iy
    u=u*u*(3-2*u);v=v*v*(3-2*v)
    field+=weight*((1-v)*((1-u)*values[iy,ix]+u*values[iy,ix+1])+v*((1-u)*values[iy+1,ix]+u*values[iy+1,ix+1]))
pixels=np.ones((n,n,4),dtype=np.float32)
for channel,base in enumerate([.255,.282,.293]):pixels[:,:,channel]=base+field*.16
image=bpy.data.images.new('Natural limestone mineral color',n,n);image.pixels.foreach_set(pixels.ravel());image.pack()
texture=mat.node_tree.nodes.new('ShaderNodeTexImage');texture.image=image
mat.node_tree.links.new(texture.outputs['Color'],bs.inputs['Base Color'])
for obj in selected:
    obj.data.materials.clear();obj.data.materials.append(mat)
    for polygon in obj.data.polygons:polygon.material_index=0
bpy.ops.outliner.orphans_purge(do_local_ids=True,do_linked_ids=True,do_recursive=True)
native.parent.mkdir(exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(native))
bpy.ops.object.select_all(action='SELECT');bpy.context.view_layer.objects.active=selected[0]
bpy.ops.object.join();bpy.context.object.name='StoneShellExterior'
bpy.ops.export_scene.gltf(filepath=str(root/'worlds/frog/source/assets/stone-shell.glb'),export_format='GLB',export_apply=True,export_animations=False,export_lights=False,export_cameras=False)
print('STONE_SHELL_EXPORTED')
