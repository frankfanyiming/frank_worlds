extends SceneTree
## Starts the production world and drives its normal CharacterBody3D controller.
## No AnimationPlayer.seek/advance, manual move_and_slide, or scripted translation.
## A visible removable barrier is added only for the final collision regression.
var world
var folder:String
var samples:Array=[]
var checks:Array=[]
var feet:Dictionary={"Left":[],"Right":[]}
var skeleton:Skeleton3D
var phase="settle"
var previous=Vector3.ZERO
var wall:StaticBody3D
var before_wall=Vector3.ZERO
var time=0.0
var shader_report:Array=[]

func _initialize():call_deferred("run")
func array3(v:Vector3)->Array:return [v.x,v.y,v.z]
func find_skeleton(n:Node)->Skeleton3D:
 if n is Skeleton3D:return n
 for child in n.get_children():
  var found=find_skeleton(child)
  if found:return found
 return null
func bind_bone(skin:Skin,index:int)->int:
 var name=skin.get_bind_name(index)
 return skeleton.find_bone(name) if name!="" else skin.get_bind_bone(index)
func gather_mesh(n:Node):
 if n is MeshInstance3D and n.mesh and n.skin:
  for surf in n.mesh.get_surface_count():
   var mat=n.get_active_material(surf)
   if mat is StandardMaterial3D:shader_report.append({"material":mat.resource_name,"albedo":str(mat.albedo_color),"texture":mat.albedo_texture.resource_path if mat.albedo_texture else "","normal_scale":mat.normal_scale})
   var arrays=n.mesh.surface_get_arrays(surf)
   var vertices=arrays[Mesh.ARRAY_VERTEX];var bones=arrays[Mesh.ARRAY_BONES];var weights=arrays[Mesh.ARRAY_WEIGHTS]
   if bones==null or weights==null:continue
   var stride=int(bones.size()/vertices.size())
   for i in vertices.size():
    if vertices[i].y>.086*1.05:continue
    for influence in stride:
     if weights[i*stride+influence]<.999:continue
     var binding=int(bones[i*stride+influence]);var bone_index=bind_bone(n.skin,binding)
     if bone_index<0:continue
     var name=skeleton.get_bone_name(bone_index)
     for side in ["Left","Right"]:
      if name==side+"Foot":feet[side].append({"point":vertices[i],"bone":bone_index,"bind":n.skin.get_bind_pose(binding)})
 for child in n.get_children():gather_mesh(child)
func sample():
 var position:Vector3=world.player.global_position
 var delta=1.0/Engine.physics_ticks_per_second
 var speed=Vector2(position.x-previous.x,position.z-previous.z).length()/delta
 previous=position;time+=delta
 var row={"t":time,"phase":phase,"position":array3(position),"velocity":array3(world.player.velocity),"actual_speed":speed,"animation":str(world.avatar_anim.current_animation),"animation_time":world.avatar_anim.current_animation_position,"animation_speed":world.avatar_anim.speed_scale,"grounded":world.player.is_on_floor(),"yaw":world.avatar.rotation.y,"feet":{}}
 for side in feet:
  var bottom=1000.0;var center=Vector3.ZERO
  for point in feet[side]:
   var p:Vector3=skeleton.global_transform*skeleton.get_bone_global_pose(point.bone)*point.bind*point.point
   bottom=min(bottom,p.y);center+=p
  if not feet[side].is_empty():center/=feet[side].size()
  row.feet[side]={"sole_y":bottom,"center":array3(center),"vertex_count":feet[side].size()}
 samples.append(row)
func follow_camera():
 var center:Vector3=world.player.position+Vector3(0,.55,0)
 world.camera.position=world.player.position+Vector3(.75,.85,1.95)
 world.camera.fov=42;world.camera.look_at(center)
func seconds(duration:float):
 for index in int(round(duration*Engine.physics_ticks_per_second)):
  await physics_frame
  await process_frame
  follow_camera();sample()
func shot(name:String):
 if OS.get_cmdline_user_args().has("--no-images"):return
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png(folder.path_join(name+".png"))
func barrier():
 wall=StaticBody3D.new();wall.name="AuditOnlyCollisionBarrier";world.add_child(wall)
 wall.position=world.player.position+Vector3(0,.65,1.3)
 var cs=CollisionShape3D.new();var box=BoxShape3D.new();box.size=Vector3(2.2,1.3,.16);cs.shape=box;wall.add_child(cs)
 var mesh=MeshInstance3D.new();var bm=BoxMesh.new();bm.size=box.size;mesh.mesh=bm;wall.add_child(mesh)
 var mat=StandardMaterial3D.new();mat.albedo_color=Color(.52,.36,.18);mat.roughness=.85;mesh.material_override=mat
func run():
 folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
 # Keep the project viewport size: MovieMaker fixes its AVI header before _initialize.
 # Changing root.size here produces JPEG frames of a different size than that header.
 world=load("res://world.tscn").instantiate();world.auditing=true;world.audit_input=Vector2.ZERO;world.manual_review_camera=true;root.add_child(world)
 world.testing=false;world.first_person=false
 for i in range(45):await process_frame
 world.ui.visible=false
 world.travel(Vector3(16.8,.22,4),0.0);world.manual_review_camera=true;world.avatar.rotation.y=0
 skeleton=find_skeleton(world.avatar);gather_mesh(world.avatar)
 checks.append({"check":"real_mesh_feet_found","passed":feet.Left.size()>20 and feet.Right.size()>20,"left":feet.Left.size(),"right":feet.Right.size()})
 checks.append({"check":"normal_physics_enabled","passed":not world.testing and world.auditing and not world.photo_mode})
 previous=world.player.position;await seconds(.6);await shot("柯南-站稳正侧面")
 if OS.get_cmdline_user_args().has("--still"):
  print("CONAN_MOTION_STILL ",folder);world.queue_free();world=null
  for i in range(4):await process_frame
  quit();return
 phase="walk_forward";world.audit_input=Vector2(0,1)
 await seconds(.8);await shot("柯南-正常迈步")
 await seconds(1.1)
 phase="run_forward";Input.action_press("run")
 await seconds(.8);await shot("柯南-正常跑步")
 await seconds(.8);Input.action_release("run")
 phase="turn_back";world.audit_input=Vector2(0,-1)
 await seconds(.6);await shot("柯南-转身")
 await seconds(1.8)
 phase="stop";world.audit_input=Vector2.ZERO
 await seconds(.7);await shot("柯南-停步站稳")
 checks.append({"check":"idle_after_stopping","passed":world.avatar_anim.current_animation.ends_with("Idle") and Vector2(world.player.velocity.x,world.player.velocity.z).length()<.005})
 barrier();before_wall=world.player.position;phase="wall_contact";world.audit_input=Vector2(0,1)
 await seconds(2.8);await shot("柯南-碰撞后停止迈步")
 var final_speed=float(samples[-1].actual_speed)
 checks.append({"check":"wall_blocks_normal_controller","passed":world.player.position.z<wall.position.z-.25 and final_speed<.005,"player":array3(world.player.position),"barrier":array3(wall.position),"actual_speed":final_speed})
 checks.append({"check":"wall_contact_switches_to_idle","passed":world.avatar_anim.current_animation.ends_with("Idle"),"clip":str(world.avatar_anim.current_animation)})
 world.audit_input=Vector2.ZERO
 var report={"real_godot_viewport":true,"engine":Engine.get_version_info().string,"renderer":"gl_compatibility","initial_pose_staged":true,"controller":"world.gd normal _physics_process / CharacterBody3D","animation_control":"production play() and speed matching, no seek or forced phase","wall_fixture":"Visible audit-only removable StaticBody3D barrier; does not alter production source.","character_motion":world.character_motion,"materials":shader_report,"checks":checks,"samples":samples}
 FileAccess.open(folder.path_join("conan-motion-v2.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
 print("CONAN_MOTION_V2_COMPLETE ",JSON.stringify(checks))
 world.queue_free();world=null
 for i in range(4):await process_frame
 quit(0 if checks.all(func(c):return c.passed) else 1)
