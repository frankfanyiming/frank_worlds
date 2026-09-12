extends SceneTree
## Captures the actual production NPC and triggers its existing E interaction.
var world
var folder:String
var checks:Array=[]
func _initialize():call_deferred("run")
func frames(count:int):
 for i in count:await process_frame
func shot(name:String):
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png(folder.path_join(name+".png"))
func run():
 folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
 world=load("res://world.tscn").instantiate();world.auditing=true;world.manual_review_camera=true;root.add_child(world)
 world.testing=false;world.first_person=true;world.audit_input=Vector2.ZERO
 await frames(45)
 var actor:Dictionary={}
 for candidate in world.actors:
  if candidate.get("key","")=="agasa":actor=candidate;break
 if actor.is_empty():push_error("Production Agasa NPC missing");quit(2);return
 var npc:Node3D=actor.node;var origin=npc.global_position
 var front=npc.global_transform.basis.z.normalized();var side=npc.global_transform.basis.x.normalized()
 world.travel(origin+front*.95,.0);world.manual_review_camera=true;world.ui.visible=false;world.avatar.visible=false
 world.camera.position=origin+front*2.85+side*.58+Vector3.UP*1.04
 world.camera.look_at(origin+Vector3.UP*.81);world.camera.fov=43
 await frames(50)
 checks.append({"check":"production_idle","passed":actor.anim.current_animation.ends_with("Idle"),"clip":str(actor.anim.current_animation)})
 await shot("阿笠博士-实机站姿")
 world.update_nearby()
 checks.append({"check":"nearest_is_agasa","passed":world.nearest.get("key","")=="agasa"})
 var event=InputEventKey.new();event.keycode=KEY_E;event.pressed=true
 world._unhandled_input(event)
 await frames(24)
 checks.append({"check":"interaction_plays_talk","passed":actor.anim.current_animation.ends_with("Talk") and "新发明" in world.hint.text,"clip":str(actor.anim.current_animation)})
 await shot("阿笠博士-实机交谈")
 checks.append({"check":"npc_stays_at_authored_position","passed":npc.global_position.distance_to(origin)<.0001})
 var report={"engine":Engine.get_version_info().string,"renderer":"gl_compatibility","production_scene":"res://world.tscn","player_initial_pose_staged":true,"npc_transform_unchanged":true,"animation":"normal AnimationPlayer playback through production Idle and E interaction; no seek","checks":checks,"clips":actor.anim.get_animation_list(),"scope":"Authored NPC standing and talking; Agasa walking remains a Blender asset check, not a production NPC walk test."}
 FileAccess.open(folder.path_join("agasa-runtime-check.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
 print("AGASA_RUNTIME_COMPLETE ",JSON.stringify(checks))
 world.queue_free();world=null;await frames(4)
 quit(0 if checks.all(func(c):return c.passed) else 1)
