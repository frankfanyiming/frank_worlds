extends SceneTree
## Actual engine frames at mobile CSS sizes plus analog movement/view checks.
var world
var folder:String
var is_frog:bool
var records=[]
func _initialize():call_deferred("run")
func frames(count:int):
	for i in range(count):await process_frame
func seconds(duration:float):
	var start=Time.get_ticks_msec()
	while Time.get_ticks_msec()-start<duration*1000:await process_frame
func shot(name:String):
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(folder.path_join(name+".png"))
func run():
	var args=OS.get_cmdline_user_args();folder=args[0];is_frog=args[1]=="frog"
	DirAccess.make_dir_recursive_absolute(folder)
	root.size=Vector2i(390,844);root.content_scale_size=root.size
	world=load("res://world.tscn").instantiate()
	if is_frog:
		world.save_path=folder.path_join("test-save.json");world.photo_directory=folder.path_join("photos");world.panda_roam_enabled=false
	root.add_child(world);await frames(40)
	for dimensions in [Vector2i(390,844),Vector2i(844,390),Vector2i(360,780)]:
		root.size=dimensions;root.content_scale_size=dimensions
		world._mobile_layout(Vector2(dimensions));await frames(10)
		await shot(("frog" if is_frog else "conan")+"-%dx%d"%[dimensions.x,dimensions.y])
		var panel=world.overlay.get_node("MainInfo") if is_frog else world.ui.get_node("MainInfo")
		var rect=panel.get_global_rect()
		records.append({"case":"HUD","size":[dimensions.x,dimensions.y],"main_fits":not panel.visible or (rect.position.x>=0 and rect.end.x<=dimensions.x+1),"panel_rect":[rect.position.x,rect.position.y,rect.size.x,rect.size.y]})
		if is_frog:
			world._show_bag();await frames(10);await shot("frog-bag-%dx%d"%[dimensions.x,dimensions.y]);world._close_panel()
	var actor=world.frog if is_frog else world.player
	var before=actor.position
	Input.action_press("forward",.65);await seconds(.75);Input.action_release("forward");await seconds(.25)
	var moved=Vector2(actor.position.x-before.x,actor.position.z-before.z).length()
	var yaw=world.yaw
	world._touch_look(Vector2(50,20));await frames(4)
	records.append({"case":"analog-and-view","moved":moved,"walks":moved>.1,"view_changed":abs(world.yaw-yaw)>.01,"input_released":not Input.is_action_pressed("forward")})
	if is_frog:
		world._enter_home("frog");await frames(12);await shot("frog-mobile-indoor")
	else:
		world.travel(world.world_point("mouri",world.specs.mouri.rooms[0].p)+Vector3.UP*.15);await frames(12);await shot("conan-mobile-indoor")
	FileAccess.open(folder.path_join("mobile-engine-check.json"),FileAccess.WRITE).store_string(JSON.stringify(records,"  "))
	print("MOBILE_ENGINE_CHECK ",JSON.stringify(records))
	world.queue_free();world=null;await frames(4);quit()
