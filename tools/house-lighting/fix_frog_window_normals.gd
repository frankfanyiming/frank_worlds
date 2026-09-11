extends SceneTree
func _initialize():call_deferred("run")
func torus_id(p):
 var centers=[Vector3(-18.0513,4.25828,-16.0822),Vector3(-9.8409,2.42517,-13.54623),Vector3(-12.31166,4.33245,-16.19749)]
 var angles=[2.15,.33,1.06];var radii=[.729,.756,.648];var scale_=Vector3(5.6/4.72,(6.6-.2)/(6.24-.2),4.9/4.72)
 for i in 3:
  var d=(p-centers[i])/scale_;var radial=Vector3(cos(angles[i]),0,-sin(angles[i]));var a=d-radial*d.dot(radial)
  var centerline=a.normalized()*radii[i]-radial*.075
  if abs((d-centerline).length()-.09)<.003 and abs(a.length()-radii[i])<.094:return i
 return -1
func run():
 if FileAccess.get_sha256("res://assets/home-enclosure.glb")!="9bce017c78a3ce5b72b2a88b83c2e8cfc831d25ace50f1fc9a4ad823b34fdc3b":
  print("WINDOW_FIX_NOT_APPLICABLE: GLB differs from known legacy source; do not blindly flip corrected exports.");quit();return
 var path="res://assets/house-lighting/frog-room.tscn";var h=load(path).instantiate();root.add_child(h)
 if h.get_meta("window_normals_corrected",false):
  fix_reveal(h);var already=PackedScene.new();already.pack(h);ResourceSaver.save(already,path);quit();return
 var mi=h.get_node("home-enclosure/HomeDetails_05");var old=mi.mesh;var a=old.surface_get_arrays(0);var verts=a[Mesh.ARRAY_VERTEX];var norms=a[Mesh.ARRAY_NORMAL];var tangents=a[Mesh.ARRAY_TANGENT];var idx=a[Mesh.ARRAY_INDEX];var selected={};var counts=[0,0,0]
 for j in range(0,idx.size(),3):
  var t0=torus_id(mi.global_transform*verts[idx[j]]);var t1=torus_id(mi.global_transform*verts[idx[j+1]]);var t2=torus_id(mi.global_transform*verts[idx[j+2]])
  if t0>=0 and t0==t1 and t1==t2:
   var tmp=idx[j+1];idx[j+1]=idx[j+2];idx[j+2]=tmp;counts[t0]+=1
   for k in 3:selected[idx[j+k]]=true
 for v in selected:
  norms[v]=-norms[v]
  if tangents!=null and tangents.size()>v*4+3:tangents[v*4+3]=-tangents[v*4+3]
 print("TORUS_NORMAL_FIX ",counts," vertices ",selected.size())
 if counts!=[1280,1280,1280]:push_error("Selection mismatch; not saved");quit(2);return
 a[Mesh.ARRAY_NORMAL]=norms;a[Mesh.ARRAY_INDEX]=idx;a[Mesh.ARRAY_TANGENT]=tangents
 var m=ArrayMesh.new();m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,a);m.surface_set_material(0,old.surface_get_material(0));m.lightmap_size_hint=old.lightmap_size_hint;mi.mesh=m
 h.get_node("BakedLights/Lamp_table_candle").set_meta("bake_day_energy",.09)
 fix_reveal(h)
 h.set_meta("window_normals_corrected",true)
 var packed=PackedScene.new();packed.pack(h);print("FIX_SAVE ",ResourceSaver.save(packed,path));FileAccess.open("res://window-normal-fix.json",FileAccess.WRITE).store_string(JSON.stringify({"mesh":"home-enclosure/HomeDetails_05","triangles_per_ring":counts,"flipped_vertices":selected.size(),"positions_unchanged":true,"runtime_only":true,"day_candle_bake_energy":.09},"  "));quit()

func fix_reveal(h):
 if h.get_meta("window_reveals_corrected",false):return
 var mi=h.get_node("home-enclosure/HomeDetails_07");var old=mi.mesh;var a=old.surface_get_arrays(0);var idx=a[Mesh.ARRAY_INDEX];var norms=a[Mesh.ARRAY_NORMAL];var tangents=a[Mesh.ARRAY_TANGENT]
 assert(idx.size()==768*3,"Unexpected reveal topology")
 for j in range(0,idx.size(),3):var t=idx[j+1];idx[j+1]=idx[j+2];idx[j+2]=t
 for v in norms.size():
  norms[v]=-norms[v]
  if tangents!=null and tangents.size()>v*4+3:tangents[v*4+3]=-tangents[v*4+3]
 a[Mesh.ARRAY_INDEX]=idx;a[Mesh.ARRAY_NORMAL]=norms;a[Mesh.ARRAY_TANGENT]=tangents
 var m=ArrayMesh.new();m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,a);m.surface_set_material(0,old.surface_get_material(0));m.lightmap_size_hint=old.lightmap_size_hint;mi.mesh=m;h.set_meta("window_reveals_corrected",true);print("STONE_REVEAL_FIX 768 triangles")
