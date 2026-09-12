extends Node3D
const SaveRecovery = preload("res://friends/save_recovery.gd")

var data: Dictionary
var stage: Node3D
var frog: CharacterBody3D
var actor: Node3D
var gear: Node3D
var animator: AnimationPlayer
var jump_buffer=0.0
var jump_prepare=0.0
var jump_takeoff=0.0
var locomotion: Dictionary = {}
var coyote=0.0
var landing_time=0.0
var was_grounded=false
var camera: Camera3D
var environment: Environment
var sun: DirectionalLight3D
var sky_fill: DirectionalLight3D
var home_enclosure: Node3D
var home_furnishings: Node3D
var baked_homes: Dictionary = {}
var home_layout: Dictionary = {}
var panda_home: Node3D
var panda_exterior: Node3D
var panda_layout: Dictionary = {}
var panda_actor: Node3D
var panda_animator: AnimationPlayer
var panda_body: CharacterBody3D
var panda_roam_enabled := true
var panda_wait := 16.0
var panda_route_index := -1
var panda_returning := false
var panda_blocked := 0.0
var interior_camera_initialized := false
var home_orbit := .40
var home_camera_distance := 3.65
var active_home := ""
var home_cooldown := 0.0
var tea_time := 0.0
const PANDA_ROOM_OFFSET = Vector3(100,0,0)
const PANDA_GARDEN_POSITION = Vector3(26,.25,13)
var home_light: OmniLight3D
var window_light: SpotLight3D
var room_lamps: Array[OmniLight3D] = []
var household_lights: Array[Light3D] = []
var manual_review_camera := false
var inside_home := false
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
var state := {"clovers":24,"packed":false,"harvest_at":0.0,"photos":[],"camp_visits":0,"panda_visits":0,"friend_life":{},"_save_sequence":0,"_saved_at":0.0}
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
var locale := "zh-CN"
var translations: Dictionary = {}
var mobile_ui := false
var mobile_menu: MenuButton
var friend_life


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
 translations=_read_layout("res://translations.json")
 if FileAccess.file_exists("res://assets/locomotion.json"):locomotion=_read_layout("res://assets/locomotion.json")
 if OS.has_feature("web"):locale=str(JavaScriptBridge.eval("new URLSearchParams(location.search).get('lang') || 'zh-CN'"))
 _setup_input()
 _setup_environment()
 stage=load("res://assets/woodland.glb").instantiate()
 add_child(stage)
 _repair_imported_navigation(stage)
 var room=stage.find_child("InteriorRoot",true,false)
 if room:room.get_parent().remove_child(room);room.queue_free()
 add_child(load("res://assets/navigation.glb").instantiate())
 _setup_homes()
 shell=stage.find_child("HouseShellRoot",true,false)
 for name in ["HouseShell_Blue_grey_shelter_stone","Architecture_Blue_grey_shelter_stone"]:
  var old_stone=stage.find_child(name,true,false)
  if old_stone:old_stone.visible=false
 stage.add_child(load("res://assets/stone-shell.glb").instantiate())
 clovers=stage.find_child("CloversRoot",true,false)
 door=stage.find_child("DoorRoot",true,false)
 boat=stage.find_child("BoatRoot",true,false)
 _configure_materials(stage)
 _setup_door()
 _setup_frog()
 _setup_camera()
 _setup_ui()
 _setup_butterfly()
 friend_life=load("res://friends/friend_life.gd").new();add_child(friend_life);friend_life.setup(self)
 boat_curve=Curve3D.new()
 for p in data.boat_path:boat_curve.add_point(vec(p))
 _refresh_hud()
 ready_world=true
 add_child(load("res://xlands_bridge.gd").new())
 _toast("家里布置好了，熊猫也搬到了营地旁。",5)
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
 environment.ssil_enabled=false
 environment.glow_enabled=true;environment.glow_intensity=.28
 environment.fog_enabled=true;environment.fog_light_color=Color("b8c8a7");environment.fog_density=.0025
 sun=DirectionalLight3D.new();sun.rotation_degrees=Vector3(-48,-30,-15);sun.light_color=Color("fff2db");sun.light_energy=1.05;sun.shadow_enabled=true;sun.directional_shadow_max_distance=95;sun.light_angular_distance=.5;add_child(sun)
 sky_fill=DirectionalLight3D.new();sky_fill.rotation_degrees=Vector3(-35,150,0);sky_fill.light_color=Color("b8d7d4");sky_fill.light_energy=.17;add_child(sky_fill)
 home_light=OmniLight3D.new();home_light.position=Vector3(-14.8,4.5,-10.9);home_light.light_color=Color("f7f3e7");home_light.light_energy=.72;home_light.omni_range=8;home_light.shadow_enabled=false;home_light.visible=false;add_child(home_light)
 window_light=SpotLight3D.new();window_light.position=Vector3(-11.15,2.70,-13.30);window_light.light_color=Color("fff0d5");window_light.light_energy=1.05;window_light.spot_range=10;window_light.spot_angle=35;window_light.spot_attenuation=.55;window_light.shadow_enabled=true;window_light.visible=false;add_child(window_light);window_light.look_at(Vector3(-16.7,.12,-9.5))
 for p in [[-14.42,1.50,-10.9],[-12.0,2.1,-12.1],[-14.0,3.9,-14.3],[24.8,1.05,6.95]]:
  var l=OmniLight3D.new();l.position=vec(p);l.light_color=Color("ffd696");l.light_energy=.65;l.omni_range=4.3;l.shadow_enabled=true;add_child(l)
  if p[0]<0:room_lamps.append(l)

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

func _configure_character_lighting(node: Node):
 if node is MeshInstance3D:node.gi_mode=GeometryInstance3D.GI_MODE_DYNAMIC
 for child in node.get_children():_configure_character_lighting(child)

func _home_collisions(node: Node):
 if node is MeshInstance3D and ("WindowBackground" in str(node.name) or "WindowBackdrop" in str(node.name)):
  node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 if node is MeshInstance3D and (str(node.name).begins_with("EnclosureWall") or str(node.name).begins_with("EnclosureCeiling") or str(node.name).begins_with("EnclosureFloorUnderlay")):
  node.create_trimesh_collision()
  # The enclosure receives furniture shadows; inward faces must not self-shadow.
  node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 for child in node.get_children():_home_collisions(child)

func _read_layout(path: String) -> Dictionary:
 if not FileAccess.file_exists(path):return {}
 var parsed=JSON.parse_string(FileAccess.get_file_as_string(path))
 return parsed if parsed is Dictionary else {}

func _collision_layer(node: Node, layer: int):
 if node is CollisionObject3D:
  node.collision_layer=layer
  node.collision_mask=0
 for child in node.get_children():_collision_layer(child,layer)

func _layout_collisions(parent: Node3D, layout: Dictionary):
 for item in layout.get("furniture_collisions",[]):
  var body=StaticBody3D.new();body.name=str(item.get("name","Furniture"))+"Collision";parent.add_child(body)
  body.position=vec(item.position);body.rotation.y=float(item.get("yaw",0))
  var collision=CollisionShape3D.new();var shape=BoxShape3D.new()
  shape.size=vec(item.size);collision.shape=shape;body.add_child(collision)
 var loft=layout.get("loft",{})
 if loft.has("polygon"):
  var outline=PackedVector2Array()
  for p in loft.polygon:outline.append(Vector2(float(p[0]),float(p[2] if p.size()>2 else p[1])))
  var triangles=Geometry2D.triangulate_polygon(outline);var faces=PackedVector3Array()
  for i in triangles:faces.append(Vector3(outline[i].x,float(loft.get("top",loft.get("height",3.25))),outline[i].y))
  _collision_faces(parent,"LoftWalkSurface",faces)
 if layout.has("stair_width") and layout.get("stair_route",[]).size()>1:
  var route=layout.stair_route;var strip=[];var faces=PackedVector3Array()
  for i in range(route.size()):
   var p=vec(route[i]);var tangent=vec(route[min(i+1,route.size()-1)])-vec(route[max(0,i-1)])
   tangent.y=0;var side=tangent.normalized().cross(Vector3.UP)*float(layout.stair_width)*.5
   strip.append([p-side,p+side])
  for i in range(strip.size()-1):
   for v in [strip[i][0],strip[i+1][0],strip[i][1],strip[i][1],strip[i+1][0],strip[i+1][1]]:faces.append(v)
  _collision_faces(parent,"MushroomStairWalkSurface",faces)

func _collision_faces(parent: Node3D, label: String, faces: PackedVector3Array):
 if faces.is_empty():return
 var body=StaticBody3D.new();body.name=label;parent.add_child(body)
 var collider=CollisionShape3D.new();var shape=ConcavePolygonShape3D.new()
 shape.set_faces(faces);shape.backface_collision=true;collider.shape=shape;body.add_child(collider)

func _setup_homes():
 home_layout=_read_layout("res://assets/home-layout.json")
 var frog_baked="res://assets/house-lighting/frog-room.scn"
 if ResourceLoader.exists(frog_baked):
  home_enclosure=load(frog_baked).instantiate();add_child(home_enclosure)
  home_furnishings=home_enclosure.get_node("home-furnishings")
  baked_homes["frog"]=home_enclosure
 else:
  home_enclosure=load("res://assets/home-enclosure.glb").instantiate();add_child(home_enclosure)
  home_furnishings=load("res://assets/home-furnishings.glb").instantiate();add_child(home_furnishings)
 _home_collisions(home_enclosure)
 _layout_collisions(home_furnishings,home_layout)
 _collision_layer(home_enclosure,2);_collision_layer(home_furnishings,2)
 home_enclosure.visible=false;home_furnishings.visible=false
 if home_layout.has("stair_route"):data.stair_route=home_layout.stair_route
 if home_layout.has("interactions"):
  data.interactions=data.interactions.filter(func(item):return item.id not in ["pack","book"])
  var labels={"pack":"准备行囊","book":"翻看旅行相册","tea":"在小圆桌旁歇一会儿"}
  for id in home_layout.interactions:
   data.interactions.append({"id":id,"label":labels.get(id,id),"home":"frog","position":home_layout.interactions[id]})
 panda_layout=_read_layout("res://assets/panda-home.json")
 panda_home=Node3D.new();panda_home.name="PandaHome";panda_home.position=PANDA_ROOM_OFFSET;add_child(panda_home)
 var panda_baked="res://assets/house-lighting/panda-room.scn"
 var room=load(panda_baked if ResourceLoader.exists(panda_baked) else "res://assets/panda-home.glb").instantiate();panda_home.add_child(room)
 if ResourceLoader.exists(panda_baked):baked_homes["panda"]=room
 _home_collisions(room);_layout_collisions(panda_home,panda_layout);_collision_layer(panda_home,2)
 panda_home.visible=false
 panda_exterior=load("res://assets/panda-exterior.glb").instantiate();panda_exterior.position=PANDA_GARDEN_POSITION;add_child(panda_exterior)
 for item in panda_layout.get("exterior",{}).get("colliders",[]):
  if item.get("type","")!="cylinder":continue
  var body=StaticBody3D.new();panda_exterior.add_child(body);body.position=vec(item.center)
  var shape=CylinderShape3D.new();shape.radius=float(item.radius);shape.height=float(item.height)
  var collision=CollisionShape3D.new();collision.shape=shape;body.add_child(collision)
 panda_body=CharacterBody3D.new();panda_body.name="PandaBody";panda_body.collision_layer=2;panda_body.collision_mask=2;panda_body.floor_snap_length=.4;panda_home.add_child(panda_body)
 panda_body.position=vec(panda_layout.get("panda_position",[-1.35,.2,-.25]))
 panda_actor=load("res://assets/panda.glb").instantiate();panda_body.add_child(panda_actor)
 _configure_character_lighting(panda_actor)
 panda_actor.rotation.y=float(panda_layout.get("panda_yaw",PI/2))
 var panda_shape=CapsuleShape3D.new();panda_shape.radius=.38;panda_shape.height=1.2
 var panda_collision=CollisionShape3D.new();panda_collision.shape=panda_shape;panda_collision.position.y=.6;panda_body.add_child(panda_collision)
 panda_animator=_find_animator(panda_actor)
 if panda_animator:
  for clip in panda_animator.get_animation_list():
   panda_animator.get_animation(clip).loop_mode=Animation.LOOP_NONE if clip in ["Greet","Stand","StandUp","SitDown"] else Animation.LOOP_LINEAR
  if panda_animator.has_animation("Idle"):panda_animator.play("Idle")
  panda_animator.animation_finished.connect(func(clip):
   if clip=="Greet" and panda_animator.has_animation("Idle"):panda_animator.play("Idle",.2))
 var sign=Label3D.new();sign.text=_tr("熊猫家");sign.font=load("res://ui-font.otf");sign.font_size=58;sign.pixel_size=.009
 sign.position=PANDA_GARDEN_POSITION+Vector3(0,2.9,4.4);sign.outline_size=9;sign.modulate=Color("fff5d5");add_child(sign)
 panda_exterior.set_meta("sign",sign)
 data.interactions.append({"id":"panda_visit","label":"拜访熊猫","position":[26,.45,18.0]})
 data.interactions.append({"id":"panda_tea","label":"和熊猫喝杯茶","home":"panda","position":[100,.2,1.15]})
 data.zones.append({"label":"熊猫的竹木茶室","position":[26,.25,16]})
 if not baked_homes.has("frog"):_build_house_lights("frog",home_layout,Vector3.ZERO)
 if not baked_homes.has("panda"):_build_house_lights("panda",panda_layout,PANDA_ROOM_OFFSET)

func _baked_room_lighting(node: Node):
 if node is LightmapGI:
  var key="dusk_data" if night else "day_data"
  var path=str(node.get_meta(key,""))
  if path!="" and ResourceLoader.exists(path):
   # Both lightmaps are built on identical UV2 geometry. Switching time of day
   # changes lighting only; collision, furniture and character state stay intact.
   if not node.light_data or node.light_data.resource_path!=path:node.light_data=load(path)
 elif node is Light3D:
  node.light_energy=float(node.get_meta("dusk_energy" if night else "day_energy",node.light_energy))
  var light_color=node.get_meta("dusk_color" if night else "day_color",node.light_color)
  node.light_color=light_color if light_color is Color else Color(str(light_color))
  if node is SpotLight3D:node.shadow_reverse_cull_face=true
 for child in node.get_children():_baked_room_lighting(child)

func _build_house_lights(id: String, layout: Dictionary, offset: Vector3):
 for item in layout.get("windows",[]).slice(0,3):
  var light=SpotLight3D.new();light.name="WindowLight_"+str(item.get("name",id));add_child(light)
  var normal=vec(item.get("inward_normal",[0,0,-1])).normalized()
  var center=offset+vec(item.position)
  light.position=center-normal*.18
  light.look_at(center+normal*4+Vector3.DOWN*2.0)
  light.light_color=Color("ffecd0");light.light_energy=.62
  light.spot_angle=42.0;light.spot_attenuation=1.3;light.spot_range=11.0
  light.shadow_enabled=true;light.shadow_blur=1.5;light.shadow_bias=.025;light.shadow_normal_bias=.45
  light.shadow_reverse_cull_face=true
  light.set_meta("home",id);light.set_meta("kind","window");light.visible=false;household_lights.append(light)
 var fallback_lamps=[{"name":"table_candle","position":[-14.42,1.25,-10.67],"range":3.0},{"name":"loft_lantern","position":[-14.0,3.9,-14.3],"range":2.5}] if id=="frog" else []
 for item in layout.get("lamps",fallback_lamps).slice(0,2):
  var light=OmniLight3D.new();light.name="LanternLight_"+str(item.get("name",id));add_child(light)
  light.position=offset+vec(item.position)
  var color=item.get("color","ffd49a")
  light.light_color=Color(float(color[0]),float(color[1]),float(color[2])) if color is Array else Color(str(color))
  light.light_energy=float(item.get("energy",.22));light.omni_range=float(item.get("range",3.2))
  light.shadow_enabled=false;light.set_meta("home",id);light.set_meta("kind","lantern");light.visible=false;household_lights.append(light)

func _room_position(key: String, fallback: Array) -> Vector3:
 if active_home=="panda":return PANDA_ROOM_OFFSET+vec(panda_layout.get(key,fallback))
 return vec(home_layout.get(key,fallback))

func _enter_home(id: String):
 active_home=id;inside_home=true;home_cooldown=.75
 frog.collision_mask=2;frog.velocity=Vector3.ZERO
 frog.position=_room_position("entry_spawn",[0,.22,3.85] if id=="panda" else [-15,.22,-7.85])
 mode=1;interior_camera_initialized=false;home_orbit=.40
 jump_prepare=0.0;jump_takeoff=0.0;landing_time=0.0;was_grounded=false
 frog.collision_layer=2
 if mode_button:mode_button.text=_tr("跟着小青蛙")
 actor.rotation.y=0;turn=0;yaw=0
 stage.visible=false;home_enclosure.visible=id=="frog";home_furnishings.visible=id=="frog"
 panda_home.visible=id=="panda";panda_exterior.visible=false
 panda_exterior.get_meta("sign").visible=false
 home_light.visible=true;window_light.visible=true
 if butterfly:butterfly.visible=false
 if id=="panda":
  panda_wait=16.0
  home_light.position=PANDA_ROOM_OFFSET+Vector3(0,4.4,.4)
  window_light.position=PANDA_ROOM_OFFSET+Vector3(3.9,4,-1);window_light.look_at(PANDA_ROOM_OFFSET+Vector3(-1,.2,.8))
  state.panda_visits+=1;_save();_toast("熊猫泡好了茶，过来坐坐。",4)
  if panda_animator and panda_animator.has_animation("Greet"):panda_animator.play("Greet",.2)
 else:
  home_light.position=Vector3(-14.8,4.8,-11.3)
  window_light.position=Vector3(-10.2,3.0,-13.3);window_light.look_at(Vector3(-17.2,.2,-10))
 _apply_lighting();_camera_update(1)
 if friend_life:friend_life.room_changed()

func _leave_home():
 jump_prepare=0.0;jump_takeoff=0.0;landing_time=0.0;was_grounded=false
 frog.collision_layer=1
 var previous=active_home
 inside_home=false;active_home="";home_cooldown=1.0;frog.collision_mask=1
 frog.position=PANDA_GARDEN_POSITION+Vector3(0,.3,5.7) if previous=="panda" else Vector3(-15,.32,-6.3)
 frog.velocity=Vector3.ZERO;turn=PI;actor.rotation.y=PI
 home_enclosure.visible=false;home_furnishings.visible=false;panda_home.visible=false
 stage.visible=true;panda_exterior.visible=true;panda_exterior.get_meta("sign").visible=true
 home_light.visible=false;window_light.visible=false
 if butterfly:butterfly.visible=true
 _apply_lighting()
 camera.position=frog.position+Vector3(0,8,10);_camera_update(1)
 if friend_life:friend_life.room_changed()

func _update_home():
 if home_cooldown>0:return
 if inside_home:
  var center_x=100.0 if active_home=="panda" else -15.0
  var exit_z=float(panda_layout.get("exit_z",4.68)) if active_home=="panda" else float(home_layout.get("exit_z",-7.38))
  if frog.position.z>exit_z and abs(frog.position.x-center_x)<1.05 and frog.position.y<1.2:_leave_home()
 elif abs(frog.position.x+15)<1.05 and frog.position.z< -7.78 and frog.position.z> -8.3 and frog.position.y<1:
  _enter_home("frog")

func _apply_lighting():
 var has_baked=inside_home and baked_homes.has(active_home)
 sun.visible=not inside_home
 sun.light_energy=0.0 if inside_home else (.50 if night else 1.05)
 sun.light_color=Color("ffa36b") if night else Color("fff2db")
 sun.rotation_degrees.x=-14 if night else -48
 sky_fill.light_energy=.08 if inside_home else .17
 sky_fill.visible=not has_baked
 sky_fill.light_color=Color("dbe4e6") if inside_home else Color("b8d7d4")
 environment.background_mode=Environment.BG_COLOR if inside_home else Environment.BG_SKY
 environment.background_color=Color("70644c")
 # Indoor exposure and diffuse bounce are independent of the outdoor sun.
 # Keep baked contact shadows and window direction; lift the unreadable backs
 # of furniture and moving characters instead of washing out the whole world.
 environment.tonemap_exposure=(1.10 if night else 1.18) if inside_home else 1.0
 environment.fog_enabled=not inside_home
 environment.ambient_light_color=Color("d7cdbb") if inside_home else (Color("a6b4c5") if night else Color("c5d0b7"))
 environment.ambient_light_energy=(.40 if night else .62) if inside_home else (.46 if night else .38)
 if has_baked:
  environment.ambient_light_color=Color("edf2ef")
  environment.ambient_light_energy=.36 if night else .48
 home_light.light_energy=.25 if night else .36
 window_light.light_energy=.28 if night else .58
 var authored_windows=false
 for light in household_lights:
  light.visible=inside_home and light.get_meta("home")==active_home
  if light.get_meta("kind")=="window":
   light.light_energy=.14 if night else .65
   light.light_color=Color("bfd0e2") if night else Color("ffecd0")
   authored_windows=authored_windows or light.visible
  else:light.light_energy=.34 if night else .18
 if authored_windows:window_light.visible=false
 for lamp in room_lamps:
  lamp.visible=active_home!="panda" and not authored_windows and not has_baked
  lamp.light_color=Color("fff0d8") if inside_home else Color("ffd696")
  lamp.light_energy=.10 if inside_home else .65
 if has_baked:
  home_light.visible=true;home_light.light_color=Color("fff4df")
  home_light.light_energy=.30 if night else .42
  home_light.omni_attenuation=.55;home_light.light_specular=0.0
  window_light.visible=false
  _baked_room_lighting(baked_homes[active_home])

func _setup_door():
 if door==null:return
 var sb=StaticBody3D.new();door.add_child(sb)
 var cs=CollisionShape3D.new();var box=BoxShape3D.new();box.size=Vector3(2.07,1.8,.16);cs.shape=box;cs.position=Vector3(1.06,.91,0);sb.add_child(cs)

func _setup_frog():
 frog=CharacterBody3D.new();frog.name="TravelFrog";frog.floor_snap_length=.4;frog.floor_max_angle=deg_to_rad(53);add_child(frog)
 var col=CollisionShape3D.new();var shape=CapsuleShape3D.new();shape.radius=.27;shape.height=1.02;col.shape=shape;col.position.y=.53;frog.add_child(col)
 actor=load("res://assets/frog.glb").instantiate();frog.add_child(actor)
 actor.position.y=col.position.y-shape.height*.5
 animator=_find_animator(actor)
 if animator:
  for clip in animator.get_animation_list():animator.get_animation(clip).loop_mode=Animation.LOOP_NONE if clip in ["JumpStart","Land"] else Animation.LOOP_LINEAR
 gear=load("res://assets/frog-gear.glb").instantiate();actor.add_child(gear);gear.position=Vector3(0,.57,.23);gear.rotation.y=PI
 _configure_character_lighting(actor)
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

func _tr(txt: String) -> String:
 return str(translations.get(txt,{}).get(locale,txt)) if locale!="zh-CN" else txt

func _label(txt: String,size: int=18) -> Label:
 var l=Label.new();l.text=_tr(txt);l.add_theme_font_size_override("font_size",size);l.add_theme_color_override("font_color",Color("34472f"));return l

func _button(txt: String,action: Callable) -> Button:
 var b=Button.new();b.text=_tr(txt);b.custom_minimum_size=Vector2(92,44);b.add_theme_stylebox_override("normal",_style(Color(.95,.95,.87,.94)));b.add_theme_stylebox_override("hover",_style(Color("e7edcc")));b.add_theme_stylebox_override("pressed",_style(Color("d7e2b4")));b.add_theme_color_override("font_color",Color("3e5136"));b.add_theme_font_size_override("font_size",17);b.pressed.connect(action);return b

func _setup_ui():
 hud=CanvasLayer.new();add_child(hud);overlay=Control.new();overlay.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);overlay.mouse_filter=Control.MOUSE_FILTER_IGNORE;hud.add_child(overlay)
 var theme=Theme.new();theme.default_font=load("res://ui-font.otf");theme.default_font_size=18;overlay.theme=theme
 var title_panel=PanelContainer.new();title_panel.name="MainInfo";title_panel.position=Vector2(26,22);overlay.add_child(title_panel);title_panel.add_theme_stylebox_override("panel",_style(Color(.96,.96,.89,.91)))
 var left=VBoxContainer.new();title_panel.add_child(left)
 var title=_label("旅行青蛙 · 林间来信",25);left.add_child(title)
 zone_label=_label("家门口  ·  午后",15);zone_label.add_theme_color_override("font_color",Color("5c7150"));left.add_child(zone_label)
 var top=HBoxContainer.new();top.name="TopActions";overlay.add_child(top);top.set_anchors_preset(Control.PRESET_TOP_RIGHT);top.offset_left=-550;top.offset_top=26;top.offset_right=-26;top.offset_bottom=70;top.add_theme_constant_override("separation",8)
 counter=_label("三叶草 24",18);counter.custom_minimum_size=Vector2(130,44);counter.add_theme_stylebox_override("normal",_style(Color(.96,.96,.89,.91)));counter.vertical_alignment=VERTICAL_ALIGNMENT_CENTER;top.add_child(counter)
 mode_button=_button("俯看小世界",_cycle_camera);top.add_child(mode_button)
 top.add_child(_button("相册",_open_album));top.add_child(_button("午后 / 黄昏",_toggle_night))
 var bottom=VBoxContainer.new();bottom.name="BottomInfo";overlay.add_child(bottom);bottom.set_anchors_preset(Control.PRESET_CENTER_BOTTOM);bottom.offset_left=-390;bottom.offset_top=-126;bottom.offset_right=390;bottom.offset_bottom=-22;bottom.alignment=BoxContainer.ALIGNMENT_CENTER
 toast_label=_label("",18);toast_label.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;toast_label.add_theme_stylebox_override("normal",_style(Color(.96,.96,.89,.92)));bottom.add_child(toast_label)
 prompt_label=_label("",20);prompt_label.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;prompt_label.add_theme_stylebox_override("normal",_style(Color(.94,.96,.84,.94)));bottom.add_child(prompt_label)
 var help=_label("WASD 移动   ·   Space 跳跃   ·   鼠标右键环视   ·   E 互动   ·   P 拍照   ·   C 视角",14);help.name="KeyboardHelp";help.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;bottom.add_child(help)
 var action_bar=HBoxContainer.new();action_bar.name="ActionBar";overlay.add_child(action_bar);action_bar.set_anchors_preset(Control.PRESET_BOTTOM_LEFT);action_bar.offset_left=28;action_bar.offset_top=-78;action_bar.offset_right=280;action_bar.offset_bottom=-34
 action_bar.add_child(_button("拍一张 P",_take_photo));action_bar.add_child(_button("行囊",_show_bag))
 mobile_menu=MenuButton.new();mobile_menu.text="⋯";mobile_menu.custom_minimum_size=Vector2(48,44);mobile_menu.visible=false;top.add_child(mobile_menu)
 mobile_menu.flat=false
 mobile_menu.add_theme_stylebox_override("normal",_style(Color(.95,.95,.87,.96)))
 mobile_menu.add_theme_color_override("font_color",Color("3e5136"));mobile_menu.add_theme_font_size_override("font_size",24)
 var popup=mobile_menu.get_popup();popup.add_theme_font_size_override("font_size",18);popup.add_theme_constant_override("v_separation",16)
 for label in ["俯看小世界","相册","午后 / 黄昏","拍一张 P","行囊"]:popup.add_item(_tr(label))
 popup.id_pressed.connect(_mobile_action)

func _mobile_action(id: int):
 match id:
  0:_cycle_camera()
  1:_open_album()
  2:_toggle_night()
  3:_take_photo()
  4:_show_bag()

func _mobile_layout(viewport_size: Vector2):
 if not overlay:return
 mobile_ui=true
 var width=max(280.0,viewport_size.x)
 var portrait=viewport_size.y>viewport_size.x
 var main=overlay.get_node("MainInfo")
 main.position=Vector2(12,12);main.visible=portrait
 main.get_child(0).get_child(0).add_theme_font_size_override("font_size",18)
 zone_label.add_theme_font_size_override("font_size",13)
 var top=overlay.get_node("TopActions")
 top.set_anchors_preset(Control.PRESET_TOP_LEFT)
 top.position=Vector2(12,104 if portrait else 12)
 for child in top.get_children():child.visible=child==counter or child==mobile_menu
 counter.size_flags_horizontal=Control.SIZE_EXPAND_FILL;counter.add_theme_font_size_override("font_size",16)
 mobile_menu.get_popup().max_size=Vector2i(viewport_size-Vector2(24,24))
 var bottom=overlay.get_node("BottomInfo")
 bottom.set_anchors_preset(Control.PRESET_TOP_LEFT);bottom.position=Vector2(16,max(144.0,viewport_size.y-230));bottom.size=Vector2(width-32,65)
 bottom.get_node("KeyboardHelp").hide();overlay.get_node("ActionBar").hide()
 for label in [toast_label,prompt_label]:
  label.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;label.custom_minimum_size.x=0;label.add_theme_font_size_override("font_size",15)
 # Minimum sizes are recomputed after hiding the desktop buttons/help line.
 # Fitting before that pass leaves the old 550/780 px container widths in place.
 top.set_deferred("size",Vector2(min(230.0,width-24),44))
 bottom.set_deferred("size",Vector2(width-32,65))
 main.set_deferred("size",Vector2.ZERO)
 if is_instance_valid(album_panel):_fit_mobile_panel()

func _fit_mobile_panel():
 var extent=get_viewport().get_visible_rect().size
 var half=Vector2(min(460.0,(extent.x-24)/2),min(320.0,(extent.y-32)/2))
 album_panel.offset_left=-half.x;album_panel.offset_right=half.x;album_panel.offset_top=-half.y;album_panel.offset_bottom=half.y

func _touch_look(delta: Vector2):
 if input_locked:return
 if inside_home and mode==1:home_orbit-=delta.x*.006
 if not inside_home or mode==2:
  yaw-=delta.x*.006;pitch=clamp(pitch+delta.y*.005,.14,1.35)

func _setup_butterfly():
 if not ResourceLoader.exists("res://assets/butterfly.glb"):return
 butterfly=load("res://assets/butterfly.glb").instantiate();add_child(butterfly);butterfly.position=Vector3(23,2,7)

func _process(delta):
 if not ready_world:return
 time+=delta
 home_cooldown=max(0.0,home_cooldown-delta)
 tea_time=max(0.0,tea_time-delta)
 if time>2 and fps_samples.size()<300:fps_samples.append(Engine.get_frames_per_second())
 _update_home()
 _camera_update(delta)
 if door:
  var d=Vector2(frog.position.x+15,frog.position.z+7.66).length();door.rotation.y=lerp_angle(door.rotation.y,-1.55 if d<3.1 else 0.0,1-exp(-delta*4))
 if shell:shell.visible=true
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
 if friend_life:friend_life.physics(delta)
 if not friend_life or not friend_life.save.companion:_panda_motion(delta)
 if riding:
  boat_time+=delta;var length=boat_curve.get_baked_length();var t=min(length,boat_time*1.10);var p=boat_curve.sample_baked(t)
  boat.position=p;frog.position=p+Vector3(0,.085,0);frog.velocity=Vector3.ZERO;_animate("Sit")
  if t>=length:
   riding=false;frog.position=Vector3(5,.45,23);boat.position=vec(data.boat_path[0]);_toast("漂到了池塘边。沿小径慢慢回家吧。",5)
  return
 var wish=Vector3.ZERO
 if auditing:wish=audit_input
 elif not input_locked:
  var v=Input.get_vector("left","right","forward","back");wish=Vector3(v.x,0,v.y).rotated(Vector3.UP,camera.rotation.y if inside_home and mode!=2 else yaw)
 var gait=locomotion.get("frog",{})
 var running=Input.is_action_pressed("run")
 var walking_speed=float(gait.get("walk_speed",1.18))
 var speed=float(gait.get("run_speed",2.45)) if running else walking_speed*(1.0 if inside_home else 1.20)
 if posing>0:wish=Vector3.ZERO
 if landing_time>.13:wish=Vector3.ZERO
 var rate=1-exp(-delta*12);frog.velocity.x=lerp(frog.velocity.x,wish.x*speed,rate);frog.velocity.z=lerp(frog.velocity.z,wish.z*speed,rate)
 jump_buffer=max(0.0,jump_buffer-delta)
 coyote=.10 if frog.is_on_floor() else max(0.0,coyote-delta)
 if Input.is_action_just_pressed("jump") and not input_locked:jump_buffer=.14
 if jump_buffer>0 and coyote>0 and jump_prepare<=0 and jump_takeoff<=0:
  jump_prepare=float(gait.get("jump_prepare",.12));jump_buffer=0;posing=0;landing_time=0;_animate("JumpStart",1.0,.045)
 if jump_prepare>0:
  jump_prepare=max(0.0,jump_prepare-delta)
  frog.velocity.x*=.55;frog.velocity.z*=.55
  if jump_prepare<=0:
   frog.velocity.y=6.4;coyote=0;jump_takeoff=float(gait.get("jump_takeoff",.13))
  else:frog.velocity.y=-.1
 elif frog.is_on_floor():frog.velocity.y=-.1
 else:frog.velocity.y-=18*delta
 var before_move=frog.position
 _step_up(delta)
 frog.move_and_slide()
 var actual_speed=Vector2(frog.position.x-before_move.x,frog.position.z-before_move.z).length()/max(delta,.001)
 if frog.is_on_floor() and not was_grounded:landing_time=float(gait.get("land_duration",1.0/3.0))
 was_grounded=frog.is_on_floor();landing_time=max(0.0,landing_time-delta)
 if jump_prepare>0:_animate("JumpStart",1.0,.045)
 elif jump_takeoff>0:
  jump_takeoff=max(0.0,jump_takeoff-delta)
 elif not frog.is_on_floor():_animate("JumpAir",1.0,.08)
 elif landing_time>0:_animate("Land",1.0,.045)
 elif actual_speed>.10:
  if wish.length()>.10:turn=lerp_angle(turn,atan2(-wish.x,-wish.z),1-exp(-delta*12))
  actor.rotation.y=turn
  var clip="Run" if running and animator and animator.has_animation("Run") else "Walk"
  var reference_speed=float(gait.get("run_speed",2.45)) if clip=="Run" else walking_speed
  _animate(clip,clamp(actual_speed/reference_speed,.15,2.0),.10)
 elif posing>0:_animate("Sit")
 else:_animate("Idle")
 if frog.position.y< -3 or (not inside_home and Vector2(frog.position.x,frog.position.z).length()>46):
  if inside_home:frog.position=_room_position("entry_spawn",[0,.22,3.85] if active_home=="panda" else [-15,.22,-7.85])
  else:frog.position=vec(data.spawn)+Vector3.UP*.2
  frog.velocity=Vector3.ZERO

func _step_up(delta):
 if not frog.is_on_floor() or frog.velocity.y>0:return
 var move=Vector3(frog.velocity.x,0,frog.velocity.z)*delta
 if move.length()<.002 or not frog.test_move(frog.global_transform,move):return
 var raised=frog.global_transform;raised.origin.y+=.35
 if frog.test_move(raised,move):return
 var probe=frog.position+move.normalized()*.36+Vector3.UP*.36
 var q=PhysicsRayQueryParameters3D.create(probe,probe-Vector3.UP*.43);q.exclude=[frog.get_rid()];q.collision_mask=frog.collision_mask
 var hit=get_world_3d().direct_space_state.intersect_ray(q)
 if not hit.is_empty() and hit.normal.y>.60:
  var step=hit.position.y-frog.position.y
  if step>.015 and step<.335:frog.position.y=hit.position.y+.008

func _animate(name: String, speed_scale: float = 1.0, blend: float = .14):
 if animator and animator.has_animation(name):
  animator.speed_scale=speed_scale
  if animator.current_animation!=name:animator.play(name,blend)

func _panda_motion(delta: float):
 if active_home!="panda" or panda_body==null:return
 var home=vec(panda_layout.get("panda_position",[-1.35,.2,-.25]))
 var route=panda_layout.get("panda_walk_route",[[-1.45,.2,1.50],[-2.35,.2,1.55],[-2.35,.2,-.25],[-1.35,.2,-.25]])
 var moving=panda_route_index>=0
 if not moving:
  panda_wait-=delta
  if panda_roam_enabled and panda_wait<=0 and tea_time<=0 and frog.global_position.distance_to(panda_body.global_position)>2.0:
   panda_route_index=0;moving=true
 if tea_time>0 and moving:panda_returning=true
 var target=home if panda_returning else (vec(route[panda_route_index]) if moving else panda_body.position)
 var direction=target-panda_body.position;direction.y=0
 if moving and direction.length()<.09:
  if panda_returning or panda_route_index>=route.size()-1:
   panda_route_index=-1;panda_returning=false;panda_wait=24.0;moving=false
  else:panda_route_index+=1
 var gait=locomotion.get("panda",{})
 var speed=float(gait.get("walk_speed",.68))
 var before=panda_body.position
 var close_to_guest=panda_body.global_position.distance_to(frog.global_position)<.92
 var desired_yaw=atan2(direction.x,direction.z)
 var turning=moving and abs(angle_difference(panda_actor.rotation.y,desired_yaw))>.45
 var advance=moving and direction.length()>.03 and not close_to_guest and not turning
 panda_body.velocity.x=direction.normalized().x*speed if advance else 0.0
 panda_body.velocity.z=direction.normalized().z*speed if advance else 0.0
 panda_body.velocity.y=-.1 if panda_body.is_on_floor() else panda_body.velocity.y-18*delta
 panda_body.move_and_slide()
 var actual_speed=Vector2(panda_body.position.x-before.x,panda_body.position.z-before.z).length()/max(delta,.001)
 if moving and advance and actual_speed<.03:panda_blocked+=delta
 else:panda_blocked=0
 if panda_blocked>1.0:panda_returning=true
 if panda_animator:
  var clip="Walk" if actual_speed>.05 and panda_animator.has_animation("Walk") else "Idle"
  if turning and panda_animator.has_animation("Turn"):clip="Turn"
  if clip=="Idle" and tea_time>0 and not moving and panda_animator.has_animation("Sit"):clip="Sit"
  if clip=="Idle" and panda_animator.current_animation=="Greet":return
  panda_animator.speed_scale=clamp(actual_speed/speed,.15,1.4) if clip=="Walk" else 1.0
  if panda_animator.has_animation(clip) and panda_animator.current_animation!=clip:panda_animator.play(clip,.16)
 if moving:panda_actor.rotation.y=lerp_angle(panda_actor.rotation.y,desired_yaw,1-exp(-delta*7))
 elif not moving:panda_actor.rotation.y=lerp_angle(panda_actor.rotation.y,float(panda_layout.get("panda_yaw",PI/2)),1-exp(-delta*5))

func _camera_update(delta):
 if frog==null or camera==null:return
 if manual_review_camera:return
 if capture_dir!="":return
 var target=frog.position+Vector3.UP*.70
 camera.fov=68 if inside_home else 44
 actor.visible=mode!=2
 if mode==2:
  camera.position=target;camera.rotation=Vector3(-pitch*.35,yaw,0);return
 if inside_home:
  _home_camera()
  return
 camera.fov=44
 var dist=distance if mode==0 else 5.4
 var p=pitch if mode==0 else clamp(pitch*.55,.18,.55)
 var offset=Vector3(sin(yaw)*cos(p),sin(p),cos(yaw)*cos(p))*dist
 var desired=target+offset
 camera.position=camera.position.lerp(desired,1-exp(-delta*7));camera.look_at(target)

func _home_camera():
 if mode==1:
  _home_follow_camera()
  return
 # The camera stays within the opaque room even when the frog jumps on the loft.
 var upper=clamp((frog.position.y-1.8)/1.4,0.0,1.0)
 var layout=panda_layout if active_home=="panda" else home_layout
 var offset=PANDA_ROOM_OFFSET if active_home=="panda" else Vector3.ZERO
 var views=layout.get("camera_views",{})
 if not views is Dictionary:views={}
 if active_home=="panda" and not views.has("loft"):
  views=views.duplicate();views["loft"]={"position":[.35,5.3,3.8],"target":[0,3.8,-2.0],"fov":68.0}
 var main=layout.get("camera_main",views.get("main",{}))
 var fallback_eye=[0,4.8,4.05] if active_home=="panda" else [-14.2,5.0,-7.72]
 var fallback_at=[0,1.9,-.5] if active_home=="panda" else [-15,1.65,-12.2]
 camera.position=offset+vec(main.get("position",fallback_eye))
 var look=offset+vec(main.get("look_at",main.get("target",fallback_at)))
 camera.fov=float(main.get("fov",main.get("vertical_fov",76.0)))
 if views.has("loft"):
  var loft_view=views.loft
  camera.position=camera.position.lerp(offset+vec(loft_view.position),upper)
  look=look.lerp(offset+vec(loft_view.get("look_at",loft_view.get("target",fallback_at))),upper)
  camera.fov=lerp(camera.fov,float(loft_view.get("fov",loft_view.get("vertical_fov",camera.fov))),upper)
 else:look.y+=upper*.45
 var entry=clamp((frog.position.z-(2.3 if active_home=="panda" else -9.7))/1.6,0.0,1.0)*(1-upper)
 look.y-=entry*2.15;camera.fov+=entry*8
 if mode==1:look=look.lerp(frog.position+Vector3.UP*.65,.17)
 camera.look_at(look)
 # Keep the frog readable near the entry without moving the camera through a wall.
 var frame=get_viewport().get_visible_rect()
 var safe=frame.grow_individual(-frame.size.x*.06,-frame.size.y*.06,-frame.size.x*.06,-frame.size.y*.08)
 for i in range(8):
  var head=frog.position+Vector3.UP*1.02
  if not camera.is_position_behind(head) and safe.has_point(camera.unproject_position(head)) and safe.has_point(camera.unproject_position(frog.position+Vector3.UP*.08)):break
  look=look.lerp(frog.position+Vector3.UP*.55,.24)
  camera.look_at(look)

func _home_follow_camera():
 var layout=panda_layout if active_home=="panda" else home_layout
 var center=Vector3(100,0,0) if active_home=="panda" else Vector3(-15,0,-12)
 var radii=Vector2(4.55,4.55) if active_home=="panda" else Vector2(5.05,4.35)
 var ceiling=float(layout.get("roof_y",layout.get("ceiling_height",6.3)))
 var look=frog.global_position+Vector3.UP*.64
 var best_eye=look+Vector3(0,2.05,3.65)
 var best_score=INF
 # Evaluate camera positions inside the actual room. Nearby wall and furniture
 # collisions shorten an arm; they never expose the garden through the shell.
 for index in range(16):
  var angle=home_orbit+TAU*float(index)/16.0
  var eye=look+Vector3(sin(angle)*home_camera_distance,1.88,cos(angle)*home_camera_distance)
  var local=Vector2((eye.x-center.x)/radii.x,(eye.z-center.z)/radii.y)
  if local.length()>1.0:
   local=local.normalized();eye.x=center.x+local.x*radii.x;eye.z=center.z+local.y*radii.y
  eye.y=min(eye.y,ceiling-.40)
  var arm=eye-look
  var q=PhysicsRayQueryParameters3D.create(look,eye,2,[frog.get_rid()])
  var hit=get_world_3d().direct_space_state.intersect_ray(q)
  if not hit.is_empty():eye=hit.position-arm.normalized()*.28
  var actual_arm=eye-look
  var angle_cost=abs(wrapf(angle-home_orbit,-PI,PI))*.50
  var proximity_cost=max(0.0,3.20-actual_arm.length())*4.0
  var continuity_cost=camera.position.distance_to(eye)*.12 if interior_camera_initialized else 0.0
  var score=angle_cost+proximity_cost+continuity_cost
  if score<best_score:
   best_score=score;best_eye=eye
 var eased=camera.position.lerp(best_eye,1-exp(-get_process_delta_time()*7)) if interior_camera_initialized else best_eye
 var safety_query=PhysicsRayQueryParameters3D.create(look,eased,2,[frog.get_rid()])
 var safety_hit=get_world_3d().direct_space_state.intersect_ray(safety_query)
 if not safety_hit.is_empty():eased=safety_hit.position-(eased-look).normalized()*.28
 camera.position=eased
 camera.fov=61.0
 camera.look_at(look)
 var frame=get_viewport().get_visible_rect().grow(-20.0)
 for attempt in range(5):
  if frame.has_point(camera.unproject_position(frog.position+Vector3.UP*1.08)) and frame.has_point(camera.unproject_position(frog.position+Vector3.UP*.02)):break
  camera.fov+=4.0
 interior_camera_initialized=true

func _unhandled_input(event):
 if event is InputEventKey and event.pressed and event.physical_keycode==KEY_ESCAPE:
  if friend_life and friend_life.panel!="":friend_life.action("close")
  else:_close_panel()
  return
 if input_locked:return
 if event is InputEventMouseMotion and Input.is_mouse_button_pressed(MOUSE_BUTTON_RIGHT):
  if inside_home and mode==1:home_orbit-=event.relative.x*.006
  if not inside_home or mode==2:
   yaw-=event.relative.x*.006;pitch=clamp(pitch+event.relative.y*.005,.14,1.35)
 if event is InputEventMouseButton and event.pressed and not inside_home:
  if event.button_index==MOUSE_BUTTON_WHEEL_UP:distance=clamp(distance-1.5,7,34)
  if event.button_index==MOUSE_BUTTON_WHEEL_DOWN:distance=clamp(distance+1.5,7,34)
 if event is InputEventMouseButton and event.pressed and inside_home and mode==1:
  if event.button_index==MOUSE_BUTTON_WHEEL_UP:home_camera_distance=clamp(home_camera_distance-.20,2.4,4.6)
  if event.button_index==MOUSE_BUTTON_WHEEL_DOWN:home_camera_distance=clamp(home_camera_distance+.20,2.4,4.6)
 if event is InputEventKey and event.pressed and not event.echo:
  match event.physical_keycode:
   KEY_E:_interact()
   KEY_P:_take_photo()
   KEY_C:_cycle_camera()
   KEY_TAB:_open_album()
   KEY_ESCAPE:_close_panel()

func _cycle_camera():
 mode=(mode+1)%3
 mode_button.text=_tr(["俯看小世界","跟着小青蛙","蛙眼看世界"][mode])

func _toggle_night():
 night=not night;_apply_lighting()

func _update_nearest():
 nearest="";var best=2.4
 for item in data.interactions:
  if str(item.get("home",""))!=active_home:continue
  var p=vec(item.position);var d=Vector2(frog.position.x-p.x,frog.position.z-p.z).length()
  if d<best and abs(frog.position.y-p.y)<1.4:
   best=d;nearest=item.id;prompt_label.text="E  ·  "+_tr(item.label)
 if riding:prompt_label.text="顺着水流，慢慢漂一会儿。"
 prompt_label.visible=nearest!="" or riding
 var zone_best=999.0
 for z in data.zones:
  var p=vec(z.position);var d=frog.position.distance_to(p)
  if d<zone_best:zone_best=d;current_zone=z.label
 if active_home=="frog":current_zone="树干小屋" if frog.position.y<2.7 else "夹层睡铺"
 elif active_home=="panda":current_zone="熊猫的竹木茶室" if frog.position.y<2.7 else "熊猫的竹床"
 if friend_life:friend_life.nearest_hint()

func _interact():
 if input_locked or riding:return
 if friend_life and friend_life.context_interact(nearest):return
 match nearest:
  "clover":
   if Time.get_unix_time_from_system()-float(state.harvest_at)<100:_toast("叶片还在慢慢长大，再去散会儿步。",4)
   else:
    state.clovers+=18;state.harvest_at=Time.get_unix_time_from_system();_save();_toast("收到了 18 枚三叶草。可以回屋准备便当了。",5)
  "mail":_message(_tr("一封森林来信"),_tr("沿着巨叶旁的小径出发，越过木桥，就能找到橙色帐篷。\n\n沿营地旁的新小路向南走，熊猫家有一壶热茶。\n\n溪水下游有一块漂流木片。累了就坐一会儿，带张照片回家。"))
  "panda_visit":_enter_home("panda")
  "panda_tea":
   if tea_time>0:return
   frog.position=PANDA_ROOM_OFFSET+vec(panda_layout.get("tea_guest_position",[0,.2,1.35]))
   frog.velocity=Vector3.ZERO;posing=7;tea_time=7;actor.rotation.y=0;turn=0
   _toast("熊猫：山路慢慢走，茶也慢慢喝。",6)
  "tea":posing=5;_toast("喝一口热茶，再翻翻旅途中带回来的明信片。",5)
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
 if toast_label:toast_label.text=_tr(txt);toast_remaining=seconds

func _refresh_hud():
 counter.text=_tr("三叶草")+"  %d"%int(state.clovers)
 zone_label.text=_tr(current_zone)+"  ·  "+_tr("黄昏" if night else "午后")+("  ·  "+_tr("行囊已备好") if state.packed else "")

func _load_state():
 var disk={}
 if FileAccess.file_exists(save_path):
  var value=JSON.parse_string(FileAccess.get_file_as_string(save_path))
  if value is Dictionary:disk=value
 var modified=float(FileAccess.get_modified_time(save_path)) if FileAccess.file_exists(save_path) else 0.0
 var recovered=SaveRecovery.choose(disk,SaveRecovery.read_mirror(),modified)
 for key in state:
  if key in recovered:state[key]=recovered[key]
 DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(photo_directory))
 SaveRecovery.repair_photos(state,photo_directory)

func _save():
 state["_save_sequence"]=int(state.get("_save_sequence",0))+1
 state["_saved_at"]=Time.get_unix_time_from_system()
 var serialized=JSON.stringify(state,"  ")
 # localStorage is synchronous, unlike the engine's next-frame IndexedDB sync.
 # A blocked/quota-limited browser falls back to the existing userfs pathway.
 SaveRecovery.mirror(serialized)
 var file=FileAccess.open(save_path,FileAccess.WRITE)
 if file:
  file.store_string(serialized);file.close()

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
 if mobile_ui:_fit_mobile_panel()
 var box=VBoxContainer.new();box.add_theme_constant_override("separation",15);album_panel.add_child(box)
 var row=HBoxContainer.new();box.add_child(row);var head=_label(title,18 if mobile_ui else 26);head.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;head.size_flags_horizontal=Control.SIZE_EXPAND_FILL;row.add_child(head);row.add_child(_button("继续散步",_close_panel));return box

func _close_panel():
 if is_instance_valid(album_panel):album_panel.queue_free()
 album_panel=null;input_locked=false

func _message(title: String,body: String):
 var box=_panel(title);var text=Label.new();text.text=body;text.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;text.add_theme_font_size_override("font_size",21);text.add_theme_color_override("font_color",Color("526047"));box.add_child(text)

func _show_bag():
 _message("今天的行囊",("便当已经备好，叶帽也带上了。\n\n到林间营地坐下吃饭，蝴蝶会在附近飞舞。" if state.packed else "行囊还是空的。\n\n回小屋找到木箱，使用 8 枚三叶草准备一份便当。")+"\n\n三叶草：%d　　营地休息：%d 次"%[int(state.clovers),int(state.camp_visits)])

 if friend_life and is_instance_valid(album_panel):
  var box=album_panel.get_child(0)
  var note=friend_life.text("bag_count").replace("{n}",str(friend_life.save.cooked.size())).replace("{m}",str(friend_life.save.memories.size()))
  box.add_child(_label(note,18));box.add_child(_button(friend_life.text("friends"),friend_life.open_journal))

func _open_album():
 # Keep legacy records, but never count a PNG that did not reach browser storage.
 var available=state.photos.filter(func(item):return item is Dictionary and FileAccess.file_exists(photo_directory.path_join(str(item.get("file","")))))
 var box=_panel("旅行相册  ·  %d 张"%available.size())
 if available.is_empty():
  var empty=_label("还没有照片。按 P，留住眼前的小世界。",18 if mobile_ui else 21);empty.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;box.add_child(empty);return
 var scroll=ScrollContainer.new();scroll.size_flags_vertical=Control.SIZE_EXPAND_FILL;box.add_child(scroll);var grid=GridContainer.new();grid.columns=1 if mobile_ui else 3;grid.add_theme_constant_override("h_separation",12);grid.add_theme_constant_override("v_separation",15);scroll.add_child(grid)
 for item in available:
  var path=ProjectSettings.globalize_path(photo_directory+"/"+item.file);var im=Image.load_from_file(path)
  if im==null:continue
  var card=VBoxContainer.new();grid.add_child(card);var pic=TextureRect.new();pic.custom_minimum_size=Vector2(270,180);pic.expand_mode=TextureRect.EXPAND_IGNORE_SIZE;pic.stretch_mode=TextureRect.STRETCH_KEEP_ASPECT_CENTERED;pic.texture=ImageTexture.create_from_image(im);card.add_child(pic);card.add_child(_label(item.place,17))

func _capture_views():
 input_locked=true;overlay.visible=false;await get_tree().create_timer(2.0).timeout
 var views=[
  {"name":"01-庭院与岩屋","eye":Vector3(-15,13,13),"at":Vector3(-17,1.1,-3.5),"frog":Vector3(-15,.35,-3)},
  {"name":"02-树干小屋室内","home":"frog","eye":Vector3(-14,4.7,-7.9),"at":Vector3(-15,1.7,-12),"frog":Vector3(-15.4,.22,-11.6)},
  {"name":"03-蓝色睡铺","home":"frog","eye":Vector3(-13.9,5.48,-9.1),"at":Vector3(-15.25,3.77,-14.6),"frog":Vector3(-16.7,3.26,-14.05)},
  {"name":"03b-熊猫的竹木茶室","home":"panda","eye":PANDA_ROOM_OFFSET+Vector3(.35,4.05,4.42),"at":PANDA_ROOM_OFFSET+Vector3(0,2,-.8),"frog":PANDA_ROOM_OFFSET+Vector3(0,.22,1.17)},
  {"name":"04-森林与溪桥","eye":Vector3(21,9,3),"at":Vector3(9,.8,-9),"frog":Vector3(13,.7,-9)},
  {"name":"05-林间营地","eye":Vector3(29,5,13),"at":Vector3(24,1.0,5.5),"frog":Vector3(22,.35,7)},
  {"name":"07-Tripo小青蛙","eye":Vector3(-13,2.2,1),"at":Vector3(-15,.85,-3),"frog":Vector3(-15,.24,-3)},
  {"name":"06-自然世界全景","eye":Vector3(-40,35,45),"at":Vector3(0,.3,-1),"frog":vec(data.spawn)}]
 for v in views:
  var residence=str(v.get("home",""))
  if residence!="":_enter_home(residence)
  elif inside_home:_leave_home()
  frog.position=v.frog;frog.velocity=Vector3.ZERO
  var rq=PhysicsRayQueryParameters3D.create(frog.position+Vector3.UP*.5,frog.position-Vector3.UP*2);rq.exclude=[frog.get_rid()];rq.collision_mask=frog.collision_mask
  var floor_hit=get_world_3d().direct_space_state.intersect_ray(rq)
  if not floor_hit.is_empty():frog.position.y=floor_hit.position.y+.015
  actor.rotation.y=PI
  _update_home()
  if inside_home:_home_camera()
  else:camera.fov=44;camera.position=v.eye;camera.look_at(v.at)
  await get_tree().create_timer(.7).timeout
  await RenderingServer.frame_post_draw
  get_viewport().get_texture().get_image().save_png(capture_dir+"/"+v.name+".png")
  print("CAPTURE ",v.name)
 if inside_home:_leave_home()
 frog.position=vec(data.spawn);_update_home();camera.position=Vector3(-15,13,13);camera.look_at(Vector3(-17,1.1,-3.5));overlay.visible=true
 await RenderingServer.frame_post_draw
 get_viewport().get_texture().get_image().save_png(capture_dir+"/08-游戏界面.png")
 print("CAPTURE_DONE");get_tree().quit()

func _walk_to(target: Vector3,timeout: float=12) -> Dictionary:
 var elapsed=0.0;var start=frog.position
 while elapsed<timeout:
  var diff=target-frog.position;diff.y=0
  if diff.length()<.12:
   audit_input=Vector3.ZERO
   if frog.is_on_floor() and abs(frog.position.y-target.y)<.34:return {"reached":true,"feet":[frog.position.x,frog.position.y,frog.position.z],"elapsed":elapsed,"target_height":target.y,"height_delta":frog.position.y-target.y}
  else:audit_input=diff.normalized()
  await get_tree().physics_frame;elapsed+=1.0/60.0
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

# The native and browser front ends call the same semantic friend actions.
func get_friend_ui_state(language: String="") -> Dictionary:
 return friend_life.ui_state(language if language!="" else locale) if friend_life else {"open":false}

func get_friend_hud_state(language: String="") -> Dictionary:
 return friend_life.hud_state(language if language!="" else locale) if friend_life else {}

func friend_ui_action(id: String):
 if friend_life:friend_life.action(id)
