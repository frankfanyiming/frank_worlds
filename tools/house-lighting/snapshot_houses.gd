extends SceneTree
func _initialize():call_deferred("run")
func v(a):return Vector3(a[0],a[1],a[2])
func run():
 root.size=Vector2i(1200,800);root.msaa_3d=Viewport.MSAA_4X
 var reports=[]
 for kind in ["panda","frog"]:
  var scene=Node3D.new();root.add_child(scene);current_scene=scene
  var house=load("res://assets/house-lighting/"+kind+"-room.scn").instantiate();scene.add_child(house)
  var environment=WorldEnvironment.new();scene.add_child(environment);environment.environment=Environment.new();var env=environment.environment;env.background_mode=Environment.BG_COLOR;env.background_color=Color("706c61");env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;env.ambient_light_color=Color("edf2ef");env.ambient_light_energy=.10;env.tonemap_mode=Environment.TONE_MAPPER_FILMIC
  var actor=load("res://assets/"+kind+".glb").instantiate();scene.add_child(actor);actor.position=Vector3(-1.35,.2,-.25) if kind=="panda" else Vector3(-16.1,.2,-10.3);actor.rotation.y=PI/2 if kind=="panda" else PI
  for mi in actor.find_children("*","MeshInstance3D",true,false):mi.gi_mode=GeometryInstance3D.GI_MODE_DYNAMIC
  var cam=Camera3D.new();scene.add_child(cam);cam.current=true;cam.near=.05
  var views={"close":[[-2.9,2.65,3],[-.15,.92,-.1],57],"overview":[[.35,4.05,4.42],[0,2,-.8],74],"tea":[[-2.3,1.63,2.95],[-.05,.78,0],55]} if kind=="panda" else {"close":[[-14,2.1,-9],[-15.2,1.03,-12.3],55],"overview":[[-14,4.7,-7.9],[-15.25,2.22,-12.55],70],"loft":[[-13.9,5.48,-9.1],[-15.25,3.77,-14.6],63]}
  for state in ["day","dusk"]:
   house.get_node("LightmapGI").light_data=load(house.get_node("LightmapGI").get_meta(state+"_data"))
   env.ambient_light_energy=.10 if state=="day" else .07
   for l in house.get_node("BakedLights").get_children():
    l.light_energy=l.get_meta(state+"_energy");l.light_color=Color(l.get_meta(state+"_color"))
    if l is SpotLight3D:l.shadow_reverse_cull_face=true
   for key in views:
    cam.position=v(views[key][0]);cam.look_at(v(views[key][1]));cam.fov=views[key][2]
    for i in range(15):await process_frame
    await RenderingServer.frame_post_draw
    root.get_texture().get_image().save_png("res://final-"+kind+"-"+state+"-"+key+".png")
   reports.append({"house":kind,"state":state,"baked_users":house.get_node("LightmapGI").light_data.get_user_count(),"actor_dynamic_meshes":actor.find_children("*","MeshInstance3D",true,false).size()})
  scene.queue_free();current_scene=null
  for i in range(5):await process_frame
 FileAccess.open("res://runtime-proof.json",FileAccess.WRITE).store_string(JSON.stringify(reports,"  "));quit()
