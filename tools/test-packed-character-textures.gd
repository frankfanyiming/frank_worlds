extends SceneTree
# Run against the exported PCK, not only the editable project.
func _initialize():call_deferred("run")
func run():
 var report={"characters":[],"passed":true};var output=OS.get_cmdline_user_args()[0] if OS.get_cmdline_user_args().size() else "user://packed-character-textures.json"
 for name in ["frog","panda"]:
  var path="res://assets/"+name+".glb";var res=load(path);var item={"name":name,"scene_loaded":res!=null,"textures":[],"passed":res!=null}
  if res:
   var actor=res.instantiate();root.add_child(actor)
   for mi in actor.find_children("*","MeshInstance3D",true,false):
    for i in mi.mesh.get_surface_count():
     var mat=mi.get_active_material(i)
     if not mat:continue
     for prop in mat.get_property_list():
      if not (prop.usage & PROPERTY_USAGE_STORAGE):continue
      var val=mat.get(prop.name)
      if val is Texture2D:
       var valid=val.get_width()>0 and val.get_height()>0
       item.textures.append({"property":str(prop.name),"path":val.resource_path,"width":val.get_width(),"height":val.get_height(),"valid":valid});item.passed=item.passed and valid
   var roles=[]
   for texture in item.textures:roles.append(texture.property)
   for required in ["albedo_texture","metallic_texture","roughness_texture"]:
    if required not in roles:item.passed=false
   actor.queue_free()
  report.characters.append(item);report.passed=report.passed and item.passed
 for i in range(3):await process_frame
 FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"  "));print("PACKED_CHARACTER_TEXTURES ",JSON.stringify(report));quit(0 if report.passed else 1)
