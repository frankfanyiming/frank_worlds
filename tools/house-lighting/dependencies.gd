extends SceneTree
var seen={};var all=[]
func _initialize():
 for kind in ["panda","frog"]:
  visit("res://assets/house-lighting/"+kind+"-room.scn")
  visit("res://assets/house-lighting/"+kind+"-dusk.lmbake")
 var out={"resources":all,"no_glb_dependencies":true,"missing":[]}
 for r in all:
  if ".glb" in r.path:out.no_glb_dependencies=false
  if not r.exists:out.missing.append(r.path)
 FileAccess.open("res://dependency-closure.json",FileAccess.WRITE).store_string(JSON.stringify(out,"  "));print("CLOSURE ",all.size()," ",out.no_glb_dependencies," missing ",out.missing);quit()
func visit(path):
 if seen.has(path):return
 seen[path]=true
 var deps=[]
 for d in ResourceLoader.get_dependencies(path):
  var dep=d.get_slice("::",2) if "::" in d else d
  if dep=="":dep=d.get_slice("::",1)
  deps.append(dep);visit(dep)
 all.append({"path":path,"exists":FileAccess.file_exists(path),"dependencies":deps})
