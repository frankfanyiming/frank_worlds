extends SceneTree

func _initialize():
 call_deferred("run")

func run():
 var report={"renderer":ProjectSettings.get_setting("rendering/renderer/rendering_method"),"characters":{}}
 for species in ["frog","panda"]:
  var model=load("res://assets/"+species+".glb").instantiate()
  root.add_child(model)
  var meshes=[]
  inspect_node(model,meshes)
  report.characters[species]=meshes
  model.queue_free()
 var args=OS.get_cmdline_user_args()
 var out=args[0] if args.size()>0 else "/private/tmp/character-materials.json"
 FileAccess.open(out,FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
 print(JSON.stringify(report))
 quit()

func texture_info(texture):
 if texture==null:return null
 var im=texture.get_image()
 return {"class":texture.get_class(),"path":texture.resource_path,"size":[texture.get_width(),texture.get_height()],"decoded_data_hex_md5":im.get_data().hex_encode().md5_text() if im!=null else "unavailable"}

func inspect_node(node,records):
 if node is MeshInstance3D:
  var mesh=node.mesh
  var entry={"node":str(node.get_path()),"lod_bias":node.lod_bias,"cast_shadow":node.cast_shadow,"skin_bind_count":node.skin.get_bind_count() if node.skin else 0,"mesh":mesh.resource_path,"shadow_mesh":mesh.shadow_mesh!=null,"surfaces":[]}
  for i in range(mesh.get_surface_count()):
   var arrays=mesh.surface_get_arrays(i)
   var material=node.get_active_material(i)
   var normals=arrays[Mesh.ARRAY_NORMAL]
   var distinct={}
   for normal in normals:distinct[str(normal.snapped(Vector3(.001,.001,.001)))]=true
   var surface={"vertices":arrays[Mesh.ARRAY_VERTEX].size(),"indices":arrays[Mesh.ARRAY_INDEX].size(),"normals":normals.size(),"distinct_normals_001":distinct.size(),"format":mesh.surface_get_format(i)}
   if material is BaseMaterial3D:
    surface["material"]={"class":material.get_class(),"name":material.resource_name,"path":material.resource_path,"albedo_color":str(material.albedo_color),"albedo":texture_info(material.albedo_texture),"normal_enabled":material.normal_enabled,"normal_scale":material.normal_scale,"normal":texture_info(material.normal_texture),"roughness":material.roughness,"roughness_texture":texture_info(material.roughness_texture),"metallic":material.metallic,"shading_mode":material.shading_mode,"cull_mode":material.cull_mode,"disable_receive_shadows":material.disable_receive_shadows}
   if mesh.shadow_mesh:
    var sa=mesh.shadow_mesh.surface_get_arrays(i)
    surface["shadow_vertices"]=sa[Mesh.ARRAY_VERTEX].size()
    surface["shadow_bones"]=sa[Mesh.ARRAY_BONES].size() if sa[Mesh.ARRAY_BONES]!=null else 0
   entry.surfaces.append(surface)
  records.append(entry)
 for child in node.get_children():inspect_node(child,records)
