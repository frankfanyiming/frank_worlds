extends SceneTree
## Real renderer footage. Scene setup places actors for a close inspection shot;
## every recorded walking/jumping movement then uses the game's normal physics.
## This is a visual asset review, not the no-teleport traversal test.

var world
var folder: String
var mode: String
var samples := []
var skeleton: Skeleton3D
var lighting_checks := []

func _initialize():call_deferred("run")

func frames(count: int):
 for index in range(count):
  await process_frame

func find_skeleton(node: Node) -> Skeleton3D:
 if node is Skeleton3D:return node
 for child in node.get_children():
  var found=find_skeleton(child)
  if found:return found
 return null

func array3(p: Vector3):return [p.x,p.y,p.z]

func take_sample():
 var sample={"time":world.time,"frog":array3(world.frog.position),"frog_animation":world.animator.current_animation,"panda":array3(world.panda_actor.global_position),"panda_animation":world.panda_animator.current_animation,"bones":{}}
 if skeleton:
  for index in range(skeleton.get_bone_count()):
   var name=skeleton.get_bone_name(index)
   if "foot" in name.to_lower() or "ankle" in name.to_lower():
    sample.bones[name]=array3(skeleton.global_transform*skeleton.get_bone_global_pose(index).origin)
 samples.append(sample)

func shot(name: String):
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png(folder.path_join(name+".png"))

func seconds(duration: float):
 var start=world.time
 while world.time-start<duration:
  await process_frame
  take_sample()

func run():
 var args=OS.get_cmdline_user_args()
 folder=args[0];mode=args[1] if args.size()>1 else "frog"
 DirAccess.make_dir_recursive_absolute(folder)
 root.size=Vector2i(1280,720)
 world=load("res://world.tscn").instantiate()
 world.save_path=folder.path_join("review-save-"+mode+".json")
 world.photo_directory=folder.path_join("review-photos")
 world.input_locked=true;world.auditing=true;world.panda_roam_enabled=false
 root.add_child(world)
 await frames(30)
 world.overlay.visible=false
 if mode=="frog":
  world._enter_home("frog")
  world.frog.position=Vector3(-16.55,.24,-9.55);world.frog.velocity=Vector3.ZERO
  world.manual_review_camera=true;world.camera.position=Vector3(-15.45,2.15,-7.65)
  world.camera.fov=82;world.camera.look_at(Vector3(-15.15,1.40,-9.55))
  skeleton=find_skeleton(world.actor)
  await seconds(.7)
  world.audit_input=Vector3(1,0,0)
  await seconds(.8);await shot("蛙-侧面迈步")
  await seconds(.65)
  world.audit_input=Vector3.ZERO
  await seconds(.45);await shot("蛙-侧面落脚")
  world.jump_buffer=.14
  await seconds(.12);await shot("蛙-蓄力")
  await seconds(.31);await shot("蛙-蹬地跃起")
  await seconds(.9)
  world.audit_input=Vector3(-1,0,0)
  await seconds(1.45)
  world.audit_input=Vector3.ZERO
  await seconds(.8);await shot("蛙-落地站稳")
 elif mode=="panda":
  world._enter_home("panda")
  world.frog.position=world.PANDA_ROOM_OFFSET+Vector3(0,.24,3.85)
  world.manual_review_camera=true;world.camera.position=world.PANDA_ROOM_OFFSET+Vector3(-3.2,1.7,3.1)
  world.camera.fov=56;world.camera.look_at(world.PANDA_ROOM_OFFSET+Vector3(-1.3,.8,.55))
  skeleton=find_skeleton(world.panda_actor)
  await seconds(.9);await shot("熊猫-侧面站姿")
  world.panda_roam_enabled=true;world.panda_wait=0.0
  await seconds(2.0);await shot("熊猫-迈步")
  await seconds(4.0);await shot("熊猫-转向")
  await seconds(5.0);await shot("熊猫-回到茶桌")
 else:
  for id in ["frog","panda"]:
   world.night=false
   world._enter_home(id)
   world.frog.position=Vector3(-16.3,.23,-10.05) if id=="frog" else world.PANDA_ROOM_OFFSET+Vector3(0,.22,1.17)
   world.mode=1
   await seconds(.6);await shot(id+"-玩家近景")
   world.mode=0
   await seconds(.6);await shot(id+"-房间全景")
   var gi_nodes=world.baked_homes[id].find_children("*","LightmapGI",true,false) if world.baked_homes.has(id) else []
   var check={"home":id,"baked_scene":world.baked_homes.has(id),"lightmaps":[]}
   for gi in gi_nodes:
    var day=gi.light_data.resource_path if gi.light_data else ""
    var dusk=str(gi.get_meta("dusk_data",""))
    check.lightmaps.append({"day":day,"dusk":dusk,"both_available":day!="" and dusk!="" and day!=dusk and ResourceLoader.exists(day) and ResourceLoader.exists(dusk)})
   world.night=true;world._apply_lighting();world.mode=1
   await seconds(.6);await shot(id+"-黄昏近景")
   for index in range(gi_nodes.size()):
    var gi=gi_nodes[index]
    check.lightmaps[index]["dusk_loaded"]=gi.light_data and gi.light_data.resource_path==str(gi.get_meta("dusk_data",""))
   lighting_checks.append(check)
   world._leave_home()
  FileAccess.open(folder.path_join("lighting-check.json"),FileAccess.WRITE).store_string(JSON.stringify(lighting_checks,"  "))
 FileAccess.open(folder.path_join(mode+"-motion.json"),FileAccess.WRITE).store_string(JSON.stringify({"real_godot_viewport":true,"staged_initial_camera_and_position":true,"movement":"world.gd normal CharacterBody3D physics","samples":samples},"  "))
 print("HOUSEHOLD_MOTION_CAPTURE ",folder," ",mode)
 world.queue_free();world=null
 await frames(4)
 quit()
