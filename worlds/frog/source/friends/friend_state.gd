extends RefCounted
## Versioned local memories. All inventory mutations share a persisted event ledger.
const VERSION = 1
const GIFTS = ["food", "tea_jar", "stone"]
const RECIPES = ["rice", "tea"]

static func fresh() -> Dictionary:
 return {"version":VERSION,"stage":"meet","companion":false,"events":{},"sequence":0,"cooking":{},"cooked":[],"gifts":{},"keepsakes":{"tea_jar":1,"stone":1},"memories":[],"checkpoint":{},"picnic_item":{},"shared_tea":false}

static func migrate(value) -> Dictionary:
 var result=fresh()
 if value is Dictionary:
  for key in result:
   if key not in value:continue
   if typeof(value[key])==typeof(result[key]):result[key]=value[key]
   elif typeof(result[key])==TYPE_INT and typeof(value[key]) in [TYPE_FLOAT,TYPE_INT]:result[key]=int(value[key])
 result.version=VERSION
 if result.stage not in ["meet","invited","cooked","gifted","outing","picnic","remembered"]:result.stage="meet"
 return result

static func next_id(s: Dictionary, prefix: String) -> String:
 s.sequence=int(s.sequence)+1
 return prefix+":"+str(s.sequence)

static func transact(s: Dictionary, event: String, kind: String, value: String="") -> bool:
 if event=="" or s.events.has(event):return false
 match kind:
  "invite":
   s.companion=true
   if s.stage=="meet":s.stage="invited"
  "tea":s.shared_tea=true
  "cook":
   if value not in RECIPES:return false
   s.cooked.append({"id":event+":a","recipe":value})
   s.cooked.append({"id":event+":b","recipe":value})
   s.cooking={}
   if s.stage in ["meet","invited"]:s.stage="cooked"
  "gift":
   if value not in GIFTS:return false
   if value=="food":
    if s.cooked.is_empty():return false
    s.cooked.pop_front()
   else:
    if int(s.keepsakes.get(value,0))<1:return false
    s.keepsakes[value]-=1
   s.gifts[value]={"event":event,"slot":"tea_table" if value=="food" else ("cabinet" if value=="tea_jar" else "window"),"shared":true}
   if s.stage in ["meet","invited","cooked"]:s.stage="gifted"
  "outing":
   s.companion=true;s.stage="outing"
  "picnic":
   if s.cooked.is_empty():return false
   s.picnic_item=s.cooked.pop_front();s.stage="picnic"
  "memory":
   if s.stage!="picnic" or value=="":return false
   s.memories.append({"id":event,"friend":"panda","place":"camp","recipe":str(s.picnic_item.get("recipe","rice")),"photo":value})
   s.stage="remembered"
  _ :return false
 s.events[event]={"kind":kind,"value":value}
 return true
