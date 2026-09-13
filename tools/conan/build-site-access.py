"""A supported garage plot replaces the exposed old riverbed, Y-up metres."""
import sys,json,shutil,bpy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import reference_geometry as g
from reference_geometry import *
init();g.GROUP='GarageSite'
concrete=mat('Garage courtyard warm aggregate','b9b8ad',.94)
joint=mat('Garage fine expansion joint','858b88',.95)
edge=mat('Garage retaining wall concrete','a3aaa5',.9)
steel=mat('Garage drainage brushed steel','84918d',.57,.35)
# Full-height foundation: no floating top sheet over a 1.55m riverbed.
box('Supported garage plot',(12.2,-.78,-5.65),(6.2,1.60,11.20),concrete,0,True)
box('Rear vehicle apron',(11.67,.019,-9.40),(5.1,.04,4.66),concrete,0,True)
# Land-side link is lower than the18cm kerb contract and continuous to the old quay.
box('Pedestrian apron link',(8.95,.019,-9.40),(.9,.04,4.66),concrete,0,True)
for z in [-11.7,-10.5,-9.3,-8.1]:
 box('Apron expansion seam',(11.45,.041,z),(5.50,.003,.012),joint,0)
box('Garage door drainage recess',(11.62,.041,-7.23),(3.75,.004,.15),joint,.001)
for j in range(50):box('Garage door drain slot',(9.82+j*.073,.046,-7.23),(.020,.004,.12),steel,.001)
box('Waterside solid retaining wall',(15.21,-.66,-5.65),(.18,1.77,11.3),edge,.02,True)
box('Waterside raised safety kerb',(15.18,.23,-5.65),(.25,.31,11.3),edge,.015,True)
box('Rear retaining wall',(12.2,-.71,-11.29),(6.15,1.69,.20),edge,.02,True)
for x in [10.4,12.1,13.8]:
 box('Garage parking paving joint',(x,.044,-3.9),(.013,.004,5.9),joint,0)
export_asset('site-access')
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'site-access22.blend'))
for variant in ['source','web-project']:
 base=ROOT/f'worlds/conan/{variant}/assets/buildings';shutil.copy2(OUT/'site-access.glb',base/'site-access.glb')
 p=base/'agasa.json';d=json.loads(p.read_text());d['detail_assets']=list(dict.fromkeys(d.get('detail_assets',[])+['site-access']))
 d['routes']=[r for r in d['routes'] if r['name']!='garage_to_rear_apron']
 d['routes'].append({'name':'garage_to_rear_apron','points':[[10.1,.065,-5.8],[10.1,.065,-6.6],[10.1,.10,-8.6],[11.6,.10,-10.4],[9.2,.10,-10.4]],'expected_y':.10})
 d['notes']['garage_site22']='Supported concrete embankment and rear vehicle apron, with full-depth retaining walls, drainage and a land-side pedestrian approach; legacy quay fence clipped out of the building plot.'
 d['notes']['garage_beetle_position'][1]=.041
 p.write_text(json.dumps(d,ensure_ascii=False,indent=2))
