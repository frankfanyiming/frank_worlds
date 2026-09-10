extends Node3D

var data: Dictionary
var stage: Node3D
var frog: CharacterBody3D
var actor: Node3D
var gear: Node3D
var animator: AnimationPlayer
var jump_buffer=0.0
var coyote=0.0
var landing_time=0.0
var was_grounded=false
var camera: Camera3D
var environment: Environment
var sun: DirectionalLight3D
var shell: Node3D
var door: Node3D
var boat: Node3D
var clovers: Node3D
var hud: CanvasLayer
var overlay: Control
var counter: Label
var zone_label: Label
var prompt_label: Label
var toast_label: Label
var album_panel: PanelContainer
var mode_button: Button
var state := {"clovers":24,"packed":false,"harvest_at":0.0,"photos":[],"camp_visits":0}
var nearest := ""
var mode := 0
var yaw := -0.53
var pitch := 0.67
var distance := 21.0
var turn := 0.0
var night := false
var time := 0.0
var toast_remaining := 0.0
var posing := 0.0
var riding := false
var boat_time := 0.0
var boat_curve: Curve3D
var current_zone := "家门口"
var input_locked := false
var audit_input := Vector3.ZERO
var auditing := false
var fps_samples: Array = []
var butterfly: Node3D
var save_path := "user://woodland-save.json"
var photo_directory := "user://photos"
var capture_dir := ""
var ready_world := false

func vec(a: Array) -> Vector3:
 return Vector3(float(a[0]),float(a[1]),float(a[2]))

func _ready():
 get_window().title="旅行青蛙 · 林间来信"
 if "--verify" in OS.get_cmdline_user_args():
  var temporary=ProjectSettings.globalize_path("res://../../../work/frog-world/verification-%d"%int(Time.get_unix_time_from_system()*1000000))
  DirAccess.make_dir_recursive_absolute(temporary)
  save_path=temporary+"/test-save.json"
  photo_directory=temporary+"/photos"
 _load_state()
 data=JSON.parse_string(FileAccess.get_file_as_string("res://assets/world.json"))
 _setup_input()
 _setup_environment()
 stage=load("res://assets/woodland.glb").instantiate()
 add_child(stage)
 _repair_imported_navigation(stage)
 var room=stage.find_child("InteriorRoot",true,false)
 if room:room.get_parent().remove_child(room);room.queue_free()
 add_child(load("res://assets/interior.glb").instantiate())
 add_child(load("res://assets/navigation.glb").instantiate())
 shell=stage.find_child("HouseShellRoot",true,false)
 clovers=stage.find_child("CloversRoot",true,false)
 door=stage.find_child("DoorRoot",true,false)
 boat=stage.find_child("BoatRoot",true,false)
 _configure_materials(stage)
 _setup_door()
 _setup_frog()
 _setup_camera()
 _setup_ui()
 _setup_butterfly()
 boat_curve=Curve3D.new()
 for p in data.boat_path:boat_curve.add_point(vec(p))
 _refresh_hud()
 ready_world=true
 add_child(load("res://xlands_bridge.gd").new())
 _toast("家门开着，今天也适合出门走走。",5)
 print("FROG_WORLD_READY ",JSON.stringify({"actor":"Tripo","scenery":"Blender","animations":animator.get_animation_list() if animator else []}))
 var args=OS.get_cmdline_user_args()
 if "--capture" in args:
  capture_dir=ProjectSettings.globalize_path("res://../实机预览")
  call_deferred("_capture_views")
 elif "--verify" in args:
  call_deferred("_verify_interactions")
 elif "--navcheck" in args:
  call_deferred("_audit",true)
 elif "--audit" in args:
  call_deferred("_audit")

func _repair_imported_navigation(n: Node):
 for ch in n.get_children():
  var label=ch.name.to_lower()
  if "spiral" in label or ("bridge" in label and "ramp" in label):n.remove_child(ch);ch.queue_free()
  else:_repair_imported_navigation(ch)

func _setup_input():
 var bindings={"left":[KEY_A,KEY_LEFT],"right":[KEY_D,KEY_RIGHT],"forward":[KEY_W,KEY_UP],"back":[KEY_S,KEY_DOWN],"run":[KEY_SHIFT],"jump":[KEY_SPACE]}
 for action in bindings:
  if not InputMap.has_action(action):InputMap.add_action(action)
  for key in bindings[action]:
   var ev=InputEventKey.new();ev.physical_keycode=key;InputMap.action_add_event(action,ev)

func _setup_environment():
 var we=WorldEnvironment.new();environment=Environment.new();we.environment=environment;add_child(we)
 var sky=Sky.new();var sky_mat=ProceduralSkyMaterial.new()
 sky_mat.sky_top_color=Color("a1babb");sky_mat.sky_horizon_color=Color("e3e4c9");sky_mat.ground_horizon_color=Color("d1d5b7");sky_mat.ground_bottom_color=Color("667851")
 sky.sky_material=sky_mat;environment.sky=sky;environment.background_mode=Environment.BG_SKY
 environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;environment.ambient_light_color=Color("c5d0b7");environment.ambient_light_energy=.38
 environment.tonemap_mode=Environment.TONE_MAPPER_FILMIC
 environment.ssao_enabled=true;environment.ssao_radius=1.5;environment.ssao_intensity=1.4
 environment.ssil_enabled=true;environment.ssil_intensity=.45
 environment.glow_enabled=true;environment.glow_intensity=.28
 environment.fog_enabled=true;environment.fog_light_color=Color("b8c8a7");environment.fog_density=.0025
 sun=DirectionalLight3D.new();sun.rotation_degrees=Vector3(-48,-30,-15);sun.light_color=Color("fff2db");sun.light_energy=1.05;sun.shadow_enabled=true;sun.directional_shadow_max_distance=95;sun.light_angular_distance=.5;add_child(sun)
 var fill=DirectionalLight3D.new();fill.rotation_degrees=Vector3(-35,150,0);fill.light_color=Color("b8d7d4");fill.light_energy=.17;add_child(fill)
 for p in [[-14.42,1.50,-10.9],[-12.0,2.1,-12.1],[-14.0,3.9,-14.3],[24.8,1.05,6.95]]:
  var l=OmniLight3D.new();l.position=vec(p);l.light_color=Color("ffd696");l.light_energy=.65;l.omni_range=4.3;l.shadow_enabled=true;add_child(l)

func _configure_materials(node: Node):
 if node is MeshInstance3D:
  var mi=node as MeshInstance3D
  if "Water" in mi.name:
   var sh=Shader.new();sh.code="""shader_type spatial;
render_mode blend_mix, depth_draw_opaque, cull_disabled;
uniform vec4 water_color: source_color = vec4(0.24,0.43,0.33,0.83);
varying vec3 world;
void vertex(){world=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz;VERTEX.y+=sin(world.x*1.7+TIME*.8)*.012+sin(world.z*2.6-TIME*.7)*.008;}
void fragment(){float w=sin(world.x*3.0+TIME*.6+sin(world.z*2.0))*sin(world.z*2.9-TIME*.5);ALBEDO=water_color.rgb+vec3(.08,.10,.085)*smoothstep(.75,1.0,w);ROUGHNESS=.22;METALLIC=.13;ALPHA=water_color.a;NORMAL_MAP=vec3(.5+sin(world.x*2.1+TIME)*.08,.5+cos(world.z*2.6-TIME*.8)*.07,1.0);}
"""
   var sm=ShaderMaterial.new();sm.shader=sh;mi.material_override=sm;mi.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
  elif "flame" in mi.name.to_lower() or "Candle_flame" in mi.name:
   mi.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 for child in node.get_children():_configure_materials(child)

func _setup_door():
 if door==null:return
 var sb=StaticBody3D.new();door.add_child(sb)
 var cs=CollisionShape3D.new();var box=BoxShape3D.new();box.size=Vector3(2.07,1.8,.16);cs.shape=box;cs.position=Vector3(1.06,.91,0);sb.add_child(cs)

func _setup_frog():
 frog=CharacterBody3D.new();frog.name="TravelFrog";frog.floor_snap_length=.4;frog.floor_max_angle=deg_to_rad(53);add_child(frog)
 var col=CollisionShape3D.new();var shape=CapsuleShape3D.new();shape.radius=.27;shape.height=1.02;col.shape=shape;col.position.y=.53;frog.add_child(col)
 actor=load("res://assets/frog.glb").instantiate();frog.add_child(actor)
 animator=_find_animator(actor)
 if animator:
  for clip in animator.get_animation_list():animator.get_animation(clip).loop_mode=Animation.LOOP_NONE if clip in ["JumpStart","Land"] else Animation.LOOP_LINEAR
 gear=load("res://assets/frog-gear.glb").instantiate();actor.add_child(gear);gear.position=Vector3(0,.57,.23);gear.rotation.y=PI
 frog.position=vec(data.spawn)+Vector3.UP*.2
 if animator and animator.has_animation("Idle"):animator.play("Idle")

func _find_animator(n: Node) -> AnimationPlayer:
 if n is AnimationPlayer:return n
 for ch in n.get_children():
  var a=_find_animator(ch)
  if a:return a
 return null

func _setup_camera():
 camera=Camera3D.new();camera.fov=44;camera.near=.06;camera.far=170;add_child(camera);camera.make_current();_camera_update(1)

func _style(bg: Color,border: Color=Color("b6bd9a")) -> StyleBoxFlat:
 var s=StyleBoxFlat.new();s.bg_color=bg;s.border_color=border;s.set_border_width_all(1);s.set_corner_radius_all(12);s.content_margin_left=16;s.content_margin_right=16;s.content_margin_top=10;s.content_margin_bottom=10;return s

func _label(txt: String,size: int=18) -> Label:
 var l=Label.new();l.text=txt;l.add_theme_font_size_override("font_size",size);l.add_theme_color_override("font_color",Color("34472f"));return l

func _button(txt: String,action: Callable) -> Button:
 var b=Button.new();b.text=txt;b.custom_minimum_size=Vector2(92,44);b.add_theme_stylebox_override("normal",_style(Color(.95,.95,.87,.94)));b.add_theme_stylebox_override("hover",_style(Color("e7edcc")));b.add_theme_stylebox_override("pressed",_style(Color("d7e2b4")));b.add_theme_color_override("font_color",Color("3e5136"));b.add_theme_font_size_override("font_size",17);b.pressed.connect(action);return b

func _setup_ui():
 hud=CanvasLayer.new();add_child(hud);overlay=Control.new();overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);overlay.mouse_filter=Control.MOUSE_FILTER_IGNORE;hud.add_child(overlay)
 var theme=Theme.new();theme.default_font=load("res://ui-font.ttc");theme.default_font_size=18;overlay.theme=theme
 var title_panel=PanelContainer.new();title_panel.position=Vector2(26,22);overlay.add_child(title_panel);title_panel.add_theme_stylebox_override("panel",_style(Color(.96,.96,.89,.91)))
 var left=VBoxContainer.new();title_panel.add_child(left)
 var title=_label("旅行青蛙 · 林间来信",25);left.add_child(title)
 zone_label=_label("家门口  ·  午后",15);zone_label.add_theme_color_override("font_color",Color("5c7150"));left.add_child(zone_label)
 var top=HBoxContainer.new();overlay.add_child(top);top.set_anchors_preset(Control.PRESET_TOP_RIGHT);top.offset_left=-550;top.offset_top=26;top.offset_right=-26;top.offset_bottom=70;top.add_theme_constant_override("separation",8)
 counter=_label("三叶草 24",18);counter.custom_minimum_size=Vector2(130,44);counter.add_theme_stylebox_override("normal",_style(Color(.96,.96,.89,.91)));counter.vertical_alignment=VERTICAL_ALIGNMENT_CENTER;top.add_child(counter)
 mode_button=_button("俯看小世界",_cycle_camera);top.add_child(mode_button)
 top.add_child(_button("相册",_open_album));top.add_child(_button("午后 / 黄昏",_toggle_night))
 var bottom=VBoxContainer.new();overlay.add_child(bottom);bottom.set_anchors_preset(Control.PRESET_CENTER_BOTTOM);bottom.offset_left=-390;bottom.offset_top=-126;bottom.offset_right=390;bottom.offset_bottom=-22;bottom.alignment=BoxContainer.ALIGNMENT_CENTER
 toast_label=_label("",18);toast_label.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;toast_label.add_theme_stylebox_override("normal",_style(Color(.96,.96,.89,.92)));bottom.add_child(toast_label)
 prompt_label=_label("",20);prompt_label.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;prompt_label.add_theme_stylebox_override("normal",_style(Color(.94,.96,.84,.94)));bottom.add_child(prompt_label)
 var help=_label("WASD 移动   ·   Space 跳跃   ·   鼠标右键环视   ·   E 互动   ·   P 拍照   ·   C 视角",14);help.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;bottom.add_child(help)
 var action_bar=HBoxContainer.new();overlay.add_child(action_bar);action_bar.set_anchors_preset(Control.PRESET_BOTTOM_LEFT);action_bar.offset_left=28;action_bar.offset_top=-78;action_bar.offset_right=280;action_bar.offset_bottom=-34
 action_bar.add_child(_button("拍一张 P",_take_photo));action_bar.add_child(_button("行囊",_show_bag))

func _setup_butterfly():
 if not ResourceLoader.exists("res://assets/butterfly.glb"):return
 butterfly=load("res://assets/butterfly.glb").instantiate();add_child(butterfly);butterfly.position=Vector3(23,2,7)

func _process(delta):
 if not ready_world:return
 time+=delta
 if time>2 and fps_samples.size()<300:fps_samples.append(Engine.get_frames_per_second())
 _camera_update(delta)
 if door:
  var d=Vector2(frog.position.x+15,frog.position.z+7.66).length();door.rotation.y=lerp_angle(door.rotation.y,-1.55 if d<3.1 else 0.0,1-exp(-delta*4))
 if shell:shell.visible=mode==2 or Vector2(frog.position.x+15,frog.position.z+12).length()>5.5
 if clovers:clovers.visible=Time.get_unix_time_from_system()-float(state.harvest_at)>100
 if gear:gear.visible=bool(state.packed) and mode!=2;gear.rotation.y=PI
 if butterfly:
  butterfly.position=Vector3(23+sin(time*.5)*1.3,1.65+sin(time*1.2)*.18,7+cos(time*.6)*.6)
  for w in ["LeftWing","RightWing"]:
   var wing=butterfly.find_child(w,true,false)
   if wing:wing.rotation.z=sin(time*13)*.65*(1 if w=="LeftWing" else -1)
 if toast_remaining>0:toast_remaining-=delta
 toast_label.visible=toast_remaining>0
 posing=max(0,posing-delta)
 _update_nearest()
 _refresh_hud()

func _physics_process(delta):
 if not ready_world:return
 if capture_dir!="":return
 if riding:
  boat_time+=delta;var length=boat_curve.get_baked_length();var t=min(length,boat_time*1.10);var p=boat_curve.sample_baked(t)
  boat.position=p;frog.position=p+Vector3(0,.085,0);frog.velocity=Vector3.ZERO;_animate("Sit")
  if t>=length:
   riding=false;frog.position=Vector3(5,.45,23);boat.position=vec(data.boat_path[0]);_toast("漂到了池塘边。沿小径慢慢回家吧。",5)
  return
 var wish=Vector3.ZERO
 if auditing:wish=audit_input
 elif not input_locked:
  var v=Input.get_vector("left","right","forward","back");wish=Vector3(v.x,0,v.y).rotated(Vector3.UP,yaw)
 var speed=4.4 if Input.is_action_pressed("run") else 2.9
 if posing>0:wish=Vector3.ZERO
 var rate=1-exp(-delta*12);frog.velocity.x=lerp(frog.velocity.x,wish.x*speed,rate);frog.velocity.z=lerp(frog.velocity.z,wish.z*speed,rate)
 jump_buffer=max(0.0,jump_buffer-delta)
 coyote=.10 if frog.is_on_floor() else max(0.0,coyote-delta)
 if Input.is_action_just_pressed("jump") and not input_locked:jump_buffer=.14
 if jump_buffer>0 and coyote>0:
  frog.velocity.y=6.4;jump_buffer=0;coyote=0;posing=0;landing_time=0;_animate("JumpStart")
 elif frog.is_on_floor():frog.velocity.y=-.1
 else:frog.velocity.y-=18*delta
 _step_up(delta)
 frog.move_and_slide()
 if frog.is_on_floor() and not was_grounded:landing_time=.22
 was_grounded=frog.is_on_floor();landing_time=max(0.0,landing_time-delta)
 if not frog.is_on_floor():_animate("JumpAir")
 elif landing_time>0:_animate("Land")
 elif wish.length()>.10:
  turn=lerp_angle(turn,atan2(-wish.x,-wish.z),1-exp(-delta*12));actor.rotation.y=turn
  _animate("Walk")
 elif posing>0:_animate("Sit")
 else:_animate("Idle")
 if frog.position.y< -3 or Vector2(frog.position.x,frog.position.z).length()>46:
  frog.position=vec(data.spawn)+Vector3.UP*.2;frog.velocity=Vector3.ZERO

func _step_up(delta):
 if not frog.is_on_floor() or frog.velocity.y>0:return
 var move=Vector3(frog.velocity.x,0,frog.velocity.z)*delta
 if move.length()<.002 or not frog.test_move(frog.global_transform,move):return
 var raised=frog.global_transform;raised.origin.y+=.35
 if frog.test_move(raised,move):return
 var probe=frog.position+move.normalized()*.36+Vector3.UP*.36
 var q=PhysicsRayQueryParameters3D.create(probe,probe-Vector3.UP*.43);q.exclude=[frog.get_rid()]
 var hit=get_world_3d().direct_space_state.intersect_ray(q)
 if not hit.is_empty() and hit.normal.y>.60:
  var step=hit.position.y-frog.position.y
  if step>.015 and step<.335:frog.position.y=hit.position.y+.008

func _animate(name):
 if animator and animator.has_animation(name) and animator.current_animation!=name:animator.play(name,.18)

func _camera_update(delta):
 if frog==null or camera==null:return
 if capture_dir!="":return
 var target=frog.position+Vector3.UP*.70
 var inside=Vector2(frog.position.x+15,frog.position.z+12).length()<5.1
 actor.visible=mode!=2
 if mode==2:
  camera.position=target;camera.rotation=Vector3(-pitch*.35,yaw,0);return
 var dist=distance if mode==0 else 5.4
 if inside and mode==0:dist=min(distance,11)
 var p=pitch if mode==0 else clamp(pitch*.55,.18,.55)
 var offset=Vector3(sin(yaw)*cos(p),sin(p),cos(yaw)*cos(p))*dist
 var desired=target+offset
 camera.position=camera.position.lerp(desired,1-exp(-delta*7));camera.look_at(target)

func _unhandled_input(event):
 if event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT):
  yaw-=event.relative.x*.006;pitch=clamp(pitch+event.relative.y*.005,.14,1.35)
 if event is InputEventMouseButton and event.pressed:
  if event.button_index==MOUSE_BUTTON_WHEEL_UP:distance=clamp(distance-1.5,7,34)
  if event.button_index==MOUSE_BUTTON_WHEEL_DOWN:distance=clamp(distance+1.5,7,34)
 if event is InputEventKey and event.pressed and not event.echo:
  match event.physical_keycode:
   KEY_E:_interact()
   KEY_P:_take_photo()
   KEY_C:_cycle_camera()
   KEY_TAB:_open_album()
   KEY_ESCAPE:_close_panel()

func _cycle_camera():
 mode=(mode+1)%3
 mode_button.text=["俯看小世界","跟着小青蛙","蛙眼看世界"][mode]

func _toggle_night():
 night=not night;sun.light_energy=.50 if night else 1.05;sun.light_color=Color("ffa36b") if night else Color("fff2db");sun.rotation_degrees.x=-14 if night else -48
 environment.ambient_light_color=Color("a6b4c5") if night else Color("c5d0b7");environment.ambient_light_energy=.46 if night else .38

func _update_nearest():
 nearest="";var best=2.4
 for item in data.interactions:
  var p=vec(item.position);var d=Vector2(frog.position.x-p.x,frog.position.z-p.z).length()
  if d<best and abs(frog.position.y-p.y)<1.4:
   best=d;nearest=item.id;prompt_label.text="E  ·  "+item.label
 if riding:prompt_label.text="顺着水流，慢慢漂一会儿。"
 prompt_label.visible=nearest!="" or riding
 var zone_best=999.0
 for z in data.zones:
  var p=vec(z.position);var d=frog.position.distance_to(p)
  if d<zone_best:zone_best=d;current_zone=z.label
 if Vector2(frog.position.x+15,frog.position.z+12).length()<4.7:current_zone="树干小屋" if frog.position.y<2 else "夹层睡铺"

func _interact():
 if input_locked or riding:return
 match nearest:
  "clover":
   if Time.get_unix_time_from_system()-float(state.harvest_at)<100:_toast("叶片还在慢慢长大，再去散会儿步。",4)
   else:
    state.clovers+=18;state.harvest_at=Time.get_unix_time_from_system();_save();_toast("收到了 18 枚三叶草。可以回屋准备便当了。",5)
  "mail":_message("一封森林来信","沿着巨叶旁的小径出发，越过木桥，就能找到橙色帐篷。\n\n溪水下游有一块漂流木片。累了就坐一会儿，带张照片回家。")
  "pack":
   if state.packed:_toast("行囊已经装好。带着便当去营地吧。",4)
   elif state.clovers>=8:
    state.clovers-=8;state.packed=true;_save();_toast("便当和小包袱装好了。今天，去林间营地吧。",5)
   else:_toast("准备便当需要 8 枚三叶草。",4)
  "book":_open_album()
  "camp":
   posing=4
   if state.packed:
    state.packed=false;state.camp_visits+=1;state.clovers+=5;_save();_toast("吃完便当，蝴蝶也来了。把这一刻拍下来吧。",5)
   else:_toast("在帐篷边坐一会儿。下次可以从家里带份便当。",5)
  "boat":
   riding=true;boat_time=0;frog.velocity=Vector3.ZERO;_toast("木片缓缓离岸了。",3)
  "pond":posing=4;_toast("水面映着树影。回家的路就在身后。",5)

func _toast(txt: String,seconds: float=4):
 if toast_label:toast_label.text=txt;toast_remaining=seconds

func _refresh_hud():
 counter.text="三叶草  %d"%int(state.clovers)
 zone_label.text=current_zone+"  ·  "+("黄昏" if night else "午后")+("  ·  行囊已备好" if state.packed else "")

func _load_state():
 if FileAccess.file_exists(save_path):
  var saved=JSON.parse_string(FileAccess.get_file_as_string(save_path))
  if saved is Dictionary:
   for key in state:
    if key in saved:state[key]=saved[key]
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(photo_directory))

func _save():
 var file=FileAccess.open(save_path,FileAccess.WRITE)
 if file:file.store_string(JSON.stringify(state,"  "))

func _take_photo():
 if input_locked or not ready_world:return
 input_locked=true;overlay.visible=false
 await RenderingServer.frame_post_draw
 var image=get_viewport().get_texture().get_image();var filename="photo-%d.png"%int(Time.get_unix_time_from_system()*1000);var path=photo_directory+"/"+filename
 var result=image.save_png(path)
 overlay.visible=true;input_locked=false
 if result==OK:
  state.photos.append({"file":filename,"place":current_zone,"time":Time.get_datetime_string_from_system()});_save();_toast("照片放进相册了："+current_zone,4)
 else:_toast("照片暂时没有保存成功。",4)

func _panel(title: String) -> VBoxContainer:
 _close_panel();input_locked=true
 album_panel=PanelContainer.new();overlay.add_child(album_panel);album_panel.set_anchors_preset(Control.PRESET_CENTER);album_panel.offset_left=-460;album_panel.offset_top=-320;album_panel.offset_right=460;album_panel.offset_bottom=320;album_panel.add_theme_stylebox_override("panel",_style(Color("f4f1df")))
 var box=VBoxContainer.new();box.add_theme_constant_override("separation",15);album_panel.add_child(box)
 var row=HBoxContainer.new();box.add_child(row);var head=_label(title,26);head.size_flags_horizontal=Control.SIZE_EXPAND_FILL;row.add_child(head);row.add_child(_button("继续散步",_close_panel));return box

func _close_panel():
 if is_instance_valid(album_panel):album_panel.queue_free()
 album_panel=null;input_locked=false

func _message(title: String,body: String):
 var box=_panel(title);var text=Label.new();text.text=body;text.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;text.add_theme_font_size_override("font_size",21);text.add_theme_color_override("font_color",Color("526047"));box.add_child(text)

func _show_bag():
 _message("今天的行囊",("便当已经备好，叶帽也带上了。\n\n到林间营地坐下吃饭，蝴蝶会在附近飞舞。" if state.packed else "行囊还是空的。\n\n回小屋找到木箱，使用 8 枚三叶草准备一份便当。")+"\n\n三叶草：%d　　营地休息：%d 次"%[int(state.clovers),int(state.camp_visits)])

func _open_album():
 var box=_panel("旅行相册  ·  %d 张"%state.photos.size())
 if state.photos.is_empty():box.add_child(_label("还没有照片。按 P，留住眼前的小世界。",21));return
 var scroll=ScrollContainer.new();scroll.size_flags_vertical=Control.SIZE_EXPAND_FILL;box.add_child(scroll);var grid=GridContainer.new();grid.columns=3;grid.add_theme_constant_override("h_separation",12);grid.add_theme_constant_override("v_separation",15);scroll.add_child(grid)
 for item in state.photos:
  var path=ProjectSettings.globalize_path(photo_directory+"/"+item.file);var im=Image.load_from_file(path)
  if im==null:continue
  var card=VBoxContainer.new();grid.add_child(card);var pic=TextureRect.new();pic.custom_minimum_size=Vector2(270,180);pic.expand_mode=TextureRect.EXPAND_IGNORE_SIZE;pic.stretch_mode=TextureRect.STRETCH_KEEP_ASPECT_CENTERED;pic.texture=ImageTexture.create_from_image(im);card.add_child(pic);card.add_child(_label(item.place,17))

func _capture_views():
 input_locked=true;overlay.visible=false;await get_tree().create_timer(2.0).timeout
 var views=[
  {"name":"01-庭院与岩屋","eye":Vector3(-15,13,13),"at":Vector3(-17,1.1,-3.5),"frog":Vector3(-15,.35,-3)},
  {"name":"02-树干小屋剖面","eye":Vector3(-6,9,-3),"at":Vector3(-15,1.7,-12),"frog":Vector3(-15,.22,-9.0)},
  {"name":"03-蓝色睡铺","eye":Vector3(-12,4.4,-10.5),"at":Vector3(-14.7,3.1,-14.1),"frog":Vector3(-17,2.75,-13.6)},
  {"name":"04-森林与溪桥","eye":Vector3(21,9,3),"at":Vector3(9,.8,-9),"frog":Vector3(13,.7,-9)},
  {"name":"05-林间营地","eye":Vector3(29,5,13),"at":Vector3(24,1.0,5.5),"frog":Vector3(22,.35,7)},
  {"name":"07-Tripo小青蛙","eye":Vector3(-13,2.2,1),"at":Vector3(-15,.85,-3),"frog":Vector3(-15,.24,-3)},
  {"name":"06-自然世界全景","eye":Vector3(-40,35,45),"at":Vector3(0,.3,-1),"frog":vec(data.spawn)}]
 for v in views:
  frog.position=v.frog;frog.velocity=Vector3.ZERO
  var rq=PhysicsRayQueryParameters3D.create(frog.position+Vector3.UP*1.6,frog.position-Vector3.UP*2);rq.exclude=[frog.get_rid()]
  var floor_hit=get_world_3d().direct_space_state.intersect_ray(rq)
  if not floor_hit.is_empty():frog.position.y=floor_hit.position.y+.015
  actor.rotation.y=PI;camera.position=v.eye;camera.look_at(v.at)
  if shell:shell.visible=not ("小屋" in v.name or "睡铺" in v.name)
  await get_tree().create_timer(.7).timeout
  if shell:shell.visible=not ("小屋" in v.name or "睡铺" in v.name)
  await RenderingServer.frame_post_draw
  get_viewport().get_texture().get_image().save_png(capture_dir+"/"+v.name+".png")
  print("CAPTURE ",v.name)
 frog.position=vec(data.spawn);camera.position=Vector3(-15,13,13);camera.look_at(Vector3(-17,1.1,-3.5));overlay.visible=true
 await RenderingServer.frame_post_draw
 get_viewport().get_texture().get_image().save_png(capture_dir+"/08-游戏界面.png")
 print("CAPTURE_DONE");get_tree().quit()

func _walk_to(target: Vector3,timeout: float=12) -> Dictionary:
 var elapsed=0.0;var start=frog.position
 while elapsed<timeout:
  var diff=target-frog.position;diff.y=0
  if diff.length()<.12:
   audit_input=Vector3.ZERO;return {"reached":abs(frog.position.y-target.y)<.34,"feet":[frog.position.x,frog.position.y,frog.position.z],"elapsed":elapsed,"target_height":target.y,"height_delta":frog.position.y-target.y}
  audit_input=diff.normalized();await get_tree().physics_frame;elapsed+=1.0/60.0
 audit_input=Vector3.ZERO;return {"reached":false,"feet":[frog.position.x,frog.position.y,frog.position.z],"start":[start.x,start.y,start.z],"target":[target.x,target.y,target.z]}

func _audit(short: bool=false):
 auditing=true;input_locked=true;var results=[]
 await get_tree().create_timer(1.2).timeout
 var tour=data.route
 if short:
  frog.position=Vector3(9,.4,-9);frog.velocity=Vector3.ZERO
  tour=[[11,.48,-9],[14,1.04,-9],[19,.18,-9]]
 for p in tour:
  var result=await _walk_to(vec(p),8);results.append(result);print("WALK_POINT ",JSON.stringify(result))
 # Return to entrance and climb the actual spiral using the controller.
 frog.position=vec(data.spawn)+Vector3.UP*.1;frog.velocity=Vector3.ZERO
 await get_tree().create_timer(.8).timeout
 var indoor=[]
 for p in [Vector3(-15,.2,-7.3),Vector3(-15,.2,-9.3),vec(data.stair_route[0])]:indoor.append(await _walk_to(p,9))
 for p in data.stair_route:
  var step=await _walk_to(vec(p),4);indoor.append(step);print("STAIR_POINT ",JSON.stringify(step))
 for p in [Vector3(-16.52,2.64,-13.85),Vector3(-16.52,2.64,-14.3)]:indoor.append(await _walk_to(p,4))
 var skin_meshes=[]
 _inspect_skin(actor,skin_meshes)
 var report={"outdoor_route":results,"interior_stairs":indoor,"animations":animator.get_animation_list() if animator else [],"skinned_meshes":skin_meshes,"mean_fps_sample":_mean(fps_samples),"capture_is_real_runtime":true}
 var f=FileAccess.open("res://../实机验收.json",FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "))
 print("AUDIT_DONE ",JSON.stringify(report));get_tree().quit()

func _mean(a: Array) -> float:
 var total=0.0
 for v in a:total+=float(v)
 return total/max(1,a.size())

func _inspect_skin(n: Node,a: Array):
 if n is MeshInstance3D and n.skin:a.append({"mesh":str(n.name),"binds":n.skin.get_bind_count()})
 for c in n.get_children():_inspect_skin(c,a)

func _verify_interactions():
 assert(save_path.contains("/work/frog-world/verification-"))
 state={"clovers":24,"packed":false,"harvest_at":0.0,"photos":[],"camp_visits":0}
 await get_tree().create_timer(2).timeout
 var checks={}
 nearest="clover";_interact();checks["harvest_adds_18"]=int(state.clovers)==42
 _interact();checks["harvest_cooldown"]=int(state.clovers)==42
 nearest="pack";_interact();checks["pack_costs_8"]=int(state.clovers)==34 and state.packed
 nearest="camp";_interact()
 var expected=state.duplicate(true);state.clovers=-1;state.camp_visits=-1;_load_state()
 checks["save_matches_current_state"]=int(state.clovers)==int(expected.clovers) and int(state.camp_visits)==int(expected.camp_visits) and state.packed==expected.packed and abs(float(state.harvest_at)-float(expected.harvest_at))<.01 and state.photos.size()==expected.photos.size()
 checks["camp_consumes_lunch"]=not state.packed and int(state.camp_visits)==1 and int(state.clovers)==39
 posing=0;nearest="mail";_interact();await get_tree().process_frame
 checks["mail_panel_visible"]=is_instance_valid(album_panel) and album_panel.get_global_rect().intersects(overlay.get_global_rect())
 _close_panel();await get_tree().process_frame
 await _take_photo();checks["photo_saved"]=state.photos.size()==1
 if state.photos.size()==1:
  var file=photo_directory+"/"+state.photos[0].file;var im=Image.load_from_file(ProjectSettings.globalize_path(file));checks["photo_dimensions"]=[im.get_width(),im.get_height()] if im else []
 _open_album();await get_tree().process_frame;checks["album_visible"]=is_instance_valid(album_panel) and album_panel.get_global_rect().intersects(overlay.get_global_rect())
 await RenderingServer.frame_post_draw
 get_viewport().get_texture().get_image().save_png("res://../实机预览/09-相册实机.png")
 _close_panel();nearest="boat";_interact();checks["boat_started"]=riding
 await get_tree().create_timer(1.0).timeout
 checks["boat_moves_with_frog"]=riding and frog.position.distance_to(boat.position+Vector3(0,.085,0))<.01 and boat_time>.8
 boat_time=boat_curve.get_baked_length()/1.1;await get_tree().physics_frame;await get_tree().physics_frame
 checks["boat_completes"]=not riding
 var skins=[];_inspect_skin(actor,skins);checks["skinned_meshes"]=skins;checks["animations"]=animator.get_animation_list() if animator else [];checks["butterfly_loaded"]=butterfly!=null
 var f=FileAccess.open("res://../玩法验收.json",FileAccess.WRITE);f.store_string(JSON.stringify(checks,"  "));print("INTERACTION_VERIFY ",JSON.stringify(checks))
 get_tree().quit()
