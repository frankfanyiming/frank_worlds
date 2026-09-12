extends SceneTree
var checks=[]
func _initialize():call_deferred("run")
func check(ok,label):
 checks.append({"case":label,"pass":ok})
 if not ok:push_error(label)
func run():
 var bridge=load("res://xlands_bridge.gd").new()
 bridge.labels=JSON.parse_string(FileAccess.get_file_as_string("res://translations.json"))
 for locale in ["zh-CN","zh-TW","en","ja","ko"]:
  bridge.locale=locale
  var collect=bridge._t("E  ·  采收三叶草")
  check(collect=="E  ·  "+bridge._t("采收三叶草"),locale+" interaction uses semantic source")
  var album=bridge._t("旅行相册  ·  27 张")
  check(album.contains("27") and (locale=="zh-CN" or album!= "旅行相册  ·  27 张"),locale+" dynamic album counter")
  var bag=bridge._t("三叶草：31　　营地休息：4 次")
  check(bag.contains("31") and bag.contains("4") and (locale=="zh-CN" or bag!="三叶草：31　　营地休息：4 次"),locale+" dynamic inventory counts")
  var caption=bridge._t("照片放进相册了：林间营地")
  check(caption==bridge._t("照片放进相册了：")+bridge._t("林间营地"),locale+" photo caption composition")
  if locale!="zh-CN":
   for source in bridge.labels:
    check(str(bridge.labels[source].get(locale,"")).length()>0,locale+" entry "+source)
 bridge.free()
 var good=true
 for c in checks:good=good and c.pass
 var out=OS.get_environment("UI_EVIDENCE")
 if not out.is_empty():
  DirAccess.make_dir_recursive_absolute(out)
  FileAccess.open(out+"/bridge-translation.json",FileAccess.WRITE).store_string(JSON.stringify({"passed":good,"checks":checks},"  "))
 print("UI_TRANSLATIONS ",checks.size()," checks; pass=",good)
 quit(0 if good else 1)
