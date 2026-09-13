extends SceneTree
var w
var out=""
var results=[]
var max_gap=0.0
var slow_streak=0.0
var worst_streak=0.0
var previous=Vector3.ZERO
func _process(delta):
 if not w or not w.ready_world or not w.friend_life.save.companion:return false
 var gap=w.frog.position.distance_to(w.panda_body.position)
 max_gap=max(max_gap,gap)
 var moved=w.panda_body.position.distance_to(previous);previous=w.panda_body.position
 slow_streak=slow_streak+delta if gap>2.2 and moved<.02*delta and w.frog.velocity.length()>.3 else 0.0
 worst_streak=max(worst_streak,slow_streak)
 return false
var checks={}
func _initialize():call_deferred("run")
func frames(n):
 for i in range(n):await physics_frame
func go(target: Vector3, label: String):
 var f=w.friend_life
 var graph=f.following.graph
 var path=graph.get_point_path(graph.get_closest_point(w.frog.position),graph.get_closest_point(target))
 if path.is_empty():checks[label]=false;return
 var okay=true
 w.auditing=true;w.input_locked=false
 for i in range(1,path.size()):
  var result=await w._walk_to(path[i],5)
  if not result.reached:
   results.append({"label":label,"point":i,"result":result});okay=false;break

 w.audit_input=Vector3.ZERO;w.auditing=false
 var gap=100.0
 for t in range(600):
  gap=w.panda_body.position.distance_to(w.frog.position)
  if gap<2.2:break
  await physics_frame
 checks[label]=okay and gap<2.2
 results.append({"label":label,"path_points":path.size(),"walk_complete":okay,"panda_gap":gap,"frog":[w.frog.position.x,w.frog.position.y,w.frog.position.z],"panda":[w.panda_body.position.x,w.panda_body.position.y,w.panda_body.position.z]})
 print("FRIEND_ROUTE ",JSON.stringify(results[-1]))
func run():
 out=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(out);root.size=Vector2i(1280,900)
 w=load("res://world.gd").new();w.save_path=out.path_join("route-save.json");w.photo_directory=out.path_join("photos");root.add_child(w);await frames(15)
 # Set up one outdoor invitation fixture, then all route movement is controller-driven.
 w.friend_life.save.companion=true;w.friend_life.save.stage="outing";w.friend_life._attach()
 w.frog.position=Vector3(26,1.1,20.7);w.panda_body.position=Vector3(26.9,1.1,19.3);w.panda_body.collision_mask=1;w.panda_body.collision_layer=1
 w.friend_life.following.invalidate();await frames(30)
 await go(Vector3(27,.4,25.5),"past_old_navigation_boundary")
 Input.action_press("run")
 await go(Vector3(24,.2,5),"panda_house_to_camp")
 Input.action_release("run")
 await go(Vector3(19,.4,-9),"camp_to_east_bridge")
 await go(Vector3(11,.4,-9),"across_bridge")
 await go(Vector3(-15,.3,-6.3),"bridge_to_frog_home")
 if DisplayServer.get_name()!="headless":
  await RenderingServer.frame_post_draw;root.get_texture().get_image().save_png(out.path_join("walking-home-together.png"))
 checks["no_wait_for_follower_in_route"]=worst_streak<2.0
 var report={"max_gap_m":max_gap,"worst_stopped_while_frog_moves_s":worst_streak,"checks":checks,"routes":results,"real_controller":true,"panda_travelled":w.friend_life.following.travelled,"panda_collision_frames":w.friend_life.following.collision_frames,"notes":"Test drives the frog along paths sampled from static geometry; Panda follows actual frog breadcrumbs and still uses move_and_slide. No waiting inserted along the route. Includes sprint and an excursion past the former navigation boundary. No route teleport or collider disable."}
 var f=FileAccess.open(out.path_join("route.json"),FileAccess.WRITE);f.store_string(JSON.stringify(report,"  "));f.close();print("FRIEND_ROUTE_DONE ",JSON.stringify(report))
 w.queue_free();w=null
 await frames(3)
 quit(0 if not checks.values().has(false) else 1)
