extends SceneTree
func _initialize():call_deferred("run")
func run():
	var folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	root.size=Vector2i(1280,800)
	var world=load("res://world.tscn").instantiate();root.add_child(world);world.testing=true
	for i in range(35):await process_frame
	world.set_process(false);world.ui.visible=false;world.avatar.visible=false
	for layer in world.find_children("*","CanvasLayer",true,false):layer.visible=false
	var report=[]
	for pair in [[.82,.55],[.5,.38],[.32,.32]]:
		world.sun.light_energy=pair[0];world.env.ambient_light_energy=pair[1]
		for view in world.specs.agasa.views:
			if not ("双圆弧" in view.name or "中央环形" in view.name):continue
			world.camera.position=world.world_point("agasa",view.p);world.camera.look_at(world.world_point("agasa",view.target));world.camera.fov=65
			for i in range(12):await process_frame
			await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png(folder.path_join(str(view.name)+"-"+str(pair[0])+".png"))
	for n in world.find_children("*","MeshInstance3D",true,false):
		for i in n.mesh.get_surface_count():
			var m=n.get_active_material(i)
			if m and "warm ivory" in m.resource_name:report.append({"name":m.resource_name,"color":str(m.albedo_color),"emission":m.emission_enabled})
	FileAccess.open(folder.path_join("materials.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	quit()
