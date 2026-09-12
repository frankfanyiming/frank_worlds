"""Connected Mouri commercial block. New source, context kept separate from playable Mouri."""
import sys,math,json,random,bpy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));import reference_geometry as g
from reference_geometry import *
S=init();clay='--grey' in sys.argv
plasters=[mat('BeikaRow facade '+str(i),h,.85) for i,h in enumerate(['c6c7bd','d6c184','b1bbb7','d1cfc1','a8b9b4','b6a18e','b5bfc5'])]
concrete=mat('BeikaRow concrete coping','b7bcb4',.89);dark=mat('BeikaRow iron charcoal','374b51',.47,.2);metal=mat('BeikaRow silver frames','899796',.42,.65);glass=mat('BeikaRow dark blue window Glass','547078',.18,0,.80);glasslit=mat('BeikaRow cream shop glazing Glass','b3b7a5',.19,0,.46);wood=mat('BeikaRow Iroha stained cedar','695846');cream=mat('BeikaRow enamel sign ivory','e4e2cb',.62);navy=mat('BeikaRow Iroha blue noren cloth','40536d',.94);red=mat('BeikaRow burgundy awning','784d51',.9);green=mat('BeikaRow sage awning','758271',.93);roofmat=mat('BeikaRow ceramic blue roof tiles','425157',.68);brick=mat('BeikaRow brown brick planter','79604b');soil=mat('BeikaRow potting soil','554d3c');leaf=mat('BeikaRow shop plants','456647');paper=mat('BeikaRow shop paper notices','d3cba9');black=mat('BeikaRow black painted lettering','29373b');R={'origin':[7.8,0,-3.4],'yaw':pi/2,'colliders':[],'lights':[],'windows':[],'rooms':[],'views':[],'routes':[],'replaces_world_regions':[]}

def window(x,y,w,h,z=.052,m=glass):
 box('Inset window dark reveal',(x,y,z-.04),(w+.11,h+.12,.115),dark,.004)
 box('Actual recessed glazing',(x,y,z+.025),(w-.06,h-.06,.028),m,0)
 for xx in [x-w/2,x,x+w/2]:box('Thin aluminum window mullion',(xx,y,z+.055),(.045,h+.08,.048),metal,.002)
 for yy in [y-h/2,y+h/2]:box('Window head and sill',(x,yy,z+.055),(w+.08,.048,.05),metal,.002)
 box('Projecting window sill',(x,y-h/2-.05,z+.15),(w+.22,.09,.30),concrete,.008)

def aircon(x,y,z=.22):
 box('Outdoor AC cabinet',(x,y,z),(.81,.54,.38),concrete,.022)
 for j in range(11):box('AC horizontal grille',(x-.15,y-.20+j*.04,z+.205),(.42,.012,.03),dark,.001)
 o=cyl('AC circular fan rim',(x+.24,y,z+.21),.17,.025,metal,20);o.rotation_euler.x=pi/2
 for a in range(6):
  aa=a*tau/6;rod('AC fan blade',(x+.24,y,z+.24),(x+.24+.12*cos(aa),y+.12*sin(aa),z+.24),.015,dark)
 line('Exposed AC conduit',[(x-.49,y-.02,z-.10),(x-.62,y-.13,z-.10),(x-.62,y-.70,.04)],.022,cream)

def roof_details(cx,w,d,h,index):
 for xx in [cx-w/2+.12,cx+w/2-.12]:box('Roof side parapet',(xx,h+.28,-d/2),(.16,.59,d),concrete,.01)
 for zz in [-.05,-d+.05]:box('Roof front rear parapet',(cx,h+.28,zz),(w,.59,.16),concrete,.01)
 for i in range(int(w/.5)):
  x=cx-w/2+.2+i*.5;rod('Roof front guardrail',(x,h+.52,-.02),(x,h+1.01,-.02),.012,metal)
 rod('Continuous rooftop rail',(cx-w/2,h+1.03,-.02),(cx+w/2,h+1.03,-.02),.022,metal)
 box('Roof stair-head service room',(cx-.2,h+1.0,-d*.68),(w*.42,2.0,2.5),plasters[index%len(plasters)],.02,True)
 box('Roof stair door',(cx-.2,h+.9,-d*.68+1.262),(.78,1.79,.045),dark,.005)
 if index%2==0:
  for xx in [-.6,.6]:
   for zz in [-.5,.5]:rod('Water tank steel legs',(cx+xx,h,-3.2+zz),(cx+xx,h+1.18,-3.2+zz),.04,metal)
  cyl('Rooftop round water tank',(cx,h+1.89,-3.2),.92,1.39,concrete,32)
  cyl('Rooftop water tank lid',(cx,h+2.62,-3.2),.98,.10,metal,32)
  line('Tank outlet pipe',[(cx+.8,h+1.44,-3.2),(cx+1.12,h+1.44,-3.2),(cx+1.12,h+.25,-3.2)],.046,metal)
 else:
  box('Roof ventilation unit',(cx+1.1,h+.48,-3),(1.4,.95,1.2),metal,.025)
  for j in range(12):box('Rooftop equipment grille',(cx+1.1,h+.84,-3.56+j*.10),(1.14,.06,.025),dark,.001)
 rod('TV antenna mast',(cx-w*.34,h,-d+.8),(cx-w*.34,h+2.5,-d+.8),.025,dark)
 for i in range(5):rod('TV antenna elements',(cx-w*.34-.52,h+1.6+i*.17,-d+.8),(cx-w*.34+.52,h+1.6+i*.17,-d+.8),.014,metal)

def module(x0,x1,h,d,index,shop,awning):
 cx=(x0+x1)/2;w=x1-x0;g.GROUP='ConnectedBlock_'+str(index)
 box('Contiguous urban building shell',(cx,h/2,-d/2),(w,h,d),plasters[index%len(plasters)],.016,True)
 # Finished party-wall widths directly abut their neighbors, with no suburban lawn gaps.
 for y in [2.90,h-.10]:box('Facade thin concrete band',(cx,y,.065),(w+.04,.15,.16),concrete,.008)
 floors=round(h/3.0);cols=max(2,int(w/2.0));ww=(w-.9)/cols-.22
 for f in range(1,floors):
  yy=f*3.0+1.48
  if yy+h*.0>h-.75:continue
  for j in range(cols):window(x0+.45+(j+.5)*(w-.9)/cols,yy,ww,1.42)
  if f%2==0:aircon(x1-.80,yy-.70)
 # Recessed storefront plane with door and individual frames.
 door=x1-.95;window(cx-.55,1.36,w-2.05,2.19,.13,glasslit);window(door,1.27,.89,2.28,.15,glasslit)
 rod('Shop door handle',(door+.26,.97,.255),(door+.26,1.32,.255),.018,metal)
 box('Store awning fascia',(cx,2.72,.41),(w-.18,.34,.58),awning,.016)
 # Actual fabric slope projects above sidewalk; all text is mesh, never an image panel.
 mesh('Shop sloping awning',[(x0+.10,2.9,.04),(x1-.10,2.9,.04),(x1-.10,2.62,.89),(x0+.10,2.62,.89)],[(0,1,2,3)],awning)
 label(shop,(cx,2.68,.724),min(.25,w/len(shop)*.7),cream)
 for j in range(3):box('Shop paper notice',(x0+.65+j*.3,1.26,.18),(.23,.32,.014),paper,.002)
 # Service items placed beside storefront, kept out of continuous sidewalk corridor.
 for xx in [x0+.26,x1-.26]:
  box('Small shop planter',(xx,.23,.43),(.34,.46,.43),brick,.012)
  for k in range(3):ell('Planter foliage',(xx+.08*cos(k*tau/3),.63,.43+.09*sin(k*tau/3)),(.18,.27,.18),leaf)
 roof_details(cx,w,d,h,index)

# Adjacent low Iroha is a characteristic recognisable neighbor, not an isolated shed in a lawn.
g.GROUP='IrohaSushi'
x0,x1=4.65,9.45;cx=(x0+x1)/2;d=11.5
box('Iroha upper connected body',(cx,4.65,-d/2),(4.8,3.40,d),plasters[2],.014,True)
for p,s in [((x0+.09,1.43,-5.7),(.18,2.86,11.4)),((x1-.09,1.43,-5.7),(.18,2.86,11.4)),((cx,1.43,-11.4),(4.8,2.86,.18)),((cx,2.78,-.02),(4.8,.34,.22))]:box('Iroha shop shell with real front opening',p,s,wood,.008,True)
box('Iroha raised shop floor',(cx,.035,-5.6),(4.8,.12,11.4),wood,.01,True)
# Closed traditional sliding slat doors, slightly inset behind curtain.
for j in range(30):box('Iroha wooden storefront vertical lattice',(x0+.14+j*.155,1.22,-.15),(.038,2.18,.07),wood,.004)
for y in [.16,.86,1.66,2.34]:box('Iroha horizontal sliding door frame',(cx,y,-.11),(4.7,.045,.075),wood,.004)
for j in range(6):box('Iroha split blue noren panel',(x0+.40+j*.79,2.16,.10),(.75,.67,.035),navy,.015)
label('い ろ は 寿 し',(cx,2.18,.13),.28,cream)
for xx in [x0+.65,x1-.65]:window(xx,4.70,1.05,1.53)
# True tiled small eave in front of upper floor; stepped overlapping rows, curved cap ridges.
for row in range(5):
 z=-.08+row*.21;y=3.30-row*.17
 for j in range(21):
  x=x0+.02+j*.235
  box('Iroha individual ceramic eave tile',(x,y,z),(.23,.065,.26),roofmat,.01)
  rod('Iroha curved tile ridge',(x,y+.047,z-.11),(x,y+.047,z+.13),.035,roofmat)
box('Iroha hanging sign bracket',(x1-.34,4.58,.45),(.05,2.64,.07),metal,.004)
box('Iroha vertical ivory sign',(x1-.35,4.62,.54),(.43,2.34,.13),cream,.025)
label('い\nろ\nは\n寿\nし',(x1-.35,4.62,.616),.26,black)
box('Iroha exterior menu board',(x0+.32,.92,.43),(.45,1.42,.08),cream,.012)
label('にぎり\nちらし\n営業中',(x0+.32,.93,.485),.13,black)
roof_details(cx,4.8,d,6.36,6)
# Compact bar interior is physical geometry behind the facade, no photo backdrop.
box('Iroha sushi counter',(cx,1.05,-3.5),(3.4,.15,.68),wood,.024,True)
for j in range(5):cyl('Iroha counter stool',(cx-1.38+j*.69,.48,-2.74),.26,.82,wood,20)

for item in [(-27,-19.4,12.1,13,0,'米花写真',red),(-19.4,-11.8,9.1,12.0,1,'BOOKS',green),(-11.8,-4.65,12.2,11.8,2,'喫茶・洋菓子',red),(9.45,16.25,12.1,12.5,3,'米花薬局',green),(16.25,24.25,9.1,13.0,4,'小林文具',red),(24.25,31.8,15.1,12.8,5,'BEIKA',green)]:module(*item)
# One clean sidewalk strip across the block, matching the existing street plane, not across the roadway.
g.GROUP='ConnectedBlock_Sidewalk'
for a,b in [(-27,-4.65),(4.65,31.8)]:
 box('Continuous storefront sidewalk',(a/2+b/2,-.015,.75),(b-a,.15,1.5),concrete,.008,True)
 for i in range(int((b-a)/.75)+1):box('Sidewalk quiet paver joint',(a+i*.75,.064,.75),(.012,.006,1.46),metal,0)
R['notes']={'source':'Blender authored building geometry; original Mouri three-storey building preserved and loaded independently','scale':'Building heights, shop widths and street distances are inferred production proportions, not official survey coordinates.','references':['User references 1–2','https://felicia1012.pixnet.net/blog/posts/14219272223'],'mouri_adjacency':{'mouri_local_x':[-4.55,4.7],'iroha_local_x':[4.65,9.45],'poirot':'Mouri 1F','office':'Mouri 2F','residence':'Mouri 3F'},'geometry_contract':'All mesh vertices are local to original Mouri origin/yaw; Collision suffix is the only automatic trimesh collider source.'}
R['views']=[{'name':'毛利与连续商铺街区','p':[39,22,36],'target':[1,5.6,-4],'lens':38},{'name':'事务所紧邻伊吕波寿司','p':[15.8,5.2,15.8],'target':[4.2,4.25,0],'lens':35},{'name':'连排街区正面','p':[.2,10.5,58],'target':[1.5,5,-3],'lens':40}]
R['replaces_world_regions']=[{'name':'Mouri commercial frontage existing District components','min':[-6.1,-.1,-35.2],'max':[7.9,18,23.6]}]
R['routes']=[{'name':'continuous_commercial_sidewalk','points':[[x,.20,1.2] for x in [-24,-15,-7,0,7,15,24]],'expected_y':.06}]
(OUT/'street-block.json').write_text(json.dumps(R,ensure_ascii=False,indent=2))
stats=export_asset('street-block');(OUT/'street-block-build-report.json').write_text(json.dumps(stats,indent=2))
setup_render();bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'street-block.blend'))
# Original Mouri is review context only and intentionally absent from new GLB and source OBJECTS.
if '--render' in sys.argv:
 bpy.ops.import_scene.gltf(filepath=str(ROOT/'worlds/conan/web-project/assets/buildings/mouri.glb'))
 render_views(R['views'],ROOT.parents[1]/'outputs/柯南与移动端升级/建筑灰模证据/毛利连排街区' if clay else ROOT/'docs/evidence/conan-architecture/mouri',grey=clay)
print('MOURI_BLOCK_DONE',stats,flush=True)
