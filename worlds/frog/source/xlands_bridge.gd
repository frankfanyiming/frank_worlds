extends Node
var callbacks=[]
var music: AudioStreamPlayer
var locale="zh-CN"
var tick=0.0
var labels={}
func _ready():
 if FileAccess.file_exists("res://translations.json"):labels=JSON.parse_string(FileAccess.get_file_as_string("res://translations.json"))
 if OS.has_feature("web"):
  locale=str(JavaScriptBridge.eval("new URLSearchParams(location.search).get('lang') || 'zh-CN'"))
  var win=JavaScriptBridge.get_interface("window")
  var cb=JavaScriptBridge.create_callback(_web_input);callbacks.append(cb);win.xlandsInput=cb
  var sound=JavaScriptBridge.create_callback(_web_sound);callbacks.append(sound);win.xlandsSound=sound
  JavaScriptBridge.eval("window.parent.postMessage({type:'xlands-ready'},'*')")
 if ResourceLoader.exists("res://assets/forest-original.wav"):
  music=AudioStreamPlayer.new();music.stream=load("res://assets/forest-original.wav");music.volume_db=-3;add_child(music);music.finished.connect(func():music.play());music.play()
  if OS.has_feature("web"):AudioServer.set_bus_mute(0,JavaScriptBridge.eval("new URLSearchParams(location.search).get('sound') !== '1'"))
 var canvas=CanvasLayer.new();add_child(canvas);var button=Button.new();button.text=_t("共创拓展区");button.position=Vector2(28,85);button.add_theme_font_override("font",load("res://ui-font.ttc"));button.add_theme_font_size_override("font_size",15);canvas.add_child(button);button.pressed.connect(_expand)
func _expand():
 if OS.has_feature("web"):JavaScriptBridge.eval("window.parent.postMessage({type:'xlands-expansion'},'*')")
 else:OS.shell_open("https://frankfanyiming.github.io/frank_worlds/#expansion/frog")
func _web_input(args):
 if args.size()<2:return
 var action=str(args[0]);var pressed=bool(args[1])
 if action in ["forward","back","left","right","run","jump"]:
  if not InputMap.has_action(action):return
  if pressed:Input.action_press(action)
  else:Input.action_release(action)
 elif action=="interact" and pressed:
  var e=InputEventKey.new();e.keycode=KEY_E;e.pressed=true;Input.parse_input_event(e)
func _web_sound(args):
 if args.size():AudioServer.set_bus_mute(0,not bool(args[0]))
func _t(value):
 if locale=="zh-CN":return value
 return labels.get(value,{}).get(locale,value)
func _process(delta):
 tick+=delta
 if tick>.4 and locale!="zh-CN":tick=0;_translate(get_parent())
func _translate(n):
 if n is Label or n is Button:n.text=_t(n.text)
 for c in n.get_children():
  if c!=self:_translate(c)
