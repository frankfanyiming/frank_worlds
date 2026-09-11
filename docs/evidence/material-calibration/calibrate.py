"""Compare constant linear RGB, generated image linear pixels, and pre-sRGB pixels.
Three identical planes, uniform white world illumination, standard transform.
Also compare original scene with GLB round-trip and sample embedded PNG bytes.
"""
import bpy, math, json
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parent
bpy.ops.wm.read_factory_settings(use_empty=True)
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=64;s.cycles.use_denoising=False
s.render.resolution_x=768;s.render.resolution_y=256;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.image_settings.color_depth='8'
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
w=bpy.data.worlds.new('Uniform white test light');w.use_nodes=True
bg=next(n for n in w.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(1,1,1,1);bg.inputs['Strength'].default_value=1;s.world=w
bpy.ops.object.camera_add(location=(0,0,5));cam=bpy.context.object;cam.rotation_euler=(0,0,0);cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=5;s.camera=cam
linear=.25;encoded=1.055*linear**(1/2.4)-.055
records=[]
for i,(name,value) in enumerate([('A_constant_linear',None),('B_generated_direct_linear',linear),('C_generated_preconverted_sRGB',encoded)]):
 m=bpy.data.materials.new(name);m.use_nodes=True;p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Base Color'].default_value=(linear,linear,linear,1);p.inputs['Roughness'].default_value=1;p.inputs['Specular IOR Level'].default_value=0
 rec={'name':name,'constant_linear':linear,'image_input':value}
 if value is not None:
  im=bpy.data.images.new(name,8,8,alpha=True,float_buffer=False);im.colorspace_settings.name='sRGB'
  im.pixels.foreach_set([v for _ in range(64) for v in [value,value,value,1]])
  rec['image_buffer_before_pack']=list(im.pixels[:4]);im.pack();rec['image_buffer_after_pack']=list(im.pixels[:4])
  rec['image_colorspace']=im.colorspace_settings.name;rec['image_is_float']=im.is_float
  tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;tex.interpolation='Closest';m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color'])
 bpy.ops.mesh.primitive_plane_add(size=1,location=(-1.55+i*1.55,0,0));o=bpy.context.object;o.name=name;o.scale=(1.24,1.24,1);o.data.materials.append(m)
 rec['render_sample_x']=round(384+(-1.55+i*1.55)*768/5);records.append(rec)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'calibration.blend'))
s.render.filepath=str(OUT/'01-original-principled.png');bpy.ops.render.render(write_still=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'calibration.glb'),export_format='GLB',export_apply=True,export_animations=False,export_cameras=False,export_lights=False)
# Capture source node output values through an emission shader, independent of lighting.
for rec in records:
 m=bpy.data.materials[rec['name']];p=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');out=next(n for n in m.node_tree.nodes if n.type=='OUTPUT_MATERIAL');e=m.node_tree.nodes.new('ShaderNodeEmission');e.inputs['Strength'].default_value=1
 if p.inputs['Base Color'].is_linked:m.node_tree.links.new(p.inputs['Base Color'].links[0].from_socket,e.inputs['Color'])
 else:e.inputs['Color'].default_value=(linear,linear,linear,1)
 m.node_tree.links.new(e.outputs[0],out.inputs['Surface'])
s.render.filepath=str(OUT/'02-original-emission.png');bpy.ops.render.render(write_still=True)
# Import the actual exported artifact and repeat the initial lit test in same scene.
for o in list(s.objects):
 if o.type=='MESH':bpy.data.objects.remove(o,do_unlink=True)
bpy.ops.import_scene.gltf(filepath=str(OUT/'calibration.glb'))
s.render.filepath=str(OUT/'03-glb-roundtrip-principled.png');bpy.ops.render.render(write_still=True)
(OUT/'experiment.json').write_text(json.dumps({'blender_version':bpy.app.version_string,'linear_gray':linear,'preencoded_gray':encoded,'scene':'three equal planes with identical normal, uniform white world strength 1, Cycles 64 samples, Standard/no-look/no-exposure','patches':records},indent=2)+'\n')
print('CALIBRATION_DONE',flush=True)
