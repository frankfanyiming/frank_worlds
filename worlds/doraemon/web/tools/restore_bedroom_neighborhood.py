"""Reference-led neighborhood revision. Run with Blender --background --python this_file.
Keeps the existing town, trees, character rigs and gameplay; replaces four buildings.
Horizontal coordinates use Blender X/Y, height Z. Metres.
"""
import bpy, math, json, random, bmesh
from pathlib import Path
from mathutils import Vector
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'public/models';random.seed(1109)
def clear():
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
clear(); groups=defaultdict(list);colliders=[];G='';mats={}
def mat(name,color,rough=.65,metal=0):
 m=bpy.data.materials.new('V11_'+name);m.diffuse_color=(*color,1);m.use_nodes=True;n=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');n.inputs['Base Color'].default_value=(*color,1);n.inputs['Roughness'].default_value=rough;n.inputs['Metallic'].default_value=metal;mats[name]=m;return m
for n,c in {'plaster':(.86,.80,.68),'white':(.94,.93,.85),'wood':(.40,.23,.11),'floor':(.65,.43,.23),'trim':(.28,.19,.12),'roof':(.48,.15,.10),'orangeRoof':(.66,.27,.08),'slate':(.28,.32,.32),'tatami':(.55,.63,.32),'tatamiEdge':(.25,.35,.18),'green':(.25,.43,.23),'glass':(.39,.66,.72),'metal':(.18,.21,.21),'yellow':(.91,.66,.18),'cream':(.91,.85,.66),'pink':(.71,.39,.39),'red':(.72,.055,.035),'blue':(.03,.43,.66),'black':(.035,.028,.021),'tile':(.37,.63,.65),'sofa':(.61,.32,.28),'paper':(.93,.89,.77),'linen':(.85,.81,.67),'leaf':(.19,.35,.10),'leafLight':(.36,.49,.13)}.items():mat(n,c,.27 if n in ['glass','tile'] else .7,.3 if n=='metal' else 0)
# A compact existing timber texture, already authored for this world.
for n in ['wood','floor','trim']:
 path=ROOT/'public/textures/wood_basecolor.png'
 if path.exists():
  im=bpy.data.images.load(str(path),check_existing=True);im.scale(256,256);im.pack();m=mats[n];tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;mix=m.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[2].default_value=(.45,.31,.20,1) if n=='trim' else (.64,.46,.29,1) if n=='wood' else (.84,.67,.45,1);m.node_tree.links.new(tex.outputs['Color'],mix.inputs[1]);m.node_tree.links.new(mix.outputs[0],next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Base Color'])
cache={}
def box(name,x,y,z,w,d,h,material='wood',bevel=.01,solid=False):
 key=(round(w,5),round(d,5),round(h,5),material,bevel)
 if key not in cache:
  bm=bmesh.new();bmesh.ops.create_cube(bm,size=1)
  for v in bm.verts:v.co.x*=w;v.co.y*=d;v.co.z*=h
  if bevel:bmesh.ops.bevel(bm,geom=list(bm.edges),offset=min(bevel,min(w,d,h)/3),segments=2,affect='EDGES')
  me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();me.materials.append(mats[material]);uv=me.uv_layers.new(name='UVMap')
  for f in me.polygons:
   axis=max(range(3),key=lambda a:abs(f.normal[a]));a,b=[i for i in range(3) if i!=axis]
   for li in f.loop_indices:v=me.vertices[me.loops[li].vertex_index].co;uv.data[li].uv=(v[a],v[b])
  cache[key]=me
 o=bpy.data.objects.new(name,cache[key]);bpy.context.collection.objects.link(o);o.location=(x,y,z);groups[G].append(o)
 if solid:colliders.append(dict(x=x,y=y,z=z,w=w,d=d,h=h,group=G))
 return o
sphere_cache={}
def ell(name,x,y,z,sx,sy,sz,material='white'):
 if material not in sphere_cache:
  bm=bmesh.new();bmesh.ops.create_uvsphere(bm,u_segments=16,v_segments=10,radius=1);me=bpy.data.meshes.new(name);bm.to_mesh(me);bm.free();me.materials.append(mats[material]);
  for p in me.polygons:p.use_smooth=True
  sphere_cache[material]=me
 o=bpy.data.objects.new(name,sphere_cache[material]);bpy.context.collection.objects.link(o);o.location=(x,y,z);o.scale=(sx,sy,sz);groups[G].append(o);return o
def rod(name,a,b,r=.025,material='metal'):
 a,b=Vector(a),Vector(b);bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=r,depth=(b-a).length,location=(a+b)/2);o=bpy.context.object;o.name=name;o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler();o.data.materials.append(mats[material]);groups[G].append(o);return o
def text(label,x,y,z,size=.2,material='trim'):
 cu=bpy.data.curves.new(label,'FONT');cu.body=label;cu.align_x='CENTER';cu.size=size;cu.extrude=.001
 for path in ['/System/Library/Fonts/STHeiti Medium.ttc','/System/Library/Fonts/PingFang.ttc']:
  if Path(path).exists():cu.font=bpy.data.fonts.load(path);break
 o=bpy.data.objects.new(label,cu);bpy.context.collection.objects.link(o);o.location=(x,y,z);o.rotation_euler=(math.pi/2,0,0);cu.materials.append(mats[material]);groups[G].append(o);return o

def floor(x0,x1,y0,y1,z,material='floor'):
 box('floor', (x0+x1)/2,(y0+y1)/2,z-.065,x1-x0,y1-y0,.13,material,.01)
 if material=='floor':
  for i in range(int((y1-y0)/.28)):box('timber joint',(x0+x1)/2,y0+i*.28,z+.001,x1-x0,.007,.003,'trim',0)
 if material=='tile':
  for x in range(int((x1-x0)/.35)+1):box('grout',x0+x*.35,(y0+y1)/2,z+.002,.009,y1-y0,.003,'white',0)
  for y in range(int((y1-y0)/.35)+1):box('grout',(x0+x1)/2,y0+y*.35,z+.002,x1-x0,.009,.003,'white',0)
def tatami(x0,x1,y0,y1,z):
 floor(x0,x1,y0,y1,z,'tatami')
 for x in [x0+.025,(x0+x1)/2,x1-.025]:box('woven rush binding',x,(y0+y1)/2,z+.008,.035,y1-y0,.015,'tatamiEdge',.003)
 for y in [y0+.02,(y0+y1)/2,y1-.02]:box('mat seam',(x0+x1)/2,y,z+.008,x1-x0,.028,.015,'tatamiEdge',.003)
 for i in range(int((y1-y0)/.035)):box('rush weave',(x0+x1)/2,y0+i*.035,z+.002,x1-x0,.004,.003,'cream',0)
def wall(x0,x1,y0,y1,z,h=2.48):
 box('plaster wall',(x0+x1)/2,(y0+y1)/2,z+h/2,x1-x0,y1-y0,h,'plaster',.014,True)
 for zz in [z+.07,z+h-.04]:box('timber wall rail',(x0+x1)/2,(y0+y1)/2,zz,x1-x0+.018,y1-y0+.018,.09,'wood',.008)
def wx(x0,x1,y,z,gap=None):
 if gap:
  wall(x0,gap[0],y-.07,y+.07,z);wall(gap[1],x1,y-.07,y+.07,z);box('door lintel',sum(gap)/2,y,z+2.24,gap[1]-gap[0],.15,.47,'plaster')
 else:wall(x0,x1,y-.07,y+.07,z)
def wy(x,y0,y1,z,gap=None):
 if gap:
  wall(x-.07,x+.07,y0,gap[0],z);wall(x-.07,x+.07,gap[1],y1,z);box('door lintel',x,sum(gap)/2,z+2.24,.15,gap[1]-gap[0],.47,'plaster')
 else:wall(x-.07,x+.07,y0,y1,z)
def window(x,y,z,w=1.5,h=1.1,side=False,curtain=False):
 # Window frames sit proud of recessed blue glass; no layered coincident planes.
 before=len(groups[G]);box('window glass',x,y,z,w,.045,h,'glass',.008)
 for xx in [x-w/2,x,x+w/2]:box('window stile',xx,y-.035,z,.045,.10,h+.1,'trim')
 for zz in [z-h/2,z+h/2]:box('window rail',x,y-.035,zz,w+.09,.10,.055,'white')
 box('window sill',x,y-.08,z-h/2-.02,w+.20,.26,.08,'wood')
 if curtain:
  rod('curtain rod',(x-w/2-.15,y+.17,z+h/2+.16),(x+w/2+.15,y+.17,z+h/2+.16),.025)
  for sign in [-1,1]:
   for i in range(6):ell('curtain pleat',x+sign*(w*.36+i*.026),y+.14+(.018 if i%2 else 0),z,.036,.043,h*.61,'green')
 if side:
  for o in groups[G][before:]:dx,dy=o.location.x-x,o.location.y-y;o.location.x=x-dy;o.location.y=y+dx;o.rotation_euler.z+=math.pi/2

def roof(x0,x1,y0,y1,z,rise,material='roof'):
 cx=(x0+x1)/2;half=(x1-x0)/2+.32;dep=y1-y0+.65;slope=math.atan2(rise,half);length=math.hypot(half,rise)
 for sign in [-1,1]:
  o=box('roof slope',cx+sign*half/2,(y0+y1)/2,z+rise/2,length,dep,.12,material,.02);o.rotation_euler.y=sign*slope
  for j in range(int(dep/.32)+1):
   y=y0-.3+j*.32;rod('standing roof seam',(cx,y,z+rise+.09),(cx+sign*half,y,z+.09),.022,material)
  for j in range(1,int(length/.35)):
   t=j*.35/length;rod('tile row',(cx+sign*half*t,y0-.32,z+rise*(1-t)+.065),(cx+sign*half*t,y1+.32,z+rise*(1-t)+.065),.015,material)
 rod('ridge cap',(cx,y0-.38,z+rise+.11),(cx,y1+.38,z+rise+.11),.095,material)
 for y in [y0-.34,y1+.34]:
  rod('white bargeboard',(x0-.33,y,z),(cx,y,z+rise),.065,'white');rod('white bargeboard',(cx,y,z+rise),(x1+.33,y,z),.065,'white')
 # Solid gable ends fill the area below each roof ridge.
 for y in [y0,y1]:
  me=bpy.data.meshes.new('gable');me.from_pydata([(x0,y,z),(x1,y,z),(cx,y,z+rise)],[],[(0,1,2)]);me.materials.append(mats['plaster']);o=bpy.data.objects.new('gable',me);bpy.context.collection.objects.link(o);groups[G].append(o)

def table(x,y,z,w=1.4,d=.8,height=.68):
 box('table top',x,y,z+height,w,d,.085,'floor',.035,True)
 for a in [-1,1]:
  for b in [-1,1]:box('table leg',x+a*(w/2-.09),y+b*(d/2-.09),z+height/2,.085,.085,height,'wood')
 for sign in [-1,1]:
  box('table aproned long rail',x,y+sign*(d/2-.075),z+height-.12,w-.12,.035,.13,'wood',.009)
  box('table aproned end rail',x+sign*(w/2-.075),y,z+height-.12,.035,d-.12,.13,'wood',.009)
  for sx in [-1,1]:
   ell('table rounded dowel',x+sx*(w/2-.10),y+sign*(d/2-.052),z+height-.12,.014,.004,.014,'trim')
 for sign in [-1,1]:
  rod('table lower stretcher',(x-w/2+.09,y+sign*(d/2-.09),z+.20),(x+w/2-.09,y+sign*(d/2-.09),z+.20),.019,'wood')
def chair(x,y,z,material='wood'):
 box('seat',x,y,z+.40,.42,.43,.08,material,.04)
 for a in [-1,1]:
  for b in [-1,1]:box('chair leg',x+a*.16,y+b*.16,z+.21,.045,.045,.40,'wood')
 box('chair top rail',x,y+.18,z+.905,.42,.075,.08,material,.022)
 for dx in [-.17,0,.17]:box('chair shaped back slat',x+dx,y+.18,z+.67,.045,.049,.41,material,.015)
 for side in [-1,1]:rod('chair lower side stretcher',(x+side*.16,y-.16,z+.18),(x+side*.16,y+.16,z+.18),.016,'wood')
 box('chair soft seat pad',x,y-.015,z+.451,.35,.345,.041,'linen',.018)
 for sy in [-1,1]:rod('chair seat piping',(x-.148,y-.015+sy*.14,z+.463),(x+.148,y-.015+sy*.14,z+.463),.0025,'cream')
def sofa(x,y,z,w=1.8,rot=0):
 start=len(groups[G]);box('sofa frame',x,y,z+.22,w,.73,.31,'wood',.08,True)
 for i in range(3):box('upholstery seat',x-w/3+i*w/3,y-.06,z+.43,w/3-.025,.57,.18,'sofa',.065)
 box('sofa back',x,y+.30,z+.68,w,.18,.61,'sofa',.065)
 for i in range(3):
  xx=x-w/3+i*w/3;box('sofa separate back cushion',xx,y+.183,z+.71,w/3-.038,.094,.40,'sofa',.040)
  for sy in [-1,1]:rod('sofa cushion stitched piping',(xx-w/6+.035,y-.06+sy*.225,z+.508),(xx+w/6-.035,y-.06+sy*.225,z+.508),.0025,'cream')
 for sx in [-1,1]:
  for sy in [-1,1]:box('sofa tapered foot',x+sx*(w/2-.16),y+sy*.245,z+.08,.095,.095,.16,'wood',.015)

 for a in [-1,1]:box('sofa arm',x+a*(w/2-.07),y,z+.55,.18,.70,.3,'sofa',.055)
 if rot:
  for o in groups[G][start:]:dx,dy=o.location.x-x,o.location.y-y;o.location.x=x+math.cos(rot)*dx-math.sin(rot)*dy;o.location.y=y+math.sin(rot)*dx+math.cos(rot)*dy;o.rotation_euler.z+=rot

def books(x,y,z,n=8):
 for i in range(n):
  h=.16+random.random()*.12;box('book spine',x+i*.07,y,z+h/2,.055,.16,h,['green','pink','blue','cream'][i%4],.006)
  box('book pages',x+i*.07,y-.005,z+h/2,.038,.165,h-.025,'paper',.004)
def shelf(x,y,z,w=1.1,h=1.5):
 for a in [-1,1]:box('shelf upright',x+a*w/2,y,z+h/2,.065,.31,h,'wood')
 box('shelf back',x,y+.14,z+h/2,w,.035,h,'wood')
 for i in range(5):
  zz=z+.08+i*(h-.16)/4;box('shelf board',x,y,zz,w,.32,.06,'floor')
  if i<4:books(x-w/2+.07,y,zz+.035,min(12,int(w/.08)))
def pillow(x,y,z,w=.6,d=.4):
 box('soft pillow',x,y,z,w,d,.16,'white',.074)
 for sign in [-1,1]:rod('pillow stitched seam',(x-w*.41,y+sign*d*.36,z),(x+w*.41,y+sign*d*.36,z),.008,'cream')
def bed(x,y,z,yellow=False):
 box('bed frame',x,y,z+.20,1.20,2.1,.31,'wood',.045,True);box('mattress',x,y,z+.42,1.17,2.02,.22,'linen',.085)
 box('soft quilt',x,y-.24,z+.60,1.15,1.40,.20,'yellow' if yellow else 'pink',.087)
 for i in range(6):
  xx=x-.50+i*.20;rod('quilt stitch',(xx,y-.85,z+.703),(xx,y+.34,z+.703),.007,'cream')
 for i in range(5):box('hanging quilt fold',x-.46+i*.23,y-.97,z+.46,.15,.08,.31,'yellow' if yellow else 'pink',.039)
 pillow(x,y+.70,z+.61);box('headboard',x,y+1.06,z+.66,1.3,.09,1.0,'floor',.04)
 if yellow:
  for zz in [z+.80,z+1.18]:box('bedside book ledge',x,y+1.05,zz,1.25,.25,.05,'floor')
  books(x-.50,y+1.03,z+.83,6)
def plant(x,y,z,scale=1):
 ell('terracotta pot',x,y,z+.15*scale,.16*scale,.16*scale,.18*scale,'roof')
 for i in range(7):
  a=i*2.4;top=(x+math.cos(a)*.2*scale,y+math.sin(a)*.2*scale,z+(.35+random.random()*.25)*scale);rod('plant stem',(x,y,z+.20*scale),top,.009*scale,'green');ell('plant leaf',*top,.13*scale,.07*scale,.045*scale,'leafLight' if i%2 else 'leaf')
def kitchen(x0,x1,y,z):
 w=x1-x0;box('kitchen cabinets',(x0+x1)/2,y,z+.43,w,.63,.86,'white',.025,True);box('counter',(x0+x1)/2,y,z+.90,w+.04,.69,.07,'slate',.02)
 for i in range(int(w/.48)):box('cabinet reveal',x0+.25+i*.48,y-.335,z+.44,.45,.016,.70,'cream');rod('cabinet handle',(x0+.10+i*.48,y-.36,z+.68),(x0+.29+i*.48,y-.36,z+.68),.012)
 box('sink',x1-.58,y,z+.947,.63,.44,.022,'metal',.05);box('sink basin',x1-.58,y,z+.953,.50,.34,.014,'glass',.06)
 rod('tap riser',(x1-.58,y+.22,z+.92),(x1-.58,y+.22,z+1.20),.027);rod('tap spout',(x1-.58,y+.22,z+1.20),(x1-.58,y,z+1.20),.027)
 for xx in [x0+.35,x0+.75]:
  for yy in [y-.15,y+.15]:ell('hob burner',xx,yy,z+.951,.09,.09,.014,'black')
 box('extractor hood',x0+.57,y,z+1.80,1,.55,.17,'slate',.04)
 for xx in [x0+.30,x1-.40]:box('wall cupboard',xx,y+.13,z+1.97,.57,.35,.57,'cream',.025)
def bath(x,y,z):
 box('bath base',x,y,z+.23,1.2,1.65,.4,'tile',.09,True)
 for xx in [-.52,.52]:box('bath rim',x+xx,y,z+.56,.15,1.65,.3,'white',.065)
 for yy in [-.75,.75]:box('bath rim',x,y+yy,z+.56,1.2,.15,.3,'white',.065)
 box('bath water',x,y,z+.44,.98,1.35,.025,'glass',.08)
def toilet(x,y,z):
 ell('toilet bowl',x,y,z+.28,.24,.32,.28);ell('toilet seat',x,y-.03,z+.50,.25,.31,.035);box('cistern',x,y+.27,z+.65,.47,.20,.45,'white',.06)
def stairs(x,y0,y1,z,upper,width=.85):
 n=15;step=(y1-y0)/n
 for i in range(n):
  top=z+(i+1)*(upper-z)/n;box('stair riser',x,y0+(i+.5)*step,(z+top)/2,width,step,top-z,'floor',.006);box('tread nosing',x,y0+i*step+.025,top+.006,width+.035,.08,.026,'wood')
 for side in [-1,1]:
  xx=x+side*(width/2+.015)
  rod('continuous stair handrail',(xx,y0,z+.85),(xx,y1,upper+.85),.035,'wood')
  for i in range(0,n+1,2):
   yy=y0+i*step;zz=z+i*(upper-z)/n;rod('stair baluster',(xx,yy,zz),(xx,yy,zz+.84),.018,'wood')
  colliders.append(dict(x=xx,y=(y0+y1)/2,z=(z+upper)/2,w=.045,d=y1-y0,h=upper-z+1,group=G))

def door(name,x,y,z,w=1,h=2,material='wood',sliding=False):
 global G
 old=G;G=name
 box('door panel',x,y,z+h/2,w,.065,h,material,.025)
 box('door inset',x,y-.038,z+h*.66,w*.65,.012,h*.28,'glass' if not sliding else 'paper')
 G='v11_home_upper' if sliding else old
 for zz in [z+.03,z+h+.03]:box('door track',x,y,zz,w+(1.10 if sliding else .1),.17,.04,'trim')
 G=name
 rod('recessed door pull',(x+w*.35,y-.043,z+.90),(x+w*.35,y-.043,z+1.10),.02,'metal')
 G=old

# Detailed replacement buildings, grouped for cutaway and floor controls.
G='v11_home_lower';floor(-17.15,-8.95,.35,8.55,.48);floor(-17.15,-13.45,-2.35,.35,.48)
# floor zones: reception forward-left, living middle-left, kitchen rear, hall and wet rooms to right.
tatami(-17,-13.15,.5,5.5,.50);floor(-16.85,-10.9,5.85,8.4,.50,'tile')
floor(-10.70,-9.1,1.05,5.8,.50,'tile');floor(-12.1,-10.85,.42,1.25,.28,'tile')
wx(-17.15,-8.95,8.55,.48);wy(-17.15,-2.35,8.55,.48);wy(-8.95,.35,8.55,.48)
wx(-17.15,-13.45,-2.35,.48);wy(-13.45,-2.35,.35,.48,gap=(-1.4,-.3));wx(-17.15,-13.1,.35,.48,gap=(-15.0,-13.8))
wy(-13.72,.4,5.7,.48,gap=(1.4,2.65));wy(-10.82,.4,5.85,.48,gap=(2.55,3.65));wx(-17.05,-13.02,5.70,.48,gap=(-14.8,-13.5))
wx(-10.75,-9.02,2.45,.48);wx(-10.75,-9.02,4.00,.48,gap=(-10.45,-9.65));# Open north end of hallway into kitchen
sofa(-15.3,-1.65,.48,2.25);table(-15.2,-.50,.48,1.30,.65,.38);chair(-16.25,-.45,.48,'sofa');chair(-14.20,-.45,.48,'sofa')
table(-15.3,3.1,.50,1.4,1.05,.34)
for xx,yy in [(-16.3,3.1),(-14.3,3.1),(-15.3,2.15)]:box('floor cushion',xx,yy,.57,.56,.56,.12,'green',.05)
shelf(-16.45,5.40,.50,1.0,1.1);box('television stand',-15.0,5.40,.75,1.40,.40,.48,'wood',.025);box('television',-15.0,5.41,1.26,.95,.24,.64,'trim',.04);box('TV glass',-15.0,5.275,1.28,.82,.025,.48,'glass',.045)
kitchen(-16.65,-12.0,8.02,.50);table(-14.3,6.65,.50,1.30,.72,.70)
for xx in [-14.85,-13.80]:chair(xx,6.10,.50,'green')
box('fridge',-11.48,7.91,1.34,.72,.70,1.68,'white',.04,True)
bath(-9.88,4.94,.50);toilet(-9.81,1.62,.50);box('vanity',-9.77,3.25,.84,.95,.48,.65,'cream',.025,True);ell('wash basin',-9.77,3.24,1.18,.34,.20,.055);box('mirror',-9.77,3.48,1.75,.7,.04,.73,'glass')
box('shoe cupboard',-10.4,.82,.87,.75,.45,.80,'wood',.03,True);plant(-16.65,-1.7,.48,1.2);plant(-16.55,1,.50,1.3)
G='v11_home_stairs';stairs(-13.15,1.30,4.75,.48,3.15,.80)
G='v11_home_front';wx(-13.45,-8.95,.35,.48,gap=(-12.10,-10.90));window(-15.3,-2.44,1.90,1.85);window(-17.24,3.2,1.90,2.0,side=True);window(-13.4,8.64,1.9,2.0)
door('v11_home_entry',-11.5,.35,.48,1.1)
# Preserve the detailed legacy bedroom east of x=-12.6.
# The rebuilt staircase meets its original west doorway without piercing the floor.
G='v11_home_upper'
floor(-17.15,-13.65,.35,6.85,3.15)
floor(-13.65,-12.60,.35,1.30,3.15)
floor(-13.65,-12.60,4.75,6.85,3.15)
tatami(-16.95,-13.85,.52,5.62,3.17)
wy(-17.15,.35,6.85,3.15)
wy(-13.75,.4,5.65,3.15)
wx(-17.15,-12.60,6.85,3.15)
wx(-17.05,-13.75,5.72,3.15,gap=(-15.0,-13.95))
bed(-15.7,2.0,3.17)
G='v11_home_upper_front'
wx(-17.15,-12.66,.35,3.15)
window(-15.2,.25,4.58,1.95,1.14,curtain=True)
G='v11_home_roof';roof(-17.15,-8.95,.35,6.85,5.65,1.7);roof(-17.15,-13.45,-2.35,.35,2.97,.85);roof(-17.1,-8.95,6.85,8.55,2.97,.70)

# Shizuka: reference plan with central hall, wet rooms west and living east.
z=.24;up=2.94;G='v11_shizuka_lower';floor(-16.0,-7.9,-22,-14,z);floor(-15.85,-12.05,-17.2,-14.15,z+.015,'tile');floor(-15.85,-13.65,-21.85,-17.35,z+.015,'tile')
wy(-16,-22,-14,z);wy(-7.9,-22,-14,z);wx(-16,-7.9,-14,z)
wy(-11.6,-22,-21.30,z);wy(-11.6,-20.10,-16.95,z);wy(-11.6,-15.70,-14,z);wy(-10.0,-22,-14,z,gap=(-20.7,-19.5));wx(-15.9,-11.67,-17.30,z,gap=(-12.90,-11.75));wx(-15.9,-13.60,-19.5,z,gap=(-14.6,-13.75));wx(-9.93,-7.99,-18.2,z,gap=(-9.7,-8.7))
kitchen(-15.65,-12.0,-14.52,z);table(-14.0,-15.85,z,1.40,.80,.70)
for xx in [-14.5,-13.5]:chair(xx,-16.5,z,'green')
bath(-14.80,-20.75,z);box('laundry machine',-15.3,-18.1,z+.48,.80,.72,.96,'white',.04,True);ell('laundry door',-15.3,-18.48,z+.49,.27,.045,.27,'glass');toilet(-14.0,-18.2,z)
sofa(-8.95,-19.00,z,1.65);sofa(-8.63,-21.02,z,1.4,math.pi/2);table(-8.94,-20.2,z,1.05,.6,.38);box('living rug',-8.96,-20.2,z+.015,1.70,2.0,.02,'cream',.01)
bed(-8.95,-15.6,z);plant(-8.35,-21.50,z,1.25);box('entry shoe cabinet',-10.43,-21.47,z+.38,.67,.45,.75,'floor',.035,True)
G='v11_shizuka_stairs';stairs(-12.13,-20.50,-17.30,z,up,.88)
G='v11_shizuka_front';wx(-16,-7.9,-22,z,gap=(-11.35,-10.20));window(-9.10,-22.09,z+1.35,1.65);window(-16.09,-15.85,z+1.40,1.7,side=True)
door('v11_shizuka_entry',-10.775,-22,z,1.05,2.05,'pink')
G='v11_shizuka_upper';floor(-16,-12.64,-22,-14,up);floor(-11.63,-7.9,-22,-14,up);floor(-12.64,-11.63,-17.3,-14,up);floor(-12.64,-11.63,-22,-20.5,up)
wy(-16,-22,-14,up);wy(-7.9,-22,-14,up);wx(-16,-7.9,-14,up)
# Four rooms around the central corridor, staircase opening at west end.
wx(-15.90,-12.66,-19.8,up,gap=(-14,-12.8));wx(-11.60,-7.98,-19.8,up,gap=(-11.3,-10.1));wx(-15.9,-7.98,-18.15,up,gap=(-14,-11.40));wy(-11.5,-18.15,-14,up);wy(-11.9,-22,-19.8,up)
# front-left Shizuka bedroom: yellow bedding, green curtains, headboard books, toys.
bed(-14.9,-20.85,up,True);shelf(-15.38,-19.99,up,.8,1.55);table(-13.32,-21.42,up,.95,.5,.70);chair(-13.32,-20.80,up,'pink');plant(-13,-19.95,up,.8)
# toy dog, rabbit and round flower cushion.
ell('toy dog body',-14.05,-21.2,up+.23,.16,.13,.23,'roof');ell('toy dog face',-14.05,-21.22,up+.53,.16,.13,.16,'cream')
for xx in [-14.21,-13.89]:ell('floppy toy ear',xx,-21.19,up+.49,.065,.06,.17,'roof')
for xx in [-14.10,-14.0]:ell('toy eye',xx,-21.345,up+.55,.016,.009,.02,'black')
ell('rabbit body',-14.9,-20.98,up+.88,.10,.075,.15,'pink');ell('rabbit head',-14.9,-20.98,up+1.07,.10,.075,.09,'cream')
for xx in [-14.95,-14.86]:ell('rabbit ear',xx,-20.98,up+1.20,.025,.028,.10,'cream')
for i in range(6):a=i*math.tau/6;ell('flower cushion petal',-13.35+math.cos(a)*.20,-20.18+math.sin(a)*.20,up+.08,.15,.15,.07,'yellow')
ell('flower cushion center',-13.35,-20.18,up+.09,.14,.14,.075,'cream')
# Parents, guest room and father's study.
bed(-14.4,-15.90,up);box('parents wardrobe',-15.45,-14.47,up+.95,.9,.6,1.9,'cream',.02,True);bed(-9.4,-15.7,up);shelf(-9.70,-19.98,up,2.10,1.8);table(-9.50,-21.2,up,1.55,.70,.73);chair(-9.5,-20.55,up);books(-9.95,-21.10,up+.79,8)
G='v11_shizuka_upper_front';wx(-16,-7.9,-22,up);window(-14.55,-22.09,up+1.40,2.10,1.20,curtain=True);window(-9.55,-22.09,up+1.40,1.75,1.20,curtain=True)
G='v11_shizuka_balcony';floor(-17.10,-16,-21.50,-14.6,up)
for yy in [-21.5,-14.6]:rod('balcony rail',(-17.12,yy,up+.9),(-16,yy,up+.9),.04,'white')
rod('balcony rail',(-17.12,-21.5,up+.9),(-17.12,-14.6,up+.9),.04,'white')
for i in range(24):rod('balcony baluster',(-17.12,-21.5+i*.3,up),(-17.12,-21.5+i*.3,up+.9),.025,'white')
G='v11_shizuka_roof';roof(-16,-7.9,-22,-14,5.44,1.7,'orangeRoof')

# Gian's compact two-storey shop, yellow sign, orange/green canvas and red vending machine.
G='v11_gian';floor(-38,-30,.7,8.8,.20);wall(-38,-30,8.70,8.85,.20,5.5);wy(-38,.7,8.8,.20);wy(-30,.7,8.8,.20)
box('shop upper frontage',-34,.80,4.35,8,.20,2.25,'plaster',.02,True)
for xx in [-36.10,-32.3]:window(xx,.66,4.6,2.15,1.30)
box('golden shop sign timber border',-34,.47,3.01,7.6,.30,.86,'wood',.04);box('yellow shop sign',-34,.29,3.01,7.4,.10,.69,'yellow',.025);text('剛 田 商 店',-34,.225,2.84,.42,'trim')
for i in range(22):
 xx=-37.8+(i+.5)*7.6/22;o=box('striped canvas',xx,-.12,2.47,7.6/22,1.26,.045,'orangeRoof' if i%2==0 else 'green',.004);o.rotation_euler.x=.25;box('canvas valance',xx,-.73,2.27,7.6/22,.045,.21,'orangeRoof' if i%2==0 else 'green')
for xx in [-37.6,-36.15,-32.50]:window(xx,.61,1.24,1.25,1.88)
# open shop entrance and shelves visible through shop front.
for xx in [-37.2,-30.8]:shelf(xx,6.9,.2,1.1,1.9)
for xx in [-35.4,-33.3]:table(xx,4.1,.2,1.4,.85,.65)
for xx in [-36.9,-35.8,-34.7]:
 box('produce crate',xx,-.02,.43,.85,.63,.45,'wood',.025,True)
 for i in range(8):ell('fresh produce',xx+(i%4-.5*3)*.16,-.07+(i//4)*.18,.75,.083,.085,.085,'orangeRoof' if int(abs(xx))%2 else 'leafLight')
box('red vending machine',-30.70,.13,1.22,1.06,.85,2.06,'red',.065,True);box('vending display',-30.7,-.31,1.56,.88,.027,1.05,'metal')
for row in range(3):
 for col in range(6):
  xx=-31.04+col*.136;zz=1.26+row*.30;rod('drink can',(xx,-.36,zz),(xx,-.36,zz+.16),.044,['blue','red','cream','green'][col%4]);ell('selection button',xx,-.373,zz-.06,.025,.01,.018,'white')
box('vending collection slot',-30.73,-.32,.53,.62,.04,.22,'black');box('vending payment panel',-30.32,-.32,.89,.16,.04,.30,'metal');roof(-38,-30,.7,8.8,5.55,1.0,'slate')

# Suneo villa with arched glazing, white masonry, red roof and tiered fountain.
G='v11_suneo';floor(-38.5,-29.5,-21.4,-14.2,.22)
for yy in [-21.4,-14.2]:wall(-38.5,-29.5,yy-.1,yy+.1,.22,5.1)
for xx in [-38.5,-29.5]:wall(xx-.1,xx+.1,-21.4,-14.2,.22,5.1)
# Individual pilasters, cornices and quoin courses give the facade depth.
for xx in [-38.45,-35.5,-32.6,-29.55]:
 box('white pilaster',xx,-21.56,2.72,.27,.33,5.15,'white',.014)
 for i in range(16):box('stone joint',xx,-21.75,.40+i*.30,.29,.015,.025,'cream',0)
for zz in [.36,2.80,5.24]:box('villa cornice',-34,-21.61,zz,9.3,.42,.17,'white',.02)
def arch(x,y,z,w=1.15,h=1.70):
 window(x,y,z+h/2-.16,w,h-.32)
 # Semicircular arched glass and segmented masonry surround.
 ell('arched glass',x,y,z+h-.28,w/2,.04,w/2,'glass')
 for i in range(17):
  a=i*math.pi/16;o=box('arched stone voussoir',x+math.cos(a)*(w/2+.09),y-.055,z+h-.28+math.sin(a)*(w/2+.09),.16,.16,.16,'white',.015);o.rotation_euler.y=-a
 rod('arch mullion',(x,y-.12,z+h-.30),(x,y-.12,z+h+w/2-.32),.025,'white')
for xx in [-37.3,-30.8]:
 for zz in [.80,3.12]:arch(xx,-21.66,zz,1.25,1.70)
arch(-34,-21.66,3.10,1.8,1.85)
for i in range(4):box('villa entry step',-34,-22.15-i*.24,.16+(3-i)*.07,2.2+i*.17,.65,.15,'cream',.01)
door('v11_suneo_entry',-34,-21.60,.43,1.65,2.2)
for xx in [-35.12,-32.88]:rod('portico column',(xx,-22,.4),(xx,-22,2.83),.11,'white')
box('portico lintel',-34,-22,2.84,2.6,.78,.23,'white',.015);roof(-35.25,-32.75,-22.43,-21.35,2.98,.61)
roof(-38.5,-29.5,-21.4,-14.2,5.45,2.0)
# Fountain entirely within the front garden, away from the entrance steps.
fx,fy=-28.0,-22.5
for radius,zz,thick in [(1.15,.20,.12),(.69,.92,.09),(.37,1.55,.07)]:
 bpy.ops.mesh.primitive_torus_add(major_radius=radius,minor_radius=thick,major_segments=32,minor_segments=8,location=(fx,fy,zz));o=bpy.context.object;o.name='fountain bowl rim';o.data.materials.append(mats['cream']);groups[G].append(o)
 ell('fountain water',fx,fy,zz-.025,radius,radius,.055,'glass')
rod('fountain pedestal',(fx,fy,.18),(fx,fy,1.78),.13,'cream');ell('fountain finial',fx,fy,1.89,.13,.13,.16,'cream')
for i in range(12):
 a=i*math.tau/12;pts=[(fx+math.cos(a)*t*.94,fy+math.sin(a)*t*.94,1.55+.3*math.sin(t*math.pi)-t*1.28) for t in [j/10 for j in range(11)]]
 for a1,b1 in zip(pts,pts[1:]):rod('water jet',a1,b1,.014,'glass')
colliders.append(dict(x=fx,y=fy,z=.8,w=2.4,d=2.4,h=1.6,group=G))
for xx in [-39.2,-27.0]:
 for yy in [-23.5,-17.0,-13.3]:plant(xx,yy,.2,2.3)

# Export batches: one mesh per material/group preserves floor visibility, doors separate.
def export_groups(path):
 exports=[];deps=bpy.context.evaluated_depsgraph_get()
 for name,objects in groups.items():
  if not objects:continue
  vs=[];fs=[];mi=[];uvs=[];slots=[];slotids={}
  for o in objects:
   ev=o.evaluated_get(deps);me=ev.to_mesh();off=len(vs);vs.extend(tuple(o.matrix_world@v.co) for v in me.vertices);uv=me.uv_layers.active
   for p in me.polygons:
    fs.append(tuple(off+i for i in p.vertices));m=me.materials[p.material_index]
    if m.name not in slotids:slotids[m.name]=len(slots);slots.append(m)
    mi.append(slotids[m.name]);uvs.extend(tuple(uv.data[li].uv) if uv else (0,0) for li in p.loop_indices)
   ev.to_mesh_clear()
  me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
  for m in slots:me.materials.append(m)
  me.polygons.foreach_set('material_index',mi);layer=me.uv_layers.new(name='UVMap');layer.data.foreach_set('uv',[v for pair in uvs for v in pair]);o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);exports.append(o)
 bpy.ops.object.select_all(action='DESELECT')
 for o in exports:o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_image_format='JPEG',export_image_quality=82,export_draco_mesh_compression_enable=True,export_draco_position_quantization=16)
 return exports
export_groups(OUT/'neighborhood-v21.glb')
(OUT/'neighborhood-v12.json').write_text(json.dumps({'colliders':colliders,'home':{'entry':[-11.5,.35],'stairs':[-13.15,1.30,4.75]},'shizuka':{'entry':[-10.775,-22],'stairs':[-12.13,-20.5,-17.3]}}))
# Native file contains editable original objects plus named runtime batches.
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'tools/neighborhood-v12.blend'))
print('NEIGHBORHOOD_READY',len(colliders),'colliders',len(groups),'groups',flush=True)
