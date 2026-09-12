extends SceneTree
## Run with --fixed-fps 60 --disable-render-loop --write-movie <path>.
## Actual production NPC: normal Idle, then existing E -> Talk. No seek or replacement rig.
var world
var folder:String
var checks:Array=[]
var sampled:Array=[]
var actor:Dictionary
func _initialize():call_deferred("run")
func frames(count:int):
 for i in count:
  await process_frame
  RenderingServer.force_draw(false)
  if not actor.is_empty():sampled.append({"clip":str(actor.anim.current_animation),"time":actor.anim.current_animation_position})
func shot(name:String):
 # frames() explicitly renders each normal process frame, including in background.
 root.get_texture().get_image().save_png(folder.path_join(name+".png"))
func run():
 folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
 world=load("res://world.tscn").instantiate();world.auditing=true;world.manual_review_camera=true;root.add_child(world)
 world.testing=false;world.first_person=true;world.audit_input=Vector2.ZERO
 await frames(45)
 for candidate in world.actors:
  if candidate.get("key","")=="kogoro":actor=candidate;break
 if actor.is_empty():push_error("Production Kogoro NPC missing");quit(2);return
 var npc:Node3D=actor.node;var origin=npc.global_position
 var front=npc.global_transform.basis.z.normalized();var side=npc.global_transform.basis.x.normalized()
 world.travel(origin+front*.95,.0);world.manual_review_camera=true;world.ui.visible=false;world.avatar.visible=false
 world.camera.position=origin+front*1.15-side*.55+Vector3.UP*1.16
 world.camera.look_at(origin+Vector3.UP*1.12);world.camera.fov=64
 await frames(60)
 checks.append({"check":"production_idle","passed":actor.anim.current_animation.ends_with("Idle"),"clip":str(actor.anim.current_animation)})
 await shot("小五郎-正常站姿正侧面")
 world.camera.position=origin+front*.96+side*.78+Vector3.UP*1.16;world.camera.look_at(origin+Vector3.UP*1.12)
 await frames(55);await shot("小五郎-正常站姿另一侧")
 world.update_nearby()
 checks.append({"check":"nearest_is_kogoro","passed":world.nearest.get("key","")=="kogoro"})
 var event=InputEventKey.new();event.keycode=KEY_E;event.pressed=true;world._unhandled_input(event)
 await frames(50)
 checks.append({"check":"interaction_plays_talk","passed":actor.anim.current_animation.ends_with("Talk") and "仔细观察" in world.hint.text,"clip":str(actor.anim.current_animation)})
 await shot("小五郎-交谈另一侧")
 await frames(65)
 world.camera.position=origin+front*1.15-side*.55+Vector3.UP*1.16;world.camera.look_at(origin+Vector3.UP*1.12)
 await frames(45);await shot("小五郎-交谈正侧面");await frames(60)
 checks.append({"check":"npc_stays_at_authored_position","passed":npc.global_position.distance_to(origin)<.0001})
 var report={"engine":Engine.get_version_info().string,"renderer":"gl_compatibility","production_scene":"res://world.tscn","player_initial_pose_staged":true,"npc_transform_unchanged":true,"animation":"normal AnimationPlayer playback through production Idle and E interaction; no seek","checks":checks,"samples":sampled,"clips":actor.anim.get_animation_list(),"scope":"Actual authored Kogoro standing and E conversation; retained Read is reviewed separately in Blender, not claimed as a book interaction."}
 FileAccess.open(folder.path_join("kogoro-runtime-check.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
 print("KOGORO_RUNTIME_COMPLETE ",JSON.stringify(checks))
 world.queue_free();world=null;actor={};await frames(4);quit(0 if checks.all(func(c):return c.passed) else 1)
