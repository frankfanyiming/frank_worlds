extends SceneTree
## Read imported scene/resource dependencies without instantiating the game.
var used := {}
func scan(folder: String):
 var directory=DirAccess.open(folder)
 if not directory:return
 for file in directory.get_files():
  if file.get_extension() not in ["glb","gltf","tscn","scn","tres","res"]:continue
  for dependency in ResourceLoader.get_dependencies(folder.path_join(file)):
   var value=str(dependency)
   var at=value.find("res://")
   if at>=0:used[value.substr(at)]=true
   elif value.begins_with("uid://"):
    var id=ResourceUID.text_to_id(value.split("::")[0])
    if ResourceUID.has_id(id):used[ResourceUID.get_id_path(id)]=true
 for child in directory.get_directories():
  if not child.begins_with("."):scan(folder.path_join(child))
func _initialize():
 scan("res://")
 print("NATIVE_RESOURCE_DEPENDENCIES ",JSON.stringify(used.keys()))
 quit()
