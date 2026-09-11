extends SceneTree
const OUT="res://assets/house-lighting/"
var report={}
func _initialize():call_deferred("build")
func v(a):return Vector3(a[0],a[1],a[2])
func own(n,p):
 p.add_child(n);n.owner=current_scene
func own_all(n):
 n.owner=current_scene
 for c in n.get_children():own_all(c)
func clean(r:Resource,seen:Dictionary):
 if seen.has(r):return
 seen[r]=true
 if "::" in r.resource_path or r.resource_path.ends_with(".glb"):r.resource_path=""
 for p in r.get_property_list():
  if not (p.usage & PROPERTY_USAGE_STORAGE):continue
  var x=r.get(p.name)
  if x is Resource and not x is Texture:clean(x,seen)
func lamp(n,p,pos,color,day,dusk,range_,size_):
 var l=OmniLight3D.new();l.name=n;own(l,p);l.position=pos;l.light_color=Color(color);l.light_energy=day;l.omni_range=range_;l.light_size=size_;l.light_bake_mode=Light3D.BAKE_STATIC
 l.set_meta("day_energy",day);l.set_meta("dusk_energy",dusk);l.set_meta("day_color",color);l.set_meta("dusk_color",color)
 return l
func build():
 for kind in ["panda","frog"]:
  var h=Node3D.new();h.name="PandaRoom" if kind=="panda" else "FrogRoom";root.add_child(h);current_scene=h
  var files=["panda-home"] if kind=="panda" else ["home-enclosure","home-furnishings"]
  var seen={};var meshreport=[]
  for file in files:
   var room=load("res://assets/"+file+".glb").instantiate();room.scene_file_path="";room.name=file;own(room,h);own_all(room)
   for mi in room.find_children("*","MeshInstance3D",true,false):
    clean(mi.mesh,seen)
    for s in mi.mesh.get_surface_count():
     if mi.get_surface_override_material(s):clean(mi.get_surface_override_material(s),seen)
    if mi.material_override:clean(mi.material_override,seen)
    mi.gi_mode=GeometryInstance3D.GI_MODE_STATIC
    if "WindowBackground" in str(mi.name) or "WindowView" in str(mi.name):
     mi.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;mi.gi_mode=GeometryInstance3D.GI_MODE_DISABLED
    if "Enclosure" in str(mi.name):mi.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
    meshreport.append({"path":str(h.get_path_to(mi)),"surfaces":mi.mesh.get_surface_count(),"uv2":mi.mesh.surface_get_arrays(0)[Mesh.ARRAY_TEX_UV2].size()})
  var lights=Node3D.new();lights.name="BakedLights";own(lights,h)
  var layout=JSON.parse_string(FileAccess.get_file_as_string("res://assets/"+("panda-home.json" if kind=="panda" else "home-layout.json")))
  for item in layout.windows:
   var l=SpotLight3D.new();l.name="Window_"+item.name;own(l,lights)
   var n=v(item.inward_normal);var c=v(item.position)
   l.position=c+n*.12;l.look_at(c+n*4+Vector3.DOWN*2);l.light_color=Color("fff6e7");l.light_energy=.65;l.spot_angle=42;l.spot_attenuation=1.3;l.spot_range=11
   l.shadow_enabled=true;l.shadow_bias=.025;l.shadow_normal_bias=.45;l.light_size=.65;l.light_bake_mode=Light3D.BAKE_STATIC
   l.set_meta("day_energy",.65);l.set_meta("dusk_energy",.14);l.set_meta("day_color","fff6e7");l.set_meta("dusk_color","bfd0e2")
  lamp("RoomFill",lights,Vector3(0,4.4,.4) if kind=="panda" else Vector3(-14.8,4.8,-11.3),"edf2ef",.36,.25,9,1.5)
  var lamps=layout.get("lamps",[{"name":"table_candle","position":[-14.42,1.25,-10.67],"range":3},{"name":"loft_lantern","position":[-14,3.9,-14.3],"range":2.5}])
  for item in lamps:lamp("Lamp_"+item.name,lights,v(item.position),"ffd49a",.18,.34,item.range,.2)
  var bounce=lamp("UnderLoftBounce",lights,Vector3(0,1.55,-2.8) if kind=="panda" else Vector3(-15,1.7,-14.1),"edf2ef",0.,0.,5.,1.5)
  bounce.set_meta("bake_day_energy",.15);bounce.set_meta("bake_dusk_energy",.07)
  var gi=LightmapGI.new();gi.name="LightmapGI";own(gi,h);gi.quality=LightmapGI.BAKE_QUALITY_MEDIUM;gi.bounces=3;gi.directional=true;gi.interior=true;gi.max_texture_size=4096;gi.use_denoiser=true;gi.generate_probes_subdiv=LightmapGI.GENERATE_PROBES_SUBDIV_8
  gi.environment_mode=LightmapGI.ENVIRONMENT_MODE_CUSTOM_COLOR;gi.environment_custom_color=Color("edf2ef");gi.environment_custom_energy=.45
  for state in ["day","dusk"]:gi.set_meta(state+"_data",OUT+kind+"-"+state+".lmbake")
  var packed=PackedScene.new();packed.pack(h);print("BUILD ",kind," ",ResourceSaver.save(packed,OUT+kind+"-room.tscn"));report[kind]=meshreport
  h.queue_free();current_scene=null
 FileAccess.open("res://final-uv2-report.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "));quit()
