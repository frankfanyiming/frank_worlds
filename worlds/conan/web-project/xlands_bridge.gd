extends Node
var callbacks=[]
var music: AudioStreamPlayer
var locale="zh-CN"
var tick=0.0
var labels={}
var mobile_mode=false
var mobile_size=Vector2.ZERO
var layout_tick=0.0
var menu_was_open=false
var panel_was_locked=false
func _ready():
 if FileAccess.file_exists("res://translations.json"):labels=JSON.parse_string(FileAccess.get_file_as_string("res://translations.json"))
 if OS.has_feature("web"):
  locale=str(JavaScriptBridge.eval("new URLSearchParams(location.search).get('lang') || 'zh-CN'"))
  var win=JavaScriptBridge.get_interface("window")
  var cb=JavaScriptBridge.create_callback(_web_input);callbacks.append(cb);win.xlandsInput=cb
  var sound=JavaScriptBridge.create_callback(_web_sound);callbacks.append(sound);win.xlandsSound=sound
  var move=JavaScriptBridge.create_callback(_web_move);callbacks.append(move);win.xlandsMove=move
  var look=JavaScriptBridge.create_callback(_web_look);callbacks.append(look);win.xlandsLook=look
  var menu_action=JavaScriptBridge.create_callback(_web_menu_action);callbacks.append(menu_action);win.xlandsMenuAction=menu_action
  _update_mobile_layout()
  JavaScriptBridge.eval("window.parent.postMessage({type:'xlands-ready'},'*')")
 if ResourceLoader.exists("res://assets/forest-original.wav"):
  music=AudioStreamPlayer.new();music.stream=load("res://assets/forest-original.wav");music.volume_db=-3;add_child(music);music.finished.connect(func():music.play());music.play()
  if OS.has_feature("web"):AudioServer.set_bus_mute(0,JavaScriptBridge.eval("new URLSearchParams(location.search).get('sound') !== '1'"))
 if OS.has_feature("web"):return
 var canvas=CanvasLayer.new();add_child(canvas);var button=Button.new();button.text=_t("共创拓展区");button.position=Vector2(28,85);button.add_theme_font_override("font",load("res://ui-font.otf"));button.add_theme_font_size_override("font_size",15);canvas.add_child(button);button.pressed.connect(_expand)
func _expand():
 if OS.has_feature("web"):JavaScriptBridge.eval("window.parent.postMessage({type:'xlands-expansion'},'*')")
 else:OS.shell_open("https://frankfanyiming.github.io/frank_worlds/#expansion/conan")
func _web_input(args):
 if args.size()<2:return
 var action=str(args[0]);var pressed=bool(args[1])
 if action in ["forward","back","left","right","run","jump"]:
  if not InputMap.has_action(action):return
  if pressed:Input.action_press(action)
  else:Input.action_release(action)
 elif action in ["interact","view"]:
  var e=InputEventKey.new();e.keycode=KEY_E if action=="interact" else KEY_V;e.physical_keycode=e.keycode;e.pressed=pressed;Input.parse_input_event(e)
func _web_move(args):
 if args.size()<2:return
 var x=clamp(float(args[0]),-1.0,1.0);var y=clamp(float(args[1]),-1.0,1.0)
 var values={"left":max(-x,0.0),"right":max(x,0.0),"forward":max(-y,0.0),"back":max(y,0.0)}
 for action in values:
  if not InputMap.has_action(action):continue
  if values[action]>.001:Input.action_press(action,values[action])
  else:Input.action_release(action)
func _web_look(args):
 if args.size()<2 or menu_was_open or panel_was_locked:return
 if get_parent().has_method("_touch_look"):get_parent()._touch_look(Vector2(float(args[0]),float(args[1])))
func _update_mobile_layout():
 if not OS.has_feature("web"):return
 var values=JSON.parse_string(str(JavaScriptBridge.eval("JSON.stringify([window.innerWidth,window.innerHeight,matchMedia('(any-pointer:coarse)').matches||Math.min(innerWidth,innerHeight)<=720])")))
 if not values:return
 mobile_mode=bool(values[2])
 if not mobile_mode:return
 var size=Vector2(float(values[0]),float(values[1]))
 if size==mobile_size or size.x<1 or size.y<1:return
 mobile_size=size
 get_window().content_scale_size=Vector2i(size)
 if get_parent().has_method("_mobile_layout"):get_parent().call_deferred("_mobile_layout",size)
func _web_sound(args):
 if args.size():AudioServer.set_bus_mute(0,not bool(args[0]))
func _t(value):
 if locale=="zh-CN":return value
 return labels.get(value,{}).get(locale,value)
func _web_menu_action(args):
 if args.is_empty():return
 var menu=get_parent().get("mobile_menu")
 if not is_instance_valid(menu):return
 var popup=menu.get_popup();var id=int(args[0]);popup.hide()
 if id>=0 and popup.get_item_index(id)>=0:popup.id_pressed.emit(id)
 _sync_touch_ui()
func _sync_touch_ui():
 if not OS.has_feature("web") or not mobile_mode:return
 var parent=get_parent();var menu=parent.get("mobile_menu")
 var is_open=is_instance_valid(menu) and menu.get_popup().visible
 if is_open!=menu_was_open:
  menu_was_open=is_open
  var payload="null"
  if is_open:
   var popup=menu.get_popup();var items=[]
   for i in range(popup.item_count):items.append({"id":popup.get_item_id(i),"text":_t(popup.get_item_text(i)),"separator":popup.is_item_separator(i),"disabled":popup.is_item_disabled(i)})
   payload=JSON.stringify({"title":_t(menu.text),"items":items})
  JavaScriptBridge.eval("window.xlandsMenu && window.xlandsMenu("+payload+")")
 var locked=bool(parent.get("input_locked")) if parent.has_method("_close_panel") else false
 if locked!=panel_was_locked:
  panel_was_locked=locked;JavaScriptBridge.eval("window.xlandsOverlayLocked && window.xlandsOverlayLocked("+("true" if locked else "false")+")")
func _process(delta):
 _sync_touch_ui()
 layout_tick+=delta
 if layout_tick>.3:layout_tick=0;_update_mobile_layout()
 tick+=delta
 if tick>.4 and locale!="zh-CN":tick=0;_translate(get_parent())
func _translate(n):
 if n is PopupMenu:
  var sources=n.get_meta("xlands_popup_sources",{})
  for i in range(n.item_count):
   var id=n.get_item_id(i);var current=n.get_item_text(i)
   if not sources.has(id) or current!=sources[id].shown:sources[id]={"source":current,"shown":current}
   var translated=_t(sources[id].source);n.set_item_text(i,translated);sources[id].shown=translated
  n.set_meta("xlands_popup_sources",sources)
 if n is MenuButton:_translate(n.get_popup())
 if n is Label or n is Button:n.text=_t(n.text)
 for c in n.get_children():
  if c!=self:_translate(c)
