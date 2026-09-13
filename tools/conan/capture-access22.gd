extends SceneTree
var w
func _initialize():call_deferred("run")
func run():
 var folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder);root.size=Vector2i(1280,860)
 w=load("res://world.tscn").instantiate();w.testing=true;root.add_child(w)
 for i in range(60):await process_frame
 w.set_process(false);w.set_physics_process(false);w.avatar.visible=false
 for layer in w.find_children("*","CanvasLayer",true,false):layer.visible=false
 w.daytime=15.5;w.update_life(0)
 var views=[
 {"id":"garage-apron","key":"agasa","p":[14.7,2.9,-11.8],"t":[11.6,.45,-5.8]},
 {"id":"garage-workbench","key":"agasa","p":[12.0,1.8,-1.25],"t":[13.55,1.05,-3.55]},
 {"id":"research-desk","key":"agasa","p":[4.8,-1.50,-3.55],"t":[4.7,-2.1,-5.6]},
 {"id":"living-cabinet","key":"agasa","p":[2.6,1.8,2.3],"t":[4.42,.60,4.48]},
 {"id":"mouri-desktop","key":"mouri","p":[-.65,5.10,-.62],"t":[-1.5,4.25,-1.75]},
 {"id":"kudo-books","key":"kudo","p":[7.9,1.6,1.0],"t":[8.73,1.00,-.77]}]
 for v in views:
  w.camera.position=w.world_point(v.key,v.p);w.camera.look_at(w.world_point(v.key,v.t));w.camera.fov=58
  for i in range(12):await process_frame
  await RenderingServer.frame_post_draw;root.get_texture().get_image().save_png(folder.path_join(v.id+".png"));print("CAPTURE22 ",v.id)
 quit()
