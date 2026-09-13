# SPDX-FileCopyrightText: 2026 Frank (frankfanyiming) and contributors
# SPDX-License-Identifier: MIT
# XLands / xlands-frankfym001 — https://github.com/frankfanyiming/frank_worlds
extends RefCounted
## A ground graph sampled from the current room's actual static collision. The
## actor still uses move_and_slide; a graph path never writes its world position.
var world
var graph := AStar3D.new()
var cells := {}
var bounds := Rect2()
var spacing := .56
var context := "unbuilt"
var path := PackedVector3Array()
var repath := 0.0
var blocked := 0.0
var last_goal := Vector3.INF
var travelled := 0.0
var stopped_frames := 0
var collision_frames := 0
var samples := 0
var breadcrumbs := PackedVector3Array()
var last_breadcrumb := Vector3.INF
var catchup_speed := 0.0
var recovery_count := 0

func _init(owner):world=owner

func invalidate():
 context="unbuilt";path.clear();last_goal=Vector3.INF;repath=0;breadcrumbs.clear();last_breadcrumb=Vector3.INF;blocked=0;catchup_speed=0

func _floor_point(x: float, z: float, mask: int) -> Vector3:
 var space=world.get_world_3d().direct_space_state
 var exclusions=[world.frog.get_rid(),world.panda_body.get_rid()]
 var q=PhysicsRayQueryParameters3D.create(Vector3(x,2.45,z),Vector3(x,-1.5,z),mask,exclusions)
 var hit=space.intersect_ray(q)
 if hit.is_empty() or hit.normal.y<.70:return Vector3.INF
 var p: Vector3=hit.position+Vector3.UP*.016
 if p.y>1.65:return Vector3.INF # Ground-floor excursions, never across a mezzanine.
 var shape=CapsuleShape3D.new();shape.radius=.405;shape.height=1.20
 var sq=PhysicsShapeQueryParameters3D.new();sq.shape=shape;sq.collision_mask=mask;sq.exclude=exclusions
 sq.transform=Transform3D(Basis.IDENTITY,p+Vector3.UP*.625)
 if not space.intersect_shape(sq,1).is_empty():return Vector3.INF
 return p

func build():
 context=world.active_home;graph.clear();cells.clear()
 var mask=2 if context!="" else 1
 if context=="frog":bounds=Rect2(-19.9,-16.5,9.8,9.4);spacing=.38
 elif context=="panda":bounds=Rect2(95.2,-4.8,9.6,9.6);spacing=.38
 else:bounds=Rect2(-37,-33,74,68);spacing=.72
 var columns=int(ceil(bounds.size.x/spacing));var rows=int(ceil(bounds.size.y/spacing))
 var index=0
 for z in range(rows+1):
  for x in range(columns+1):
   var p=_floor_point(bounds.position.x+x*spacing,bounds.position.y+z*spacing,mask)
   if p==Vector3.INF:continue
   cells[Vector2i(x,z)]=index;graph.add_point(index,p);index+=1
 for cell in cells:
  for shift in [Vector2i(1,0),Vector2i(0,1),Vector2i(1,1),Vector2i(-1,1)]:
   var other=cell+shift
   if not cells.has(other):continue
   if shift.x!=0 and shift.y!=0 and (not cells.has(cell+Vector2i(shift.x,0)) or not cells.has(cell+Vector2i(0,shift.y))):continue
   var a=graph.get_point_position(cells[cell]);var b=graph.get_point_position(cells[other])
   if _clear_segment(a,b,mask):graph.connect_points(cells[cell],cells[other])
 print("FRIEND_NAV ",context," points=",graph.get_point_count())

func _flat_distance(a: Vector3, b: Vector3) -> float:
 return Vector2(a.x-b.x,a.z-b.z).length()

func _clear_segment(a: Vector3, b: Vector3, mask: int) -> bool:
 # Test the full panda footprint against the actual floor/obstacles. A line ray
 # alone cuts corners through rocks, chair legs and the edge of the creek.
 var count=max(1,int(ceil(_flat_distance(a,b)/.27)))
 var previous=a
 for i in range(1,count+1):
  var q=a.lerp(b,float(i)/count);var floor=_floor_point(q.x,q.z,mask)
  if floor==Vector3.INF or abs(floor.y-previous.y)>.23:return false
  previous=floor
 return true

func tick(delta: float, active: bool, target: Vector3, pause: bool=false):
 var body=world.panda_body;var actor=world.panda_actor;var animator=world.panda_animator
 if not active:return
 if context!=world.active_home:build()
 repath-=delta
 var distance=Vector2(body.global_position.x-target.x,body.global_position.z-target.z).length()
 if world.active_home=="" and not pause and world.frog.is_on_floor() and target.distance_to(last_breadcrumb)>.55:
  breadcrumbs.append(target);last_breadcrumb=target
  if breadcrumbs.size()>240:breadcrumbs.remove_at(0)
 while not breadcrumbs.is_empty() and _flat_distance(breadcrumbs[0],body.global_position)<.80:breadcrumbs.remove_at(0)
 if repath<=0 and not pause:
  repath=.24
  var mask=2 if context!="" else 1
  var nav_goal=target
  var direct=distance<9 and _clear_segment(body.global_position,target,mask)
  if direct:
   breadcrumbs.clear();path=PackedVector3Array([target])
  else:
   # Follow the newest visible breadcrumb, never an obsolete loop all the way
   # back around the clearing. Reject unreachable/off-grid crumbs after a stall.
   for i in range(breadcrumbs.size()-1,-1,-1):
    if _flat_distance(body.global_position,breadcrumbs[i])<7 and _clear_segment(body.global_position,breadcrumbs[i],mask):
     for j in range(i):breadcrumbs.remove_at(0)
     break
   if not breadcrumbs.is_empty():nav_goal=breadcrumbs[0]
  if not direct and graph.get_point_count()>0:
   var start=graph.get_closest_point(body.global_position);var end=graph.get_closest_point(nav_goal)
   path=graph.get_point_path(start,end);last_goal=nav_goal
   while path.size()>1 and _flat_distance(body.global_position,path[0])<.35:path.remove_at(0)
   # Smooth only segments verified for a full capsule, not the untested diagonal
   # between grid points that used to send the follower into the same obstacle.
   for i in range(min(path.size()-1,7),0,-1):
    if _clear_segment(body.global_position,path[i],mask):
     for j in range(i):path.remove_at(0)
     break
 while not path.is_empty() and _flat_distance(path[0],body.global_position)<.19:path.remove_at(0)
 var direction=Vector3.ZERO
 if not pause and distance>1.30 and not path.is_empty():
  direction=path[0]-body.global_position;direction.y=0;direction=direction.normalized()
 var yaw=atan2(direction.x,direction.z)
 var turning=direction.length()>.1 and abs(angle_difference(actor.rotation.y,yaw))>.55
 var reference=float(world.locomotion.get("panda",{}).get("walk_speed",.68))
 var frog_speed=Vector2(world.frog.velocity.x,world.frog.velocity.z).length()
 var desired=clamp(frog_speed+max(0.0,distance-1.65)*.52,.88,2.95)
 if direction.length()<.1:desired=0
 catchup_speed=move_toward(catchup_speed,desired,delta*4.8)
 var speed=catchup_speed*(.65 if turning else 1.0)
 body.velocity.x=direction.x*speed
 body.velocity.z=direction.z*speed
 body.velocity.y=-.1 if body.is_on_floor() else body.velocity.y-18*delta
 var before=body.global_position
 # The graph accepts low thresholds only after a full capsule clearance test.
 var motion=Vector3(body.velocity.x,0,body.velocity.z)*delta
 if body.is_on_floor() and motion.length()>.002 and body.test_move(body.global_transform,motion):
  var raised=body.global_transform;raised.origin.y+=.24
  if not body.test_move(raised,motion):
   var probe=body.global_position+motion.normalized()*.43+Vector3.UP*.26
   var q=PhysicsRayQueryParameters3D.create(probe,probe-Vector3.UP*.34,body.collision_mask,[body.get_rid(),world.frog.get_rid()])
   var hit=world.get_world_3d().direct_space_state.intersect_ray(q)
   if not hit.is_empty() and hit.normal.y>.70 and hit.position.y-body.global_position.y>.01 and hit.position.y-body.global_position.y<.23:body.global_position.y=hit.position.y+.008
 body.move_and_slide()
 var actual=Vector2(body.global_position.x-before.x,body.global_position.z-before.z).length()/max(delta,.001)
 travelled+=actual*delta;samples+=1
 if actual<.03:stopped_frames+=1
 if body.get_slide_collision_count()>1:collision_frames+=1
 blocked=blocked+delta if direction.length()>.1 and actual<.04 else 0.0
 if blocked>1.0:
  path.clear();repath=0;blocked=0;recovery_count+=1
  if not breadcrumbs.is_empty():breadcrumbs.remove_at(0)
 if direction.length()>.1:actor.rotation.y=lerp_angle(actor.rotation.y,yaw,1-exp(-delta*7))
 elif distance<3 and not pause:actor.rotation.y=lerp_angle(actor.rotation.y,atan2(target.x-body.global_position.x,target.z-body.global_position.z),1-exp(-delta*4))
 if animator:
  var clip="Walk" if actual>.05 else "Idle"
  if turning and actual<.12 and animator.has_animation("Turn"):clip="Turn"
  if pause and world.tea_time>0 and animator.has_animation("Sit"):clip="Sit"
  animator.speed_scale=clamp(actual/reference,.15,4.5) if clip=="Walk" else 1.0
  if animator.has_animation(clip) and animator.current_animation!=clip:animator.play(clip,.18)
