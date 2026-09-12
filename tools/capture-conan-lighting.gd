extends SceneTree
## Captures the real Compatibility renderer at repeatable interior viewpoints.
var world
func _initialize():call_deferred("run")
func run():
	var folder=OS.get_cmdline_user_args()[0]
	DirAccess.make_dir_recursive_absolute(folder)
	root.size=Vector2i(1280,800)
	world=load("res://world.tscn").instantiate();root.add_child(world)
	world.testing=true
	for i in range(40):await process_frame
	world.ui.visible=false;world.avatar.visible=false
	for layer in world.find_children("*","CanvasLayer",true,false):layer.visible=false
	var report=[]
	for key in ["mouri","kudo","agasa"]:
		for view in world.specs[key].get("views",[]):
			if "外" in str(view.name) or "立面" in str(view.name) or "卧室" in str(view.name):continue
			world.player.position=world.world_point(key,view.target)
			world.camera.position=world.world_point(key,view.p)
			world.camera.look_at(world.world_point(key,view.target));world.camera.fov=70
			for hour in [15.5,21.0]:
				world.daytime=hour
				for i in range(20):await process_frame
				await RenderingServer.frame_post_draw
				var file=key+"-"+str(view.name)+("-day" if hour<18 else "-night")+".png"
				root.get_texture().get_image().save_png(folder.path_join(file))
				report.append({"file":file,"hour":hour,"exposure":world.env.tonemap_exposure,"ambient":world.env.ambient_light_energy})
	FileAccess.open(folder.path_join("capture.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	for view in world.inspection_views:
		if not ("商铺" in view.name or "寿司" in view.name or "街区正面" in view.name):continue
		world.camera.position=view.p;world.camera.look_at(view.target);world.camera.fov=58;world.daytime=15.5
		for i in range(20):await process_frame
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(folder.path_join(view.name+".png"))
	print("CONAN_LIGHTING_CAPTURE ",folder)
	world.queue_free();world=null
	for i in range(4):await process_frame
	quit()
