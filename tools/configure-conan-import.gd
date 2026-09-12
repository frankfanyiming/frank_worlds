extends SceneTree
## Runs after the first editor import has generated .glb.import files.
## ConfigFile preserves unrelated advanced import settings and UID metadata.
func _initialize():
 var changed_files:Array=[]
 for key in ["conan","agasa"]:
  var path="res://assets/"+key+".glb.import"
  var config=ConfigFile.new()
  if config.load(path)!=OK:
   push_error("Import the project once before configuring: "+path);quit(2);return
  var changed=false
  if config.get_value("params","gltf/embedded_image_handling",1)!=2:
   config.set_value("params","gltf/embedded_image_handling",2);changed=true
  var subresources:Dictionary=config.get_value("params","_subresources",{})
  var nodes:Dictionary=subresources.get("nodes",{})
  var animation_node:Dictionary=nodes.get("PATH:AnimationPlayer",{})
  for option in ["optimizer/enabled","compression/enabled"]:
   if not animation_node.has(option) or animation_node[option]!=false:animation_node[option]=false;changed=true
  if changed:
   nodes["PATH:AnimationPlayer"]=animation_node;subresources["nodes"]=nodes
   config.set_value("params","_subresources",subresources)
   if config.save(path)!=OK:push_error("Could not save: "+path);quit(3);return
   changed_files.append(path)
 print("CONAN_IMPORT_CONFIGURATION ",JSON.stringify({"changed":not changed_files.is_empty(),"files":changed_files}))
 quit()
