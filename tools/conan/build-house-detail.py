"""Blender add-on joinery, readable shop signs and authored practical fixtures.

Small, separate GLBs preserve the old buildings' collision and imported texture
buffers. The engine loads detail_assets and applies the explicit day/night data.
"""
import bpy,sys,json,shutil,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import reference_geometry as g
from reference_geometry import *
import agasa_furniture as f

def stage(name,spec):
    export_asset(name+'-details')
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(name+'-details.blend')))
    for version in ['source','web-project']:
        folder=ROOT/f'worlds/conan/{version}/assets/buildings'
        shutil.copy2(OUT/(name+'-details.glb'),folder/(name+'-details.glb'))
        path=folder/(name+'.json');data=json.loads(path.read_text())
        for k,v in spec.items():data[k]=v
        if name=='mouri':
            for l in data.get('lights',[]):
                if .1<l['p'][1]<3 and -8<l['p'][2]<0 and l['p'][0]<0:l['color']='faf3e6';l['night_color']='ffbd76';l['night_energy_multiplier']=3.2
        path.write_text(json.dumps(data,ensure_ascii=False,indent=2))

def palette(prefix):
    m=f.palette()
    for ma in bpy.data.materials:
        if ma.name.startswith('Agasa fitted'):ma.name=ma.name.replace('Agasa fitted',prefix)
    return m

init();m=palette('Mouri detail');g.GROUP='MouriReference_WindowSigns'
ink=mat('Mouri sign dark ink','1c303d',.85)
backing=mat('Mouri sign illuminated ivory','e1e6df',.77)
cafeink=mat('Poirot sign warm ivory','efe5cf',.68)
frame=mat('Mouri sign aluminum frame','b4c4c5',.40,.32)
lamp=mat('Poirot warm pendant opal','efe2be',.63)
slate=mat('Mouri practical lamp housing','617586',.62)
# Seven distinct window panes carry seven large black Japanese characters.
for j,ch in enumerate('毛利探偵事務所'):
    x=-4.02+j*.728
    box('Milk opal office sign pane',(x,4.89,.089),(.722,1.03,.014),backing,.009)
    label(ch,(x,4.89,.120),.705,ink,weight='W7',max_width=.63)
    if j<6:box('Office sign narrow glazing bar',(x+.364,4.89,.119),(.017,1.042,.031),frame,.004)
for y in [4.369,5.411]:box('Office sign perimeter horizontal trim',(-1.836,y,.115),(5.11,.022,.031),frame,.004)
# Retain the original narrow bracket/sign housing; replace the tiny thin glyphs.
for j,ch in enumerate('毛利探偵事務所'):
    label(ch,(-4.507,6.16-j*.302,.566),.295,ink,weight='W8',max_width=.315)
# The cafe uses a bold window mark; it stays legible against a warm lit room.
label('ポアロ',(-.93,1.908,.118),.625,ink,weight='W7',max_width=2.12)
label('ポアロ',(-.932,1.916,.122),.601,cafeink,weight='W7',max_width=2.06)
line('Cafe cup mark bowl',[(-1.17,1.47,.123),(-1.12,1.31,.123),(-.77,1.31,.123),(-.72,1.47,.123)],.016,cafeink)
line('Cafe cup mark saucer',[(-1.24,1.255,.124),(-1.14,1.224,.124),(-.75,1.224,.124),(-.66,1.255,.124)],.012,cafeink)
line('Cafe cup mark handle',[(-.725,1.44,.123),(-.61,1.44,.123),(-.61,1.34,.123),(-.735,1.34,.123)],.014,cafeink)
# Practical light housings are actual Blender geometry, not floating light blobs.
g.GROUP='MouriReference_PracticalFixtures'
for x in [-2.02,-.21]:
    rod('Cafe pendant wire',(x,2.95,-.39),(x,2.42,-.39),.012,slate)
    cyl('Cafe pendant top ring',(x,2.42,-.39),.115,.065,slate,24)
    ell('Cafe pendant warm opal globe',(x,2.29,-.39),(.16,.19,.16),lamp)
for y in [4.35,5.47]:
    box('Office sign shallow light housing',(-1.84,y,.20),(4.92,.060,.15),slate,.018)
    box('Office sign diffuse strip',(-1.84,y-.027 if y>5 else y+.027,.207),(4.68,.018,.10),backing,.004)
rod('Exterior cool lamp bracket',(-4.47,5.65,.22),(-4.47,5.65,1.04),.034,slate)
box('Exterior lamp weather hood',(-4.47,5.65,1.04),(.58,.13,.22),slate,.028)
box('Exterior lamp diffuser',(-4.47,5.576,1.04),(.46,.016,.15),backing,.018)
# Furniture additions align with measured existing tabletop / cabinet bounds.
g.GROUP='MouriReference_OfficeJoinery'
for z in [-1.18,-2.06]:
    box('Office desk carved apron',(-1.25,3.963,z),(1.84,.086,.035),m['walnut'],.013)
    rod('Office desk fine brass bead',(-2.13,4.077,z),(-.37,4.077,z),.007,m['trim'])
for x in [-2.11,-.39]:
    box('Office desk side apron',(x,3.963,-1.62),(.035,.086,.88),m['walnut'],.013)
    box('Office desk corner joint',(x,3.886,-1.97),(.079,.23,.082),m['oak'],.011)
box('Desk letter tray bottom',(-.72,4.114,-1.71),(.42,.027,.29),m['walnut'],.02)
for x in [-.928,-.512]:box('Desk letter tray side',(x,4.164,-1.71),(.016,.094,.30),m['oak'],.004)
for k in range(4):box('Desk individual cream document',(-.73,4.137+k*.004,-1.71),(.345,.0025,.235),m['paper'],.001)
box('Office desk open notebook',(-1.98,4.113,-1.78),(.23,.016,.34),m['blue'],.007)
for x in [-2.046,-1.918]:box('Open notebook page',(x,4.125,-1.78),(.117,.003,.305),m['paper'],.002)
rod('Notebook resting pencil',(-2.059,4.137,-1.94),(-1.911,4.137,-1.66),.006,m['oak'])
for z in [-4.91,-3.19]:box('Tea table end reveal',(-1.62,3.77,z),(.61,.032,.027),m['walnut'],.008)
for z in [-7.66]:
    for x in [-3.60,-2.35,-1.10]:
        for yy in [3.56,3.82,4.08]:
            box('Archive drawer inset front',(x,yy,z+.245),(.985,.225,.017),m['white'],.006)
            box('Archive brass label holder',(x,yy+.04,z+.260),(.27,.070,.009),m['trim'],.005)
            box('Archive paper drawer label',(x,yy+.04,z+.266),(.235,.043,.007),m['paper'],.003)
            rod('Archive metal pull',(x-.13,yy-.06,z+.284),(x+.13,yy-.06,z+.284),.012,m['trim'])
g.GROUP='MouriReference_CafeJoinery'
for z in [-2.4,-4.4,-6.6]:
    line('Cafe booth tailored upper seam',f.rounded_outline(.64,.539,z,.681,1.50,.045),.007,m['linen'],closed=True)
    line('Cafe tabletop walnut perimeter',f.rounded_outline(-.15,.779,z,.690,.719,.025),.008,m['walnut'],closed=True)
    box('Cafe folded linen napkin',(-.28,.783,z+.20),(.20,.012,.21),m['linen'],.008)
    rod('Cafe spoon handle',(-.30,.797,z+.28),(-.30,.797,z+.14),.006,m['trim'])
    ell('Cafe spoon bowl',(-.30,.797,z+.11),(.022,.005,.028),m['trim'])
    box('Cafe porcelain sugar dish',(-.16,.790,z-.26),(.135,.028,.10),m['white'],.016)
    for k in range(3):box('Sugar cube on dish',(-.20+k*.032,.818,z-.26),(.023,.023,.023),m['pillow'],.002)
    # Brass ferrules and apron lines make the table construction visible near eye level.
    for xx in [-.465,.165]:box('Cafe table under-top apron',(xx,.686,z),(.035,.073,.665),m['walnut'],.012)
stage('mouri',{'detail_assets':['mouri-details'],
    'accent_lights':[
      {'name':'Street-side cool lamp','p':[-4.43,5.49,1.03],'color':'b9d7f2','day_energy':.015,'night_energy':1.25,'range':7.5,'specular':.04},
      {'name':'Office window opal wash','p':[-1.85,4.96,1.15],'color':'c3deef','day_energy':.015,'night_energy':.75,'range':5.5,'specular':.03},
      {'name':'Poirot pendant left','p':[-2.02,2.28,-.38],'color':'ffc985','day_energy':.06,'night_energy':1.55,'range':3.8,'specular':.06},
      {'name':'Poirot pendant right','p':[-.21,2.28,-.38],'color':'ffc985','day_energy':.06,'night_energy':1.55,'range':3.8,'specular':.06},
      {'name':'Poirot warm interior bounce','p':[-1.30,2.15,-2.45],'color':'ffd296','day_energy':0,'night_energy':.70,'range':4.1,'specular':.03}],
    'emissive_materials':{
      'Mouri sign illuminated ivory':{'color':'d9e6e8','day_energy':.02,'night_energy':.50},
      'Poirot sign warm ivory':{'color':'f4dfbd','day_energy':0,'night_energy':.17},
      'Poirot warm pendant opal':{'color':'ffe3b8','day_energy':.05,'night_energy':.85}},
    'detail_revision':'2026-09-13: pale blue-gray stucco, seven W7 dark window glyphs with opal backs, W8 vertical lettering, bold cafe window mark, practical night fixtures and fitted joinery.'})

init();g.OBJECTS.clear();m=palette('Kudo detail');g.GROUP='KudoReference_FittedFurniture'
for x,z,w,face in [(3.54,-.77,1.3,1),(8.73,-.77,1.3,1),(1.25,8.70,.80,-1)]:
    # Panel-and-frame construction on existing sideboards, bounded by old furniture.
    front=z+face*.240
    for xx in [x-w*.25,x+w*.25]:
        box('Sideboard inset door surround',(xx,.408,front),(w*.43,.486,.021),m['walnut'],.012)
        box('Sideboard recessed wood panel',(xx,.408,front+face*.014),(w*.34,.393,.013),m['oak'],.011)
        for yy in [.222,.596]:box('Sideboard panel rail',(xx,yy,front+face*.025),(w*.34,.023,.020),m['walnut'],.007)
    for xx in [x-.085,x+.085]:ell('Sideboard rounded brass pull',(xx,.43,front+face*.055),(.017,.020,.015),m['trim'])
    box('Sideboard slender drawer',(x,.709,front),(w*.87,.128,.025),m['oak'],.012)
    rod('Sideboard drawer handle',(x-.12,.710,front+face*.030),(x+.12,.710,front+face*.030),.009,m['trim'])
    for xx in [x-w*.40,x+w*.40]:box('Sideboard individual toe',(xx,.10,z),(.095,.14,.36),m['walnut'],.011)
# Existing kitchen base is a single cabinet block; separate framed doors clarify it.
for x in [-7.42,-6.50,-5.58]:
    box('Kitchen inset cabinet door',(x,.478,1.918),(.812,.663,.022),m['white'],.012)
    box('Kitchen door raised center',(x,.468,1.936),(.638,.500,.018),m['linen'],.014)
    rod('Kitchen turned cabinet pull',(x+.287,.595,1.965),(x+.287,.755,1.965),.011,m['trim'])
    box('Kitchen shallow drawer',(x,.841,1.922),(.819,.098,.020),m['oak'],.006)
    rod('Kitchen drawer brass pull',(x-.11,.840,1.947),(x+.11,.840,1.947),.009,m['trim'])
# The dining table receives a hemmed runner and a small breakfast service.
box('Dining linen runner',(-6.25,.796,6.26),(2.21,.009,.34),m['linen'],.007)
for z in [6.105,6.415]:rod('Runner sewn border',(-7.31,.803,z),(-5.19,.803,z),.003,m['white'])
f.cup((-6.95,.810,6.26),m,.92);f.cup((-5.56,.810,6.26),m,.92)
box('Dining folded newspaper',(-6.31,.811,6.26),(.44,.012,.285),m['paper'],.006)
for z in [6.17,6.21,6.25,6.29,6.33]:box('Newspaper fine rule',(-6.31,.819,z),(.35,.001,.003),m['seam'],0)
stage('kudo',{'detail_assets':['kudo-details'],'detail_revision':'2026-09-13: measured fitted sideboard panels, drawers, hardware, kitchen doors and hemmed dining service, without moving prior furniture or route colliders.'})
print('HOUSE_DETAIL_COMPLETE')
