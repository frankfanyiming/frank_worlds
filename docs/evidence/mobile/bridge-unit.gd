extends SceneTree
func _initialize():
 var base=OS.get_environment("XLANDS_REPO").trim_suffix("/")+"/"
 for folder in ["worlds/frog/source/","worlds/conan/web-project/"]:
  var script=load(base+folder+"xlands_bridge.gd")
  assert(script!=null)
  var bridge=script.new()
  bridge.labels=JSON.parse_string(FileAccess.get_file_as_string(base+folder+"translations.json"))
  var popup=PopupMenu.new();popup.add_item("相册",4);popup.set_item_metadata(0,{"p":[1,2,3]})
  bridge.locale="en";bridge._translate(popup);assert(popup.get_item_text(0)=="Album")
  bridge._translate(popup);assert(popup.get_item_text(0)=="Album");assert(popup.get_item_metadata(0).p==[1,2,3])
  popup.set_item_text(0,"行囊");bridge._translate(popup);assert(popup.get_item_text(0)=="Travel bag")
  bridge.locale="ja";bridge._translate(popup);assert(popup.get_item_text(0)=="旅じたく")
  for action in ["left","right","forward","back"]:
   if not InputMap.has_action(action):InputMap.add_action(action)
  bridge._web_move([.7,-.4]);assert(abs(Input.get_action_strength("right")-.7)<.001);assert(abs(Input.get_action_strength("forward")-.4)<.001)
  bridge._web_move([0,0]);assert(Input.get_action_strength("right")==0);assert(Input.get_action_strength("forward")==0)
  popup.free();bridge.free()
  print("PASS "+folder+" script parse, popup retranslation + metadata preserved, analog move + release")
 quit(0)
