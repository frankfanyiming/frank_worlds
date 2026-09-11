extends SceneTree
func _initialize():call_deferred("run")
func run():
 root.size=Vector2i(1000,800);root.msaa_3d=Viewport.MSAA_4X
 for kind in ["frog","panda"]:
  var scene=Node3D.new();root.add_child(scene);current_scene=scene
  var house=load("res://assets/house-lighting/"+kind+"-room.scn").instantiate();scene.add_child(house)
  house.get_node("LightmapGI").light_data=load(house.get_node("LightmapGI").get_meta("day_data"))
  for l in house.get_node("BakedLights").get_children():l.light_energy=l.get_meta("day_energy");l.light_color=Color(l.get_meta("day_color"))
  var e=WorldEnvironment.new();scene.add_child(e);e.environment=Environment.new();e.environment.background_mode=Environment.BG_COLOR;e.environment.background_color=Color("706c61");e.environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;e.environment.ambient_light_color=Color("edf2ef");e.environment.ambient_light_energy=.1;e.environment.tonemap_mode=Environment.TONE_MAPPER_FILMIC
  var actor=load("res://assets/"+kind+".glb").instantiate();scene.add_child(actor)
  for mi in actor.find_children("*","MeshInstance3D",true,false):mi.gi_mode=GeometryInstance3D.GI_MODE_DYNAMIC
  var camera=Camera3D.new();scene.add_child(camera);camera.current=true;camera.near=.05;camera.fov=52
  var anim=actor.find_children("*","AnimationPlayer",true,false)[0]
  var cases=[{"name":"front-idle","position":Vector3(-16.6,.2,-9.7),"yaw":PI,"clip":"Idle","t":.0},{"name":"quarter-walk","position":Vector3(-16.8,.2,-11.30),"yaw":PI*.65,"clip":"Walk","t":.2},{"name":"back-jump","position":Vector3(-16.8,.7,-9.7),"yaw":0.,"clip":"JumpAir","t":.2}] if kind=="frog" else [{"name":"quarter-walk","position":Vector3(-1.35,.2,-.25),"yaw":PI/2,"clip":"Walk","t":.2}]
  for c in cases:
   actor.position=c.position;actor.rotation.y=c.yaw;anim.play(c.clip);anim.seek(c.t,true);anim.pause()
   camera.position=Vector3(-14,2.1,-9) if kind=="frog" else Vector3(-2.9,2.65,3)
   camera.look_at(actor.position+Vector3.UP*.62)
   for reverse in [false,true]:
    for l in house.get_node("BakedLights").get_children():
     if l is SpotLight3D:l.shadow_reverse_cull_face=reverse
    for i in range(10):await process_frame
    await RenderingServer.frame_post_draw
    root.get_texture().get_image().save_png("res://frog-dynamic-audit/verify-"+kind+"-"+c.name+("-reverse" if reverse else "-baseline")+".png")
  scene.queue_free();current_scene=null
  for i in range(5):await process_frame
 quit()
