extends SceneTree
## Production Compatibility screenshots. Does not modify scene lighting or materials.
## Run with: Godot --path worlds/conan/web-project --script <absolute script> -- <output folder>
var w
func _initialize():call_deferred("run")
func run():
	var folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	root.size=Vector2i(1280,800)
	w=load("res://world.tscn").instantiate();root.add_child(w);w.testing=true
	for i in range(35):await process_frame
	w.set_process(false);w.set_physics_process(false);w.ui.visible=false;w.avatar.visible=false
	for layer in w.find_children("*","CanvasLayer",true,false):layer.visible=false
	for a in w.actors:
		w.play(a.anim,"Idle");a.anim.advance(.3);a.anim.pause()
	var views=[{"name":"office","key":"mouri","p":[.4,4.92,-.48],"t":[-1.7,4.12,-5.1]}, {"name":"kogoro","key":"mouri","p":[-.75,4.8,-.1],"t":[-2.7,4.4,-1.2]}, {"name":"kitchen","key":"agasa","p":[4.8,2.0,5.9],"t":[-1.6,1.45,.2]}, {"name":"street","key":"mouri","p":[12,8,14],"t":[0,4,-1]}]
	for view in w.inspection_views:
		if "工藤" in view.name or "实验" in view.name:views.append({"name":view.name,"p_world":view.p,"t_world":view.target})
	var report=[]
	for night in [false,true]:
		w.daytime=22 if night else 15.5;w.update_life(0)
		for v in views:
			w.camera.position=v.p_world if v.has("p_world") else w.world_point(v.key,v.p);w.camera.look_at(v.t_world if v.has("t_world") else w.world_point(v.key,v.t));w.camera.fov=60
			for i in range(10):await process_frame
			await RenderingServer.frame_post_draw
			var name=("night-" if night else "day-")+v.name+".png";root.get_texture().get_image().save_png(folder.path_join(name));report.append({"file":name,"sun":w.sun.light_energy,"ambient":w.env.ambient_light_energy,"saturation":w.env.adjustment_saturation})
	FileAccess.open(folder.path_join("report.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	w.queue_free();await process_frame;quit()
