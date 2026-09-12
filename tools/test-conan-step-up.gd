extends SceneTree
## Separate collision fixtures for the real Conan controller's low-kerb rule.
## These are test geometry, not world-route evidence or rendered design assets.
var world
var report=[]
var folder:String

func _initialize():call_deferred("run")
func frames(n:int):
	for i in range(n):await physics_frame
func box(name:String,position:Vector3,size:Vector3):
	var body=StaticBody3D.new();body.name=name;world.add_child(body);body.position=position
	var shape=CollisionShape3D.new();var bounds=BoxShape3D.new();bounds.size=size;shape.shape=bounds;body.add_child(shape)

func run():
	folder=OS.get_cmdline_user_args()[0];DirAccess.make_dir_recursive_absolute(folder)
	world=load("res://world.tscn").instantiate();world.auditing=true;root.add_child(world)
	while not world.gi_ready:await process_frame
	box("QA_floor",Vector3(160,-.10,98),Vector3(30,.20,12))
	var fixtures=[{"name":"12cm_kerb","height":.12,"allowed":true},{"name":"18cm_kerb","height":.18,"allowed":true},{"name":"24cm_block","height":.24,"allowed":false},{"name":"wall","height":1.8,"allowed":false},{"name":"low_ceiling","height":.12,"allowed":false}]
	for i in range(fixtures.size()):
		var x=150+i*4.0;var fixture=fixtures[i]
		box(fixture.name,Vector3(x,fixture.height/2,98.8),Vector3(1.5,fixture.height,1.6))
		if fixture.name=="low_ceiling":box("QA_low_ceiling",Vector3(x,1.25,99),Vector3(1.8,.32,3.2))
	await frames(20)
	for i in range(fixtures.size()):
		var fixture=fixtures[i];var x=150+i*4.0
		world.audit_input=Vector2.ZERO;world.travel(Vector3(x,.12,101));await frames(30)
		var start:Vector3=world.player.position;var peak=start.y;var samples=[]
		world.yaw=0;world.audit_input=Vector2(0,-1)
		for f in range(360):
			await physics_frame;peak=max(peak,world.player.position.y)
			if f%6==0:samples.append([world.player.position.x,world.player.position.y,world.player.position.z])
		world.audit_input=Vector2.ZERO;await frames(12)
		var crossed=world.player.position.z<97.9
		var passed=crossed==fixture.allowed and (fixture.allowed or peak<.07)
		var row={"name":fixture.name,"fixture_height":fixture.height,"should_cross":fixture.allowed,"passed":passed,"crossed":crossed,"start":[start.x,start.y,start.z],"end":[world.player.position.x,world.player.position.y,world.player.position.z],"peak_root_y":peak,"position_trace_10hz":samples}
		report.append(row);print("CONAN_STEP_FIXTURE ",fixture.name," ",passed," end=",world.player.position," peak=",peak)
	FileAccess.open(folder.path_join("step-fixtures.json"),FileAccess.WRITE).store_string(JSON.stringify({"engine":Engine.get_version_info(),"testing":world.testing,"auditing":world.auditing,"world_sha256":FileAccess.get_sha256("res://world.gd"),"fixtures":report},"  "))
	var passed=true
	for row in report:passed=passed and row.passed
	world.queue_free();world=null
	for i in range(3):await process_frame
	quit(0 if passed else 1)
