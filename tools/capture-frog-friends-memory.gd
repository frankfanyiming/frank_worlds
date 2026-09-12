extends SceneTree
## Visual-only follow-up: uses the saved camp fixture from test-frog-friends-runtime.
## Resets picnic stage for a new comparison photo, never used in the playable world.
var w
func _initialize():call_deferred("run")
func run():
 var out=OS.get_cmdline_user_args()[0];root.size=Vector2i(1280,900)
 w=load("res://world.gd").new();w.save_path=out.path_join("save.json");w.photo_directory=out.path_join("photos");root.add_child(w)
 for i in range(40):await physics_frame
 if not w.friend_life.save.companion or w.active_home!="":
  push_error("Run the friend runtime test first to create its camp fixture.");quit(1);return
 w.friend_life.save.stage="picnic";w.friend_life._sync_props();w.friend_life.context_interact("camp");w.friend_ui_action("photo")
 for i in range(240):
  await process_frame
  if not w.friend_life.busy_photo:break
 print("PHOTO_REVIEW ",w.friend_life.save.memories[-1].photo)
 quit()
