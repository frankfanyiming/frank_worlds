extends SceneTree
## Run with Godot --path worlds/frog/source --script <absolute script> -- <output directory>.
## Exercises the real character controller, room boundaries and rendered cameras.
var world
var folder: String
var checks := {}
var route := []

func _initialize():call_deferred("run")

func frames(count=12):
 for i in range(count):await process_frame

func shot(name: String):
 await frames(12)
 await RenderingServer.frame_post_draw
 root.get_texture().get_image().save_png(folder.path_join(name+".png"))

func place(position: Vector3, mode=0):
 world.frog.position=position;world.frog.velocity=Vector3.ZERO;world.mode=mode
 await frames(20)

func walk(target: Vector3):
 var result=await world._walk_to(target,5)
 route.append(result)
 print("HOME_WALK ",JSON.stringify(result))
 return result.reached

func run():
 var args=OS.get_cmdline_user_args()
 folder=args[0] if args.size() else ProjectSettings.globalize_path("user://home-check")
 DirAccess.make_dir_recursive_absolute(folder)
 world=load("res://world.tscn").instantiate();root.add_child(world)
 world.input_locked=true;world.auditing=true;world.audit_input=Vector3.ZERO
 await frames(60)
 world.overlay.visible=false
 await place(Vector3(-15,.3,-4))
 checks.roof_stays_outside=not world.inside_home and world.stage.visible and world.shell.visible
 await shot("01-门外保持完整屋顶")
 checks.enter=await walk(Vector3(-15,.2,-8.08))
 await shot("02a-刚进家门")
 checks.enclosed_transition=world.inside_home and not world.stage.visible and world.home_enclosure.visible
 checks.cross_door=await walk(Vector3(-14.7,.2,-9.45))
 await shot("02-密闭室内全景")
 var before=world.camera.position
 var wheel=InputEventMouseButton.new();wheel.button_index=MOUSE_BUTTON_WHEEL_DOWN;wheel.pressed=true
 world._unhandled_input(wheel);world._camera_update(1)
 checks.wheel_stays_inside=world.camera.position.is_equal_approx(before)
 var floor_y=world.frog.position.y
 world.jump_buffer=.14
 var peak=floor_y
 for i in range(70):
  await physics_frame
  peak=max(peak,world.frog.position.y)
 checks.jump_and_land=peak-floor_y>.8 and abs(world.frog.position.y-floor_y)<.15 and world.inside_home
 checks.stairs=await walk(world.vec(world.data.stair_route[0]))
 for point in world.data.stair_route:
  var reached=await walk(world.vec(point))
  checks.stairs=checks.stairs and reached
 checks.loft=await walk(Vector3(-16.52,2.64,-14.3))
 await shot("03-夹层睡铺")
 # The new enclosing wall must block the real capsule, including on the loft.
 world.audit_input=Vector3(0,0,-1)
 for i in range(100):await physics_frame
 world.audit_input=Vector3.ZERO
 checks.wall_blocks=world.frog.position.z>-16.75 and world.inside_home
 await place(Vector3(-14,.2,-10),2)
 await shot("04-室内蛙眼视角")
 checks.first_person_inside=world.inside_home and world.camera.position.distance_to(world.frog.position+Vector3.UP*.7)<.01
 await place(Vector3(-14.7,.2,-9.45))
 world.overlay.visible=true
 await shot("05-室内游戏画面")
 world._toggle_night()
 await shot("05b-室内黄昏")
 checks.indoor_light=world.sun.light_energy==0 and world.home_light.visible and not world.environment.fog_enabled
 world._toggle_night()
 checks.exit=await walk(Vector3(-15,.2,-6.1))
 await shot("06-出门恢复庭院")
 checks.exit_restores_world=not world.inside_home and world.stage.visible and not world.home_enclosure.visible and world.environment.fog_enabled
 var report={"checks":checks,"route":route,"jump_height":peak-floor_y,"real_runtime":true}
 FileAccess.open(folder.path_join("home-check.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
 print("HOME_TEST ",JSON.stringify(checks))
 quit(0 if checks.values().all(func(v):return v) else 1)
