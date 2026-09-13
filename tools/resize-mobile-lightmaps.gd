extends SceneTree
func _initialize():
 if not "native-mobile24" in ProjectSettings.globalize_path("res://"):push_error("Use an isolated mobile project");quit(1);return
 for name in ["frog-day","frog-dusk","panda-day","panda-dusk"]:
  var path="res://assets/house-lighting/"+name+".exr"
  if not FileAccess.file_exists(path):continue
  var config=ConfigFile.new();config.load(path+".import")
  var rows=int(config.get_value("params","slices/vertical",1));var cols=int(config.get_value("params","slices/horizontal",1))
  var original=Image.load_from_file(path);var width=original.get_width()/cols;var height=original.get_height()/rows
  if width<=256 and height<=256:continue
  var scale=min(256.0/width,256.0/height);var w=max(1,int(width*scale));var h=max(1,int(height*scale))
  var result=Image.create(w*cols,h*rows,false,original.get_format())
  for y in range(rows):
   for x in range(cols):
    var layer=original.get_region(Rect2i(x*width,y*height,width,height));layer.resize(w,h,Image.INTERPOLATE_LANCZOS)
    result.blit_rect(layer,Rect2i(0,0,w,h),Vector2i(x*w,y*h))
  var error=result.save_exr(path)
  if error!=OK:push_error("Cannot save "+path);quit(1);return
  print("LIGHTMAP ",name," layers=",rows*cols," ",width,"x",height," -> ",w,"x",h," format=",result.get_format())
 quit()
