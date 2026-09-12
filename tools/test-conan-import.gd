extends SceneTree
## Run against a newly imported two-GLB project to catch importer key reduction.
var checks:Array=[]
var resources:Dictionary={}
func _initialize():call_deferred("run")
func animation_in(n:Node)->AnimationPlayer:
 if n is AnimationPlayer:return n
 for child in n.get_children():
  var a=animation_in(child)
  if a:return a
 return null
func textures_in(n:Node,found:Array):
 if n is MeshInstance3D:
  for surface in n.mesh.get_surface_count():
   var material=n.get_active_material(surface)
   if material is StandardMaterial3D and material.albedo_texture:
    found.append({"path":material.albedo_texture.resource_path,"width":material.albedo_texture.get_width(),"height":material.albedo_texture.get_height()})
 for child in n.get_children():textures_in(child,found)
func run():
 for key in ["conan","agasa"]:
  var node=load("res://assets/"+key+".glb").instantiate();root.add_child(node)
  var animation=animation_in(node);var textures:Array=[];textures_in(node,textures)
  checks.append({"check":key+"_embedded_texture","passed":not textures.is_empty() and textures.all(func(t):return ".glb::" in t.path and t.width>=1024)})
  checks.append({"check":key+"_seven_actions","passed":animation!=null and ["Idle","Walk","Run","Wave","Talk","Read","Sit"].all(func(name):return animation.has_animation(name))})
  resources[key]={"textures":textures,"clips":animation.get_animation_list()}
  if key=="conan":
   var walk=animation.get_animation("Walk");var found=false
   for track in walk.get_track_count():
    if walk.track_get_type(track)==Animation.TYPE_ROTATION_3D and str(walk.track_get_path(track)).ends_with(":LeftShin"):
     var q=walk.rotation_track_interpolate(track,.4);found=true
     resources[key]["left_shin_x_at_walk_0_4"]=q.x
     checks.append({"check":"required_left_shin_key_survives_import","passed":abs(q.x-.271376371)<.00001,"observed_quaternion_x":q.x,"expected_raw_glb_x":.271376371})
   if not found:checks.append({"check":"left_shin_track_exists","passed":false})
  node.queue_free()
 for i in range(4):await process_frame
 var report={"engine":Engine.get_version_info().string,"checks":checks,"resources":resources}
 if not OS.get_cmdline_user_args().is_empty():FileAccess.open(OS.get_cmdline_user_args()[0],FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
 print("CONAN_FRESH_IMPORT_PROOF ",JSON.stringify(report))
 quit(0 if checks.all(func(c):return c.passed) else 1)
