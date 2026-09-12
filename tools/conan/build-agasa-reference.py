"""Agasa house rebuilt from the user's exterior/plan/interior reference set, revision 2026-09."""
import sys,math,json,random,bpy,bmesh
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import reference_geometry as g
from reference_geometry import *
import agasa_furniture as furniture
S=init();clay='--grey' in sys.argv
cream=mat('Agasa reference warm ivory facade','dfd0a4');pink=mat('Agasa reference dusty rose central spine','ad8794');floor=mat('Agasa reference teal floor','9bb4a8',.86);oak=mat('Agasa reference honey joinery','997044',.65);walnut=mat('Agasa reference dark walnut','684b36',.7);silver=mat('Agasa reference satin aluminum','94a5a2',.35,.65);dark=mat('Agasa reference charcoal trim','33414b');glass=mat('Agasa reference blue clear Glass','9bbcc5',.1,0,.24);white=mat('Agasa reference enamel white','e8e6d5',.48);purple=mat('Agasa reference muted purple upholstery','79738b',.95);linen=mat('Agasa reference cream bed linen','d5ccab',.94);red=mat('Agasa reference warm rug','934b45',.96);solar=mat('Agasa reference solar cells','4d6476',.30,.25);stone=mat('Agasa reference cellar concrete','9d9e94',.92);tile=mat('Agasa reference cellar pale tiles','b4b4a4',.8);grass=mat('Agasa reference green lawn','658e50',.96);leaf=mat('Agasa reference garden foliage','406c43',.9);leaf2=mat('Agasa reference light foliage','71945a',.9);bark=mat('Agasa reference bark','75624b');brass=mat('Agasa reference brass','b79b50',.32,.6);blue=mat('Agasa reference lab blue equipment','597984');screen=mat('Agasa reference muted CRT display','334b49',.4);pages=mat('Agasa reference book paper','e0d7b8');bookm=[mat('Agasa reference book '+str(i),h) for i,h in enumerate(['736951','686853','886459','5c7580','9b997c'])]
# Capsule-like twin round wings. Keep a real central entrance and tall round rear stair tower.
W=8.8;D=6.8;TOWER=(0,-5.9);TFLOOR=.06;UP=3.18;BASE=-3.12
R={'origin':[64,0,-7],'yaw':0,'spawn':[0,.08,8.3],'rooms':[],'lights':[],'routes':[],'views':[],'colliders':[],'npcs':[],'windows':[],'interactions':[],'interior_zones':[]}
outline=[]
for i in range(96):
 a=tau*i/96;outline.append((W*cos(a),D*sin(a)))
g.GROUP='AgasaReference_Ground'
slab=prism('Continuous main floor with real rear stair hole',outline,-.15,TFLOOR,floor,True);boolean_hole(slab,(0,0,-5.9),2.18)
# Main floor is open to both storeys; upper ring is an actual gallery with a central atrium.
g.GROUP='AgasaReference_Facade'
for level in [0,UP]:
 low=level+.76;high=level+2.37
 for i in range(96):
  a=tau*i/96;b=tau*(i+1)/96;mid=(a+b)/2
  # Front portico opening, rear stair connection and a right-side garden exit.
  front=abs(math.atan2(sin(mid-pi/2),cos(mid-pi/2)))<.13
  rear=abs(math.atan2(sin(mid-3*pi/2),cos(mid-3*pi/2)))<.24
  side_exit=(i in [90,91,92,93]) and level==0
  if front or rear or side_exit:continue
  p1=(W*cos(a),D*sin(a));p2=(W*cos(b),D*sin(b));vs=[]
  for x,z in [p1,p2]:
   inward=Vector((-x/W**2,-z/D**2)).normalized()
   for off,y in [(0,level+.06),(0,low),(.20,level+.06),(.20,low)]:vs.append((x+inward.x*off,y,z+inward.y*off))
  mesh('Curved facade sill band',vs,[(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)],cream,True,recalc=True)
  # Separate solid head/spandrel keeps recognisable cream bands, not glass-box elevations.
  p=[p1,p2,(p2[0]*.977,p2[1]*.971),(p1[0]*.977,p1[1]*.971)]
  prism('Cream curved storey crown',p,high,level+3.12,cream,True)
  mesh('Actual curved transparent window opening',[(p1[0],low,p1[1]),(p2[0],low,p2[1]),(p2[0],high,p2[1]),(p1[0],high,p1[1])],[(0,1,2,3)],glass,False)
  if i%3==0:
   rod('Window aluminum mullion',(p1[0],low,p1[1]),(p1[0],high,p1[1]),.026,silver)
  if i%12==0:
   n=Vector((-W*cos(mid),0,-D*sin(mid))).normalized();R['windows'].append({'name':f'curve_{level}_{i}','position':[W*cos(mid),level+1.6,D*sin(mid)],'inward_normal':list(n),'width':2.7,'height':1.6,'room':'main' if level==0 else 'gallery'})
  # Ground window safety collision is transparent yet physically closed.
  if level==0:
   dx,dz=p2[0]-p1[0],p2[1]-p1[1];R['colliders'].append({'p':[(p1[0]+p2[0])/2,1.58,(p1[1]+p2[1])/2],'s':[math.hypot(dx,dz)+.04,2.9,.10],'r':-math.atan2(dz,dx),'rx':0})
# Central pink entrance pier, narrow tall window, open door.
for x in [-1.08,1.08]:box('Central rose entrance pier',(x,3.12,6.94),(.32,6.24,.62),pink,.02,True)
box('Central entrance head',(0,4.30,6.94),(1.86,3.91,.62),pink,.02,True)
box('Entrance projecting canopy',(0,2.56,7.45),(2.60,.20,1.15),cream,.035)
box('Entrance tall slim window',(0,4.67,7.268),(.48,1.70,.015),glass,0)
for x in [-.31,.31]:box('Central window upright',(x,4.67,7.28),(.055,1.80,.04),silver,.002)
box('Entry door parked open',(-.84,1.19,6.13),(.065,2.30,1.4),oak,.014,True)
for z in [5.77,6.31]:box('Door inset',(-.798,1.23,z),(.017,1.75,.43),walnut,.008)
rod('Entry brass handle',(-.77,1.04,6.55),(-.77,1.27,6.55),.018,brass)
box('Front path',(0,-.016,8.78),(2.7,.13,3.7),stone,.01,True)
# Roof has two wings divided by a raised central band, solar arrays and rear turret.
g.GROUP='AgasaReference_Roof'
roof=prism('Closed curved double-wing roof',outline,6.23,6.45,cream,False);boolean_hole(roof,(0,6.4,-5.9),1.9)
box('Central rose roof link',(0,6.44,.10),(1.20,.18,11.30),pink,.02)
for x in [-1.42,1.42]:box('Roof spine raised white edging',(x,6.60,.05),(.24,.43,11.5),cream,.022)
box('Broad rose valley between rounded roof wings',(0,6.49,.08),(2.60,.05,11.20),pink,.01)
for side in [-1,1]:
 box('Roof solar panel frame',(side*4.0,6.58,.25),(3.6,.13,5.65),silver,.014)
 for ix in range(5):
  for iz in range(8):box('Real individual solar cell',(side*4.0+(ix-2)*.68,6.66,.25+(iz-3.5)*.67),(.64,.045,.63),solar,.005)
# Rear round tower houses a continuous stair both above and below ground.
g.GROUP='AgasaReference_Tower'
for low,high in [(BASE,0),(.06,6.65),(6.8,8.38)]:
 for i in range(72):
  a=tau*i/72;b=tau*(i+1)/72;mid=(a+b)/2
  if low<1 and math.radians(50)<mid<math.radians(155):continue
  p=[(2.40*cos(a),-5.9+2.40*sin(a)),(2.40*cos(b),-5.9+2.40*sin(b)),(2.18*cos(b),-5.9+2.18*sin(b)),(2.18*cos(a),-5.9+2.18*sin(a))]
  prism('Real cylindrical rear stair tower wall',p,low,high,cream,True)
ring('Turret cap cornice',TOWER,0,2.48,8.32,8.53,cream,collision=False)
ell('Rear silver observation dome',(0,8.46,-5.9),(2.16,1.55,2.16),silver)
rod('Rear aerial mast',(0,9.8,-5.9),(0,10.50,-5.9),.022,dark)
# Rear turret dome is visual; closed slab at roof level keeps upper play area sheltered.
g.GROUP='AgasaReference_Stair'
STAIR_ROUTES=[]
def stair_progress(t):return max(0,min(1,(t-1/12)/(10/12)))
for base,target,title in [(BASE,TFLOOR,'Basement to main'),(TFLOOR,UP,'Main to gallery')]:
 n=80;inner=.66;outer=2.10;vs=[]
 for rr in [inner,outer]:
  for j in range(n+1):a=pi/2+tau*j/n;y=base+(target-base)*stair_progress(j/n);vs.append((rr*cos(a),y,-5.9+rr*sin(a)))
 faces=[(j,j+1,n+1+j+1,n+1+j) for j in range(n)]
 ramp=mesh(title+' continuous helix collision',vs,faces,stone,True,recalc=False)
 # Visible treads describe the slope but never add duplicate staircase colliders.
 for j in range(24):
  a=pi/2+tau*j/24;b=pi/2+tau*(j+1)/24;y=base+(target-base)*stair_progress((j+.35)/24)
  ring(title+' stone tread',TOWER,inner,outer,y-.05,y,stone,a,b,4)
 for rr in [inner-.045,outer+.03]:line(title+' continuous handrail',[(rr*cos(pi/2+tau*j/80),base+(target-base)*stair_progress(j/80)+.89,-5.9+rr*sin(pi/2+tau*j/80)) for j in range(81)],.032,oak)
 for j in range(0,24,2):
  a=pi/2+tau*j/24;y=base+(target-base)*stair_progress(j/24);rod('Stair baluster',(outer*cos(a),y,-5.9+outer*sin(a)),(outer*cos(a),y+.88,-5.9+outer*sin(a)),.018,silver)
 STAIR_ROUTES.append({'name':title,'points':[[1.46*cos(pi/2+tau*j/20),base+(target-base)*stair_progress(j/20)+.025,-5.9+1.46*sin(pi/2+tau*j/20)] for j in range(21)],'expected_y':target})
for y in [BASE,TFLOOR,UP]:
 # The final/initial30-degree flats form a full60-degree landing, wide enough for bridge plus capsule.
 p=[(-.45,-4.44),(.45,-4.44),(.45,-3.36),(-.45,-3.36)]
 prism('Tower front level landing bridge visual',p,y-.13,y+.006,oak,False)
 mesh('Tower front level landing walk surface',[(x,y+.006,z) for x,z in p],[(3,2,1,0)],oak,True)
# Front rim guard leaves the70–110degree radial entrance open.
for i in range(8):
 a=math.radians(55+i*9);b=math.radians(55+(i+1)*9);rr=2.30
 if math.radians(65)<(a+b)/2<math.radians(114):continue
 p=(rr*cos((a+b)/2),TFLOOR+.49,-5.9+rr*sin((a+b)/2));box('Main stair opening protective rail panel',p,(rr*(b-a),.90,.035),silver,.005,True,angle=-(a+b)/2-pi/2)
 rod('Main stair opening top handrail',(rr*cos(a),TFLOOR+.98,-5.9+rr*sin(a)),(rr*cos(b),TFLOOR+.98,-5.9+rr*sin(b)),.032,oak)
# Peripheral upper gallery: continuous ring with open central volume.
g.GROUP='AgasaReference_Gallery'
for i in range(96):
 a=tau*i/96;b=tau*(i+1)/96
 if i in range(65,79):continue
 p=[(8.48*cos(a),6.47*sin(a)),(8.48*cos(b),6.47*sin(b)),(6.70*cos(b),4.73*sin(b)),(6.70*cos(a),4.73*sin(a))]
 prism('Upper circular perimeter gallery',p,UP-.17,UP,oak,True)
 for aa in [a]:rod('Gallery vertical baluster',(6.70*cos(aa),UP,4.73*sin(aa)),(6.70*cos(aa),UP+.95,4.73*sin(aa)),.017,silver)
 line('Gallery handrail',[(6.70*cos(a),UP+.97,4.73*sin(a)),(6.70*cos(b),UP+.97,4.73*sin(b))],.031,oak)
rearbridge=box('Rear gallery bridge with open stair headroom',(0,UP-.085,-4.55),(8.4,.17,1.55),oak,0,True);boolean_hole(rearbridge,(0,UP,-5.9),2.40)
box('Gallery bridge in front of stair headroom',(0,UP-.085,-3.0),(11.4,.17,.9),oak,.012,True)
for x in [-3.10,3.10]:box('Gallery side bridge link',(x,UP-.085,-3.68),(.95,.17,1.65),oak,.012,True)
# Four tall room posts frame the central kitchen and curved book-lined walls.
g.GROUP='AgasaReference_Hall'
for x,z in [(-6,-2.5),(-6,3.25),(6,-2.5),(6,3.25)]:
 cyl('Full-height structural post',(x,3.12,z),.19,6.13,cream,24,True)
 for y in [.30,3.13,6.04]:cyl('Column collar',(x,y,z),.24,.10,silver,24)
# Reference furniture shares one coordinate plan and scale. The central kitchen
# has a visible service opening; paired beds face the entry instead of rotating
# one sleeping area sideways into the counter zone.
fm=furniture.palette()
KC=furniture.kitchen(fm)
furniture.bedroom(fm)
# Bathroom occupies the upper-left sector shown in the supplied plan. The doorway is real.
g.GROUP='AgasaReference_Bathroom'
for p,s in [((-5.82,1.33,-4.14),(.13,2.54,2.75)),((-2.90,1.33,-4.94),(.13,2.54,1.15)),((-4.65,1.33,-2.77),(2.34,2.54,.13)),((-3.10,2.33,-2.77),(.80,.54,.13))]:box('Bathroom privacy wall beside door',p,s,white,.01,True)
box('Bathroom pale tiled floor',(-4.45,.08,-4.1),(2.64,.04,2.54),white,.01)
box('Bathroom bathtub base',(-5.1,.39,-4.37),(1.14,.61,1.81),white,.15,True)
box('Bathroom tub water recess',(-5.1,.705,-4.37),(.85,.014,1.46),glass,.14)
rod('Tub brass tap',(-5.63,.82,-4.72),(-5.20,.82,-4.72),.026,silver)
box('Bathroom small sink cabinet',(-3.65,.47,-4.99),(.9,.79,.62),cream,.035,True)
ell('Bathroom ceramic basin',(-3.65,.91,-4.96),(.48,.10,.33),white)
box('Bathroom mirror',(-3.65,1.63,-5.31),(.76,.82,.025),silver,.018)
label('浴室',(-3.10,2.17,-2.682),.12,silver)
# The two facing sofas, set-in coffee table and book-filled cabinets read as
# complete furniture assemblies rather than unrelated primitive placeholders.
furniture.living(fm)
furniture.bookcases(fm)
# Real underground work spaces. Coordinate depth is explicit; external terrain hole supplied separately.
g.GROUP='AgasaReference_Basement'
prism('Basement actual tiled floor',[(-7,-8.50),(7,-8.50),(7,3.5),(-7,3.5)],BASE-.20,BASE,tile,True)
for p,s in [((0,BASE+1.45,3.5),(14,2.9,.22)),((-7,BASE+1.45,-2.5),(.22,2.9,12.0)),((7,BASE+1.45,-2.5),(.22,2.9,12.0)),((0,BASE+1.45,-8.50),(14,2.9,.22))]:box('Cellar continuous enclosing wall',p,s,stone,.012,True)
ceiling=prism('Basement opaque ceiling below terrain underside',[(-7,-8.50),(7,-8.50),(7,3.5),(-7,3.5)],-.56,-.48,stone,False);boolean_hole(ceiling,(0,0,-5.9),2.40)
# Partition laboratory from invention workshop with a true 1.3 m doorway.
for x,w in [(-4.65,4.7),(3.35,7.3)]:box('Research partition beside doorway',(x,BASE+1.47,-.55),(w,2.94,.15),white,.008,True)
box('Research doorway lintel',(-1.8,BASE+2.69,-.55),(1.3,.48,.15),white,.006,True)
for x in [-2.50,-1.11]:box('Research doorway frame',(x,BASE+1.15,-.55),(.065,2.30,.20),silver,.004)
# Grid joints are geometry atop the cellar floor; sparse enough for mobile draw budget.
for x in range(-7,8):box('Cellar tile joint',(x,BASE+.003,-2.5),(.013,.007,12.0),stone,.001)
for z in range(-8,4):box('Cellar tile joint',(0,BASE+.004,z),(14,.007,.013),stone,.001)
# Reuse Blender-authored workshop detail, never a Tripo building or picture backdrop.
g.GROUP='AgasaReference_Laboratory'
legacy=OUT/'originals/agasa-lab-source.blend'
if not clay and not legacy.exists():raise RuntimeError('Restore the archived originals/agasa-lab-source.blend source subassembly before building a detailed release.')
if not clay and legacy.exists():
 with bpy.data.libraries.load(str(legacy),link=False) as (a,b):b.objects=list(a.objects)
 kept=[]
 for o in b.objects:
  if o and str(o.get('batch','')).startswith('Agasa_Laboratory'):
   bpy.context.scene.collection.objects.link(o);o.parent=None;o.location.z+=BASE;o.location.y-=2.35;o.location.x-=2.0;o['group']='AgasaReference_Lab_instruments';o['collision']=False;g.OBJECTS.append(o);kept.append(o)
 for o in b.objects:
  if o and o not in kept:bpy.data.objects.remove(o,do_unlink=True)
 print('Reused original Blender lab detail',len(kept),flush=True)
# Furniture and safe colliders are authored independently of reused small equipment.
for x,z,w in [(-4.7,2.72,3.1),(3.9,2.72,4.0),(4.6,-5.5,3.6)]:
 box('Research workbench',(x,BASE+.83,z),(w,.08,.77),white,.024,True)
 for xx in [x-w*.43,x+w*.43]:box('Research desk steel leg',(xx,BASE+.43,z),(.07,.82,.65),silver,.006)
for x,z in [(-4.25,2.6),(4.10,2.6)]:
 box('Research CRT monitor',(x,BASE+1.16,z),(.58,.56,.49),cream,.045);box('Research CRT screen',(x,BASE+1.17,z-.253),(.47,.37,.015),screen,.025)
 box('Research computer keyboard',(x,BASE+.89,z-.44),(.65,.04,.24),silver,.006)
 for i in range(12):
  for j in range(4):box('Computer individual key',(x+(i-5.5)*.043,BASE+.918,z-.51+j*.043),(.032,.011,.030),white,.002)
# Actual microscope, vial racks, tube storage and rolling chairs identify the research room.
for x,z in [(2.75,2.67),(-5.55,2.67)]:
 box('Microscope weighted base',(x,BASE+.91,z),(.44,.10,.35),white,.035)
 line('Microscope curved arm',[(x+.15,BASE+.94,z),(x+.15,BASE+1.38,z),(x,BASE+1.52,z-.04)],.045,silver)
 box('Microscope sample stage',(x,BASE+1.21,z),(.33,.06,.25),dark,.012)
 rod('Microscope optical barrel',(x,BASE+1.32,z-.09),(x-.035,BASE+1.58,z-.16),.055,white)
 rod('Microscope black eyepiece',(x-.035,BASE+1.58,z-.16),(x-.05,BASE+1.66,z-.19),.045,dark)
 cyl('Microscope focusing dial',(x+.15,BASE+1.30,z),.060,.15,dark,20)
 box('Test-tube rack',(x+.50,BASE+.97,z),(.36,.17,.25),oak,.007)
 for k in range(5):cyl('Glass sample tube',(x+.37+k*.065,BASE+1.10,z),.022,.29,glass,12)
for x,z in [(-4.3,1.50),(3.95,1.50),(4.8,-4.35)]:
 cyl('Research chair five-wheel pedestal',(x,BASE+.31,z),.045,.47,silver,16)
 cyl('Research chair seat',(x,BASE+.56,z),.34,.15,purple,28)
 box('Research chair padded back',(x,BASE+.95,z-.30),(.59,.49,.15),purple,.05)
 for i in range(5):
  a=i*tau/5;xx,zz=x+.38*cos(a),z+.38*sin(a);rod('Chair castor spoke',(x,BASE+.14,z),(xx,BASE+.10,zz),.025,silver)
  o=cyl('Chair small castor',(xx,BASE+.075,zz),.061,.048,dark,12);o.rotation_euler.x=pi/2
R['colliders'].append({'p':[-4.45,BASE+.43,-3.35],'s':[4.35,.86,1.55],'r':0,'rx':0})
for x in [-5.8,-3.9,4.3,6.0]:
 box('Basement equipment rack',(x,BASE+1.13,-6.60),(1.25,2.22,.63),silver,.02,True)
 for j in range(5):
  box('Rack instrument drawer',(x,BASE+.33+j*.39,-6.23),(1.10,.32,.13),white,.012)
  for k in range(4):cyl('Rack instrument status dial',(x-.34+k*.21,BASE+.34+j*.39,-6.135),.027,.02,brass,12)
# Reference research-room wall furniture and lighting housings are visual only; QA geometry stays fixed.
g.GROUP='AgasaReference_Research_Detail'
for x in [-4.7,3.9]:
 for j in range(3):
  xx=x-.95+j*.92;box('Research fitted drawer cabinet',(xx,BASE+.38,2.76),(.81,.70,.62),blue,.012)
  for k in range(3):
   box('Laboratory shallow drawer front',(xx,BASE+.16+k*.22,2.428),(.74,.18,.034),white,.004);rod('Laboratory drawer recessed handle',(xx-.16,BASE+.17+k*.22,2.40),(xx+.16,BASE+.17+k*.22,2.40),.012,silver)
 box('Laboratory upper open shelf',(x,BASE+2.02,3.05),(3.02,.075,.53),silver,.008)
 for xx in [x-1.38,x+1.38]:rod('Laboratory shelf bracket',(xx,BASE+1.73,3.37),(xx,BASE+1.99,2.81),.025,silver)
 for k in range(9):
  xx=x-1.17+k*.28
  if k%3==0:
   box('Archive binder',(xx,BASE+2.26,3.03),(.18,.40,.29),bookm[k%len(bookm)],.005);box('Archive binder cream label',(xx,BASE+2.29,2.878),(.10,.11,.012),pages,.002)
  else:
   cyl('Reagent bottle body',(xx,BASE+2.17,3.02),.063,.26,glass if k%2 else blue,16);cyl('Reagent bottle cap',(xx,BASE+2.315,3.02),.056,.035,dark,16);box('Reagent bottle paper label',(xx,BASE+2.19,2.955),(.080,.095,.006),pages,.003)
 box('Basement ventilation grille frame',(x,BASE+2.36,3.362),(1.8,.22,.036),silver,.006)
 for k in range(22):box('Basement ventilation slat',(x-.80+k*.076,BASE+2.36,3.335),(.022,.17,.026),dark,.001)
for x,z in [(-3,1.22),(3,1.22),(-3,-4.1),(3,-4.1)]:
 box('Ceiling fluorescent fixture housing',(x,BASE+2.45,z),(2.10,.15,.47),silver,.012)
 for zz in [z-.10,z+.10]:rod('White fluorescent tube',(x-.90,BASE+2.35,zz),(x+.90,BASE+2.35,zz),.04,white)
for x,z in [(-3.4,2.71),(5.40,2.71)]:
 for h in [0,.12,.24]:
  box('Stacked instrument sample tray',(x,BASE+.94+h,z),(.38,.045,.36),silver,.005)
  for xx in [x-.18,x+.18]:box('Sample tray raised rim',(xx,BASE+.985+h,z),(.018,.10,.36),white,.002)
box('Research notes cork board',(-.50,BASE+1.78,3.365),(2.45,1.18,.045),oak,.006)
for j in range(7):
 x=-1.40+(j%4)*.56;y=BASE+1.52+(j//4)*.50;box('Pinned experiment note',(x,y,3.329),(.43,.36,.012),pages,.004)
 for k in range(4):box('Handwritten note rule',(x,y-.10+k*.058,3.32),(.28-random.random()*.07,.009,.005),blue,0)
for x,z in [(3.07,2.50),(-5.87,2.49)]:
 for k in range(3):cyl('Small reagent dish',(x+k*.13,BASE+.88,z),.05,.018,glass,16)

# Compact garage attached behind right wing, explicit pedestrian doorway and raised shutter.
g.GROUP='AgasaReference_Garage'
box('Rear garage foundation',(10.63,-.06,-3.72),(5.17,.20,6.7),stone,.02,True)
for p,s in [((8.05,1.45,-4.95),(.18,2.9,4.30)),((8.05,1.45,-.64),(.18,2.9,.52)),((8.05,2.62,-1.85),(.18,.56,1.90)),((13.20,1.45,-3.72),(.18,2.9,6.7)),((8.92,1.45,-.38),(1.56,2.9,.18)),((12.05,1.45,-.38),(2.3,2.9,.18)),((10.28,2.55,-.38),(1.2,.70,.18))]:box('Garage rendered wall beside true pedestrian entrance',p,s,cream,.01,True)
box('Garage side pedestrian approach',(9.90,-.015,1.45),(2.1,.13,3.5),stone,.01,True)
box('Garage flat roof',(10.63,2.96,-3.72),(5.45,.22,7.0),cream,.025,True)
for x in [8.43,12.82]:box('Garage rear opening jamb',(x,1.39,-7.05),(.76,2.78,.22),cream,.01,True)
box('Garage shutter upper header',(10.63,2.70,-7.05),(3.64,.40,.22),cream,.01,True)
for z in [-6.9,-6.45,-6.0,-5.55]:box('Garage retracted shutter rib',(10.63,2.57,z),(3.65,.045,.35),silver,.006)
box('Garage tool workbench',(12.64,.88,-3.6),(.74,.08,3.0),oak,.01,True)
for j in range(4):box('Garage stacked storage box',(12.59,.30+j*.42,-5.45),(.85,.38,.65),stone,.012)
for z in [-5.3,-4.3,-3.3]:
 for y in [.29,.64]:o=cyl('Garage spare tire',(8.56,y,z),.32,.20,dark,24);o.rotation_euler.x=pi/2
# Keep garage outside the round main facade; a short real passage joins the two doors.
for o in g.OBJECTS:
 if o.get('group')=='AgasaReference_Garage':o.location.x+=1.0
box('House to garage passage floor',(8.85,.005,-1.75),(1.55,.12,1.80),stone,.01,True)
box('House to garage covered passage',(8.85,2.51,-1.75),(1.55,.15,1.85),cream,.01)
for z in [-2.67,-.84]:box('House to garage passage side wall',(8.88,1.20,z),(1.55,2.4,.13),cream,.01,True)
# Garden boundary is continuous, with a clear central path and a rear car approach.
g.GROUP='AgasaReference_Garden'
lawn=box('Visible lawn around round house',(0,-.016,0),(22.2,.012,19.0),grass,0,False);boolean_hole(lawn,(0,0,-5.9),2.18)
for p,s in [((-11.2,.45,0),(.20,.90,19.2)),((11.2,.45,3.3),(.20,.90,7.6)),((-6.30,.45,9.6),(9.8,.90,.20)),((6.30,.45,9.6),(9.8,.90,.20))]:box('Low ivory plot boundary wall',p,s,cream,.022,True)
for p in [(-9.8,0,5.8),(8.6,0,7.0),(-9.9,0,-5.8)]:
 rod('Garden tree trunk',p,(p[0],4.4,p[2]),.19,bark)
 for dx,dy,dz in [(-.8,3.6,.2),(.7,4.1,.4),(0,4.8,-.4)]:
  center=Vector((p[0]+dx,dy,p[2]+dz));rod('Garden tree canopy branch',(p[0],2.8,p[2]),center,.07,bark)
  vv=[];ff=[]
  for k in range(170):
   a=random.random()*tau;t=random.uniform(-1,1);rad=random.random()**(1/3);c=center+Vector((1.35*rad*math.sqrt(1-t*t)*cos(a),rad*t,1.20*rad*math.sqrt(1-t*t)*sin(a)))
   u=Vector((cos(a),random.uniform(-.6,.6),sin(a)))*random.uniform(.14,.24);v=Vector((-sin(a),random.uniform(-.4,.4),cos(a)))*random.uniform(.065,.115);n=len(vv)
   vv.extend([tuple(c-u),tuple(c+v),tuple(c+u),tuple(c-v),tuple(c+Vector((0,.025,0)))]);ff.extend([(n,n+1,n+4),(n+1,n+2,n+4),(n+2,n+3,n+4),(n+3,n,n+4)])
  mesh('Volumetric individually modeled garden leaves',vv,ff,leaf if dx<0 else leaf2)
# Spatial contract, real walk routes and separate lighting zones.
R['rooms']=[{'name':'阿笠宅 · 浴室','p':[-3.18,.08,-3.32]},{'name':'阿笠宅 · 环形厨房','p':[-1.15,.08,3.10]},{'name':'阿笠宅 · 双床休息区','p':[-4.70,.08,2.20]},{'name':'阿笠宅 · 客厅','p':[4.25,.08,3.08]},{'name':'阿笠宅 · 圆塔楼梯','p':[0,.08,-3.45]},{'name':'阿笠宅 · 二楼环廊','p':[3.8,UP+.02,-4.50]},{'name':'阿笠宅 · 地下研究室','p':[-3.45,BASE+.02,1.08]},{'name':'阿笠宅 · 发明工作间','p':[2.8,BASE+.02,-3.22]},{'name':'阿笠宅 · 后车库','p':[11.5,.06,-5.0]}]
R['npcs']=[{'asset':'agasa','p':[.80,.08,3.40],'yaw':0},{'asset':'haibara','p':[-2.3,BASE+.02,1.6],'yaw':pi}]
R['routes']=[{'name':'front_to_round_kitchen','points':[[0,.08,8.3],[0,.08,5.7],[0,.08,3.25],[-1.3,.08,3.10],[-1.55,.08,3.10]],'expected_y':TFLOOR},{'name':'main_to_tower','points':[[0,.08,3.25],[1.95,.08,2.50],[1.95,.08,-2.80],[0,.08,-3.45],[0,.08,-4.44]],'expected_y':TFLOOR}]+STAIR_ROUTES
R['routes']+=[{'name':'cellar_to_research','points':[[0,BASE+.02,-4.44],[0,BASE+.02,-1.6],[-1.8,BASE+.02,-1.15],[-1.8,BASE+.02,.20],[-3.45,BASE+.02,1.08]],'expected_y':BASE}]
R['routes']+=[{'name':'living_to_garage','points':[[6.4,.08,2.1],[7.25,.08,-1.65],[8.85,.08,-1.65],[10.3,.08,-1.65],[11.5,.06,-5.0]],'expected_y':.06}];R['lights']=[{'name':'Bathroom diffuse','p':[-4.15,2.30,-4.1],'energy':.55,'range':3.0,'color':'eef2ef'},{'name':'Living indirect','p':[4,3.7,.7],'energy':1.0,'range':7,'color':'f3f1e7'},{'name':'Kitchen diffuse','p':[-1.6,4.5,.2],'energy':.95,'range':6.5,'color':'f6f1df'},{'name':'Beds and library fill','p':[-5,2.7,.8],'energy':.70,'range':5,'color':'edf2f0'},{'name':'Gallery fill','p':[0,5.35,-3.7],'energy':.65,'range':7,'color':'eef2ef'},{'name':'Cellar workshop soft light','p':[2,BASE+2.30,-3.6],'energy':1.10,'range':7,'color':'f0f2eb'},{'name':'Research room soft light','p':[-2,BASE+2.30,1.6],'energy':1.0,'range':7,'color':'eef2ef'},{'name':'Rear garage soft light','p':[11.5,2.5,-4.0],'energy':.9,'range':6,'color':'f2f1e6'}]
for lamp in R['lights']:lamp.update(shadow=False,attenuation=1.3)
R['views']=[{'name':'双圆弧住宅与花园','p':[22,13,22],'target':[0,3.5,0],'lens':42},{'name':'入口正立面','p':[.2,5.2,25],'target':[0,3.45,0],'lens':43},{'name':'后塔与车库','p':[-19,12,-21],'target':[1,3,-1],'lens':39},{'name':'中央环形厨房','p':[3.85,2.1,4.8],'target':[-1.15,1.3,-.1],'lens':23},{'name':'并列双床','p':[-3.5,1.8,3.45],'target':[-5.5,.87,-.1],'lens':30},{'name':'地下研究室','p':[.8,BASE+1.60,.12],'target':[-3.5,BASE+1.15,2.55],'lens':25}]
R['views']+=[{'name':'阿笠发明工作台','p':[-.65,BASE+1.65,-1.30],'target':[-4.3,BASE+1.3,-3.3],'lens':28},{'name':'后塔真实地下楼梯','p':[2.6,BASE+1.7,-3.05],'target':[0,BASE+1.65,-5.9],'lens':26},{'name':'后车库与屋内通道','p':[11.4,1.7,-9.0],'target':[11.2,1.1,-3.4],'lens':28}]
R['interior_zones']=[{'name':'main','min':[-8.8,0,-7.8],'max':[8.8,6.4,7.2]},{'name':'basement','min':[-7,BASE-.2,-8.6],'max':[7,0,3.6]},{'name':'garage','min':[8.4,-.15,-7.2],'max':[14.3,3.1,-.2]}]
R['notes']={'source':'Blender native geometry, original Blender instrument subassemblies reused','references':'User images 3,6,9–12 and https://felicia1012.pixnet.net/blog/posts/14219272223','dimensions':'Inferred production dimensions, not a surveyed or official scale plan.','floor_levels':[BASE,TFLOOR,UP],'main_atrium_clear_height':6.17,'tower_stair_opening':{'center':[0,0,-5.9],'radius':2.18},'terrain_collision_cut_world':{'shape':'circle','center':[64,0,-12.9],'radius':2.18,'y_range':[-.4,.4]},'garage_beetle_position':[11.50,.065,-4.85],'glass':'Actual apertures, separate transparent glazing meshes, no whole-wall removal.'}
R['floor_levels']={'basement':BASE,'ground':TFLOOR,'gallery':UP};R['stair_hole']={'center':[0,0,-5.9],'radius':2.18,'world_center':[64,0,-12.9]};R['interactions']=[{'id':'agasa-kitchen','name':'环形料理台','position':[-1.15,.8,1.70]},{'id':'haibara-research','name':'研究记录','position':[-4.25,BASE+1.1,2.60]},{'id':'agasa-inventions','name':'发明工作台','position':[4.6,BASE+.9,-5.50]},{'id':'agasa-garage','name':'博士的车库','position':[11.50,.7,-5.7]}]
R['routes']+=[{'name': 'kitchen_to_living', 'points': [[-1.55, 0.08, 3.1], [0, 0.08, 3.25], [3.8, 0.08, 3.1], [5.55, 0.08, 3.05], [5.95, 0.08, 2.62], [6.4, 0.08, 2.1]], 'expected_y': 0.06}, {'name': 'gallery_bridge', 'points': [[0, 3.205, -4.44], [3.8, 3.205, -4.44]], 'expected_y': 3.18}, {'name': 'kitchen_work_aisle', 'points': [[1.95, 0.08, -2.8], [-0.15, 0.08, -2.65], [-0.75, 0.08, -1.5], [-0.5, 0.08, -0.4]], 'expected_y': 0.06}]
for rt in R['routes']:
 if rt['name']=='living_to_garage':rt['points'][-1]=[10.10,.06,-5.8]
for room in R['rooms']:
 if '车库' in room['name']:room['p']=[10.10,.06,-5.8]
R['notes']['garage_beetle_yaw']=0
for rt in R['routes']:
 if rt['name']=='kitchen_work_aisle':rt['points']=[[1.95,.08,-2.8],[1.95,.08,2.50],[0,.08,3.25],[-1.15,.08,2.60],[-1.15,.08,1.30],[-.26,.08,.08]]
 if rt['name']=='main_to_tower':rt['points']=[[0,.08,3.25],[1.95,.08,2.50],[1.95,.08,-2.80],[0,.08,-3.0],[0,.08,-3.45],[0,.08,-4.44]]
 if rt['name']=='gallery_bridge':rt['points']=[[0,UP+.026,-4.44],[0,UP+.026,-3.0],[5.30,UP+.026,-3.0]]
R['routes']=[rt for rt in R['routes'] if rt['name']!='gallery_perimeter']
# Follow the real gallery, with outer detours around the two front structural columns.
# The missing rear sector is replaced by the real front/side bridge arrangement.
perimeter=[]
for a in range(-30,241,15):
 perimeter.append([7.55*cos(math.radians(a)),UP+.026,5.58*sin(math.radians(a))])
 if a==30:perimeter.extend([[6.68,UP+.026,3.15],[6.50,UP+.026,3.70]])
 if a==135:perimeter.extend([[-6.50,UP+.026,3.70],[-6.68,UP+.026,3.15]])
R['routes'].append({'name':'gallery_perimeter','points':[[5.30,UP+.026,-3.0],[6.55,UP+.026,-2.84]]+perimeter+[[-4.20,UP+.026,-4.44],[-3.1,UP+.026,-4.44],[-3.1,UP+.026,-3.0],[0,UP+.026,-3.0],[0,UP+.026,-4.44]],'expected_y':UP})
R['notes']['stair_connection']='Each spiral turn has first/last30degrees at the level landing; remaining300degrees rise continuously. Front radial bridge fits landing with full capsule clearance. Rear gallery radius2.40 headroom opening.'
R['notes']['basement_clear_height']=2.56
R['notes']['furniture_revision']='2026-09-13: paired beds share head wall and face entry; circular kitchen opening faces front with 1.3m clear gap; fitted shelf contents, sofa cushions and coffee service follow reference assemblies.'
R['notes']['furniture_clearances']={'kitchen_front_opening_m':1.3,'kitchen_inner_radius_m':1.27,'extractor_base_radius_m':.48,'bed_between_gap_m':.23,'bed_foot_access_depth_m':1.3}
R['views'] += [{'name':'客厅成套家具','p':[1.7,1.75,3.8],'target':[4.15,.85,.50],'lens':30},{'name':'厨房料理细节','p':[-.3,1.65,2.32],'target':[-1.55,1.2,-.6],'lens':30},{'name':'双床与书柜细节','p':[-5.0,1.45,2.58],'target':[-5.40,1.0,-1.0],'lens':32}]

(OUT/'agasa.json').write_text(json.dumps(R,ensure_ascii=False,indent=2))
setup_render()
for li in R['lights']:
 d=bpy.data.lights.new(li['name'],'AREA');d.energy=100 if li['p'][1]>0 else 160;d.shape='DISK';d.size=2.0;o=bpy.data.objects.new(li['name'],d);S.collection.objects.link(o);o.location=G(li['p'])
# Export does not include review lights/cameras. The editable source does include the same building.
stats=export_asset('agasa');(OUT/'agasa-build-report.json').write_text(json.dumps(stats,indent=2))
for im in bpy.data.images:
 if im.source=='FILE' and im.size[0]>0:
  try:im.pack()
  except:pass
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'agasa-reference.blend'))
if '--render' in sys.argv:render_views(R['views'][:4] if clay else R['views'],ROOT.parents[1]/'outputs/柯南与移动端升级/建筑灰模证据' if clay else ROOT/'docs/evidence/conan-architecture/agasa',grey=clay)
print('AGASA_REFERENCE_DONE',stats,flush=True)
