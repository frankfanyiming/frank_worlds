extends SceneTree
var world
var folder="/private/tmp/character-lighting"
var skin: MeshInstance3D
var material: BaseMaterial3D
func _initialize():call_deferred("run")
func frames(n):
 for i in range(n):await process_frame
func shot(name):
 await frames(4)
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png(folder.path_join(name+".png"))
func find_skin(node):
 if node is MeshInstance3D and node.skin!=null:return node
 for child in node.get_children():
  var found=find_skin(child)
  if found:return found
 return null
func run():
 if OS.get_cmdline_user_args().size()>0:folder=OS.get_cmdline_user_args()[0]
 DirAccess.make_dir_recursive_absolute(folder)
 root.size=Vector2i(1080,720)
 world=load("res://world.tscn").instantiate()
 world.save_path=folder.path_join("audit-only-save.json");world.photo_directory=folder.path_join("audit-only-photos")
 world.auditing=true;world.input_locked=true;world.panda_roam_enabled=false
 root.add_child(world);await frames(20)
 world._enter_home("frog");world.frog.position=Vector3(-16.3,.23,-10.05);world.frog.velocity=Vector3.ZERO;world.mode=1
 world.overlay.visible=false;await frames(20)
 world.set_process(false);world.set_physics_process(false);world.animator.pause();world.panda_animator.pause()
 skin=find_skin(world.actor);material=skin.get_active_material(0).duplicate();skin.set_surface_override_material(0,material)
 var report={"per_pixel_enum":BaseMaterial3D.SHADING_MODE_PER_PIXEL,"material_shading":material.shading_mode,"camera":str(world.camera.global_transform),"lights":[]}
 for light in world.household_lights:
  if light.visible:report.lights.append({"name":light.name,"position":str(light.global_position),"energy":light.light_energy,"shadow_enabled":light.shadow_enabled,"bias":light.shadow_bias,"normal_bias":light.shadow_normal_bias})
 await shot("01-current")
 material.disable_receive_shadows=true;await shot("02-no-receive-shadows")
 material.disable_receive_shadows=false;material.normal_enabled=false;await shot("03-no-normal-map")
 material.disable_receive_shadows=true;await shot("04-no-shadow-no-normal")
 material.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;await shot("05-unlit-albedo")
 material.shading_mode=BaseMaterial3D.SHADING_MODE_PER_PIXEL;material.normal_enabled=true;material.disable_receive_shadows=false
 var changed=[]
 for light in world.household_lights:
  if light.visible and light.shadow_enabled:
   changed.append([light,light.shadow_normal_bias,light.shadow_bias]);light.shadow_normal_bias=.1;light.shadow_bias=.02
 await shot("06-smaller-normal-shadow-bias")
 for row in changed:row[0].shadow_normal_bias=row[1];row[0].shadow_bias=row[2]
 skin.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;await shot("07-no-self-cast-shadow")
 skin.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_ON
 root.mesh_lod_threshold=0.0
 await shot("08-lod-disabled")
 material.normal_enabled=false
 var debug=Shader.new();debug.code="shader_type spatial;render_mode unshaded;void fragment(){ALBEDO=NORMAL*.5+.5;}"
 var debug_material=ShaderMaterial.new();debug_material.shader=debug;skin.set_surface_override_material(0,debug_material)
 await shot("09-geometric-normal-debug")
 skin.set_surface_override_material(0,material)
 for light in world.household_lights:light.visible=false
 world.home_light.visible=false;world.window_light.visible=false;world.sky_fill.visible=false
 for light in world.room_lamps:light.visible=false
 world.environment.ambient_light_color=Color.WHITE;world.environment.ambient_light_energy=.35
 var white=DirectionalLight3D.new();world.add_child(white);white.rotation_degrees=Vector3(-35,-30,0);white.light_color=Color.WHITE;white.light_energy=.65;white.shadow_enabled=false
 await shot("10-one-white-light")
 world.environment.tonemap_mode=Environment.TONE_MAPPER_LINEAR
 await shot("11-white-light-linear-tonemap")
 white.visible=false
 world.environment.tonemap_mode=Environment.TONE_MAPPER_FILMIC
 world.home_light.visible=true;world.sky_fill.visible=true;world._apply_lighting()
 for light in world.household_lights:
  if light.visible and light is SpotLight3D:
   light.spot_angle=68;light.spot_attenuation=1.3;light.light_energy=.38;light.light_color=Color("fff4e5")
 await shot("12-soft-window-cones")
 world.environment.tonemap_mode=Environment.TONE_MAPPER_LINEAR
 await shot("13-soft-windows-linear-tonemap")
 world.environment.tonemap_mode=4
 await shot("14-soft-windows-agx-tonemap")
 for light in world.household_lights:
  if light.visible and light is SpotLight3D:light.light_energy=.50
 await shot("15-soft-windows-agx-energy-050")
 world.environment.tonemap_mode=Environment.TONE_MAPPER_FILMIC
 material.normal_enabled=true;world._apply_lighting()
 for light in world.household_lights:
  if light.visible and light is SpotLight3D:light.spot_angle=68;light.spot_attenuation=.35
 await shot("16-only-wider-cone-original-energy")
 for light in world.household_lights:
  if light.visible and light is SpotLight3D:light.spot_angle=42;light.spot_attenuation=1.3
 await shot("17-only-softer-attenuation-original-energy")
 for property in world.environment.get_property_list():
  if property.name=="tonemap_mode":report["tonemap_modes"]=property.hint_string
 FileAccess.open(folder.path_join("lighting-audit.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
 print("CHARACTER_LIGHTING_AUDIT ",folder)
 quit()
