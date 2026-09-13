extends SceneTree
var entries=[]
var world
func _initialize():call_deferred("run")
func run():
 var output=OS.get_environment("PROFILE_OUTPUT")
 if output.is_empty():push_error("Set PROFILE_OUTPUT to a writable report path");quit(2);return
 world=load("res://world.tscn").instantiate()
 if world.has_method("_save"):
  # Override before _ready loads/saves anything; profiling must not touch play saves.
  var isolated=output.get_base_dir().path_join("profile-userfs-"+str(Time.get_ticks_usec()))
  DirAccess.make_dir_recursive_absolute(isolated)
  world.save_path=isolated.path_join("test-save.json");world.photo_directory=isolated.path_join("photos")
 root.add_child(world)
 for i in range(12):await process_frame
 scan(world)
 entries.sort_custom(func(a,b):return a.triangles>b.triangles)
 var report={"world":ProjectSettings.get_setting("application/config/name"),"meshes":entries.size(),"triangles":0,"entries":entries}
 for e in entries:report.triangles+=e.triangles
 var file=FileAccess.open(output,FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));file.close()
 print("PROFILE ",report.world," meshes=",report.meshes," triangles=",report.triangles)
 quit()
func scan(node):
 if node is MeshInstance3D and node.mesh:
  var triangles=0
  for i in range(node.mesh.get_surface_count()):
   var a=node.mesh.surface_get_arrays(i);triangles+=(a[Mesh.ARRAY_INDEX].size() if a[Mesh.ARRAY_INDEX]!=null and a[Mesh.ARRAY_INDEX].size()>0 else a[Mesh.ARRAY_VERTEX].size())/3
  var lods=0
  if node.mesh is ArrayMesh:
   for s in node.mesh.get("_surfaces"):
    lods+=s.get("lods",[]).size()
  entries.append({"path":str(node.get_path()),"triangles":triangles,"surfaces":node.mesh.get_surface_count(),"lods":lods,"visible":node.is_visible_in_tree(),"shadow":node.cast_shadow,"size":str(node.get_aabb().size),"position":str(node.global_position)})
 for child in node.get_children():scan(child)
