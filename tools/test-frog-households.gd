extends SceneTree
## Run using the rendering Godot build, not --headless, to save real viewport images.
## Godot --path worlds/frog/source --script <absolute script> -- <output directory>
## Layout route coordinates are authored with the models. No player teleport is used
## to substitute for a failed route; only the game's ordinary doorway/tea transitions move it.

var world
var folder := ""
var checks := {}
var routes := []
var jumps := []
var walls := []
var cameras := []
var pictures := []
var panda_meshes := []
var floor_samples := []
var npc_contacts := []
var locale_frames := []
var panda_walk_samples := []
var notes := []

func _initialize():
 call_deferred("run")

func frames(count: int = 12):
 for i in range(count):await process_frame

func physics_frames(count: int = 12):
 for i in range(count):await physics_frame

func array3(p: Vector3) -> Array:
 return [p.x,p.y,p.z]

func point(layout: Dictionary, key: String, offset: Vector3 = Vector3.ZERO) -> Vector3:
 return offset+world.vec(layout[key])

func record(key: String, value: bool):
 checks[key]=value
 print("HOUSEHOLD_CHECK ",key," ",value)

func shot(name: String):
 await frames(8)
 await RenderingServer.frame_post_draw
 var image=root.get_texture().get_image()
 var result=image.save_png(folder.path_join(name+".png"))
 record("screenshot_"+name,result==OK and image.get_width()>0 and image.get_height()>0)
 pictures.append({"name":name,"file":name+".png","feet":array3(world.frog.position),"camera":array3(world.camera.position),"home":world.active_home,"mode":world.mode,"night":world.night})

func walk(label: String, target: Vector3, timeout: float = 22.0) -> bool:
 var result=await world._walk_to(target,timeout)
 result["label"]=label;result["home"]=world.active_home;result["target"]=array3(target)
 routes.append(result)
 print("HOUSEHOLD_WALK ",JSON.stringify(result))
 return bool(result.reached)

func player_capsule() -> CollisionShape3D:
 for child in world.frog.get_children():
  if child is CollisionShape3D and child.shape is CapsuleShape3D:return child
 return null

func walk_route(label: String, points: Array, offset: Vector3 = Vector3.ZERO, reverse: bool = false, sample_outdoor_floor: bool = false) -> bool:
 var ordered=points.duplicate(true)
 if reverse:ordered.reverse()
 var passed=not ordered.is_empty()
 for i in range(ordered.size()):
  var target=offset+world.vec(ordered[i])
  if sample_outdoor_floor:
   # Heights from the original tour can be stale when terrain changes. Sample
   # the actual layer-1 surface at the next waypoint without moving the player.
   var query=PhysicsRayQueryParameters3D.create(target+Vector3.UP*4.0,target-Vector3.UP*6.0,1,[world.frog.get_rid()])
   var hit=world.get_world_3d().direct_space_state.intersect_ray(query)
   var sample={"label":label+"_"+str(i),"authored_target":array3(target),"collision_mask":1,"found":not hit.is_empty()}
   if hit.is_empty() or hit.normal.y<.60:
    sample["error"]="No walkable outdoor surface at waypoint"
    floor_samples.append(sample);passed=false
    continue
   var capsule=player_capsule()
   var bottom=capsule.position.y-capsule.shape.height*.5
   target.y=hit.position.y-bottom+world.frog.safe_margin
   sample["surface"]=array3(hit.position);sample["normal"]=array3(hit.normal);sample["collider"]=str(hit.collider.get_path());sample["expected_root_y"]=target.y
   floor_samples.append(sample)
  var reached=await walk(label+"_"+str(i),target)
  passed=passed and reached
 return passed

func transition(label: String, target: Vector3, wanted_home: String, seconds: float = 8.0) -> bool:
 var start=world.frog.position
 var elapsed=0.0
 var reached=false
 while elapsed<seconds:
  if world.active_home==wanted_home:
   reached=true;break
  var direction=target-world.frog.position;direction.y=0
  world.audit_input=direction.normalized()
  await physics_frame
  elapsed+=1.0/60.0
 world.audit_input=Vector3.ZERO
 var result={"label":label,"reached":reached,"start":array3(start),"feet":array3(world.frog.position),"target":array3(target),"home":world.active_home,"elapsed":elapsed,"ordinary_door_transition":true}
 routes.append(result)
 print("HOUSEHOLD_TRANSITION ",JSON.stringify(result))
 await physics_frames(14)
 return reached

func key_interact(expected: String) -> bool:
 world._update_nearest()
 var matched=world.nearest==expected
 if not matched:return false
 world.input_locked=false
 var event=InputEventKey.new();event.keycode=KEY_E;event.physical_keycode=KEY_E;event.pressed=true
 world._unhandled_input(event)
 world.input_locked=true
 await physics_frames(2)
 return true

func jump_check(label: String, minimum_height: float = .65):
 world.audit_input=Vector3.ZERO
 await physics_frames(25)
 var initial=world.frog.position
 var expected_home=world.active_home
 var peak=initial.y
 var retained=true
 var landed=false
 var clips=[]
 world.jump_buffer=.14
 for i in range(110):
  await physics_frame
  var clip=str(world.animator.current_animation)
  if clips.is_empty() or clips.back()!=clip:clips.append(clip)
  peak=max(peak,world.frog.position.y)
  retained=retained and world.inside_home and world.active_home==expected_home and world.frog.collision_mask==2
  if i>35 and world.frog.is_on_floor() and abs(world.frog.position.y-initial.y)<.22:landed=true
 var result={"label":label,"start":array3(initial),"end":array3(world.frog.position),"height":peak-initial.y,"landed":landed,"stayed_in_same_home":retained,"animation_sequence":clips}
 jumps.append(result)
 record(label,retained and landed and peak-initial.y>minimum_height)
 record(label+"_visible_takeoff",clips.has("JumpStart") and clips.has("JumpAir") and clips.has("Land"))

func camera_check(label: String, layout: Dictionary, offset: Vector3 = Vector3.ZERO):
 world._camera_update(1)
 var p=world.camera.position-offset
 var bounds=layout.get("room_bounds",{})
 var inside=false
 if bounds.has("min") and bounds.has("max"):
  var lower=world.vec(bounds.min);var upper=world.vec(bounds.max)
  inside=p.x>lower.x and p.y>lower.y and p.z>lower.z and p.x<upper.x and p.y<upper.y and p.z<upper.z
 else:
  notes.append("Missing model-authored room_bounds for "+label+"; no invented bounds were treated as verified.")
 var observation={"label":label,"position":array3(p),"fov":world.camera.fov,"inside_authored_bounds":inside,"bounds":bounds,"mode":world.mode}
 if world.mode!=2:
  # The installed Tripo frog's authored standing height is 1.08 m. Keep this
  # measurement separate from its 1.02 m capsule and its .70 m eye camera.
  var height=1.08
  var viewport=world.camera.get_viewport().get_visible_rect()
  var safe=viewport.grow(-5.0)
  var landmarks={"feet":world.frog.global_position+Vector3.UP*.02,"center":world.frog.global_position+Vector3.UP*(height*.5),"head":world.frog.global_position+Vector3.UP*height}
  var projected={}
  var all_in_front=true
  for landmark in landmarks:
   var world_point=landmarks[landmark]
   var screen=world.camera.unproject_position(world_point)
   var behind=world.camera.is_position_behind(world_point)
   all_in_front=all_in_front and not behind
   projected[landmark]={"world":array3(world_point),"pixels":[screen.x,screen.y],"fraction":[(screen.x-viewport.position.x)/viewport.size.x,(screen.y-viewport.position.y)/viewport.size.y],"behind_camera":behind,"within_5px_margin":safe.has_point(screen)}
  var projected_height=abs(float(projected.feet.pixels[1])-float(projected.head.pixels[1]))
  observation["frog_projection"]={"standing_height_m":height,"viewport_pixels":[viewport.size.x,viewport.size.y],"landmarks":projected,"height_pixels":projected_height,"height_fraction":projected_height/viewport.size.y,"all_in_front":all_in_front}
  # Sample deliberate ground/loft compositions, not every stair frame: a brief
  # natural obstruction while moving should not hide a broken main composition.
  record(label+"_frog_in_frame",all_in_front and bool(projected.center.within_5px_margin) and bool(projected.head.within_5px_margin) and bool(projected.feet.within_5px_margin) and projected_height>0)
 cameras.append(observation)
 record(label,inside and world.inside_home and not world.stage.visible)

func ray_to_enclosure(from: Vector3, to: Vector3) -> Dictionary:
 var excluded=[world.frog.get_rid()]
 # A radial ray may begin inside the tea-table collider. Skip furniture by
 # identity so the measurement ends at the actual enclosing wall geometry.
 for i in range(48):
  var query=PhysicsRayQueryParameters3D.create(from,to,2,excluded)
  query.hit_from_inside=true
  var hit=world.get_world_3d().direct_space_state.intersect_ray(query)
  if hit.is_empty():return {}
  if "EnclosureWall" in str(hit.collider.get_path()):return hit
  excluded.append(hit.rid)
 return {}

func wall_check(label: String, layout: Dictionary, offset: Vector3 = Vector3.ZERO):
 if not layout.has("qa_wall_start") or not layout.has("qa_wall_direction"):
  notes.append("Missing model-authored wall probe for "+label)
  record(label,false);return
 if layout.has("qa_wall_route"):
  record(label+"_approach",await walk_route(label+"_approach",layout.qa_wall_route,offset))
 record(label+"_start",await walk(label+"_start",point(layout,"qa_wall_start",offset)))
 await physics_frames(20)
 var direction=world.vec(layout.qa_wall_direction).normalized();direction.y=0
 var start=world.frog.position
 var query=PhysicsRayQueryParameters3D.create(start+Vector3.UP*.56,start+Vector3.UP*.56+direction*12.0,2,[world.frog.get_rid()])
 var hit=world.get_world_3d().direct_space_state.intersect_ray(query)
 if hit.is_empty():
  record(label,false);walls.append({"label":label,"error":"No interior collision on wall probe"});return
 var collider=hit.collider
 var collider_path=str(collider.get_path())
 var true_wall="EnclosureWall" in collider_path
 var boundary=hit.position
 var approach_distance=(boundary-start).dot(direction)
 var reference_speed=float(world.locomotion.get("frog",{}).get("walk_speed",1.18))
 var duration=clamp((approach_distance+1.5)/reference_speed,1.0,8.0)
 var expected_home=world.active_home
 var contact_count=0;var contacts=[]
 world.audit_input=direction
 for i in range(int(duration*60)):
  await physics_frame
  for index in range(world.frog.get_slide_collision_count()):
   var contact=world.frog.get_slide_collision(index)
   if "EnclosureWall" in str(contact.get_collider().get_path()):
    contact_count+=1
    if contacts.size()<12:contacts.append({"position":array3(contact.get_position()),"normal":array3(contact.get_normal()),"feet":array3(world.frog.position)})
 world.audit_input=Vector3.ZERO
 await physics_frames(20)
 var progress=(world.frog.position-start).dot(direction)
 var center=offset+world.vec(layout.get("center",[0,0,0]))
 center.y=world.frog.position.y+.56
 var body_center=world.frog.position+Vector3.UP*.56
 var radial=(body_center-center).normalized()
 var final_hit=ray_to_enclosure(center,body_center+radial*12.0)
 var radial_evidence={"from":array3(center),"body_center":array3(body_center),"found":not final_hit.is_empty()}
 var inside_boundary=false
 if not final_hit.is_empty():
  var wall_distance=(final_hit.position-center).dot(radial)
  var body_distance=(body_center-center).dot(radial)
  var radius=player_capsule().shape.radius
  var clearance=wall_distance-body_distance
  inside_boundary=clearance>=radius-.01
  radial_evidence.merge({"wall":array3(final_hit.position),"normal":array3(final_hit.normal),"collider":str(final_hit.collider.get_path()),"wall_radius":wall_distance,"body_radius":body_distance,"clearance":clearance,"capsule_radius":radius,"inside_with_capsule_clearance":inside_boundary})
 var blocked=contact_count>0 and inside_boundary and world.inside_home and world.active_home==expected_home
 walls.append({"label":label,"start":array3(start),"end":array3(world.frog.position),"surface":array3(boundary),"collider":collider_path,"wall_hit":true_wall,"progress":progress,"initial_boundary_distance":approach_distance,"wall_contact_count":contact_count,"contacts":contacts,"final_radial_boundary":radial_evidence})
 record(label,true_wall and blocked)

func panda_body_check():
 var body=world.panda_home.get_node_or_null("PandaBody")
 if body==null:
  record("panda_body_blocks",false);notes.append("PandaBody collision is missing");return
 var npc_shape: CollisionShape3D
 for child in body.get_children():
  if child is CollisionShape3D and child.shape is CapsuleShape3D:npc_shape=child
 if npc_shape==null:
  record("panda_body_blocks",false);notes.append("PandaBody has no capsule");return
 var npc=world.panda_actor.global_position
 # The tea table's left edge is x=-.95. This model-authored corridor x=-1.35
 # leaves clearance for the frog, and reaches the panda from its front side.
 var approach=npc+Vector3(0,0,1.60)
 approach.y=float(world.panda_layout.get("floor_y",.20))
 record("panda_body_approach",await walk("panda_body_approach",approach))
 await physics_frames(20)
 var required_distance=player_capsule().shape.radius+npc_shape.shape.radius
 var minimum_distance=INF;var contacts=[]
 for i in range(100):
  var direction=npc-world.frog.position;direction.y=0
  world.audit_input=direction.normalized()
  await physics_frame
  var separation=Vector2(world.frog.position.x-npc.x,world.frog.position.z-npc.z).length()
  minimum_distance=min(minimum_distance,separation)
  for index in range(world.frog.get_slide_collision_count()):
   var contact=world.frog.get_slide_collision(index)
   if contact.get_collider()==body and contacts.size()<12:contacts.append({"position":array3(contact.get_position()),"normal":array3(contact.get_normal()),"feet":array3(world.frog.position)})
 world.audit_input=Vector3.ZERO
 await physics_frames(20)
 npc_contacts.append({"body":str(body.get_path()),"minimum_horizontal_distance":minimum_distance,"combined_capsule_radii":required_distance,"contact_samples":contacts,"feet":array3(world.frog.position),"npc":array3(npc)})
 record("panda_body_blocks",not contacts.is_empty() and minimum_distance>=required_distance-.01 and world.active_home=="panda")
 record("panda_body_retreat",await walk("panda_body_retreat",approach))

func panda_walk_check():
 world.panda_roam_enabled=true;world.panda_wait=0.0
 var started=false;var distance=0.0;var maximum_step=0.0;var walk_frames=0
 var start=world.panda_body.position
 var previous=start
 for i in range(1800):
  await physics_frame
  var current=world.panda_body.position
  var step=Vector2(current.x-previous.x,current.z-previous.z).length()
  distance+=step;maximum_step=max(maximum_step,step);previous=current
  if world.panda_route_index>=0:started=true
  if world.panda_animator.current_animation=="Walk":walk_frames+=1
  if i%15==0:panda_walk_samples.append({"frame":i,"position":array3(current),"animation":world.panda_animator.current_animation,"route_index":world.panda_route_index,"speed_scale":world.panda_animator.speed_scale})
  if started and world.panda_route_index<0:break
 world.panda_roam_enabled=false
 record("panda_walks_physical_loop",started and world.panda_route_index<0 and distance>4.0 and maximum_step<.06 and walk_frames>180)
 record("panda_returns_to_tea_seat",world.panda_body.position.distance_to(start)<.14)
 notes.append({"panda_walk_distance":distance,"maximum_single_physics_step":maximum_step,"walk_animation_frames":walk_frames,"start":array3(start),"end":array3(world.panda_body.position)})

func panda_live_translation_check():
 # Inspect actual UI writers across normal frames. Do not call _tr, refresh the
 # labels manually, or fetch expected strings from the implementation dictionary.
 var expected=[
  ["en","E  ·  Have tea with Panda","Panda’s tea room"],
  ["ja","E  ·  パンダとお茶を飲む","パンダの茶の間"],
  ["ko","E  ·  판다와 차 마시기","판다의 다실"],
  ["zh-TW","E  ·  和熊貓喝杯茶","熊貓的竹木茶室"]
 ]
 world.audit_input=Vector3.ZERO
 for row in expected:
  world.locale=row[0]
  await frames(2)
  var samples=[];var stable=true
  for i in range(8):
   await process_frame
   var prompt=world.prompt_label.text
   var zone=world.zone_label.text
   var correct=world.nearest=="panda_tea" and world.prompt_label.visible and prompt==row[1] and zone.begins_with(row[2]+"  ·  ")
   stable=stable and correct
   samples.append({"frame":i,"prompt":prompt,"zone":zone,"nearest":world.nearest,"correct":correct})
  locale_frames.append({"locale":row[0],"samples":samples,"stable":stable})
  record("panda_live_translation_"+str(row[0]),stable)
 world.locale="zh-CN"
 await frames(2)
 record("panda_translation_restores_chinese",world.prompt_label.text=="E  ·  和熊猫喝杯茶" and world.zone_label.text.begins_with("熊猫的竹木茶室  ·  "))

func inspect_panda(node: Node):
 if node is MeshInstance3D and node.mesh:
  var triangles=0;var textures=[]
  for surface in range(node.mesh.get_surface_count()):
   var arrays=node.mesh.surface_get_arrays(surface)
   var indices=arrays[Mesh.ARRAY_INDEX];var vertices=arrays[Mesh.ARRAY_VERTEX]
   triangles+=int(indices.size()/3) if indices!=null and indices.size()>0 else int(vertices.size()/3)
   var material=node.get_active_material(surface)
   if material is BaseMaterial3D and material.albedo_texture:
    textures.append({"width":material.albedo_texture.get_width(),"height":material.albedo_texture.get_height(),"path":material.albedo_texture.resource_path})
  panda_meshes.append({"name":str(node.name),"triangles":triangles,"albedo_textures":textures,"skin_binds":node.skin.get_bind_count() if node.skin else 0})
 for child in node.get_children():inspect_panda(child)

func verify_panda_source():
 inspect_panda(world.panda_actor)
 var triangles=0;var textured=false
 for mesh in panda_meshes:
  triangles+=int(mesh.triangles)
  for texture in mesh.albedo_textures:textured=textured or (int(texture.width)>=64 and int(texture.height)>=64)
 record("panda_has_detailed_textured_mesh",triangles>=1000 and textured)
 var provenance_path=ProjectSettings.globalize_path("res://../../../docs/panda-asset-source.json")
 var provenance={}
 if FileAccess.file_exists(provenance_path):
  var parsed=JSON.parse_string(FileAccess.get_file_as_string(provenance_path))
  if parsed is Dictionary:provenance=parsed
 var task=RegEx.new();task.compile("^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
 record("panda_tripo_provenance_recorded",str(provenance.get("source","")).to_lower()=="tripo" and task.search(str(provenance.get("task_id","")))!=null and str(provenance.get("runtime_asset",""))=="worlds/frog/source/assets/panda.glb")
 notes.append({"panda_provenance_file":provenance_path,"panda_provenance":provenance})

func interior_pass(id: String, layout: Dictionary, offset: Vector3 = Vector3.ZERO):
 var ground_route=layout.get("qa_ground_route",[])
 var stair_route=layout.get("stair_route",[])
 var loft_route=layout.get("qa_loft_route",[])
 record(id+"_layout_has_routes",not ground_route.is_empty() and not stair_route.is_empty() and not loft_route.is_empty())
 record(id+"_ground_route",await walk_route(id+"_ground",ground_route,offset))
 await physics_frames(25)
 camera_check(id+"_main_camera_inside",layout,offset)
 await shot("02-青蛙家主视角" if id=="frog" else "08-熊猫家主视角")
 var wheel=InputEventMouseButton.new();wheel.button_index=MOUSE_BUTTON_WHEEL_DOWN;wheel.pressed=true
 world._unhandled_input(wheel);world._camera_update(1)
 await frames(20)
 camera_check(id+"_wheel_camera_inside",layout,offset)
 await jump_check(id+"_ground_jump")
 record(id+"_stairs_up",await walk_route(id+"_stairs_up",stair_route,offset))
 record(id+"_loft_route",await walk_route(id+"_loft",loft_route,offset))
 await physics_frames(20)
 camera_check(id+"_loft_camera_inside",layout,offset)
 await shot("03-青蛙夹层睡铺" if id=="frog" else "09-熊猫竹床夹层")
 await jump_check(id+"_loft_jump_stays_inside",.35)
 world.mode=2;world._camera_update(1)
 record(id+"_frog_eye_tracks_character",world.camera.position.distance_to(world.frog.position+Vector3.UP*.70)<.015 and not world.actor.visible)
 camera_check(id+"_frog_eye_inside",layout,offset)
 await shot("04-青蛙家蛙眼视角" if id=="frog" else "10-熊猫家蛙眼视角")
 world.mode=0
 record(id+"_loft_return",await walk_route(id+"_loft_return",loft_route,offset,true))
 record(id+"_stairs_down",await walk_route(id+"_stairs_down",stair_route,offset,true))
 record(id+"_ground_return",await walk_route(id+"_ground_return",ground_route,offset,true))
 await wall_check(id+"_wall_blocks",layout,offset)
 if layout.has("qa_wall_route"):
  record(id+"_wall_return",await walk_route(id+"_wall_return",layout.qa_wall_route,offset,true))
 world._toggle_night()
 record(id+"_evening_is_indoor",world.inside_home and world.sun.light_energy==0 and world.home_light.visible and not world.environment.fog_enabled)
 await shot("05-青蛙家黄昏" if id=="frog" else "11-熊猫家黄昏")
 world._toggle_night()

func run():
 var args=OS.get_cmdline_user_args()
 folder=args[0] if args.size() else ProjectSettings.globalize_path("user://household-check")
 DirAccess.make_dir_recursive_absolute(folder)
 world=load("res://world.tscn").instantiate()
 # Set test-owned paths before _ready reads the existing save.
 world.save_path=folder.path_join("isolated-test-save-%d.json"%Time.get_ticks_usec())
 world.photo_directory=folder.path_join("isolated-test-photos")
 world.input_locked=true;world.auditing=true;world.audit_input=Vector3.ZERO
 # Isolate player route/body-contact checks; NPC's actual full walking loop is
 # verified independently below with normal physics and no position resets.
 world.panda_roam_enabled=false
 root.add_child(world)
 await physics_frames(75)
 world.overlay.visible=false
 var frog_skins=[]
 world._inspect_skin(world.actor,frog_skins)
 var frog_clips=world.animator.get_animation_list() if world.animator else []
 var frog_motion=true
 for name in ["Idle","Walk","JumpStart","JumpAir","Land","Sit"]:frog_motion=frog_motion and name in frog_clips
 record("frog_skin_and_movement_clips",not frog_skins.is_empty() and frog_motion)
 notes.append({"frog_skinned_meshes":frog_skins,"frog_animation_clips":frog_clips})
 record("spawn_outdoors",not world.inside_home and world.stage.visible and world.shell.visible and world.frog.collision_mask==1)
 await shot("01-原出生点与青蛙家外观")
 record("frog_enter_via_door",await transition("frog_enter",Vector3(-15,.2,-8.1),"frog"))
 record("frog_enclosed",world.active_home=="frog" and world.home_enclosure.visible and world.home_furnishings.visible and not world.panda_home.visible and not world.stage.visible and world.frog.collision_mask==2)
 camera_check("frog_entry_camera_inside",world.home_layout)
 await shot("01b-刚踏进青蛙家")
 await interior_pass("frog",world.home_layout)
 record("frog_exit_approach",await walk("frog_exit_approach",point(world.home_layout,"entry_spawn")))
 record("frog_exit_via_door",await transition("frog_exit",Vector3(-15,.2,float(world.home_layout.get("exit_z",-7.38))+.35),""))
 record("frog_exit_restores_world",not world.inside_home and world.stage.visible and not world.home_enclosure.visible and not world.home_furnishings.visible and world.environment.fog_enabled and world.frog.collision_mask==1)
 await shot("06-青蛙家出门恢复庭院")
 # Walk existing woodland paths to the south side of the panda house rather than
 # cutting through its exterior mesh or teleporting directly to its interaction.
 var outside=[]
 for i in range(1,min(10,world.data.route.size())):outside.append(world.data.route[i])
 outside.append([26,.35,22]);outside.append([26,.45,18])
 record("woodland_to_panda",await walk_route("woodland_to_panda",outside,Vector3.ZERO,false,true))
 await shot("07-沿小径来到熊猫家")
 record("panda_visit_interaction",await key_interact("panda_visit"))
 record("panda_entered_separate_room",world.active_home=="panda" and world.inside_home and world.panda_home.visible and not world.home_enclosure.visible and not world.stage.visible and world.frog.collision_mask==2)
 camera_check("panda_entry_camera_inside",world.panda_layout,world.PANDA_ROOM_OFFSET)
 await shot("07b-刚踏进熊猫家")
 verify_panda_source()
 await interior_pass("panda",world.panda_layout,world.PANDA_ROOM_OFFSET)
 await panda_body_check()
 var tea=world.PANDA_ROOM_OFFSET+world.vec(world.panda_layout.get("tea_guest_position",[0,.2,1.35]))
 record("panda_tea_approach",await walk("panda_tea_approach",tea))
 await panda_live_translation_check()
 record("panda_tea_interaction",await key_interact("panda_tea"))
 await physics_frames(20)
 record("panda_tea_pose",world.active_home=="panda" and world.tea_time>0 and world.posing>0 and world.animator!=null and world.animator.current_animation=="Sit")
 world.overlay.visible=true
 await shot("12-和熊猫喝茶")
 world.overlay.visible=false
 await physics_frames(450)
 record("panda_exit_approach",await walk("panda_exit_approach",point(world.panda_layout,"entry_spawn",world.PANDA_ROOM_OFFSET)))
 await panda_walk_check()
 record("panda_exit_via_door",await transition("panda_exit",world.PANDA_ROOM_OFFSET+Vector3(0,.2,float(world.panda_layout.get("exit_z",4.68))+.35),""))
 record("panda_exit_restores_world",not world.inside_home and world.stage.visible and world.panda_exterior.visible and not world.panda_home.visible and world.environment.fog_enabled and world.frog.collision_mask==1)
 await shot("13-熊猫家出门恢复森林")
 var failures=[]
 for key in checks:
  if not checks[key]:failures.append(key)
 var report={"checks":checks,"failed":failures,"routes":routes,"jumps":jumps,"walls":walls,"cameras":cameras,"screenshots":pictures,"panda_meshes":panda_meshes,"outdoor_floor_samples":floor_samples,"npc_contacts":npc_contacts,"panda_walk_samples":panda_walk_samples,"locale_frames":locale_frames,"notes":notes,"save_path":world.save_path,"real_runtime":true,"player_teleports_by_test":0}
 FileAccess.open(folder.path_join("households-check.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
 print("HOUSEHOLDS_TEST ",JSON.stringify({"passed":failures.is_empty(),"checks":checks.size(),"failed":failures,"report":folder.path_join("households-check.json")}))
 quit(0 if failures.is_empty() else 1)
