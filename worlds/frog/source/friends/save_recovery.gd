extends RefCounted
## Synchronous, small JSON mirror closes the Web frame-to-IDB commit window.
## Photos remain in userfs/IndexedDB; no image bytes are stored in localStorage.
const KEY="xlands:frog:state:v1"

static func choose(idb: Dictionary, mirror: Dictionary, idb_modified: float=0.0) -> Dictionary:
 if mirror.is_empty():return idb
 if idb.is_empty():return mirror
 var disk_rev=int(idb.get("_save_sequence",0));var mirror_rev=int(mirror.get("_save_sequence",0))
 var disk_time=float(idb.get("_saved_at",idb_modified));var mirror_time=float(mirror.get("_saved_at",0))
 # An older game may save without our sequence fields. Respect its newer file
 # timestamp instead of restoring a stale mirror over a subsequent legacy save.
 if disk_rev==0 and disk_time>mirror_time:return idb
 if disk_rev!=mirror_rev:return mirror if mirror_rev>disk_rev else idb
 return mirror if mirror_time>disk_time else idb

static func read_mirror() -> Dictionary:
 if not OS.has_feature("web"):return {}
 var raw=JavaScriptBridge.eval("(function(){try{return localStorage.getItem("+JSON.stringify(KEY)+")||'';}catch(e){return '';}})()")
 if raw is String and raw!="":
  var value=JSON.parse_string(raw)
  if value is Dictionary:return value
 return {}

static func mirror(serialized: String) -> bool:
 if not OS.has_feature("web"):return true
 return bool(JavaScriptBridge.eval("(function(){try{localStorage.setItem("+JSON.stringify(KEY)+","+JSON.stringify(serialized)+");return true;}catch(e){return false;}})()"))

static func repair_photos(s: Dictionary, directory: String) -> Dictionary:
 var report={"removed":[],"retry_picnic":false}
 if not s.get("photos",[]) is Array:return report
 var retained=[]
 for photo in s.photos:
  # Preserve older photo records. Only our semantic friend photos participate
  # in recovery; a missing file must never be rendered as a broken image.
  if photo is Dictionary and photo.get("friend","")=="panda" and not FileAccess.file_exists(directory.path_join(str(photo.get("file","")))):
   report.removed.append(str(photo.get("file","")))
  else:retained.append(photo)
 s.photos=retained
 if s.get("friend_life",{}) is Dictionary and not report.removed.is_empty():
  var life=s.friend_life
  life.memories=life.get("memories",[]).filter(func(memory):return str(memory.get("photo","")) not in report.removed)
  if str(life.get("stage",""))=="remembered":
   life.stage="picnic";report.retry_picnic=true
 return report
