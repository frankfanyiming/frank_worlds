extends Node
# The browser owns one interface layer. Native controls keep their callbacks but
# never paint behind a web sheet. Gameplay remains in the world scripts.
var callbacks=[]
var music: AudioStreamPlayer
var locale="zh-CN"
var labels={}
var tick=0.0
var mobile_mode=false
var mobile_size=Vector2.ZERO
var menu_was_open=false
var panel_was_locked=false
var external_locked=false
var applied_lock=false
var is_frog=false
var last_state=""
var last_panel_id=0
var panel_cache={}
var panel_buttons={}
func _ready():
 is_frog=get_parent().has_method("_interact")
 if FileAccess.file_exists("res://translations.json"):labels=JSON.parse_string(FileAccess.get_file_as_string("res://translations.json"))
 if OS.has_feature("web"):
  locale=str(JavaScriptBridge.eval("new URLSearchParams(location.search).get('lang') || 'zh-CN'"))
  var win=JavaScriptBridge.get_interface("window")
  for pair in [["xlandsInput",_web_input],["xlandsSound",_web_sound],["xlandsMove",_web_move],["xlandsLook",_web_look],["xlandsMenuAction",_web_menu_action],["xlandsUIAction",_web_ui_action]]:
   var cb=JavaScriptBridge.create_callback(pair[1]);callbacks.append(cb);win[pair[0]]=cb
  _update_mobile_layout()
  var canvas=get_parent().get("hud" if is_frog else "ui")
  if is_instance_valid(canvas):canvas.hide()
  JavaScriptBridge.eval("window.parent.postMessage({type:'xlands-ready'},'*')")
 if ResourceLoader.exists("res://assets/forest-original.wav"):
  music=AudioStreamPlayer.new();music.stream=load("res://assets/forest-original.wav");music.volume_db=-3;add_child(music);music.finished.connect(func():music.play());music.play()
  if OS.has_feature("web"):AudioServer.set_bus_mute(0,JavaScriptBridge.eval("new URLSearchParams(location.search).get('sound') !== '1'"))
func _web_sound(args):
 if args.size():AudioServer.set_bus_mute(0,not bool(args[0]))
func _locked():
 return menu_was_open or panel_was_locked or external_locked
func _web_input(args):
 if args.size()<2:return
 var action=str(args[0]);var pressed=bool(args[1])
 if pressed and _locked():return
 if action in ["forward","back","left","right","run","jump"]:
  if not InputMap.has_action(action):return
  if pressed:Input.action_press(action)
  else:Input.action_release(action)
 elif action in ["interact","view"]:
  var e=InputEventKey.new();e.keycode=KEY_E if action=="interact" else (KEY_C if is_frog else KEY_V);e.physical_keycode=e.keycode;e.pressed=pressed;Input.parse_input_event(e)
func _web_move(args):
 if args.size()<2:return
 var x=clamp(float(args[0]),-1.0,1.0);var y=clamp(float(args[1]),-1.0,1.0)
 if _locked():x=0;y=0
 var values={"left":max(-x,0.0),"right":max(x,0.0),"forward":max(-y,0.0),"back":max(y,0.0)}
 for action in values:
  if not InputMap.has_action(action):continue
  if values[action]>.001:Input.action_press(action,values[action])
  else:Input.action_release(action)
func _web_look(args):
 if args.size()<2 or _locked():return
 if get_parent().has_method("_touch_look"):get_parent()._touch_look(Vector2(float(args[0]),float(args[1])))
func _update_mobile_layout():
 if not OS.has_feature("web"):return
 var values=JSON.parse_string(str(JavaScriptBridge.eval("JSON.stringify([innerWidth,innerHeight,matchMedia('(any-pointer:coarse)').matches])")))
 if not values:return
 mobile_mode=bool(values[2]);var extent=Vector2(float(values[0]),float(values[1]))
 if extent==mobile_size or extent.x<1 or extent.y<1:return
 mobile_size=extent;get_window().content_scale_size=Vector2i(extent)
 # No synthetic 'mobile' mode based on a short desktop window.
func _t(value):
 var source=str(value)
 if locale=="zh-CN":return source
 if labels.has(source):return str(labels[source].get(locale,source))
 var album=RegEx.new();album.compile("^旅行相册\\s*·\\s*(\\d+) 张$")
 var album_match=album.search(source)
 if album_match:
  var result=_t("旅行相册 {n}").replace("{n}",album_match.get_string(1))
  return result.replace(" photos"," photo") if locale=="en" and album_match.get_string(1)=="1" else result
 var bag=RegEx.new();bag.compile("^三叶草：(\\d+)　　营地休息：(\\d+) 次$")
 var bag_match=bag.search(source)
 if bag_match:return _t("行囊统计 {n} {m}").replace("{n}",bag_match.get_string(1)).replace("{m}",bag_match.get_string(2))
 # Stable source templates, not mutation of a label's previous translation.
 if source.begins_with("照片放进相册了："):return _t("照片放进相册了：")+_t(source.trim_prefix("照片放进相册了："))
 for separator in ["\n\n","  ·  ","　·　","："]:
  if source.contains(separator):
   var parts=source.split(separator);var translated=[]
   for part in parts:translated.append(_t(part))
   return separator.join(translated)
 for prefix in ["E  ·  ","E　", "照片放进相册了："]:
  if source.begins_with(prefix):return _t(prefix)+_t(source.trim_prefix(prefix))
 return source
func _menu_data():
 var menu=get_parent().get("mobile_menu");var items=[]
 if is_instance_valid(menu):
  var popup=menu.get_popup()
  for i in range(popup.item_count):
   var id=popup.get_item_id(i);var label=_t(popup.get_item_text(i))
   if is_frog and id==0:label=_t("切换视角")
   if is_frog and id==3:label=label.trim_suffix(" P")
   items.append({"id":id,"text":label,"separator":popup.is_item_separator(i),"disabled":popup.is_item_disabled(i)})
 return {"items":items}
func _set_lock():
 var world=get_parent()
 if is_frog:
  var panel=world.get("album_panel")
  var friend=world.get_friend_ui_state(locale) if world.has_method("get_friend_ui_state") else {}
  panel_was_locked=is_instance_valid(panel) or bool(friend.get("open",false))
  var friend_life=world.get("friend_life")
  var busy=is_instance_valid(friend_life) and bool(friend_life.get("busy_photo"))
  if _locked() or busy:world.input_locked=true
  elif applied_lock:world.input_locked=false
  applied_lock=_locked() or busy
 else:world.web_ui_locked=_locked()
 if _locked():
  for action in ["left","right","forward","back","run","jump"]:
   if InputMap.has_action(action):Input.action_release(action)
  Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
func _web_menu_action(args):
 if args.is_empty():return
 var menu=get_parent().get("mobile_menu");var id=int(args[0]);menu_was_open=false
 if is_instance_valid(menu):
  var popup=menu.get_popup();popup.hide()
  if id>=0 and popup.get_item_index(id)>=0:popup.id_pressed.emit(id)
 _set_lock();_sync_touch_ui()
func _web_ui_action(args):
 if args.is_empty():return
 var action=str(args[0]);var world=get_parent()
 match action:
  "menu":
   _close_panel();menu_was_open=true
  "close":
   _close_panel();menu_was_open=false
  "external-lock":external_locked=bool(args[1]) if args.size()>1 else false
  "panel-button":
   var id=int(args[1]) if args.size()>1 else 0
   if panel_buttons.has(id) and is_instance_valid(panel_buttons[id]):panel_buttons[id].pressed.emit()
  "friend":
   menu_was_open=false
   if world.has_method("friend_ui_action"):world.friend_ui_action(str(args[1]) if args.size()>1 else "open")
  "album":
   menu_was_open=false
   if is_frog:world._open_album()
  "bag":
   menu_was_open=false
   if is_frog:world._show_bag()
  "photo":
   _close_panel();menu_was_open=false;_set_lock()
   if is_frog:world._take_photo()
  "view":
   if is_frog:world._cycle_camera()
   else:world.first_person=not world.first_person
  "day":
   if is_frog:world._toggle_night()
   else:world.daytime=21.0 if world.daytime<18 else 15.5
 _set_lock();_sync_touch_ui()
func _close_panel():
 if not is_frog:return
 get_parent()._close_panel()
 if get_parent().has_method("friend_ui_action"):get_parent().friend_ui_action("close")
 last_panel_id=0;panel_cache={};panel_buttons={}
func _read_panel(node,result):
 if node is Label:
  if not result.has("title"):result.title=_t(node.text)
  elif not node.text.is_empty():result.blocks.append({"type":"text","text":_t(node.text)})
 elif node is Button:
  if node.text in ["继续散步",_t("继续散步")]:return
  var id=node.get_instance_id();panel_buttons[id]=node;result.actions.append({"id":id,"label":_t(node.text)})
 elif node is TextureRect and node.texture:
  var im=node.texture.get_image()
  if im:
   if im.get_width()>600:im.resize(600,max(1,int(im.get_height()*600.0/im.get_width())),Image.INTERPOLATE_LANCZOS)
   result.blocks.append({"type":"image","src":"data:image/png;base64,"+Marshalls.raw_to_base64(im.save_png_to_buffer())})
 for child in node.get_children():_read_panel(child,result)
func _panel_state():
 var world=get_parent()
 if not is_frog:return null
 if world.has_method("get_friend_ui_state"):
  var friend=world.get_friend_ui_state(locale)
  if friend.get("open",false):return {"kind":"friend","title":friend.get("title",""),"blocks":[{"type":"text","text":friend.get("body","")}],"actions":friend.get("choices",[])}
 var panel=world.get("album_panel")
 if not is_instance_valid(panel):last_panel_id=0;return null
 if last_panel_id!=panel.get_instance_id():
  last_panel_id=panel.get_instance_id();panel_buttons={};panel_cache={"kind":"panel","blocks":[],"actions":[]};_read_panel(panel,panel_cache)
  var title=str(panel_cache.get("title",""))
  if title.contains("旅行相册") or title.contains("album") or title.contains("Album") or title.contains("アルバム") or title.contains("앨범") or title.contains("相簿"):panel_cache.kind="album"
 return panel_cache
func _sync_touch_ui():
 if not OS.has_feature("web"):return
 var world=get_parent();var state={"world":"frog" if is_frog else "conan","menu":_menu_data() if menu_was_open else null,"panel":_panel_state()}
 if is_frog:
  var friend_life=world.get("friend_life")
  state.busy=is_instance_valid(friend_life) and bool(friend_life.get("busy_photo"))
  state.place=_t(world.current_zone);state.time=_t("黄昏" if world.night else "午后");state.counter=int(world.state.clovers);state.toast=_t(world.toast_label.text) if world.toast_label.visible else ""
  state.prompt=""
  if world.prompt_label.visible:state.prompt=_t(world.prompt_label.text).trim_prefix("E  ·  ")
  if world.has_method("get_friend_hud_state"):state.friend=world.get_friend_hud_state(locale)
 else:
  state.place=_t(world.info.text);state.time="%02d:%02d"%[int(world.daytime),int(fmod(world.daytime,1)*60)];state.prompt="";state.toast=""
  if not world.nearest.is_empty():state.prompt=_t("交谈")+" · "+_t(world.nearest.name)
  if world.elapsed<=world.message_until:state.toast=_t(world.hint.text)
 var serialized=JSON.stringify(state)
 if serialized!=last_state:
  last_state=serialized;JavaScriptBridge.eval("window.xlandsState && window.xlandsState("+serialized+")")
 _set_lock()
func _process(delta):
 if not OS.has_feature("web"):return
 tick+=delta
 if tick<.15:return
 tick=0
 var canvas=get_parent().get("hud" if is_frog else "ui")
 if is_instance_valid(canvas):canvas.hide()
 _update_mobile_layout();_sync_touch_ui()
