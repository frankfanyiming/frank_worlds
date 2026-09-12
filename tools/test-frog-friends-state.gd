extends SceneTree
const Store=preload("res://friends/friend_state.gd")
const Recovery=preload("res://friends/save_recovery.gd")
var results={}
func check(name: String, passed: bool):
 results[name]=passed;print("FRIENDS_STATE ",name," ",passed)
func _initialize():
 var s=Store.migrate({})
 check("fresh_free_keepsakes",s.keepsakes.tea_jar==1 and s.keepsakes.stone==1 and s.stage=="meet")
 check("invite_once",Store.transact(s,"invite:first","invite") and not Store.transact(s,"invite:first","invite") and s.companion)
 check("cook_two_servings",Store.transact(s,"cook:1","cook","rice") and s.cooked.size()==2)
 check("duplicate_cook_no_extra_food",not Store.transact(s,"cook:1","cook","rice") and s.cooked.size()==2)
 check("food_gift_consumes_one",Store.transact(s,"gift:meal","gift","food") and s.cooked.size()==1)
 check("food_gift_replay_safe",not Store.transact(s,"gift:meal","gift","food") and s.cooked.size()==1)
 check("keepsake_display_slot",Store.transact(s,"gift:stone","gift","stone") and s.keepsakes.stone==0 and s.gifts.stone.slot=="window")
 check("no_duplicate_keepsake",not Store.transact(s,"gift:stone:2","gift","stone") and s.keepsakes.stone==0)
 check("picnic_consumes_remaining_serving",Store.transact(s,"picnic:1","picnic") and s.cooked.size()==0 and s.stage=="picnic")
 s.sequence=17
 var restored=Store.migrate(JSON.parse_string(JSON.stringify(s)))
 check("json_numeric_sequence_preserved",restored.sequence==17 and Store.next_id(restored,"cook")=="cook:18")
 check("refresh_keeps_food_gifts_and_stage",restored.stage=="picnic" and restored.gifts.stone.slot=="window" and restored.cooked.is_empty())
 check("photo_memory_once",Store.transact(restored,"photo:1","memory","panda-photo.png") and not Store.transact(restored,"photo:1","memory","panda-photo.png") and restored.memories.size()==1)
 check("invalid_recipe_rejected",not Store.transact(restored,"bad-cook","cook","invalid"))
 check("no_negative_inventory",not Store.transact(restored,"empty-meal","gift","food") and not Store.transact(restored,"empty-picnic","picnic") and restored.cooked.is_empty())
 var data=JSON.parse_string(FileAccess.get_file_as_string("res://friends/text.json"))
 var languages=true
 for loc in ["zh-CN","zh-TW","ja","ko","en"]:
  languages=languages and data[loc].size()==data["zh-CN"].size()
  for key in data["zh-CN"]:languages=languages and data[loc].get(key,"")!=""
 check("all_five_languages_have_same_keys",languages)
 var older={"_save_sequence":4,"_saved_at":100.0,"value":"older"}
 var newer={"_save_sequence":5,"_saved_at":101.0,"value":"newer"}
 check("newer_mirror_wins",Recovery.choose(older,newer).value=="newer")
 check("newer_idb_not_overwritten",Recovery.choose(newer,older).value=="newer")
 check("same_revision_uses_time",Recovery.choose({"_save_sequence":5,"_saved_at":102.0,"value":"disk"},newer).value=="disk")
 check("later_legacy_idb_not_overwritten",Recovery.choose({"value":"legacy"},older,105.0).value=="legacy")
 check("mirror_restores_if_idb_empty",Recovery.choose({},newer).value=="newer")
 var photo_state={"photos":[{"file":"old.png","place":"legacy"},{"file":"not-yet-in-idb.png","friend":"panda"}],"friend_life":{"stage":"remembered","memories":[{"id":"memory:1","photo":"not-yet-in-idb.png"}],"cooked":[{"id":"meal:2"}],"gifts":{"stone":{}},"picnic_item":{"id":"meal:1"}}}
 var repaired=Recovery.repair_photos(photo_state,"user://intentionally-missing-photos")
 check("uncommitted_friend_photo_not_broken_card",repaired.removed.size()==1 and photo_state.photos.size()==1 and photo_state.photos[0].place=="legacy")
 check("uncommitted_photo_can_retry_without_food_loss",photo_state.friend_life.stage=="picnic" and photo_state.friend_life.memories.is_empty() and photo_state.friend_life.cooked.size()==1 and photo_state.friend_life.gifts.has("stone") and photo_state.friend_life.picnic_item.id=="meal:1")
 var output=OS.get_cmdline_user_args()
 if not output.is_empty():
  var f=FileAccess.open(output[0],FileAccess.WRITE);f.store_string(JSON.stringify(results,"  "))
 quit(0 if not results.values().has(false) else 1)
