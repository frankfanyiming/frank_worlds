extends SceneTree
func _initialize():call_deferred("run")
func run():
 for kind in ["panda","frog"]:
  var path="res://assets/house-lighting/"+kind+"-room.scn";var scene=load(path).instantiate();root.add_child(scene)
  for light in scene.get_node("BakedLights").get_children():
   if light is SpotLight3D:light.shadow_reverse_cull_face=true
  var packed=PackedScene.new();packed.pack(scene);print("RESAVE_SOURCE ",kind," ",ResourceSaver.save(packed,path,ResourceSaver.FLAG_COMPRESS));scene.queue_free()
 for i in range(2):await process_frame
 quit()
