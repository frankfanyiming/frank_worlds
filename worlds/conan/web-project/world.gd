extends Node3D
const BUILDINGS=["mouri","kudo","agasa"]
var specs:Dictionary={}
var homes:Dictionary={}
var assets:Dictionary={}
var material_meta:Dictionary={}
var material_cache:Dictionary={}
var exterior:Node3D
var player:CharacterBody3D
var camera:Camera3D
var avatar:Node3D
var avatar_anim:AnimationPlayer
var actors:Array=[]
var traffic:Array=[]
var traffic_curve:Curve3D
var traffic_specs:Dictionary={}
var motion_review=false
var signals:Array=[]
var lamps:Array=[]
var window_lights:Array=[]
var ui:CanvasLayer
var info:Label
var hint:Label
var clock_text:Label
var env:Environment
var sun:DirectionalLight3D
var yaw=0.0
var pitch=-.08
var first_person=false
var elapsed=0.0
var daytime=15.5
var mouse_drag=false
var nearest:Dictionary={}
var message_until=0.0
var testing=false
var controls_panel:PanelContainer
var inspection_views:Array=[]
var current_view=0
var photo_mode=false
var gi_ready=false
func vec(a:Array)->Vector3:return Vector3(float(a[0]),float(a[1]),float(a[2]))
func world_point(key:String,p:Array)->Vector3:return homes[key].to_global(vec(p))
func model(key:String,parent:Node3D,pos:Vector3,angle:float=0.0,size:float=1.0)->Node3D:
	var path="res://assets/"+key+".glb"
	if not ResourceLoader.exists(path):push_error("Missing model: "+path);return Node3D.new()
	if not assets.has(key):assets[key]=load(path)
	var n:Node3D=assets[key].instantiate();parent.add_child(n);n.position=pos;n.rotation.y=angle;n.scale=Vector3.ONE*size;n.set_meta("asset",key);apply_materials(n)
	if not key.begins_with("buildings/") and key!="street":disable_baking(n)
	return n
func collision(parent:Node3D,pos:Vector3,size:Vector3,angle:float=0.0,rx:float=0.0)->void:
	var b=StaticBody3D.new();parent.add_child(b);b.position=pos;b.rotation=Vector3(rx,angle,0);var c=CollisionShape3D.new();var s=BoxShape3D.new();s.size=size;c.shape=s;b.add_child(c)
func collision_meshes(n:Node)->void:
	if n is MeshInstance3D and "_Collision" in str(n.name):n.create_trimesh_collision()
	for c in n.get_children():
		if not c is CollisionObject3D:collision_meshes(c)
func _ready()->void:
	motion_review=OS.get_cmdline_user_args().has("--review-motion")
	testing=OS.get_cmdline_user_args().has("--verify") or OS.get_cmdline_user_args().has("--capture") or motion_review
	for a in [["forward",KEY_W],["back",KEY_S],["left",KEY_A],["right",KEY_D],["run",KEY_SHIFT]]:
		InputMap.add_action(a[0]);var e=InputEventKey.new();e.physical_keycode=a[1];InputMap.action_add_event(action_name(a[0]),e)
	for path in ["street_materials.json","building_materials.json"]:
		if FileAccess.file_exists("res://assets/"+path):material_meta.merge(JSON.parse_string(FileAccess.get_file_as_string("res://assets/"+path)),true)
	lighting();build_street();build_houses();build_player();build_ui();build_people();build_weather();build_grass();travel(Vector3(16.8,.2,4),.4)
	await get_tree().process_frame
	await prepare_indirect_light()
	add_child(load("res://xlands_bridge.gd").new())
	print("BLENDER_TOWN_READY buildings=",homes.size()," tripo_characters=",actors.size()+1," cars=",traffic.size()," remote_rooms=0")
	if motion_review:await review_motion();get_tree().quit();return
	if OS.get_cmdline_user_args().has("--bake"):get_tree().quit();return
	if OS.get_cmdline_user_args().has("--capture"):await capture_all();get_tree().quit();return
	if OS.get_cmdline_user_args().has("--verify"):await verify();get_tree().quit();return
func action_name(n)->StringName:return StringName(n)
func lighting()->void:
	env=Environment.new();env.background_mode=Environment.BG_SKY;env.sky=Sky.new();env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;env.ambient_light_color=Color(.68,.75,.86);env.ambient_light_sky_contribution=.35;env.ambient_light_energy=.65;env.tonemap_mode=Environment.TONE_MAPPER_ACES;env.tonemap_exposure=.95
	env.ssao_enabled=true;env.ssao_radius=.55;env.ssao_intensity=1.25;env.ssil_enabled=true;env.ssil_intensity=.7;env.fog_enabled=true;env.fog_density=.0014;env.fog_sky_affect=.08;env.fog_light_color=Color(.72,.80,.86)
	var we=WorldEnvironment.new();we.environment=env;add_child(we)
	sun=DirectionalLight3D.new();sun.rotation_degrees=Vector3(-38,35,0);sun.light_color=Color(1,.94,.84);sun.light_energy=1.35;sun.shadow_enabled=true;sun.directional_shadow_max_distance=100;sun.shadow_bias=.12;sun.shadow_normal_bias=1.0;sun.light_angular_distance=2.0;add_child(sun)
func build_street()->void:
	exterior=Node3D.new();exterior.name="BlenderStreet";add_child(exterior)
	if ResourceLoader.exists("res://assets/street.glb"):
		var street=model("street",exterior,Vector3.ZERO);collision_meshes(street)
	else:collision(exterior,Vector3(10,-.1,0),Vector3(200,.15,200))
	model("beetle",exterior,Vector3(67.7,.06,3.6),-.45)
	# All ordinary vehicles are Blender assets with +Z fronts, ground-zero tires,
	# and four separate wheel pivots. The doctor's Tripo Beetle stays above.
	traffic_specs=JSON.parse_string(FileAccess.get_file_as_string("res://assets/vehicles/manifest.json"))
	traffic_curve=Curve3D.new()
	var anchors=[Vector3(11.1,.045,-45),Vector3(11.1,.045,45),Vector3(12.5,.045,49),Vector3(14.0,.045,45),Vector3(14.0,.045,-45),Vector3(12.5,.045,-49)]
	for i in range(anchors.size()):
		var tangent=(anchors[(i+1)%anchors.size()]-anchors[(i-1+anchors.size())%anchors.size()]).normalized()*1.3
		traffic_curve.add_point(anchors[i],-tangent,tangent)
	traffic_curve.add_point(anchors[0],Vector3(0,0,-1.3),Vector3(0,0,1.3));traffic_curve.bake_interval=.05
	for i in range(6):
		var key=["hatchback","van","pickup"][i%3];var car=model("vehicles/"+key,exterior,Vector3.ZERO);var wheels=[]
		for label in traffic_specs[key].wheels:
			var pivot=car.find_child(label,true,false)
			if not pivot:push_error("Missing wheel pivot: "+key+"/"+label);continue
			wheels.append({"node":pivot,"rest":pivot.transform,"front":"_F" in label})
		traffic.append({"node":car,"key":key,"distance":i*traffic_curve.get_baked_length()/6.0+8,"speed":3.6+float(i)*.12,"velocity":0.0,"wheels":wheels,"roll":0.0})
		place_traffic(traffic[-1],0.0)
	for item in [[Vector3(9.1,0,21),0.0],[Vector3(16,0,27),PI],[Vector3(9.1,0,-25),0.0]]:
		var signal_model=model("props/signal",exterior,item[0],item[1]);var surfaces=[]
		collect_signal_materials(signal_model,surfaces);signals.append(surfaces)
	var street_probe=ReflectionProbe.new();street_probe.position=Vector3(12.5,3,0);street_probe.size=Vector3(35,12,94);street_probe.box_projection=true;street_probe.intensity=.8;exterior.add_child(street_probe)
func collect_signal_materials(n:Node,surfaces:Array)->void:
	if n is MeshInstance3D:
		for i in n.mesh.get_surface_count():
			var m=n.get_active_material(i)
			if m is StandardMaterial3D and m.resource_name.begins_with("Signal_lens_") and not m in surfaces:
				m.emission_enabled=true;m.emission=m.albedo_color;surfaces.append(m)
	for c in n.get_children():collect_signal_materials(c,surfaces)
func place_traffic(car:Dictionary,travelled:float)->void:
	var length=traffic_curve.get_baked_length();var d=fposmod(car.distance,length)
	var p=traffic_curve.sample_baked(d,true);var ahead=traffic_curve.sample_baked(fposmod(d+.08,length),true);var direction=(ahead-p).normalized()
	car.node.position=p;car.node.rotation.y=atan2(direction.x,direction.z)
	var next_direction=(traffic_curve.sample_baked(fposmod(d+.68,length),true)-traffic_curve.sample_baked(fposmod(d+.60,length),true)).normalized()
	var curvature=direction.signed_angle_to(next_direction,Vector3.UP)/.60
	var steer=clamp(atan(float(traffic_specs[car.key].wheelbase)*curvature),-.56,.56)
	car.roll=fposmod(car.roll+travelled/float(traffic_specs[car.key].radius),TAU)
	for wheel in car.wheels:
		# Steering and rolling rotate about the stored axle, never the model origin.
		wheel.node.transform=wheel.rest
		wheel.node.basis=Basis(Vector3.UP,steer if wheel.front else 0.0)*Basis(Vector3.RIGHT,car.roll)*wheel.rest.basis
func build_houses()->void:
	for key in BUILDINGS:
		var path="res://assets/buildings/"+key+".json"
		if not FileAccess.file_exists(path):continue
		var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(path));specs[key]=spec
		var root=Node3D.new();root.name="Blender_"+key;add_child(root);root.position=vec(spec.origin);root.rotation.y=float(spec.get("yaw",0));homes[key]=root
		var architecture=model("buildings/"+key,root,Vector3.ZERO);collision_meshes(architecture)
		for c in spec.get("colliders",[]):collision(root,vec(c.p),vec(c.s),float(c.get("r",0)),float(c.get("rx",0)))
		for r in spec.get("ramps",[]):collision(root,vec(r.p),vec(r.s),float(r.get("r",0)),float(r.get("rx",0)))
		for item in spec.get("lights",[]):
			var l=OmniLight3D.new();l.position=vec(item.p);l.omni_range=float(item.get("range",5));l.light_energy=float(item.get("energy",.8));l.light_color=Color(1,.93,.82);l.light_size=.06;l.shadow_enabled=true;l.omni_attenuation=.85;l.light_specular=.18;root.add_child(l);
			if key=="kudo":l.position.y-=.36 if l.position.y<3 else .40
			l.set_meta("base_energy",l.light_energy);lamps.append(l)
		add_window_lights(key,root)
		var probe=ReflectionProbe.new();probe.position=vec(spec.get("probe_center",[0,2.5,-2]));probe.size=vec(spec.get("probe_size",[23,9,28]));probe.interior=true;probe.box_projection=true;probe.intensity=.62;probe.enable_shadows=true;root.add_child(probe)
		for view in spec.get("views",[]):
			if view.name=="工藤宅-前立面":view.p=[.4,7.4,18.3];view.target=[0,3.8,4.5]
			if view.name=="毛利事务所":view.p=[.4,4.92,-.48];view.target=[-1.7,4.12,-5.1]
			if key=="agasa" and view.name=="实验区":view.p=[-4.4,1.65,-2.9];view.target=[-2.0,1.25,-5.72]
			inspection_views.append({"name":view.name,"p":root.to_global(vec(view.p)),"target":root.to_global(vec(view.target))})
func build_player()->void:
	player=CharacterBody3D.new();player.name="Player";player.floor_snap_length=.32;player.floor_max_angle=deg_to_rad(48);add_child(player)
	var shape=CollisionShape3D.new();var capsule=CapsuleShape3D.new();capsule.radius=.23;capsule.height=1.02;shape.shape=capsule;shape.position.y=.515;player.add_child(shape)
	camera=Camera3D.new();camera.near=.045;camera.far=230;camera.fov=67;add_child(camera);camera.current=true;avatar=model("conan",player,Vector3.ZERO);avatar_anim=animation_in(avatar);play(avatar_anim,"Idle")
func build_people()->void:
	var names={"ran":"毛利兰","kogoro":"毛利小五郎","haibara":"灰原哀","agasa":"阿笠博士"}
	var words={"ran":"来坐坐吧。事务所在二楼，从右边楼梯就能上去。","kogoro":"先仔细观察现场，答案往往藏在小细节里。","haibara":"窗边的光线很好，我在整理今天的实验记录。","agasa":"新发明快做好了！工作台上的小零件别弄丢。"}
	for key in specs:
		for d in specs[key].get("npcs",[]):
			var n=model(d.asset,homes[key],vec(d.p),float(d.get("yaw",0)));var a=animation_in(n);play(a,"Idle");actors.append({"node":n,"anim":a,"name":names.get(d.asset,d.asset),"dialog":words.get(d.asset,"下午好。"),"walking":false,"home":n.position,"key":d.asset})
	for i in range(6):
		var n=model("pedestrian_m" if i%2==0 else "pedestrian_f",exterior,Vector3(16.6 if i%2==0 else 8.65,.16,-19+float(i)*8));var a=animation_in(n);play(a,"Walk");actors.append({"node":n,"anim":a,"name":"街坊","dialog":"午后好，河边和车站都可以步行过去。","walking":true,"home":n.position,"phase":float(i)*1.31})
func build_ui()->void:
	ui=CanvasLayer.new();add_child(ui);ui.name="Interface"
	var theme=Theme.new();theme.default_font=load("res://ui-font.ttc");theme.default_font_size=15
	var panel=PanelContainer.new();panel.position=Vector2(24,22);panel.theme=theme;ui.add_child(panel)
	var style=StyleBoxFlat.new();style.bg_color=Color(.055,.09,.115,.87);style.corner_radius_top_left=14;style.corner_radius_top_right=14;style.corner_radius_bottom_left=14;style.corner_radius_bottom_right=14;style.content_margin_left=18;style.content_margin_right=18;style.content_margin_top=13;style.content_margin_bottom=13;panel.add_theme_stylebox_override("panel",style)
	var col=VBoxContainer.new();col.add_theme_constant_override("separation",8);panel.add_child(col)
	var title=Label.new();title.text="米花町　／　frank 小世界";title.add_theme_font_size_override("font_size",22);col.add_child(title);clock_text=Label.new();col.add_child(clock_text)
	var nav=HBoxContainer.new();col.add_child(nav)
	var street=Button.new();street.text="街区";street.pressed.connect(func():travel(Vector3(16.8,.2,4),.4));nav.add_child(street)
	for key in specs:
		var menu=MenuButton.new();menu.text={"mouri":"白罗 · 毛利楼","kudo":"工藤家","agasa":"博士家"}[key];nav.add_child(menu)
		var popup=menu.get_popup();popup.add_item("门外",0)
		for room in specs[key].get("rooms",[]):popup.add_item(room.name)
		popup.id_pressed.connect(func(id):
			if id==0:travel(world_point(key,specs[key].spawn),float(specs[key].get("yaw",0)))
			else:travel(world_point(key,specs[key].rooms[id-1].p)+Vector3(0,.12,0),float(specs[key].get("yaw",0)))
		)
	info=Label.new();info.add_theme_color_override("font_color",Color(.83,.86,.84));col.add_child(info)
	controls_panel=PanelContainer.new();controls_panel.theme=theme;controls_panel.position=Vector2(25,836);controls_panel.add_theme_stylebox_override("panel",style);ui.add_child(controls_panel)
	var controls=Label.new();controls.text="WASD 行走   Shift 快走   鼠标右键 环视   V 视角   E 交谈   N 昼夜   F 隐藏界面";controls_panel.add_child(controls)
	hint=Label.new();hint.theme=theme;hint.position=Vector2(30,786);hint.add_theme_font_size_override("font_size",19);ui.add_child(hint)
func travel(p:Vector3,angle:float=0)->void:
	photo_mode=false;player.position=p;player.velocity=Vector3.ZERO;yaw=angle;pitch=-.06;camera.position=p+Vector3(0,1.05,0)
func _unhandled_input(event:InputEvent)->void:
	if testing:return
	if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_RIGHT:mouse_drag=event.pressed;Input.mouse_mode=Input.MOUSE_MODE_CAPTURED if mouse_drag else Input.MOUSE_MODE_VISIBLE
	if event is InputEventMouseMotion and (mouse_drag or Input.mouse_mode==Input.MOUSE_MODE_CAPTURED):yaw-=event.relative.x*.003;pitch=clamp(pitch-event.relative.y*.003,-1.15,1.0)
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode==KEY_ESCAPE:Input.mouse_mode=Input.MOUSE_MODE_VISIBLE;mouse_drag=false
		if event.keycode==KEY_V:first_person=not first_person
		if event.keycode==KEY_N:daytime=21.0 if daytime<18 else 15.5
		if event.keycode==KEY_F:ui.visible=not ui.visible
		if event.keycode==KEY_E and not nearest.is_empty():hint.text=nearest.name+"："+nearest.dialog;message_until=elapsed+7;play(nearest.anim,"Talk")
func _physics_process(delta:float)->void:
	if not player or testing or photo_mode:return
	var input=Input.get_vector("left","right","forward","back");var dir=Vector3(input.x,0,input.y).rotated(Vector3.UP,yaw);var speed=1.85 if Input.is_action_pressed("run") else .85
	player.velocity.x=move_toward(player.velocity.x,dir.x*speed,delta*12);player.velocity.z=move_toward(player.velocity.z,dir.z*speed,delta*12)
	player.velocity.y=-.35 if player.is_on_floor() else player.velocity.y-delta*14;player.move_and_slide()
	if player.position.y< -6:travel(Vector3(16.8,.2,4),.4)
	avatar.visible=not first_person
	if dir.length()>.05:avatar.rotation.y=lerp_angle(avatar.rotation.y,atan2(dir.x,dir.z),delta*10)
	var moving_speed=Vector2(player.velocity.x,player.velocity.z).length()
	var running=Input.is_action_pressed("run")
	play(avatar_anim,"Run" if running and moving_speed>.05 else ("Walk" if moving_speed>.05 else "Idle"))
	if avatar_anim:avatar_anim.speed_scale=moving_speed/(.79545 if running else .36667) if moving_speed>.05 else 1.0
	var target=player.position+Vector3(0,1.05,0);camera.rotation=Vector3(pitch,yaw,0)
	if first_person:camera.position=target
	else:
		var end=target+Vector3(0,.55,3.0).rotated(Vector3.RIGHT,pitch).rotated(Vector3.UP,yaw)
		var query=PhysicsRayQueryParameters3D.create(target,end);query.exclude=[player.get_rid()];var hit=get_world_3d().direct_space_state.intersect_ray(query);camera.position=hit.position+(target-hit.position).normalized()*.15 if hit else end
	update_nearby()
func _process(delta:float)->void:
	if not player or motion_review:return
	elapsed+=delta;daytime=fmod(daytime+delta*.001,24);update_life(delta)
func update_nearby()->void:
	nearest={};var best=2.0
	for a in actors:
		var distance=a.node.global_position.distance_to(player.position)
		if distance<best:nearest=a;best=distance
	if elapsed>message_until:hint.text="E　与 "+str(nearest.name)+" 交谈" if not nearest.is_empty() else ""
	var title="街巷与住宅";var distance=5.0
	for key in specs:
		for room in specs[key].get("rooms",[]):
			var d=world_point(key,room.p).distance_to(player.position)
			if d<distance:title=room.name;distance=d
	info.text=title;clock_text.text="%02d:%02d　·　%s"%[int(daytime),int(fmod(daytime,1)*60),"夜间" if daytime>=18 or daytime<6 else "晴朗午后"]
func update_life(delta:float)->void:
	var night=daytime>=18 or daytime<6;
	for light in window_lights:light.light_energy=.04 if night else float(light.get_meta("day_energy"))
	sun.light_energy=.12 if night else 1.35;sun.light_color=Color(.55,.67,1) if night else Color(1,.94,.84)
	if env.sky.sky_material is ShaderMaterial:env.sky.sky_material.set_shader_parameter("night_mix",1.0 if night else 0.0)
	for a in actors:
		if a.walking:
			var phase=elapsed*.075+a.phase;a.node.position=a.home+Vector3(0,0,sin(phase)*5.5);a.node.rotation.y=lerp_angle(a.node.rotation.y,0 if cos(phase)>0 else PI,delta*4);a.anim.speed_scale=max(.3,abs(cos(phase))*.6)
		elif elapsed>message_until:play(a.anim,"Read" if a.get("key","")=="kogoro" else "Idle")
	var red=fmod(elapsed,25)>14;var length=traffic_curve.get_baked_length()
	for car in traffic:
		var p=traffic_curve.sample_baked(fmod(car.distance,length),true);var next=traffic_curve.sample_baked(fmod(car.distance+.15,length),true);var direction=(next-p).normalized()
		var stop=red and ((direction.z>.5 and p.z>16.6 and p.z<18.8) or (direction.z<-.5 and p.z>28 and p.z<30.4))
		for other in traffic:
			if other!=car and fposmod(other.distance-car.distance,length)<6.5:stop=true
		# Yield to the player as well as the car ahead.
		var to_player=player.position-p
		if to_player.dot(direction)>0 and to_player.dot(direction)<4.5 and abs(to_player.cross(direction).y)<1.0:stop=true
		var near_turn=abs(p.z)>42.5
		car.velocity=move_toward(car.velocity,0.0 if stop else (1.25 if near_turn else car.speed),delta*2.4)
		var travelled=delta*car.velocity;car.distance+=travelled;place_traffic(car,travelled)
	for surfaces in signals:
		for m in surfaces:
			var index=int(m.resource_name.right(1));m.emission_energy_multiplier=1.2 if (index==2 if red else index==0) else .0
func apply_materials(n:Node)->void:
	if n is MeshInstance3D:
		n.gi_mode=GeometryInstance3D.GI_MODE_STATIC
		var all_glass=true
		for i in n.mesh.get_surface_count():
			var source=n.get_active_material(i)
			if not source is StandardMaterial3D:continue
			var key=source.resource_name;var m:StandardMaterial3D
			var lower=key.to_lower()
			var glass=("glass" in lower or "glazing" in lower or lower.begins_with("window")) and not ("lamp" in lower or "tail" in lower or "amber" in lower or "gasket" in lower)
			if not glass:all_glass=false
			var cache_key=str(source.get_instance_id())
			if material_cache.has(cache_key):m=material_cache[cache_key]
			else:
				m=source.duplicate();m.texture_filter=BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
				var spec:Dictionary=material_meta.get(key,{})
				if spec.get("scan")!=null and not spec.get("baked_tint",false):
					var path="res://assets/pbr/"+str(spec.scan)+"/";var albedo=path+"albedo.jpg"
					if not ResourceLoader.exists(albedo):albedo=path+"albedo.png"
					if ResourceLoader.exists(albedo):m.albedo_texture=load(albedo);m.albedo_color=Color(str(spec.get("tint_hex","ffffff"))) if spec.get("tint_hex")!=null else Color.WHITE
					if ResourceLoader.exists(path+"normal.png"):m.normal_enabled=true;m.normal_texture=load(path+"normal.png");m.normal_scale=float(spec.get("normal_strength",.25))
					if ResourceLoader.exists(path+"roughness.jpg"):m.roughness_texture=load(path+"roughness.jpg");m.roughness_texture_channel=BaseMaterial3D.TEXTURE_CHANNEL_RED;m.roughness=1
				if key=="M_Continuous_asphalt":m.albedo_color=Color(.52,.54,.55)
				if key=="Town_grass_ground":m.albedo_color=Color(.55,.68,.37);m.roughness=1
				if glass:
					m.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA;m.albedo_color=Color(.78,.86,.88,.12);m.roughness=.12;m.metallic=.1;m.cull_mode=BaseMaterial3D.CULL_DISABLED;m.depth_draw_mode=BaseMaterial3D.DEPTH_DRAW_DISABLED
				material_cache[cache_key]=m
			n.set_surface_override_material(i,m)
		if all_glass:n.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	for c in n.get_children():apply_materials(c)
func build_weather()->void:
	var shader=Shader.new();shader.code="""shader_type sky;
uniform float night_mix=0.0;
float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
float noise(vec2 p){vec2 i=floor(p);vec2 f=fract(p);f=f*f*(3.0-2.0*f);return mix(mix(hash(i),hash(i+vec2(1,0)),f.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),f.x),f.y);}
float clouds(vec2 p){float v=0.0;float a=.5;for(int i=0;i<5;i++){v+=a*noise(p);p=p*2.03+7.1;a*=.5;}return v;}
void sky(){vec3 d=normalize(EYEDIR);float elevation=max(d.y,0.0);vec3 color=mix(vec3(.77,.84,.87),vec3(.24,.43,.65),pow(elevation,.42));if(d.y>.03){vec2 p=d.xz/(d.y+.18)*2.1+vec2(TIME*.002,0.0);float cloud=smoothstep(.46,.68,clouds(p));color=mix(color,vec3(.98,.98,.96),cloud*smoothstep(.03,.18,d.y)*.82);}COLOR=mix(color,vec3(.022,.034,.073),night_mix);}
"""
	var material=ShaderMaterial.new();material.shader=shader;env.sky.sky_material=material;env.sky.radiance_size=Sky.RADIANCE_SIZE_128
func capture_all()->void:
	ui.visible=false;avatar.visible=false;daytime=15.5;update_life(0)
	var dir=ProjectSettings.globalize_path("res://../实机预览/");DirAccess.make_dir_recursive_absolute(dir)
	var views=[{"name":"00-米花街区","p":Vector3(20,5,3),"target":Vector3(3,4,-3)}]+inspection_views
	var count=0
	for view in views:
		camera.position=view.p;camera.look_at(view.target);camera.fov=58;daytime=15.5;update_life(0)
		for frame in range(12):await get_tree().process_frame
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png(dir+"%02d-"%count+str(view.name)+".png");print("CAPTURE ",view.name," time=",daytime," sun=",sun.light_energy);count+=1
func walk_route(key:String,route:Dictionary)->Dictionary:
	var points=route.points
	player.position=world_point(key,points[0])+Vector3(0,.12,0);player.velocity=Vector3.ZERO
	for i in range(24):await get_tree().physics_frame;player.velocity=Vector3(0,-2.5,0);player.move_and_slide()
	var reached=true;var steps=[]
	for point in points.slice(1):
		var target=world_point(key,point);var arrived=false
		for i in range(600):
			await get_tree().physics_frame;var delta=target-player.position;delta.y=0
			if delta.length()<.15:arrived=true;break
			var direction=delta.normalized();player.velocity.x=direction.x*2.3;player.velocity.z=direction.z*2.3;player.velocity.y=-.5 if player.is_on_floor() else player.velocity.y-14.0/60;player.move_and_slide()
		steps.append({"point":point,"actual":str(homes[key].to_local(player.position)),"arrived":arrived})
		if not arrived:reached=false;break
	var expected=float(route.get("expected_y",points[-1][1]))+homes[key].position.y
	return {"building":key,"route":route.name,"passed":reached and abs(player.position.y-expected)<.24,"height":player.position.y,"steps":steps}
func verify()->void:
	var report={"engine":"Godot native physics and renderer","architecture_source":"Blender","remote_interiors":0,"buildings":homes.size(),"characters":[],"rooms":[],"routes":[]}
	for key in ["conan","ran","haibara","kogoro","agasa"]:
		var n=model(key,self,Vector3(200,0,0));var anim=animation_in(n);report.characters.append({"name":key,"clips":anim.get_animation_list() if anim else [],"exists":anim!=null});n.queue_free()
	for key in specs:
		if OS.get_cmdline_user_args().has("--only-kudo") and key!="kudo":continue
		if OS.get_cmdline_user_args().has("--only-agasa") and key!="agasa":continue
		for room in specs[key].get("rooms",[]):
			player.position=world_point(key,room.p)+Vector3(0,.2,0);player.velocity=Vector3.ZERO
			for i in range(35):await get_tree().physics_frame;player.velocity=Vector3(0,-2,0);player.move_and_slide()
			var grounded=player.is_on_floor() and abs(player.position.y-world_point(key,room.p).y)<.30
			report.rooms.append({"name":room.name,"grounded":grounded,"actual":str(homes[key].to_local(player.position))})
		for route in specs[key].get("routes",[]):
			var result=await walk_route(key,route);report.routes.append(result);print("ROUTE ",JSON.stringify(result))
	FileAccess.open("res://../实走验收.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "));print("VERIFY ",JSON.stringify(report))

func animation_in(n:Node)->AnimationPlayer:
	if n is AnimationPlayer:return n
	for c in n.get_children():
		var a=animation_in(c)
		if a:return a
	return null
func play(a:AnimationPlayer,clip:String)->void:
	if not a:return
	for nm in a.get_animation_list():
		if str(nm).get_slice("/",str(nm).get_slice_count("/")-1)==clip:
			if a.current_animation!=nm:a.get_animation(nm).loop_mode=Animation.LOOP_LINEAR;a.play(nm,.20)
			return

func build_grass()->void:
	var source:Node3D=load("res://assets/props/grass.glb").instantiate()
	var instance=first_mesh(source)
	if not instance:source.free();return
	var mesh=instance.mesh.duplicate();source.free()
	var shader=Shader.new();shader.code="""shader_type spatial;render_mode cull_disabled;
varying vec3 wp;
void vertex(){wp=(MODEL_MATRIX*vec4(VERTEX,1.0)).xyz;float wind=sin(TIME*1.4+wp.x*.4+wp.z*.36);VERTEX.x+=wind*UV.y*UV.y*.016;VERTEX.z+=cos(TIME+wp.z)*UV.y*UV.y*.010;}
void fragment(){float variety=fract(sin(dot(floor(wp.xz*8.0),vec2(12.98,78.23)))*43758.54);ALBEDO=mix(vec3(.09,.17,.035),vec3(.25,.35,.09),UV.y*.55+variety*.25);ROUGHNESS=.98;BACKLIGHT=ALBEDO*.35;}
"""
	var material=ShaderMaterial.new();material.shader=shader;mesh.surface_set_material(0,material)
	var rng=RandomNumberGenerator.new();rng.seed=515
	# Public lawns only: planted instances stay outside the three architecture footprints.
	for patch in [[Vector2(20,-10),Vector2(5,16)],[Vector2(-27,-6),Vector2(3,18)],[Vector2(-18,1.8),Vector2(17,2)],[Vector2(24,12),Vector2(7,14)],[Vector2(21,37),Vector2(2,12)]]:
		var mm=MultiMesh.new();mm.transform_format=MultiMesh.TRANSFORM_3D;mm.mesh=mesh;mm.instance_count=1200 if OS.has_feature("web") else 4500
		for i in range(mm.instance_count):
			var size=rng.randf_range(.7,1.4);var pos=Vector3(rng.randf_range(-patch[1].x/2,patch[1].x/2),.034,rng.randf_range(-patch[1].y/2,patch[1].y/2));mm.set_instance_transform(i,Transform3D(Basis(Vector3.UP,rng.randf()*TAU).scaled(Vector3.ONE*size),pos))
		var node=MultiMeshInstance3D.new();node.multimesh=mm;node.position=Vector3(patch[0].x,0,patch[0].y);node.visibility_range_end=55;node.visibility_range_end_margin=8;node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;exterior.add_child(node)

func prepare_indirect_light()->void:
	if OS.has_feature("web"):gi_ready=true;return
	var volumes={"mouri":[Vector3(0,5,-6),Vector3(10.3,11.5,14)],"kudo":[Vector3(0,4,-1.5),Vector3(25,11,28)],"agasa":[Vector3(0,3,0),Vector3(17.5,8,16)]}
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://assets/lighting/"))
	for key in homes:
		var gi=VoxelGI.new();gi.name="IndirectLight_"+key;gi.position=volumes[key][0];gi.size=volumes[key][1];gi.subdiv=VoxelGI.SUBDIV_128;homes[key].add_child(gi)
		var path="res://assets/lighting/"+key+".res"
		if ResourceLoader.exists(path) and not OS.get_cmdline_user_args().has("--bake"):gi.data=load(path)
		elif OS.get_cmdline_user_args().has("--bake"):
			info.text="正在整理屋内的间接光…";await get_tree().process_frame;gi.bake(homes[key],false)
			if gi.data:gi.data.interior=false;gi.data.use_two_bounces=true;gi.data.normal_bias=.7;gi.data.energy=.75;ResourceSaver.save(gi.data,path);print("GI_BAKED ",key)
	gi_ready=true

func disable_baking(n:Node)->void:
	if n is GeometryInstance3D:n.gi_mode=GeometryInstance3D.GI_MODE_DYNAMIC
	for c in n.get_children():disable_baking(c)

func add_window_lights(key:String,root:Node3D)->void:
	var placements={
		"mouri":[[[-2.1,1.9,-.38],[-2,1.1,-5],1.5,7],[[-1.5,4.9,-.35],[-1.5,4.4,-5],1.5,7]],
		"kudo":[[[6.1,1.8,8.95],[6.1,1.1,4],2.0,8],[[-6.1,1.8,8.95],[-6.1,1.1,4],1.8,8],[[6.1,4.6,8.95],[6.1,3.8,4.7],1.5,7],[[-6.1,4.6,8.95],[-6.1,3.8,4.7],1.5,7]],
		"agasa":[[[-6.4,2.0,1.5],[0,1.1,1.5],1.7,10],[[6.4,2.0,1.5],[0,1.1,1.5],1.6,10],[[-6.6,1.9,-4.5],[-2.4,1.2,-4.5],1.5,6]]
	}
	for item in placements.get(key,[]):
		var light=SpotLight3D.new();root.add_child(light);light.position=vec(item[0]);light.look_at(root.to_global(vec(item[1])));light.light_color=Color(.84,.90,1);light.light_energy=item[2];light.spot_range=item[3];light.spot_angle=78;light.spot_attenuation=.55;light.light_size=.38;light.shadow_enabled=true;light.shadow_blur=2;light.light_specular=.08;light.set_meta("day_energy",light.light_energy);window_lights.append(light)
	# The library chandelier illuminates both tiers; lights stay below its opaque arms.
	if key=="kudo":
		for y in [2.5,4.55]:
			var light=OmniLight3D.new();root.add_child(light);light.position=Vector3(-4.7,y,-7.4);light.omni_range=6.4;light.light_energy=.65;light.light_color=Color(1,.88,.70);light.omni_attenuation=.45;light.light_specular=.08;light.shadow_enabled=false;lamps.append(light)

func first_mesh(n:Node)->MeshInstance3D:
	if n is MeshInstance3D:return n
	for c in n.get_children():
		var result=first_mesh(c)
		if result:return result
	return null
func skeleton_in(n:Node)->Skeleton3D:
	if n is Skeleton3D:return n
	for c in n.get_children():
		var result=skeleton_in(c)
		if result:return result
	return null
func review_motion()->void:
	ui.visible=false;avatar.visible=true;first_person=false;daytime=15.5;update_life(0)
	var dir=ProjectSettings.globalize_path("res://../动作与车辆实机复核/");DirAccess.make_dir_recursive_absolute(dir)
	var report={"cars":[],"conan":[],"asset_policy":"Characters and doctor's Beetle: Tripo. All scenery and ordinary traffic: Blender."}
	player.position=Vector3(15.9,.136,3);avatar.rotation.y=0;avatar_anim.speed_scale=1
	for actor in actors:
		if actor.walking:actor.node.visible=false
	camera.position=player.position+Vector3(.95,.80,2.15);camera.look_at(player.position+Vector3(0,.53,0));camera.fov=42
	for clip in ["Idle","Walk","Run"]:
		avatar_anim.play(clip,0.0);avatar_anim.advance(0);avatar_anim.pause()
		var length=avatar_anim.current_animation_length
		for phase in [0.0,.125,.25,.375,.5,.625,.75,.875]:
			avatar_anim.seek(length*phase,true);avatar_anim.advance(0)
			for frame in range(10):await get_tree().process_frame
			RenderingServer.force_draw(false)
			get_viewport().get_texture().get_image().save_png(dir+"柯南-"+clip+"-%03d.png"%int(phase*1000))
			var skeleton=skeleton_in(avatar);var foot=skeleton.find_bone("LeftFoot")
			report.conan.append({"clip":clip,"phase":phase,"left_foot":str(skeleton.get_bone_global_pose(foot).origin),"rendered":true})
	# Continuous native capture: move the real CharacterBody on the pavement,
	# matching playback speed to covered distance. This is not a still montage.
	var frames_dir=dir+"连续动作帧/";DirAccess.make_dir_recursive_absolute(frames_dir)
	Engine.physics_ticks_per_second=30;Engine.max_fps=30
	var frame_number=0
	for clip in ["Walk","Run"]:
		player.position=Vector3(16.8,.26,2);player.velocity=Vector3.ZERO;avatar.rotation.y=0
		for settle in range(12):await get_tree().physics_frame;player.velocity=Vector3(0,-1,0);player.move_and_slide()
		avatar_anim.play(clip,0);avatar_anim.advance(0);avatar_anim.pause();var duration=avatar_anim.current_animation_length
		var speed=.85 if clip=="Walk" else 1.85;var cycle_speed=.36667 if clip=="Walk" else .79545
		var grounded_frames=0
		for frame in range(90):
			await get_tree().physics_frame
			player.velocity=Vector3(0,-.35,speed);player.move_and_slide()
			if player.is_on_floor():grounded_frames+=1
			avatar_anim.seek(fposmod(frame/30.0*speed/cycle_speed,duration),true);avatar_anim.advance(0)
			camera.position=player.position+Vector3(.95,.78,2.15);camera.look_at(player.position+Vector3(0,.5,0));camera.fov=42
			elapsed+=1.0/30.0;update_life(1.0/30.0)
			RenderingServer.force_draw(false)
			get_viewport().get_texture().get_image().save_png(frames_dir+"frame_%04d.png"%frame_number);frame_number+=1
		report.conan.append({"clip":clip,"continuous_native_frames":90,"grounded_frames":grounded_frames,"actual_distance":player.position.z-2,"speed_mps":speed})
	Engine.max_fps=0;Engine.physics_ticks_per_second=60
	avatar.visible=false
	for index in range(traffic.size()):
		var car=traffic[index];car.node.visible=index<3;car.distance=35.0+index*8;place_traffic(car,0)
	for index in range(3):
		var car=traffic[index];var minimum_dot=1.0;var max_y_error=0.0;var max_pivot_error=0.0
		for step in range(180):
			car.distance=step*traffic_curve.get_baked_length()/180.0;place_traffic(car,.12)
			var d=fposmod(car.distance,traffic_curve.get_baked_length());var tangent=(traffic_curve.sample_baked(fposmod(d+.08,traffic_curve.get_baked_length()),true)-car.node.position).normalized()
			minimum_dot=min(minimum_dot,car.node.basis.z.dot(tangent));max_y_error=max(max_y_error,abs(car.node.position.y-.045))
			for w in car.wheels:max_pivot_error=max(max_pivot_error,w.node.position.distance_to(w.rest.origin))
		report.cars.append({"model":car.key,"source":"Blender","wheels":car.wheels.size(),"minimum_front_dot_motion":minimum_dot,"body_height_error":max_y_error,"pivot_drift":max_pivot_error})
		car.distance=44;place_traffic(car,.2)
		for other in traffic:other.node.visible=other==car
		for side in [-1,1]:
			camera.position=car.node.position+Vector3(side*3.5,1.50,4.2);camera.look_at(car.node.position+Vector3(0,.72,0));camera.fov=48
			for frame in range(7):await get_tree().process_frame
			RenderingServer.force_draw(false)
			get_viewport().get_texture().get_image().save_png(dir+car.key+"-"+str(side)+".png")
	for i in range(traffic.size()):traffic[i].node.visible=true;traffic[i].distance=i*11+10;place_traffic(traffic[i],0)
	camera.position=Vector3(18.8,2.4,18);camera.look_at(Vector3(11.5,1.2,0));camera.fov=60
	for frame in range(180):
		elapsed+=1.0/30.0;update_life(1.0/30.0)
		await get_tree().process_frame
		if frame%15==0:
			RenderingServer.force_draw(false)
			get_viewport().get_texture().get_image().save_png(dir+"车流-%03d.png"%frame)
	FileAccess.open(dir+"实机验收.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "));print("MOTION_REVIEW ",JSON.stringify(report))
