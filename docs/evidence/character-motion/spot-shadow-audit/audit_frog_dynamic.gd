extends SceneTree
var scene:Node3D
var actor:Node3D
var house:Node3D
var meshes=[]
var lights=[]
var materials=[]
var report={}
func _initialize():call_deferred("run")
func run():
 root.size=Vector2i(1200,800);root.msaa_3d=Viewport.MSAA_4X
 DirAccess.make_dir_recursive_absolute("res://frog-dynamic-audit")
 scene=Node3D.new();root.add_child(scene);current_scene=scene
 house=load("res://assets/house-lighting/frog-room.scn").instantiate();scene.add_child(house)
 var environment=WorldEnvironment.new();scene.add_child(environment);environment.environment=Environment.new();var env=environment.environment;env.background_mode=Environment.BG_COLOR;env.background_color=Color("706c61");env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;env.ambient_light_color=Color("edf2ef");env.ambient_light_energy=.10;env.tonemap_mode=Environment.TONE_MAPPER_FILMIC
 house.get_node("LightmapGI").light_data=load(house.get_node("LightmapGI").get_meta("day_data"))
 for l in house.get_node("BakedLights").get_children():
  l.light_energy=l.get_meta("day_energy");l.light_color=Color(l.get_meta("day_color"))
  lights.append({"node":l,"shadow":l.shadow_enabled,"bias":l.shadow_bias,"normal_bias":l.shadow_normal_bias})
 actor=load("res://assets/frog.glb").instantiate();scene.add_child(actor);actor.position=Vector3(-16.1,.2,-10.3);actor.rotation.y=PI
 for mi in actor.find_children("*","MeshInstance3D",true,false):
  mi.gi_mode=GeometryInstance3D.GI_MODE_DYNAMIC;meshes.append(mi)
  for i in mi.mesh.get_surface_count():
   var mat=mi.get_active_material(i).duplicate();mi.set_surface_override_material(i,mat);materials.append({"material":mat,"normal_enabled":mat.normal_enabled})
 var key=DirectionalLight3D.new();key.name="DiagnosticDirectionalKey";scene.add_child(key);key.rotation_degrees=Vector3(-55,-35,0);key.light_energy=.23;key.light_color=Color("edf2ef");key.light_bake_mode=Light3D.BAKE_DYNAMIC;key.shadow_enabled=true;key.shadow_bias=.04;key.shadow_normal_bias=.70;key.directional_shadow_mode=DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS;key.directional_shadow_max_distance=18;key.visible=false
 var cam=Camera3D.new();scene.add_child(cam);cam.current=true;cam.near=.05;cam.position=Vector3(-14,2.1,-9);cam.look_at(Vector3(-15.2,1.03,-12.3));cam.fov=55
 report["lights"]=[]
 for row in lights:
  var l=row.node
  report.lights.append({"name":l.name,"type":l.get_class(),"shadow":l.shadow_enabled,"bias":l.shadow_bias,"normal_bias":l.shadow_normal_bias,"bake_mode":l.light_bake_mode,"energy":l.light_energy})
 report["materials"]=[]
 for row in materials:
  var m=row.material
  report.materials.append({"name":m.resource_name,"normal":m.normal_enabled,"normal_scale":m.normal_scale,"diffuse_mode":m.diffuse_mode,"shading_mode":m.shading_mode,"roughness":m.roughness,"metallic":m.metallic})
 for mode in ["01-dynamic-baseline","02-gi-disabled","03-normal-disabled","04-spot-shadows-disabled","05-gi-and-shadows-disabled","06-spot-bias-010","07-spot-normal-bias-080","08-frog-cast-shadow-disabled","09-frog-receive-shadows-disabled","10-window-0-shadow-disabled","11-window-1-shadow-disabled","12-window-2-shadow-disabled","13-spot-bias-100","14-spot-normal-bias-400","15-spot-reverse-cull","16-spot-bias-025","17-spot-bias-050","18-directional-key","19-directional-key-no-shadow"]:
  key.visible=false
  for mi in meshes:mi.gi_mode=GeometryInstance3D.GI_MODE_DYNAMIC;mi.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_ON
  for row in materials:row.material.normal_enabled=row.normal_enabled;row.material.disable_receive_shadows=false
  for row in lights:
   row.node.shadow_enabled=row.shadow;row.node.shadow_bias=row.bias;row.node.shadow_normal_bias=row.normal_bias;row.node.shadow_reverse_cull_face=false
  if mode in ["02-gi-disabled","05-gi-and-shadows-disabled"]:
   for mi in meshes:mi.gi_mode=GeometryInstance3D.GI_MODE_DISABLED
  if mode=="03-normal-disabled":
   for row in materials:row.material.normal_enabled=false
  if mode in ["04-spot-shadows-disabled","05-gi-and-shadows-disabled"]:
   for row in lights:
    if row.node is SpotLight3D:row.node.shadow_enabled=false
  if mode=="06-spot-bias-010":
   for row in lights:
    if row.node is SpotLight3D:row.node.shadow_bias=.10
  if mode=="07-spot-normal-bias-080":
   for row in lights:
    if row.node is SpotLight3D:row.node.shadow_normal_bias=.80
  if mode=="08-frog-cast-shadow-disabled":
   for mi in meshes:mi.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
  if mode=="09-frog-receive-shadows-disabled":
   for row in materials:row.material.disable_receive_shadows=true
  if mode in ["10-window-0-shadow-disabled","11-window-1-shadow-disabled","12-window-2-shadow-disabled"]:
   var index=int(mode.substr(10,1))
   house.get_node("BakedLights/Window_FrogWindow"+str(index)).shadow_enabled=false
  if mode=="13-spot-bias-100":
   for row in lights:
    if row.node is SpotLight3D:row.node.shadow_bias=1.0
  if mode=="14-spot-normal-bias-400":
   for row in lights:
    if row.node is SpotLight3D:row.node.shadow_normal_bias=4.0
  if mode=="15-spot-reverse-cull":
   for row in lights:
    if row.node is SpotLight3D:row.node.shadow_reverse_cull_face=true
  if mode in ["16-spot-bias-025","17-spot-bias-050"]:
   for row in lights:
    if row.node is SpotLight3D:row.node.shadow_bias=.25 if mode=="16-spot-bias-025" else .50
  if mode in ["18-directional-key","19-directional-key-no-shadow"]:
   for row in lights:
    if row.node is SpotLight3D:row.node.shadow_enabled=false
   key.visible=true;key.shadow_enabled=mode=="18-directional-key"
  for i in range(8):await process_frame
  await RenderingServer.frame_post_draw
  root.get_texture().get_image().save_png("res://frog-dynamic-audit/"+mode+".png")
 FileAccess.open("res://frog-dynamic-audit/properties.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
 quit()
