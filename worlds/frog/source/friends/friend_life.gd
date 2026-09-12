extends Node
const Store = preload("res://friends/friend_state.gd")
const Follow = preload("res://friends/friend_follow.gd")
var world
var save: Dictionary
var words: Dictionary
var following
var panel := ""
var message_key := ""
var panel_revision := 0
var companion_context := "panda"
var checkpoint_clock := 0.0
var tea_pause := 0.0
var bridge_seen := false
var busy_photo := false
var displays: Node3D
var picnic_props: Node3D
var cooking_props: Node3D
var gifts_nodes := {}
var restore_pending := false

func setup(owner):
 world=owner;words=JSON.parse_string(FileAccess.get_file_as_string("res://friends/text.json"))
 save=Store.migrate(world.state.get("friend_life",{}));world.state.friend_life=save
 following=Follow.new(world)
 world.data.interactions.append({"id":"friend_stove","label":"在窗边做点吃的","home":"frog","position":[-11.8,.3,-11.80]})
 _make_props();_sync_props()
 restore_pending=not save.checkpoint.is_empty()
 call_deferred("_restore")

func text(key: String, lang: String="") -> String:
 var loc=lang if lang!="" else world.locale
 return str(words.get(loc,words["zh-CN"]).get(key,key))

func _remember_line() -> String:
 if save.gifts.has("stone"):return "remember_stone"
 if save.gifts.has("tea_jar"):return "remember_jar"
 if not save.memories.is_empty():return "remember_picnic"
 return "greeting"

func near() -> bool:
 return companion_context==world.active_home and world.frog.global_position.distance_to(world.panda_body.global_position)<3.4

func _at_stove() -> bool:
 return world.active_home=="frog" and world.frog.global_position.distance_to(Vector3(-11.8,.3,-11.80))<2.7

func _at_camp() -> bool:
 return world.active_home=="" and world.frog.global_position.distance_to(Vector3(22,.25,7))<3.0

func _show(page: String, note: String=""):
 world._close_panel();panel=page;message_key=note;world.input_locked=true;panel_revision+=1
 if not OS.has_feature("web"):_native_panel()

func _native_panel():
 var data=ui_state(world.locale)
 var box=world._panel(str(data.title))
 box.get_child(0).get_child(1).pressed.connect(func():panel="")
 var half=min(290.0,(world.get_viewport().get_visible_rect().size.x-24)*.5)
 world.album_panel.offset_left=-half;world.album_panel.offset_right=half;world.album_panel.offset_top=-170;world.album_panel.offset_bottom=170
 var label=Label.new();label.text=str(data.body);label.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART;label.custom_minimum_size=Vector2(260,95);label.add_theme_color_override("font_color",Color("435a48"));label.add_theme_font_size_override("font_size",20);box.add_child(label)
 for choice in data.choices:
  var id=str(choice.id);var button=world._button(str(choice.label),func():action(id));box.add_child(button)

func open_journal():
 if near():_show("chat")
 else:_show("journal")

func context_interact(id: String) -> bool:
 match id:
  "friend_chat","panda_tea":_show("chat");return true
  "friend_stove":
   if not save.cooking.is_empty():_show("cooking")
   else:_show("recipes")
   return true
  "camp":
   if save.companion:
    if not near():_show("notice","wait_friend")
    elif save.stage=="picnic":_show("picnic")
    elif save.cooked.is_empty():_show("notice","no_food")
    else:_show("camp")
    return true
 return false

func _choices(ids: Array, labels: Array, lang: String) -> Array:
 var result=[]
 for i in range(ids.size()):result.append({"id":ids[i],"label":text(labels[i],lang)})
 return result

func ui_state(lang: String) -> Dictionary:
 var result={"open":panel!="","revision":panel_revision,"kind":"friends","title":text("friends",lang),"body":"","choices":[]}
 if panel=="":return result
 match panel:
  "chat":
   result.title=text("panda",lang);result.body=text(_remember_line(),lang)
   result.choices=_choices(["sit","invite","gifts"],["sit","invite","gift_menu"],lang) if not save.companion else _choices(["recipes","gifts","outing"],["cook","gift_menu","outing"],lang)
  "journal":
   result.title=text("journal",lang)
   result.body=text("find_panda" if not save.companion else ("outing_hint" if save.stage in ["outing","picnic"] else "home_hint"),lang)+"\n\n"+text("bag_count",lang).replace("{n}",str(save.cooked.size())).replace("{m}",str(save.memories.size()))
   result.choices=_choices(["close"],["close"],lang)
   if save.companion and _at_camp() and near():result.choices=_choices(["camp","close"],["picnic","close"],lang)
  "recipes":
   result.title=text("kitchen",lang);result.body=text("recipes",lang)
   result.choices=_choices(["recipe:rice","recipe:tea","close"],["rice","green_tea","close"],lang)
  "cooking":
   var step=int(save.cooking.get("step",0));var recipe=str(save.cooking.get("recipe","rice"))
   result.title=text("rice" if recipe=="rice" else "green_tea",lang)+" · "+text("cook_progress",lang).replace("{n}",str(step+1))
   result.body=text(recipe+"_step"+str(step),lang)
   result.choices=_choices(["advance:"+str(save.cooking.get("id",""))+":"+str(step),"close"],[["add","mix","wrap"][step] if recipe=="rice" else ["add","pour","serve"][step],"close"],lang)
  "cooked":
   result.title=text("kitchen",lang);result.body=text("cooked",lang)
   result.choices=_choices(["gifts","recipes","close"],["gift_menu","cook","close"],lang)
  "gifts":
   result.title=text("gifts",lang);result.body=text("gift_intro",lang)
   result.choices=_choices(["gift:food","gift:tea_jar","gift:stone"],["food","jar","stone"],lang)
  "gifted":
   result.title=text("panda",lang);result.body=text(message_key,lang)
   result.choices=_choices(["outing","gifts","close"],["outing","gift_menu","close"],lang)
  "camp":
   result.title=text("picnic",lang);result.body=text("picnic_ready",lang)
   result.choices=_choices(["picnic","close"],["lay_food","close"],lang)
  "picnic":
   result.title=text("picnic",lang);result.body=text("picnic_story",lang)
   result.choices=_choices(["photo","close"],["photo","close"],lang)
  "memory":
   result.title=text("journal",lang);result.body=text("memory_saved",lang)
   result.choices=_choices(["album","close"],["journal","close"],lang)
  "notice":
   result.title=text("panda",lang);result.body=text(message_key,lang);result.choices=_choices(["close"],["close"],lang)
 return result

func hud_state(lang: String) -> Dictionary:
 var key="find_panda"
 if save.companion:key="outing_hint" if save.stage in ["outing","picnic"] else "company"
 return {"summary":text(key,lang),"actionLabel":text("friends",lang),"stage":save.stage,"companion":save.companion,"servings":save.cooked.size(),"memories":save.memories.size()}

func action(id: String):
 if busy_photo:return
 if id not in ["close","open","journal"]:
  var allowed=false
  for choice in ui_state(world.locale).choices:
   if str(choice.id)==id:allowed=true
  if not allowed:return
 if id=="close":
  panel="";world._close_panel();return
 if id=="album":
  panel="";world._open_album();return
 if id in ["journal","open"]:open_journal();return
 if id=="invite":
  if not near():_show("notice","near_friend");return
  if not save.companion:
   Store.transact(save,"invite:first","invite");_attach()
  _persist();panel="";world._close_panel();world._toast(text("invited"),7);return
 if id=="sit":
  if not near():_show("notice","near_friend");return
  Store.transact(save,"tea:first","tea");tea_pause=7;world.tea_time=7;world.posing=7
  _persist();panel="";world._close_panel();world._toast(text(_remember_line()),7);return
 if id=="recipes":
  if not _at_stove():_show("notice","home_hint");return
  _show("cooking" if not save.cooking.is_empty() else "recipes");return
 if id.begins_with("recipe:"):
  if not _at_stove():_show("notice","home_hint");return
  var recipe=id.trim_prefix("recipe:")
  if recipe not in Store.RECIPES:return
  if save.cooking.is_empty():save.cooking={"id":Store.next_id(save,"cook"),"recipe":recipe,"step":0}
  _persist();_show("cooking");return
 if id.begins_with("advance:"):
  if not _at_stove() or save.cooking.is_empty():return
  var expected="advance:"+str(save.cooking.id)+":"+str(int(save.cooking.step))
  if id!=expected:return # A repeated UI event cannot skip steps or cook twice.
  save.cooking.step=int(save.cooking.step)+1
  if int(save.cooking.step)>=3:
   Store.transact(save,str(save.cooking.id),"cook",str(save.cooking.recipe));_persist();_show("cooked")
  else:_persist();_show("cooking")
  _sync_props();return
 if id=="gifts":
  if not near():_show("notice","near_friend");return
  _show("gifts");return
 if id.begins_with("gift:"):
  if not near():_show("notice","near_friend");return
  var gift=id.trim_prefix("gift:")
  if gift not in Store.GIFTS:return
  var event="gift:"+gift if gift!="food" else ("gift:"+str(save.cooked[0].id) if not save.cooked.is_empty() else "")
  if not Store.transact(save,event,"gift",gift):_show("notice","no_food" if gift=="food" else "already_gift");return
  _persist();_sync_props();_show("gifted","gift_"+gift);return
 if id=="outing":
  if not near():_show("notice","near_friend");return
  if not save.companion:_attach()
  Store.transact(save,Store.next_id(save,"outing"),"outing");_persist();panel="";world._close_panel();world._toast(text("outing_hint"),7);return
 if id=="camp":context_interact("camp");return
 if id=="picnic":
  if not _at_camp() or not near():_show("notice","wait_friend");return
  if save.stage!="picnic":
   if not Store.transact(save,Store.next_id(save,"picnic"),"picnic"):_show("notice","no_food");return
  world.posing=9;world.tea_time=9;tea_pause=9;_persist();_sync_props();_show("picnic");return
 if id=="photo":
  if save.stage=="picnic" and _at_camp() and near():_take_memory()

func _attach():
 if world.panda_body.get_parent()!=world:world.panda_body.reparent(world,true)
 companion_context=world.active_home;world.panda_body.visible=true
 world.panda_roam_enabled=false;following.invalidate()
 world.panda_body.add_collision_exception_with(world.frog)
 world.frog.add_collision_exception_with(world.panda_body)

func room_changed():
 if not save.companion:
  companion_context="panda";_sync_props();return
 # Rooms are separate engine spaces. Both characters pass through the same
 # doorway transition once; continuous outdoor following never teleports.
 _attach();world.panda_body.collision_mask=world.frog.collision_mask;world.panda_body.collision_layer=world.frog.collision_layer
 var p=world.frog.global_position
 if world.active_home=="frog":p+=Vector3(-.78,.05,-.55)
 elif world.active_home=="panda":p+=Vector3(-.82,.05,-.55)
 else:p+=Vector3(.85,.05,.55)
 world.panda_body.global_position=p;world.panda_body.velocity=Vector3.ZERO
 following.invalidate();_persist();_sync_props()

func _persist():
 var point=world.frog.global_position
 save.checkpoint={"home":world.active_home,"frog":[point.x,point.y,point.z]}
 if save.companion:
  var p=world.panda_body.global_position;save.checkpoint.panda=[p.x,p.y,p.z]
 world.state.friend_life=save;world._save()

func _restore():
 if not restore_pending:return
 var checkpoint=save.checkpoint.duplicate(true);restore_pending=false
 var home=str(checkpoint.get("home",""))
 if home in ["frog","panda"]:world._enter_home(home)
 if checkpoint.get("frog",[]) is Array and checkpoint.get("frog",[]).size()==3:
  world.frog.global_position=world.vec(checkpoint.frog);world.frog.velocity=Vector3.ZERO
 if save.companion:
  _attach();world.panda_body.collision_mask=world.frog.collision_mask;world.panda_body.collision_layer=world.frog.collision_layer
  if checkpoint.get("panda",[]) is Array and checkpoint.get("panda",[]).size()==3:world.panda_body.global_position=world.vec(checkpoint.panda)
  else:world.panda_body.global_position=world.frog.global_position+Vector3(.85,0,.65)
 # Entering a room saves its door handoff. Replace that temporary checkpoint
 # immediately after restoring positions so two rapid reloads stay at the stove.
 following.invalidate();_sync_props();_persist();world._toast(text("resume"),6)

func physics(delta: float):
 tea_pause=max(0.0,tea_pause-delta)
 if save.companion:
  following.tick(delta,true,world.frog.global_position,world.input_locked or tea_pause>0 or world.riding)
 elif world.active_home=="panda":companion_context="panda"
 checkpoint_clock+=delta
 if checkpoint_clock>5 and not world.riding and world.frog.is_on_floor():checkpoint_clock=0;_persist()
 if save.companion and world.active_home=="" and not bridge_seen and world.frog.position.distance_to(Vector3(14,1,-9))<2.6 and near():
  bridge_seen=true;tea_pause=3;world._toast(text("bridge"),5)
 if cooking_props:cooking_props.rotation.y=sin(world.time*.5)*.04

func nearest_hint():
 if world.riding:return
 if near() and (world.nearest=="" or world.nearest=="panda_tea"):
  world.nearest="friend_chat";world.prompt_label.text="E · "+text("chat_hint");world.prompt_label.visible=true
 elif world.nearest=="friend_stove":world.prompt_label.text="E · "+text("stove_hint")
 elif world.nearest=="camp" and save.companion:world.prompt_label.text="E · "+text("picnic" if near() else "walk_wait")

func _take_memory():
 busy_photo=true;panel="";world._close_panel();world.input_locked=true;world.manual_review_camera=true;world.overlay.visible=false
 var previous_transform=world.camera.global_transform;var previous_fov=world.camera.fov
 var center=(world.frog.global_position+world.panda_body.global_position)*.5
 world.camera.position=center+Vector3(-4.2,3.6,-5.5);world.camera.look_at(center+Vector3.UP*.65);world.camera.fov=48
 var frog_rotation=world.actor.rotation.y;var panda_rotation=world.panda_actor.rotation.y
 var toward=world.camera.global_position-world.frog.global_position
 world.actor.rotation.y=atan2(-toward.x,-toward.z)
 toward=world.camera.global_position-world.panda_body.global_position
 world.panda_actor.rotation.y=atan2(toward.x,toward.z)
 world.posing=4;world.tea_time=4;tea_pause=4
 await get_tree().create_timer(.4).timeout
 await RenderingServer.frame_post_draw
 var filename="friends-"+Store.next_id(save,"memory").replace(":","-")+".png"
 var error=world.get_viewport().get_texture().get_image().save_png(world.photo_directory.path_join(filename))
 world.camera.global_transform=previous_transform;world.camera.fov=previous_fov;world.manual_review_camera=false;world.overlay.visible=true;world.input_locked=false;busy_photo=false
 world.actor.rotation.y=frog_rotation;world.panda_actor.rotation.y=panda_rotation
 if error==OK:
  var event="memory:"+filename
  if Store.transact(save,event,"memory",filename):
   world.state.photos.append({"file":filename,"place":text("photo_title"),"place_key":"friend_picnic","time":Time.get_datetime_string_from_system(),"friend":"panda","event":event})
  _persist();_show("memory")
 else:_persist();_show("notice","photo_failed")

func _mat(color: String) -> StandardMaterial3D:
 var m=StandardMaterial3D.new();m.albedo_color=Color(color);m.roughness=.9;return m

func _mesh(parent: Node3D, mesh: Mesh, position: Vector3, material: Material) -> MeshInstance3D:
 var n=MeshInstance3D.new();n.mesh=mesh;n.material_override=material;n.position=position;parent.add_child(n);return n

func _sphere(parent: Node3D, position: Vector3, scale: Vector3, material: Material):
 var mesh=SphereMesh.new();mesh.radius=1;mesh.height=2;mesh.radial_segments=24;mesh.rings=12
 var n=_mesh(parent,mesh,position,material);n.scale=scale;return n

func _cylinder(parent: Node3D, position: Vector3, radius: float, height: float, material: Material):
 var mesh=CylinderMesh.new();mesh.top_radius=radius;mesh.bottom_radius=radius*.92;mesh.height=height;mesh.radial_segments=32
 return _mesh(parent,mesh,position,material)

func _meal(parent: Node3D, position: Vector3) -> Node3D:
 var group=Node3D.new();parent.add_child(group);group.position=position
 var leaf=_mat("78935a");var rice=_mat("e8dfbb");var wood=_mat("9b744d")
 _cylinder(group,Vector3(0,.025,0),.33,.045,wood)
 for i in range(2):
  var p=Vector3(-.13+i*.26,.13,.01)
  var ball=_sphere(group,p,Vector3(.14,.12,.12) if i==0 else Vector3(.155,.105,.135),rice)
  ball.rotation.z=.14 if i==1 else -.07
  _sphere(group,p+Vector3(0,-.08,.01),Vector3(.16,.025,.14),leaf)
  for j in range(7):_sphere(group,p+Vector3(sin(j*2.4)*.08,.09,cos(j*2.4)*.06),Vector3(.017,.009,.026),rice)
 return group

func _make_props():
 displays=Node3D.new();displays.name="FriendGiftDisplays";world.add_child(displays)
 var jar=Node3D.new();displays.add_child(jar);jar.position=Vector3(96.47,1.24,.4);jar.name="GiftTeaJar"
 _sphere(jar,Vector3(0,.16,0),Vector3(.15,.19,.15),_mat("82a18c"));_cylinder(jar,Vector3(0,.335,0),.105,.045,_mat("b69d70"))
 var label=BoxMesh.new();label.size=Vector3(.15,.13,.014);_mesh(jar,label,Vector3(0,.17,.146),_mat("efe4c5"));gifts_nodes.tea_jar=jar
 var stone=Node3D.new();displays.add_child(stone);stone.name="GiftWindowStone";stone.position=Vector3(96.15,1.24,-.65)
 _cylinder(stone,Vector3.ZERO,.20,.035,_mat("a08056"));var rock=_sphere(stone,Vector3(0,.12,0),Vector3(.15,.12,.11),_mat("87988c"));rock.rotation.z=.2;gifts_nodes.stone=stone
 gifts_nodes.food=_meal(displays,Vector3(100.48,.94,.22));gifts_nodes.food.name="GiftSharedMeal"
 picnic_props=Node3D.new();picnic_props.name="FriendPicnic";world.add_child(picnic_props);picnic_props.position=Vector3(21.2,.33,8.1)
 var mat=BoxMesh.new();mat.size=Vector3(2.5,.035,1.65)
 var cloth_material=_mat("a5ae82");cloth_material.cull_mode=BaseMaterial3D.CULL_DISABLED
 _mesh(picnic_props,mat,Vector3.ZERO,cloth_material)
 _meal(picnic_props,Vector3(-.3,.03,0))
 for x in [-.7,.55]:
  _cylinder(picnic_props,Vector3(x,.11,.40),.085,.17,_mat("81a092"));_cylinder(picnic_props,Vector3(x,.20,.40),.073,.012,_mat("667449"))
 cooking_props=Node3D.new();cooking_props.name="FriendCookingProgress";world.add_child(cooking_props);cooking_props.position=Vector3(-11.2,1.065,-13.12)
 _meal(cooking_props,Vector3.ZERO)

func _sync_props():
 if not displays:return
 if world.active_home=="" and save.stage in ["picnic","remembered"]:call_deferred("_ground_picnic")
 displays.visible=world.active_home=="panda"
 for key in gifts_nodes:gifts_nodes[key].visible=save.gifts.has(key)
 picnic_props.visible=world.active_home=="" and save.stage in ["picnic","remembered"]
 cooking_props.visible=world.active_home=="frog" and not save.cooking.is_empty()

func _ground_picnic():
 # A picnic blanket follows the existing uneven clearing; it is not a raised
 # table. Sample after physics is available, including after save restoration.
 if not is_instance_valid(picnic_props):return
 var space=world.get_world_3d().direct_space_state
 var exclude=[world.frog.get_rid(),world.panda_body.get_rid()]
 var base=picnic_props.position
 var center_ray=PhysicsRayQueryParameters3D.create(Vector3(base.x,2.4,base.z),Vector3(base.x,-2,base.z),1,exclude)
 var center=space.intersect_ray(center_ray)
 if center.is_empty():return
 base.y=center.position.y+.028;picnic_props.position=base
 var blanket=picnic_props.get_child(0)
 var vertices=PackedVector3Array();var normals=PackedVector3Array();var uv=PackedVector2Array();var indices=PackedInt32Array()
 var nx=12;var nz=8
 for z in range(nz+1):
  for x in range(nx+1):
   var local=Vector3((float(x)/nx-.5)*2.3,0,(float(z)/nz-.5)*1.45)
   var point=base+local
   var ray=PhysicsRayQueryParameters3D.create(Vector3(point.x,2.4,point.z),Vector3(point.x,-2,point.z),1,exclude)
   var hit=space.intersect_ray(ray)
   local.y=(hit.position.y-base.y+.055) if not hit.is_empty() else 0.0
   vertices.append(local);normals.append(Vector3.UP);uv.append(Vector2(float(x)/nx,float(z)/nz))
 for z in range(nz):
  for x in range(nx):
   var a=z*(nx+1)+x;var b=a+1;var c=a+nx+1;var d=c+1
   indices.append_array(PackedInt32Array([a,b,c,b,d,c]))
 var arrays=[];arrays.resize(Mesh.ARRAY_MAX);arrays[Mesh.ARRAY_VERTEX]=vertices;arrays[Mesh.ARRAY_NORMAL]=normals;arrays[Mesh.ARRAY_TEX_UV]=uv;arrays[Mesh.ARRAY_INDEX]=indices
 var cloth=ArrayMesh.new();cloth.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays);blanket.mesh=cloth
 for child in picnic_props.get_children():
  if child==blanket:continue
  var point=child.global_position
  var ray=PhysicsRayQueryParameters3D.create(Vector3(point.x,2.4,point.z),Vector3(point.x,-2,point.z),1,exclude)
  var hit=space.intersect_ray(ray)
  if not hit.is_empty():
   if child is MeshInstance3D:continue
   child.position.y=hit.position.y-base.y+.032
