extends Node
# Runtime-only mobile policy. Collision, animation speed and authored resources
# stay intact. The browser's HTML UI has its own full-resolution surface.
var world:Node
var mobile=false
var lamps=[]
var meshes=[]
var tick=0.0
var elapsed=0.0
var callback
var hidden=false
func _ready():
 world=get_parent()
 mobile=OS.has_feature("web") and bool(JavaScriptBridge.eval("matchMedia('(any-pointer: coarse)').matches"))
 if not mobile:return
 var view=get_viewport()
 view.msaa_3d=Viewport.MSAA_2X
 view.mesh_lod_threshold=4.0
 view.positional_shadow_atlas_size=1024
 RenderingServer.directional_shadow_atlas_set_size(512,true)
 RenderingServer.directional_soft_shadow_filter_set_quality(RenderingServer.SHADOW_QUALITY_SOFT_VERY_LOW)
 RenderingServer.positional_soft_shadow_filter_set_quality(RenderingServer.SHADOW_QUALITY_SOFT_VERY_LOW)
 Engine.max_fps=30
 scan(world)
 if world.get("sun"):
  world.sun.directional_shadow_max_distance=28
  world.sun.directional_shadow_mode=DirectionalLight3D.SHADOW_ORTHOGONAL
 if world.get("env") and world.env.sky:
  # A changing TIME sky used to invalidate the entire reflection cubemap each
  # frame. These worlds have authored ambient fill and do not need that cost.
  world.env.reflected_light_source=Environment.REFLECTION_SOURCE_DISABLED
  var material=world.env.sky.sky_material
  if material is ShaderMaterial:
   material.shader=material.shader.duplicate()
   material.shader.code=material.shader.code.replace("TIME","0.0").replace("i<5","i<3")
 if world.get("environment") and world.environment.sky:
  world.environment.reflected_light_source=Environment.REFLECTION_SOURCE_DISABLED
 callback=JavaScriptBridge.create_callback(read_health)
 JavaScriptBridge.get_interface("window").xlandsSamplePerformance=callback
 JavaScriptBridge.eval("window.xlandsReadPerformance=()=>{window.xlandsSamplePerformance();return window.__xlandsRenderHealth}")
 set_process(true)
func scan(node):
 if node is ReflectionProbe:
  node.visible=false
 if node is OmniLight3D or node is SpotLight3D:
  lamps.append(node)
  # Each local shadow adds a scene pass (six for a point lamp). Retain the
  # authored diffuse fill, baked contacts and the sun's main shadow on phones.
  node.shadow_enabled=false
 if node is GeometryInstance3D:
  node.lod_bias=.45
  if node is MultiMeshInstance3D:
   node.multimesh.visible_instance_count=min(240,node.multimesh.instance_count)
   node.visibility_range_end=28;node.visibility_range_end_margin=4
  elif node is MeshInstance3D:
   var bounds=node.get_aabb()
   if node.skin:node.lod_bias=.7
   meshes.append({"mesh":node,"bounds":bounds,"layers":node.layers})
   if not node.skin and bounds.size.length()<.35:
    node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
   if "Leaf_veins" in str(node.name):node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
 for child in node.get_children():
  if child!=self:scan(child)
func _process(delta):
 if not mobile:return
 elapsed+=delta;tick+=delta
 if tick<.25:return
 tick=0
 var is_hidden=bool(JavaScriptBridge.eval("document.hidden"))
 if is_hidden!=hidden:
  hidden=is_hidden
  RenderingServer.render_loop_enabled=not hidden
  Engine.max_fps=5 if hidden else 30
 if hidden:return
 var camera=world.get("camera")
 if not camera:camera=world.get("cam")
 if not camera:return
 for item in meshes:
  var node=item.mesh
  if not is_instance_valid(node):continue
  var bounds:AABB=node.global_transform*item.bounds
  # Distance to the box, not its centre: large street meshes containing the
  # camera remain visible, while entire distant houses can finally be culled.
  var nearest_point=camera.global_position.clamp(bounds.position,bounds.end)
  var distance=camera.global_position.distance_to(nearest_point)
  # Layer exclusion preserves every existing indoor/outdoor visibility flag.
  node.layers=0 if distance>42 else item.layers
 for lamp in lamps:
  if not is_instance_valid(lamp):continue
  var range_value=lamp.omni_range if lamp is OmniLight3D else lamp.spot_range
  lamp.distance_fade_enabled=true
  lamp.distance_fade_begin=max(12.0,range_value+6.0)
  lamp.distance_fade_length=5.0
func read_health(_args):
 var data={"profile":"mobile-speed","fps":Engine.get_frames_per_second(),"targetFps":Engine.max_fps,"drawCalls":Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME),"primitives":Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME),"videoMemoryMiB":Performance.get_monitor(Performance.RENDER_VIDEO_MEM_USED)/1048576.0,"textureMiB":Performance.get_monitor(Performance.RENDER_TEXTURE_MEM_USED)/1048576.0,"msaa":get_viewport().msaa_3d,"lodThreshold":get_viewport().mesh_lod_threshold,"hidden":hidden}
 JavaScriptBridge.eval("window.__xlandsRenderHealth="+JSON.stringify(data))
 return JavaScriptBridge.get_interface("window").__xlandsRenderHealth
