@tool
extends EditorPlugin
const OUT="res://assets/house-lighting/"
func _enter_tree():call_deferred("run_bake")
func run_bake():
 await get_tree().create_timer(2).timeout
 var reports=[]
 for kind in ["panda","frog"]:
  EditorInterface.open_scene_from_path(OUT+kind+"-room.tscn")
  for i in range(15):await get_tree().process_frame
  var house=EditorInterface.get_edited_scene_root();var gi=house.get_node("LightmapGI")
  EditorInterface.set_main_screen_editor("3D");EditorInterface.get_selection().clear();EditorInterface.get_selection().add_node(gi);EditorInterface.edit_node(gi)
  await get_tree().create_timer(1).timeout
  for state in ["day","dusk"]:
   var data=LightmapGIData.new();ResourceSaver.save(data,OUT+kind+"-"+state+".lmbake");data.take_over_path(OUT+kind+"-"+state+".lmbake");gi.light_data=data
   for l in house.get_node("BakedLights").get_children():
    l.light_energy=float(l.get_meta("bake_"+state+"_energy",l.get_meta(state+"_energy")))*12.0
    l.light_color=Color(l.get_meta(state+"_color"))
   gi.environment_custom_energy=.45 if state=="day" else .18
   var buttons=[]
   for c in EditorInterface.get_base_control().find_children("*","Button",true,false):
    if c.is_visible_in_tree() and "Bake Lightmaps" in c.text:buttons.append(c)
   if buttons.size()!=1:push_error("Bake button unavailable");get_tree().quit(2);return
   print("HOUSE_BAKE_START ",kind," ",state)
   buttons[0].pressed.emit()
   await get_tree().create_timer(1).timeout
   reports.append({"house":kind,"state":state,"users":gi.light_data.get_user_count(),"data":gi.light_data.resource_path})
   print("HOUSE_BAKE_END ",reports[-1])
  for l in house.get_node("BakedLights").get_children():
   l.light_energy=l.get_meta("day_energy");l.light_color=Color(l.get_meta("day_color"))
   if l is SpotLight3D:l.shadow_reverse_cull_face=true
  gi.environment_custom_energy=.45;gi.light_data=load(OUT+kind+"-day.lmbake")
  EditorInterface.save_scene()
  var packed=PackedScene.new();packed.pack(house);print("SCN_SAVE ",ResourceSaver.save(packed,OUT+kind+"-room.scn",ResourceSaver.FLAG_COMPRESS))
 FileAccess.open("res://final-bake-report.json",FileAccess.WRITE).store_string(JSON.stringify(reports,"  "))
 get_tree().quit()
