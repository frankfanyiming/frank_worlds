extends SceneTree
## Real CharacterBody3D navigation through the model-authored reference routes.
## Godot --headless --fixed-fps 60 --path worlds/conan/web-project \
##   --script /absolute/tools/test-conan-reference-routes.gd -- /absolute/output
## Never pass --verify, --capture, or --review-motion: the world disables physics
## for those modes. Each indoor case starts once at its outdoor menu spawn. No
## interior waypoint, staircase, or failed segment is completed by teleporting.

var world
var folder := ""
var checks := {}
var routes := []
var trace := []
var setups := []
var notes := []
var hashes := {}
var scenario := ""
var seconds := 0.0
var block_spec := {}
var route_map := {}
var abort_scenario := false
var save_images := false
var only := ""

func _initialize():call_deferred("run")

func a3(p: Vector3) -> Array:return [p.x,p.y,p.z]

func check(name: String, passed: bool):
	checks[name]=passed
	print("CONAN_ROUTE_CHECK ",name," ",passed)

func tick(count: int = 1):
	for i in range(count):
		await physics_frame
		seconds+=1.0/float(Engine.physics_ticks_per_second)

func local_point(key: String, value: Array) -> Vector3:
	if key=="street-block":
		return Transform3D(Basis(Vector3.UP,float(block_spec.get("yaw",0))),world.vec(block_spec.origin))*world.vec(value)
	return world.world_point(key,value)

func contacts() -> Array:
	var found=[]
	for i in range(world.player.get_slide_collision_count()):
		var hit=world.player.get_slide_collision(i)
		var node=hit.get_collider()
		var item={"point":a3(hit.get_position()),"normal":a3(hit.get_normal()),"depth":hit.get_depth(),"collider":str(node.get_path()) if node is Node else str(node)}
		if node is Node3D:
			item["collider_position"]=a3(node.global_position)
			for child in node.get_children():
				if child is CollisionShape3D and child.shape is BoxShape3D:
					item["box_size"]=a3(child.shape.size)
		found.append(item)
	return found

func forward_contacts(target:Vector3) -> Array:
	var direction=target-world.player.position;direction.y=0
	if direction.length()<.001:return []
	var collision=KinematicCollision3D.new()
	if not world.player.test_move(world.player.global_transform,direction.normalized()*.08,collision,.001,true,8):return []
	var found=[]
	for i in range(collision.get_collision_count()):
		var node=collision.get_collider(i)
		found.append({"collider":str(node.get_path()) if node is Node else str(node),"point":a3(collision.get_position(i)),"normal":a3(collision.get_normal(i))})
	return found

func sample(label: String):
	trace.append({"s":snapped(seconds,.001),"scenario":scenario,"segment":label,"position":a3(world.player.position),"velocity":a3(world.player.velocity),"on_floor":world.player.is_on_floor(),"animation":str(world.avatar_anim.current_animation),"animation_speed":world.avatar_anim.speed_scale})

func persist(complete: bool = false):
	var failed=[]
	for key in checks:
		if not checks[key]:failed.append(key)
	var report={"complete":complete,"requested_scenario":only if not only.is_empty() else "all","engine":Engine.get_version_info(),"renderer":RenderingServer.get_current_rendering_method(),"display_server":DisplayServer.get_name(),"physics_hz":Engine.physics_ticks_per_second,"controller":{"auditing":world.auditing,"testing":world.testing,"walk_mps":.85,"run_mps":1.85,"floor_snap":world.player.floor_snap_length,"capsule_radius":.23,"capsule_height":1.02},"asset_sha256":hashes,"scenario_start_placements":setups,"checks":checks,"failures":failed,"routes":routes,"trace_file":"physical-route-trace.json","notes":notes,"simulated_seconds":seconds}
	FileAccess.open(folder.path_join("physical-routes.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	FileAccess.open(folder.path_join("physical-route-trace.json"),FileAccess.WRITE).store_string(JSON.stringify(trace))

func snapshot(label: String):
	if not save_images:return
	await RenderingServer.frame_post_draw
	var picture=root.get_texture().get_image()
	if picture and not picture.is_empty():picture.save_png(folder.path_join(label.validate_filename()+".png"))

func walk(label: String, target: Vector3, running: bool = false) -> bool:
	var start:Vector3=world.player.position
	var speed=1.85 if running else .85
	var distance=Vector2(start.x-target.x,start.z-target.z).length()
	var limit=max(5.0,distance/speed*2.5+3.0)
	var elapsed=0.0
	var travelled=0.0
	var peak=start.y
	var low=start.y
	var last=start
	var stagnant=0.0
	var checkpoint=start
	var checkpoint_at=0.0
	var found=false
	var reason="timeout"
	var clips=[]
	var frames=0
	if running:Input.action_press("run")
	else:Input.action_release("run")
	while elapsed<limit:
		var p:Vector3=world.player.position
		var planar=Vector2(target.x-p.x,target.z-p.z)
		if planar.length()<.10 and abs(p.y-target.y)<.23 and world.player.is_on_floor():
			found=true;reason="arrived";break
		if p.y< -5.8 or p.distance_to(last)>1.2:
			reason="fell_or_unexpected_position_reset";break
		if elapsed-checkpoint_at>=1.0:
			if p.distance_to(checkpoint)<.04:stagnant+=elapsed-checkpoint_at
			else:stagnant=0.0
			checkpoint=p;checkpoint_at=elapsed
		if stagnant>=2.0:
			reason="stalled_against_collision_or_wrong_floor";break
		# Align the same forward action and yaw used by the normal player. Vertical
		# movement is entirely gravity, floor snap and actual slope collisions.
		if planar.length()>.005:
			world.yaw=atan2(-planar.x,-planar.y)
			world.audit_input=Vector2(0,-1)
		else:world.audit_input=Vector2.ZERO
		last=p
		await tick()
		var dt=1.0/float(Engine.physics_ticks_per_second)
		elapsed+=dt;frames+=1
		travelled+=world.player.position.distance_to(p)
		peak=max(peak,world.player.position.y);low=min(low,world.player.position.y)
		var clip=str(world.avatar_anim.current_animation)
		if not clips.has(clip):clips.append(clip)
		if frames%6==0:sample(label)
	world.audit_input=Vector2.ZERO
	Input.action_release("run")
	var result={"scenario":scenario,"label":label,"passed":found,"reason":reason,"start":a3(start),"target":a3(target),"end":a3(world.player.position),"horizontal_error":Vector2(target.x-world.player.position.x,target.z-world.player.position.z).length(),"vertical_error":world.player.position.y-target.y,"elapsed":elapsed,"distance_walked":travelled,"peak_y":peak,"lowest_y":low,"on_floor":world.player.is_on_floor(),"mode":"run" if running else "walk","animation_clips":clips}
	if not found:
		result["slide_contacts"]=contacts()
		result["test_only_forward_contacts"]=forward_contacts(target)
		result["capsule_bounds"]={"min":a3(world.player.position+Vector3(-.23,.005,-.23)),"max":a3(world.player.position+Vector3(.23,1.025,.23))}
		if world.homes.has("agasa"):result["end_agasa_local"]=a3(world.homes.agasa.to_local(world.player.position))
		if world.homes.has("mouri"):result["end_mouri_local"]=a3(world.homes.mouri.to_local(world.player.position))
		notes.append("Dependent route stopped after "+label+"; no interior reset was used to bypass it.")
		print("CONAN_ROUTE_FAILURE ",JSON.stringify(result))
	routes.append(result)
	sample(label+"_end")
	await tick(6)
	return found

func follow(label: String, key: String, points: Array, reverse: bool = false, running: bool = false) -> bool:
	if abort_scenario:
		notes.append("Not attempted after earlier failure: "+label)
		return false
	var ordered=points.duplicate(true)
	if reverse:ordered.reverse()
	var passed=not ordered.is_empty()
	for i in range(ordered.size()):
		if not await walk(label+"/"+str(i),local_point(key,ordered[i]),running):
			passed=false;abort_scenario=true;break
	check(scenario+"/"+label,passed)
	persist()
	await snapshot(label)
	return passed

func authored(name: String, reverse: bool = false, running: bool = false) -> bool:
	if not route_map.has(name):
		check(name+"_authored_metadata_present",false)
		notes.append("Missing authored route: "+name)
		abort_scenario=true;return false
	return await follow(name+("_reverse" if reverse else ""),"agasa",route_map[name].points,reverse,running)

func start_at_door(key: String, case_name: String = ""):
	world.audit_input=Vector2.ZERO;Input.action_release("run")
	abort_scenario=false;scenario=key+("_"+case_name if not case_name.is_empty() else "")
	var before:Vector3=world.player.position
	# This is the existing user-facing destination menu's OUTDOOR spawn, not an
	# interior room teleport. All claimed entrance/stair/room results start here.
	world.travel(world.world_point(key,world.specs[key].spawn),float(world.specs[key].get("yaw",0)))
	setups.append({"scenario":scenario,"type":"existing_outdoor_destination_menu_spawn","from":a3(before),"to":a3(world.player.position),"interior_teleports":0})
	await tick(25)
	sample("outdoor_start")

func test_frontage():
	scenario="connected_mouri_frontage";abort_scenario=false
	# Preserve the real game's initial spawn and cross the existing street before
	# walking the model-authored continuous sidewalk in both directions.
	await follow("street_to_frontage","street-block",[[-7.4,.20,1.10]],false,true)
	var block_routes=block_spec.get("routes",[])
	if block_routes.is_empty():
		check("connected_frontage_route_metadata_present",false)
		notes.append("Connected block supplies no route; no frontage pass is claimed.")
	else:
		var points:Array=block_routes[0].points
		await follow("connected_frontage_forward","street-block",points,false,true)
		await follow("connected_frontage_reverse","street-block",points,true,true)
		await follow("frontage_to_mouri_outside","mouri",[world.specs.mouri.spawn],false,true)

func test_agasa():
	# Each independent feature test walks in from the ordinary OUTDOOR spawn.
	# A failure stops its dependent steps, but does not hide other rooms' failures.
	for case_name in ["basement","gallery","kitchen","garage"]:
		if not only.is_empty() and only!=case_name:continue
		await start_at_door("agasa",case_name)
		await authored("front_to_round_kitchen")
		if case_name=="garage":
			await authored("kitchen_to_living")
			await authored("living_to_garage")
			await authored("living_to_garage",true)
			await authored("kitchen_to_living",true)
		else:
			await follow("kitchen_front_to_hall","agasa",[[-1.3,.08,3.1],[0,.08,3.25]])
			if case_name=="kitchen":
				# This is the first portion of the model-authored tower approach,
				# stopping before the stair opening to enter the counter's real gap.
				await follow("hall_to_kitchen_aisle","agasa",route_map.main_to_tower.points.slice(0,3))
				await authored("kitchen_work_aisle")
				await authored("kitchen_work_aisle",true)
				await follow("hall_to_kitchen_aisle_reverse","agasa",route_map.main_to_tower.points.slice(0,3),true)
			else:
				await authored("main_to_tower")
				if case_name=="basement":
					await authored("Basement to main",true)
					await authored("cellar_to_research")
					await authored("cellar_to_research",true)
					await authored("Basement to main")
				else:
					await authored("Main to gallery")
					await authored("gallery_bridge")
					await authored("gallery_perimeter")
					await authored("gallery_perimeter",true)
					await authored("gallery_bridge",true)
					await authored("Main to gallery",true)
				await authored("main_to_tower",true)
			await follow("hall_to_kitchen_front","agasa",[[0,.08,3.25],[-1.3,.08,3.1],[-1.55,.08,3.1]])
		await authored("front_to_round_kitchen",true)

func run():
	var args=OS.get_cmdline_user_args()
	folder=args[0] if not args.is_empty() else ProjectSettings.globalize_path("res://route-evidence")
	for arg in args:
		if arg.begins_with("--only="):only=arg.trim_prefix("--only=")
	if not only.is_empty() and not ["frontage","basement","gallery","kitchen","garage"].has(only):
		push_error("Unknown route scenario: "+only);quit(2);return
	DirAccess.make_dir_recursive_absolute(folder)
	save_images=args.has("--pictures") and DisplayServer.get_name()!="headless"
	Engine.physics_ticks_per_second=60
	root.size=Vector2i(1120,720)
	world=load("res://world.tscn").instantiate();world.auditing=true
	root.add_child(world)
	while not world.gi_ready:await process_frame
	await tick(30)
	check("normal_characterbody_physics_enabled",world.player is CharacterBody3D and world.auditing and not world.testing and not world.photo_mode)
	if not checks.normal_characterbody_physics_enabled:
		notes.append("Run without --verify / --capture / --review-motion.");persist(true);quit(2);return
	block_spec=JSON.parse_string(FileAccess.get_file_as_string("res://assets/buildings/street-block.json"))
	for route in world.specs.agasa.routes:route_map[str(route.name)]=route
	for path in ["world.gd","assets/street.glb","assets/buildings/agasa.glb","assets/buildings/agasa.json","assets/buildings/street-block.glb","assets/buildings/street-block.json","assets/buildings/mouri.glb","assets/buildings/mouri.json","assets/character-motion.json"]:
		hashes[path]=FileAccess.get_sha256("res://"+path)
	notes.append("Headless results establish actual controller movement/collision only. They do not establish rendered appearance, mobile performance, or release status.")
	notes.append("Outdoor scenario reset is explicitly listed. No player position is assigned inside walk/follow and no raycast substitutes for movement.")
	if only.is_empty() or only=="frontage":await test_frontage()
	await test_agasa()
	world.audit_input=Vector2.ZERO;Input.action_release("run")
	persist(true)
	var failed=0
	for key in checks:
		if not checks[key]:failed+=1
	print("CONAN_REFERENCE_ROUTES_DONE checks=",checks.size()," failures=",failed," segments=",routes.size()," output=",folder)
	world.queue_free();world=null
	for i in range(3):await process_frame
	quit(1 if failed else 0)
