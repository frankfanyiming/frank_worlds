import bpy
from pathlib import Path
im=bpy.data.images.new('srgb-chip',16,16);v=.5370987304831942;im.pixels.foreach_set([x for _ in range(256) for x in [v,v,v,1]]);im.file_format='JPEG';im.filepath_raw=str(Path(__file__).resolve().parent/'srgb-chip.jpg');im.save()
