extends SceneTree
var w
var f
var out=""
var checks={}
var observations={}
func check(id: String, value: bool):
 checks[id]=value;print("FRIEND_RUNTIME ",id," ",value)
func frames(n: int=12):
 for i in range(n):await physics_frame
func shot(name: String):
 await process_frame;await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png(out.path_join(name+".png"))
func action(id: String):
 w.friend_ui_action(id);await frames(2)
func walk(target: Vector3, limit: float=20.0):
 w.auditing=true;w.input_locked=false
 var query=PhysicsRayQueryParameters3D.create(target+Vector3.UP*1.8,target-Vector3.UP*2,w.frog.collision_mask,[w.frog.get_rid(),w.panda_body.get_rid()])
 var hit=w.get_world_3d().direct_space_state.intersect_ray(query)
 if not hit.is_empty():target.y=hit.position.y+.016
 var r=await w._walk_to(target,limit)
 print("FRIEND_TEST_WALK ",JSON.stringify(r))
 w.auditing=false;return r.reached
func wait_panda(limit: int=900):
 for i in range(limit):
  if w.panda_body.global_position.distance_to(w.frog.global_position)<1.9:return true
  await physics_frame
 return false
func _initialize():call_deferred("run")
func run():
 out=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(out)
 root.size=Vector2i(1280,900)
 var legacy={"clovers":57,"packed":true,"harvest_at":0.0,"photos":[{"file":"old-photo.png","place":"old","time":"2026"}],"camp_visits":4,"panda_visits":9}
 var sf=FileAccess.open(out.path_join("save.json"),FileAccess.WRITE);sf.store_string(JSON.stringify(legacy));sf.close()
 w=load("res://world.gd").new();w.save_path=out.path_join("save.json");w.photo_directory=out.path_join("photos");root.add_child(w)
 await frames(20);f=w.friend_life
 check("legacy_clovers_album_preserved",w.state.clovers==57 and w.state.photos.size()==1 and w.state.camp_visits==4)
 w._open_album();var album_box=w.album_panel.get_child(0)
 check("missing_legacy_photo_empty_album_keeps_record",w.state.photos.size()==1 and album_box.get_child(0).get_child(0).text.contains("0 张") and album_box.get_child(1).text.contains("还没有照片"))
 w._close_panel()
 w._enter_home("panda");await frames(20)
 check("walk_to_panda_tea",await walk(Vector3(100,.22,1.2)))
 w.nearest="panda_tea";w._interact();await action("sit");await frames(4)
 check("shared_tea_saved",f.save.shared_tea)
 w.tea_time=0;f.tea_pause=0;w.posing=0
 f.open_journal();await action("invite")
 check("invited_physics_actor",f.save.companion and w.panda_body.get_parent()==w and w.panda_body is CharacterBody3D)
 await walk(Vector3(100,.22,3.6));await wait_panda();await shot("01-panda-visit-follow")
 # Exercise both ordinary doorway transitions; only door handoffs change rooms.
 w._leave_home();await frames(15)
 check("outdoor_collision_layer",w.panda_body.collision_mask==1 and w.panda_body.collision_layer==1)
 var before=w.panda_body.global_position
 check("outdoor_walk",await walk(Vector3(27,.35,23),15))
 var caught=await wait_panda(700)
 check("outdoor_follows_by_collisions",caught and w.panda_body.global_position.distance_to(before)>1)
 observations.nav_points=f.following.graph.get_point_count();observations.outdoor_travel=f.following.travelled;observations.outdoor_start=[before.x,before.y,before.z];observations.outdoor_end=[w.panda_body.position.x,w.panda_body.position.y,w.panda_body.position.z];observations.outdoor_distance=w.panda_body.global_position.distance_to(w.frog.global_position)
 await shot("02-outdoor-follow")
 # Sample a fixed wall: companion must stop rather than move through furniture.
 w._enter_home("frog");await frames(20)
 var routes=[Vector3(-15.8,.20,-8.95),Vector3(-16.8,.20,-9.65),Vector3(-16.8,.20,-11.3),Vector3(-15.9,.20,-12.7),Vector3(-13.55,.20,-12.7),Vector3(-12.3,.20,-11.8)]
 for i in range(routes.size()):
  var reached=await walk(routes[i],16)
  check("frog_kitchen_route_"+str(i),reached)
  if not reached:break
 await wait_panda(1500)
 check("panda_reaches_kitchen_without_furniture_clip",f.near())
 w.nearest="friend_stove";w._interact();await action("recipe:rice")
 var token=f.ui_state("en").choices[0].id;await action(token);await action(token)
 check("double_input_does_not_skip_cooking_step",int(f.save.cooking.step)==1)
 var old_sequence=f.save.sequence;f._persist()
 var cooking_save=JSON.parse_string(FileAccess.get_file_as_string(w.save_path))
 check("unfinished_cooking_written_for_refresh",int(cooking_save.friend_life.cooking.step)==1 and cooking_save.clovers==57 and cooking_save.photos.size()==1)
 await shot("03-cooking-progress")
 w.queue_free();await frames(2)
 w=load("res://world.gd").new();w.save_path=out.path_join("save.json");w.photo_directory=out.path_join("photos");root.add_child(w);await frames(30);f=w.friend_life
 var recovered_json=JSON.parse_string(FileAccess.get_file_as_string(w.save_path))
 check("restored_position_replaces_door_checkpoint",w.vec(recovered_json.friend_life.checkpoint.frog).distance_to(w.frog.global_position)<.25)
 var first_reload_position=w.frog.global_position
 w.queue_free();await frames(2)
 w=load("res://world.gd").new();w.save_path=out.path_join("save.json");w.photo_directory=out.path_join("photos");root.add_child(w);await frames(30);f=w.friend_life
 check("consecutive_refresh_keeps_stove_position",w.frog.global_position.distance_to(first_reload_position)<.25)
 f.context_interact("friend_stove")
 check("refresh_resumes_exact_cooking_step",int(f.save.cooking.get("step",-1))==1 and w.active_home=="frog" and f.ui_state("en").title.contains("Step 2 of 3"))
 while not f.save.cooking.is_empty():await action(str(f.ui_state("en").choices[0].id))
 check("two_rice_servings_free",f.save.cooked.size()==2 and w.state.clovers==57)
 await action("gifts");await action("gift:food");await action("gift:food")
 check("food_gift_once_after_repeated_click",f.save.gifts.has("food") and f.save.cooked.size()==1)
 await action("gifts");await action("gift:tea_jar");await action("gifts");await action("gift:stone")
 check("three_gift_types_saved",f.save.gifts.size()==3 and f.save.keepsakes.tea_jar==0 and f.save.keepsakes.stone==0)
 await action("close");w._enter_home("panda");await frames(10)
 check("gifts_display_after_return",f.displays.visible and f.gifts_nodes.stone.visible and f.gifts_nodes.tea_jar.visible and f.gifts_nodes.food.visible)
 w.manual_review_camera=true;w.camera.position=Vector3(100.2,3.1,3.95);w.camera.look_at(Vector3(98.5,1.1,-.3));w.camera.fov=70
 await shot("04-gift-displays")
 w.manual_review_camera=false
 # A second recipe is independent and resumes through the same three operations.
 w._enter_home("frog");w.frog.position=Vector3(-12.3,.2,-11.8);w.panda_body.position=Vector3(-13.4,.2,-11.8);await frames(10)
 f.context_interact("friend_stove");await action("recipe:tea")
 for i in range(3):await action(str(f.ui_state("en").choices[0].id))
 check("second_recipe_two_tea_servings",f.save.cooked.size()==3 and f.save.cooked[1].recipe=="tea")
 await action("close");w._leave_home();await frames(5)
 # Camp fixture tests picnic, screenshot and persistence; locomotion is covered above.
 w.frog.position=Vector3(22,.35,8.6);w.panda_body.position=Vector3(23.2,.35,8.3);f.following.invalidate();await frames(30)
 f.context_interact("camp");await action("picnic")
 check("picnic_real_props_and_single_consumption",f.picnic_props.visible and f.save.stage=="picnic" and f.save.cooked.size()==2)
 await shot("05-picnic")
 await action("photo")
 for i in range(240):
  if not f.busy_photo:break
  await process_frame
 check("two_character_photo_and_memory",f.save.memories.size()==1 and w.state.photos.size()==2 and FileAccess.file_exists(w.photo_directory.path_join(str(f.save.memories[0].photo))))
 var photo_file=str(f.save.memories[0].photo) if not f.save.memories.is_empty() else ""
 observations.photo=photo_file
 await action("close")
 f._persist();var saved=JSON.parse_string(FileAccess.get_file_as_string(w.save_path));w.queue_free();await frames(2)
 w=load("res://world.gd").new();w.save_path=out.path_join("save.json");w.photo_directory=out.path_join("photos");root.add_child(w);await frames(40);f=w.friend_life
 check("fresh_world_reload_keeps_memories_gifts_photos",f.save.stage=="remembered" and f.save.memories.size()==1 and f.save.gifts.size()==3 and w.state.photos.size()==2 and w.state.clovers==57)
 check("reload_keeps_companion_context",f.save.companion and f.companion_context==w.active_home and w.panda_body.visible)
 for lang in ["zh-CN","zh-TW","ja","ko","en"]:
  f.open_journal();var state=f.ui_state(lang);check("localized_friend_card_"+lang,state.title!="" and state.body!="" and state.choices.size()<=3)
 var report={"checks":checks,"observations":observations,"real_engine":true,"notes":["Walking uses normal CharacterBody movement; doorway transitions use production handoff.","Separate kitchen tea and camp fixture positions are explicit to isolate recipe/photo tests, not claimed as complete map walking."]}
 var file=FileAccess.open(out.path_join("runtime.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report,"  "));print("FRIEND_RUNTIME_DONE ",JSON.stringify(report));quit(0 if not checks.values().has(false) else 1)
