extends SceneTree
func _initialize():call_deferred("run")
func signature(mi):
 var dumpname=str(mi.get_parent().name)+"__"+str(mi.name)
 var prefix="baseline" if mi.get_parent().get_parent()==root else "runtime"
 var raw=mi.mesh.get_faces()
 for x in raw.size():raw[x]=mi.global_transform*raw[x]
 FileAccess.open("res://geometry-dumps/"+prefix+"__"+dumpname+".bin",FileAccess.WRITE).store_buffer(raw.to_byte_array())
 var triangles=[];var faces=mi.mesh.get_faces();var t=mi.global_transform
 for j in range(0,faces.size(),3):
  var vs=[]
  for k in range(3):
   var p=t*faces[j+k];vs.append("%d,%d,%d"%[roundi(p.x*10000),roundi(p.y*10000),roundi(p.z*10000)])
  vs.sort();triangles.append(";".join(vs))
 triangles.sort()
 return {"triangles":faces.size()/3,"sha256":"|".join(triangles).sha256_text(),"transform":str(t)}
func run():
 var report={};var pass_all=true
 for kind in ["panda","frog"]:
  var h=load("res://assets/house-lighting/"+kind+"-room.scn").instantiate();root.add_child(h);var results=[]
  for file in (["panda-home"] if kind=="panda" else ["home-enclosure","home-furnishings"]):
   var original=load("res://baseline/"+file+".scn").instantiate();root.add_child(original)
   var fresh=h.get_node(file)
   for mi in original.find_children("*","MeshInstance3D",true,false):
    var dest=fresh.get_node(original.get_path_to(mi));var a=signature(mi);var b=signature(dest);var ok=a==b;pass_all=pass_all and ok
    results.append({"node":file+"/"+str(original.get_path_to(mi)),"same_triangle_coordinates_and_transform":ok,"source":a,"runtime":b})
   original.queue_free()
  var deps=ResourceLoader.get_dependencies("res://assets/house-lighting/"+kind+"-room.scn");report[kind]={"geometry":results,"dependencies":Array(deps)};h.queue_free()
 report.pass_all=pass_all;FileAccess.open("res://geometry-closure-proof.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "));print("GEOMETRY_EQUIVALENT ",pass_all);quit(0 if pass_all else 1)
