extends SceneTree
## Capture actual Compatibility production rooms; no lighting overrides / hidden walls.
var w
func _initialize():call_deferred("run")
func run():
	var folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	root.size=Vector2i(1440,900)
	w=load("res://world.tscn").instantiate();root.add_child(w);w.testing=true
	for i in range(45):await process_frame
	w.set_process(false);w.set_physics_process(false);w.avatar.visible=false
	for layer in w.find_children("*","CanvasLayer",true,false):layer.visible=false
	for a in w.actors:w.play(a.anim,"Idle");a.anim.advance(.3);a.anim.pause()
	var views=[
		{"id":"mouri-street","key":"mouri","p":[12,7.3,14],"t":[0,4.6,-4.0],"fov":58},
		{"id":"mouri-windows","key":"mouri","p":[3.5,3.1,9.5],"t":[-1.9,3.35,0],"fov":54},
		{"id":"mouri-night-reference","key":"mouri","p":[-7.4,3.1,7.5],"t":[-1.6,3.9,0],"fov":52},
		{"id":"mouri-sign-close","key":"mouri","p":[1.4,4.6,4.3],"t":[-1.8,4.9,.1],"fov":56},
		{"id":"mouri-poirot-close","key":"mouri","p":[1.3,1.7,2.2],"t":[-1.2,1.45,0],"fov":58},
		{"id":"mouri-office","key":"mouri","p":[.4,4.92,-.48],"t":[-1.7,4.12,-5.1],"fov":60},
		{"id":"poirot-tables","key":"mouri","p":[-1.65,1.50,-1.03],"t":[-.2,.73,-4.2],"fov":55},
		{"id":"agasa-whole-plan","key":"agasa","p":[4.8,2.0,5.9],"t":[-1.6,1.45,.2],"fov":60},
		{"id":"agasa-kitchen","key":"agasa","p":[-.3,1.65,2.32],"t":[-1.55,1.2,-.6],"fov":58},
		{"id":"agasa-beds","key":"agasa","p":[-3.5,1.8,3.45],"t":[-5.5,.87,-.1],"fov":59},
		{"id":"agasa-living","key":"agasa","p":[1.7,1.75,3.8],"t":[4.15,.85,.5],"fov":58},
		{"id":"agasa-gallery","key":"agasa","p":[3.7,4.63,-3.05],"t":[-2,.68,.4],"fov":66},
		{"id":"agasa-research","key":"agasa","p":[.8,-1.52,.12],"t":[-3.5,-1.97,2.55],"fov":64},
		{"id":"kudo-joinery","key":"kudo","p":[4.0,1.6,3.7],"t":[6.3,1.18,-.5],"fov":58},
		{"id":"kudo-dining","key":"kudo","p":[-3.1,1.7,8.15],"t":[-6.7,1.1,.2],"fov":59}]
	var report=[]
	for night in [false,true]:
		w.daytime=22 if night else 15.5;w.update_life(0)
		for v in views:
			if night and not str(v.id).begins_with("mouri") and v.id!="agasa-whole-plan":continue
			w.camera.position=w.world_point(v.key,v.p);w.camera.look_at(w.world_point(v.key,v.t));w.camera.fov=v.fov
			for i in range(12):await process_frame
			await RenderingServer.frame_post_draw
			var name=("night-" if night else "day-")+v.id+".png"
			root.get_texture().get_image().save_png(folder.path_join(name));print("REFERENCE_CAPTURE ",name)
			report.append({"file":name,"camera":v,"daytime":w.daytime,"sun":w.sun.light_energy,"ambient":w.env.ambient_light_energy,"production_lighting":true,"architecture_visible":true})
	var assets={}
	for name in ["agasa","mouri","mouri-details","kudo","kudo-details"]:
		assets[name]=FileAccess.get_sha256("res://assets/buildings/"+name+".glb")
	FileAccess.open(folder.path_join("capture-report.json"),FileAccess.WRITE).store_string(JSON.stringify({"views":report,"engine":Engine.get_version_info(),"renderer":RenderingServer.get_current_rendering_method(),"assets":assets},"  "))
	w.queue_free();await process_frame;quit()
