import bpy, math, random, json, os, sys, time
import numpy as np
from mathutils import Vector, Matrix
from collections import defaultdict
random.seed(22)
PROJECT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DELIVER=os.path.dirname(PROJECT)
OUT=PROJECT+'/public/models'
os.makedirs(DELIVER+'/渲染预览',exist_ok=True)
os.makedirs(OUT,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for d in bpy.data.materials: bpy.data.materials.remove(d)
GROUP='town'; groups=defaultdict(list); colliders=[]; mats={}; cache={}; origin=Vector((0,0,0))

def mat(name,color,rough=.72,metal=0,tex=None):
 m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
 if tex:
  a=m.node_tree.nodes.new('ShaderNodeTexImage'); a.image=tex; m.node_tree.links.new(a.outputs['Color'],p.inputs['Base Color'])
 mats[name]=m; return m

def texture(name,base,kind):
 n=512; rng=np.random.default_rng(18); y,x=np.mgrid[0:n,0:n]; noise=rng.normal(0,.022,(n,n)); t=x/n; s=y/n
 if kind=='wood': v=.92+.085*np.sin((t+.012*np.sin(s*14)+.006*np.sin(s*49))*180)+.035*np.sin(t*650+s*4)+noise
 elif kind=='tatami': v=.9+.045*np.sin(y*2.7)+.025*np.cos(x*2.2)+noise*.35
 elif kind=='road': v=.97+noise*1.8
 else: v=.95+noise*.65
 a=np.ones((n,n,4),dtype=np.float32); a[:,:,:3]=np.clip(np.array(base)[None,None,:]*v[:,:,None],0,1)
 im=bpy.data.images.new(name,width=n,height=n); im.pixels.foreach_set(a.ravel()); im.filepath_raw=OUT+'/'+name+'.png'; im.file_format='PNG'; im.save(); im.pack(); return im
wood=mat('warm oak',(.52,.31,.14),tex=texture('wood',(.62,.43,.25),'wood'))
darkwood=mat('aged walnut',(.25,.135,.07),tex=texture('darkwood',(.36,.24,.14),'wood'))
floorwood=mat('honey floor',(.62,.43,.24),tex=texture('floorwood',(.71,.51,.31),'wood'))
tatami=mat('woven rush',(.45,.53,.25),tex=texture('tatami',(.66,.71,.43),'tatami'))
cream=mat('warm plaster',(.86,.80,.65),tex=texture('plaster',(.90,.84,.72),'plaster'))
road=mat('weathered asphalt',(.27,.31,.31),tex=texture('asphalt',(.37,.41,.40),'road'))
for name,c in {'paper':(.95,.91,.78),'white':(.91,.91,.83),'black':(.022,.03,.033),'red':(.67,.14,.105),'tile':(.48,.19,.115),'tileLight':(.58,.255,.15),'tileDark':(.37,.135,.088),'slate':(.24,.32,.35),'blue':(.012,.42,.69),'yellow':(.99,.69,.10),'bell':(.9,.58,.055),'pink':(.80,.39,.38),'skin':(.93,.68,.44),'hair':(.035,.026,.022),'navy':(.07,.18,.32),'green':(.19,.35,.23),'curtain':(.38,.47,.25),'concrete':(.59,.61,.56),'edge':(.42,.47,.38),'sand':(.64,.56,.35),'soil':(.31,.26,.16),'futon':(.85,.77,.64),'roofBlue':(.18,.28,.32),'roofGreen':(.25,.36,.28),'bath':(.30,.56,.57),'water':(.28,.62,.63),'orange':(.93,.36,.09),'flowerPink':(.76,.40,.59),'flowerPurple':(.40,.36,.64)}.items(): mat(name,c, .3 if name in ['bell','water'] else .72, .6 if name=='bell' else 0)

# Generated albedo maps are the final material source. The procedural maps are retained only as scratch fallback.
for material,filename,scale,bump in [(wood,'wood_basecolor.png',1,.045),(darkwood,'wood_basecolor.png',1,.038),(floorwood,'wood_basecolor.png',1,.04),(tatami,'tatami_basecolor.png',5,.022),(cream,'plaster_basecolor.png',2,.018)]:
 im=bpy.data.images.load(PROJECT+'/public/textures/'+filename,check_existing=True);im.pack()
 nt=material.node_tree;pbr=nt.nodes.get('Principled BSDF');it=next(n for n in nt.nodes if n.type=='TEX_IMAGE');it.image=im
 tc=nt.nodes.new('ShaderNodeTexCoord');mapping=nt.nodes.new('ShaderNodeMapping');mapping.inputs['Scale'].default_value=(scale,scale,1);nt.links.new(tc.outputs['UV'],mapping.inputs['Vector']);nt.links.new(mapping.outputs['Vector'],it.inputs['Vector'])
 bn=nt.nodes.new('ShaderNodeBump');bn.inputs['Strength'].default_value=.18;bn.inputs['Distance'].default_value=bump;nt.links.new(it.outputs['Color'],bn.inputs['Height']);nt.links.new(bn.outputs['Normal'],pbr.inputs['Normal'])
 if material in [darkwood,wood,floorwood]:
  mx=nt.nodes.new('ShaderNodeMixRGB');mx.blend_type='MULTIPLY';mx.inputs[0].default_value=1;v=.34 if material==darkwood else (.66 if material==wood else .85);mx.inputs[2].default_value=(v,v*.91,v*.82,1);nt.links.new(it.outputs['Color'],mx.inputs[1]);nt.links.new(mx.outputs[0],pbr.inputs['Base Color'])
mats.update({'wood':wood,'darkwood':darkwood,'floorwood':floorwood,'tatami':tatami,'cream':cream,'road':road})
for i,c in enumerate([(.24,.40,.11),(.32,.48,.15),(.38,.51,.16),(.20,.35,.12),(.44,.57,.22),(.29,.43,.16)]): mat('leaf'+str(i),c)
for i,c in enumerate([(.63,.28,.18),(.24,.39,.48),(.57,.51,.29),(.67,.55,.41),(.22,.34,.24),(.64,.38,.32)]): mat('book'+str(i),c)

def obj(name,mesh,loc=(0,0,0),material='wood',scale=None,rot=None):
 o=bpy.data.objects.new(name,mesh); bpy.context.collection.objects.link(o); o.location=Vector(loc)+origin
 if scale:o.scale=scale
 if rot:o.rotation_euler=rot
 o.data=mesh
 if len(mesh.materials)==0: mesh.materials.append(mats[material] if isinstance(material,str) else material)
 elif mesh.materials[0]!=(mats[material] if isinstance(material,str) else material):
  o.data=mesh.copy(); o.data.materials.clear(); o.data.materials.append(mats[material] if isinstance(material,str) else material)
 groups[GROUP].append(o); return o

def box(name,loc,dims,material='wood',bevel=0,rot=None,solid=False):
 bevel=min(bevel,min(dims)*.40)
 key=('box',tuple(dims),material,round(bevel,4))
 if key not in cache:
  a,b,c=[v/2 for v in dims]; verts=[(-a,-b,-c),(a,-b,-c),(a,b,-c),(-a,b,-c),(-a,-b,c),(a,-b,c),(a,b,c),(-a,b,c)]
  faces=[(0,3,2,1),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7),(4,5,6,7)]
  me=bpy.data.meshes.new(name); me.from_pydata(verts,[],faces); me.update()
  uv=me.uv_layers.new(name='UVMap')
  for poly in me.polygons:
   coords=[(0,0),(1,0),(1,1),(0,1)]
   for j,li in enumerate(poly.loop_indices):uv.data[li].uv=coords[j]
  if bevel:
   import bmesh
   bm=bmesh.new(); bm.from_mesh(me)
   bmesh.ops.bevel(bm,geom=list(bm.edges),offset=bevel,segments=2,affect='EDGES'); bm.to_mesh(me); bm.free()
  cache[key]=me
 o=obj(name,cache[key],loc,material,rot=rot)
 if solid:colliders.append({'x':o.location.x,'y':o.location.y,'z':o.location.z,'w':dims[0],'d':dims[1],'h':dims[2],'group':GROUP})
 return o

def sphere(name,loc,scale,material='white',seg=16,rings=10):
 key=('sphere',seg,rings,material)
 if key not in cache:
  import bmesh
  me=bpy.data.meshes.new(name); bm=bmesh.new(); bmesh.ops.create_uvsphere(bm,u_segments=seg,v_segments=rings,radius=1); bm.to_mesh(me); bm.free()
  for p in me.polygons:p.use_smooth=True
  cache[key]=me
 return obj(name,cache[key],loc,material,scale)

def cyl(name,loc,radius,depth,material='wood',r2=None,rot=None,vertices=16):
 r2=radius if r2 is None else r2; key=('cyl',radius,r2,depth,material,vertices)
 if key not in cache:
  vs=[(math.cos(i*math.tau/vertices)*r,math.sin(i*math.tau/vertices)*r,z) for z,r in [(-depth/2,radius),(depth/2,r2)] for i in range(vertices)]
  fs=[tuple(reversed(range(vertices))),tuple(range(vertices,vertices*2))]+[(i,(i+1)%vertices,(i+1)%vertices+vertices,i+vertices) for i in range(vertices)]
  me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update()
  for p in list(me.polygons)[2:]:p.use_smooth=True
  cache[key]=me
 return obj(name,cache[key],loc,material,rot=rot)

def rod(name,a,b,r=.035,material='wood'):
 av=Vector(a);bv=Vector(b);o=cyl(name,(av+bv)/2,r,(bv-av).length,material);o.rotation_euler=(bv-av).to_track_quat('Z','Y').to_euler();return o

def line(name,points,r=.012,material='black'):
 for a,b in zip(points,points[1:]):rod(name,a,b,r,material)

def torus(name,loc,major,minor,material='black',rot=(math.pi/2,0,0)):
 key=('torus',major,minor,material)
 if key not in cache:
  verts=[];faces=[];n=32;m=8
  for i in range(n):
   a=i*math.tau/n
   for j in range(m):
    b=j*math.tau/m;verts.append(((major+minor*math.cos(b))*math.cos(a),(major+minor*math.cos(b))*math.sin(a),minor*math.sin(b)))
  for i in range(n):
   for j in range(m):faces.append((i*m+j,((i+1)%n)*m+j,((i+1)%n)*m+(j+1)%m,i*m+(j+1)%m))
  me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update()
  for p in me.polygons:p.use_smooth=True
  cache[key]=me
 return obj(name,cache[key],loc,material,rot=rot)

def txt(name,body,loc,size=.3,material='darkwood',rot=(math.pi/2,0,0)):
 cu=bpy.data.curves.new(name,'FONT');cu.body=body;cu.size=size;cu.extrude=.001;cu.align_x='CENTER';cu.align_y='CENTER';o=bpy.data.objects.new(name,cu);bpy.context.collection.objects.link(o);o.location=Vector(loc)+origin;o.rotation_euler=rot;cu.materials.append(mats[material]);groups[GROUP].append(o);return o
# Native font is bundled into the editable source; texts become meshes for GLB.
fontpaths=['/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc','/System/Library/Fonts/STHeiti Medium.ttc']
for p in fontpaths:
 if os.path.exists(p):
  try: FONT=bpy.data.fonts.load(p);break
  except:pass

def sign(body,loc,w=1.1,h=.42):
 box('name plaque',loc,(w,.055,h),'paper',.015)
 o=txt('lettering',body,(loc[0],loc[1]-.031,loc[2]),min(h*.6,w/max(2,len(body))*.8));
 if 'FONT' in globals():o.data.font=FONT

def roof(x,y,z,w,d,h=1.65,material='tile'):
 # The ridge runs north-south. Individual overlapping barrel tiles catch sunlight.
 angle=math.atan2(h,w/2);length=math.hypot(w/2,h)
 for side in [-1,1]:
  box('roof underlay',(x+side*w/4,y,z+h/2),(length+.1,d,.16),material,rot=(0,side*angle,0))
  rows=max(4,int(length/.42));cols=max(6,int(d/.44))
  for i in range(rows):
   u=(i+.5)/rows
   for j in range(cols):
    c=material if material!='tile' else random.choice(['tile','tile','tileLight','tileDark'])
    box('overlapping clay tile',(x+side*(w/2*u),y-d/2+(j+.5)*d/cols,z+h*(1-u)+.12),(length/rows+.08,d/cols-.017,.075),c,.018,rot=(0,side*angle,0))
  rod('eave fascia',(x+side*w/2,y-d/2-.1,z),(x+side*w/2,y+d/2+.1,z),.075,'darkwood')
 for j in range(int(d/.4)+1):cyl('ridge cap',(x,y-d/2+j*.4,z+h+.13),.13,.44,material,rot=(math.pi/2,0,0))
 for sy in [-1,1]:
  rod('gable timber',(x-w/2,y+sy*d/2,z-.07),(x,y+sy*d/2,z+h-.07),.095,'paper');rod('gable timber',(x,y+sy*d/2,z+h-.07),(x+w/2,y+sy*d/2,z-.07),.095,'paper')
 # gable triangles
 me=bpy.data.meshes.new('gable');vs=[(x-w/2,y-d/2,z-.1),(x+w/2,y-d/2,z-.1),(x,y-d/2,z+h),(x-w/2,y+d/2,z-.1),(x+w/2,y+d/2,z-.1),(x,y+d/2,z+h)];me.from_pydata(vs,[],[(0,1,2),(5,4,3)]);obj('gable plaster',me,material='cream')

def window(x,y,z,w=2,h=1.45,rot=0,curtains=False):
 # Window geometry, facing the south street.
 objs=[];start=len(groups[GROUP])
 box('window recess',(x,y,z),(w+.15,.12,h+.16),'darkwood')
 box('soft blue window glass',(x,y-.072,z),(w,.025,h),'bath')
 for xx in [-w/2,0,w/2]:box('wood window mullion',(x+xx,y-.102,z),(.055,.08,h+.08),'paper')
 for zz in [-h/2,0,h/2]:box('window rail',(x,y-.115,z+zz),(w+.12,.09,.055),'paper')
 box('window ledge',(x,y-.22,z-h/2),(w+.3,.42,.10),'wood',.022)
 box('window awning',(x,y-.14,z+h/2+.16),(w+.4,.5,.10),'tile',.025,rot=(.12,0,0))
 if curtains:
  for s in [-1,1]:curtain(x+s*w*.36,y+.04,z,w*.26,h)
 if rot:
  pivot=Vector((x,y,0))+origin;R=Matrix.Rotation(rot,4,'Z')
  for o in groups[GROUP][start:]:o.location=pivot+R.to_3x3()@(o.location-pivot);o.rotation_euler.rotate(R)

def curtain(x,y,z,w,h):
 vs=[];fs=[];n=28
 for i in range(n+1):
  t=i/n;vs.extend([(x-w/2+t*w,y+math.sin(t*math.pi*12)*.055,z-h/2+.06*math.sin(t*math.pi*3)),(x-w/2+t*w,y+math.sin(t*math.pi*12)*.055,z+h/2)])
 for i in range(n):fs.append((i*2,i*2+2,i*2+3,i*2+1))
 me=bpy.data.meshes.new('pleated linen');me.from_pydata(vs,[],fs);me.update();obj('green pleated curtain',me,material='curtain')
 rod('curtain tie',(x-w*.45,y-.06,z-h*.16),(x+w*.45,y-.06,z-h*.16),.025,'yellow')

def leaf(pos,size,material):
 key=('leaf',material)
 if key not in cache:
  me=bpy.data.meshes.new('folded leaf');vs=[(-1,0,0),(-.55,-.38,.06),(.35,-.43,.03),(1,0,0),(.35,.43,.03),(-.55,.38,.06),(0,0,.14)];fs=[(6,i,(i+1)%6) for i in range(6)];me.from_pydata(vs,[],fs);me.update();cache[key]=me
 return obj('individual tree leaf',cache[key],pos,material,scale=(size,size,size),rot=(random.uniform(-.8,.8),random.uniform(-.8,.8),random.uniform(0,math.tau)))

def tree(x,y,h=4.6,r=1.8):
 cyl('tree trunk',(x,y,h*.34),.14,h*.68,'darkwood',r2=.09)
 for i in range(4):
  a=i*2.4;rod('branch',(x,y,h*.45),(x+math.cos(a)*r*.7,y+math.sin(a)*r*.7,h*.75),.06,'darkwood')
 for i in range(18):
  a=random.random()*math.tau;rr=random.random()*r*.7;z=h*.74+random.uniform(-.15,.55)*r
  center=Vector((x+math.cos(a)*rr,y+math.sin(a)*rr,z));scale=Vector((r*random.uniform(.36,.65),r*random.uniform(.36,.62),r*random.uniform(.32,.58)))
  sphere('inner leafy volume',center,scale*.66,'leaf'+str(random.randrange(4)),12,8)
  for j in range(32):
   theta=j*2.39996;zz=1-2*(j+.5)/32;rho=math.sqrt(1-zz*zz);v=Vector((math.cos(theta)*rho,math.sin(theta)*rho,zz));pos=center+Vector((v.x*scale.x,v.y*scale.y,v.z*scale.z))*.83
   leaf(pos,random.uniform(.16,.25),'leaf'+str(random.randrange(6)))

def shrub(x,y,r=.55,z=.3,flower=False):
 for i in range(4):
  a=i*2.4;sphere('garden shrub',(x+math.cos(a)*r*.35,y+math.sin(a)*r*.35,z+r*.5),(r*.7,r*.65,r*.7),'leaf'+str(random.randrange(6)),12,8)
 if flower:
  for i in range(8):
   a=random.random()*math.tau;rr=random.random()*r
   sphere('hydrangea',(x+math.cos(a)*rr,y+math.sin(a)*rr,z+r*.9),(.12,.12,.10),random.choice(['flowerPink','flowerPurple','paper']),10,6)

def pot(x,y,z=.1,s=.35):
 cyl('terracotta pot',(x,y,z+s*.45),s*.62,s*.9,'tile',r2=s*.78);cyl('pot lip',(x,y,z+s*.91),s*.81,.075,'tileLight');cyl('pot soil',(x,y,z+s*.95),s*.7,.03,'soil')
 for i in range(7):
  a=i*2.4;rod('plant stem',(x,y,z+s),(x+math.cos(a)*s*.3,y+math.sin(a)*s*.3,z+s*(1.4+i*.08)),.009,'green');o=sphere('plant leaf',(x+math.cos(a)*s*.43,y+math.sin(a)*s*.43,z+s*(1.4+i*.07)),(s*.42,s*.16,s*.09),'leaf'+str(i%6),12,6);o.rotation_euler=(.3,random.random(),a)

def books(x,y,z,n=8):
 for i in range(n):
  h=random.uniform(.27,.44);box('book spine',(x+i*.10,y,z+h/2),(.077,.24,h),'book'+str(i%6),.008,rot=(0,random.uniform(-.06,.06),0));box('spine stripe',(x+i*.10,y-.126,z+h*.7),(.078,.009,.02),'paper')

def table(x,y,z=.3,w=1.5,d=1,h=.55):
 box('solid wood tabletop',(x,y,z+h),(w,d,.10),'wood',.04)
 for i in [-1,1]:
  for j in [-1,1]:box('table leg',(x+i*(w/2-.12),y+j*(d/2-.12),z+h/2),(.10,.10,h),'darkwood',.012)

def cup(x,y,z):
 cyl('ceramic cup',(x,y,z+.055),.062,.11,'white');cyl('tea',(x,y,z+.112),.05,.004,'green');torus('cup handle',(x+.069,y,z+.056),.038,.013,'white')

def tatamiroom(x,y,z,w,d):
 box('tatami foundation',(x,y,z-.04),(w,d,.15),'darkwood')
 nx=max(1,round(w/1.6));ny=max(1,round(d/1.9));a=w/nx;b=d/ny
 for i in range(nx):
  for j in range(ny):
   xx=x-w/2+(i+.5)*a; yy=y-d/2+(j+.5)*b
   box('individual woven tatami',(xx,yy,z+.05),(a-.018,b-.018,.085),'tatami',.012)
   for s in [-1,1]:box('tatami cloth border',(xx+s*(a/2-.035),yy,z+.096),(.055,b-.02,.008),'green')

def panelwall(loc,dims,level='home_ground',solid=True):
 global GROUP
 old=GROUP;GROUP=level;box('plaster wall',loc,dims,'cream',.015,solid=solid);GROUP=old

def roomwall(x,y,z,w,h=2.95,front=False):
 # A wall with an actual window opening for interior light and clear sight lines.
 box('wall below window',(x,y,z+.50),(w,.17,1),'cream',solid=True)
 box('wall above window',(x,y,z+2.70),(w,.17,.5),'cream')
 for s in [-1,1]:box('side of window',(x+s*(w/2-.32),y,z+1.73),(.64,.17,1.48),'cream',solid=True)
 # open glazing with thin light tint and timber frames
 for s in [-1,1]:box('window jamb',(x+s*(w/2-.62),y,z+1.70),(.08,.22,1.50),'darkwood')
 for zz in [1,1.73,2.45]:box('window horizontal frame',(x,y-.014,z+zz),(w-1.2,.10,.07),'wood')
 box('window center frame',(x,y,z+1.72),(.06,.10,1.50),'wood')
 for s in [-1,1]:curtain(x+s*(w/2-.85),y+.15,z+1.72,.55,1.65)
 box('window sill',(x,y,z+1.0),(w-1,.34,.11),'wood',.014)

def wallframe(x,y,z,w,d,h=2.96):
 for xx in [-w/2,w/2]:
  for yy in [-d/2,d/2]:box('timber structural post',(x+xx,y+yy,z+h/2),(.15,.15,h),'wood')
 for zz in [.12,2.43,2.95]:
  for yy in [-d/2,d/2]:box('horizontal timber',(x,y+yy,z+zz),(w+.16,.13,.12),'wood')
  for xx in [-w/2,w/2]:box('horizontal timber',(x+xx,y,z+zz),(.13,d,.12),'wood')

def shoji(x,y,z,w=2,h=2.45):
 box('fusuma doors',(x,y,z+h/2),(w,.08,h),'paper',.015,solid=True)
 box('pink fusuma band',(x,y-.047,z+h*.35),(w,.016,.30),'pink')
 for xx in [-w/2,0,w/2]:box('sliding door stile',(x+xx,y-.055,z+h/2),(.035,.075,h),'wood')
 for s in [-1,1]:cyl('sliding door recessed pull',(x+s*.23,y-.065,z+1.1),.044,.014,'darkwood',rot=(math.pi/2,0,0))

def lamp(x,y,z):
 rod('hanging light wire',(x,y,z),(x,y,z-.45),.012,'darkwood');cyl('pendant shade',(x,y,z-.50),.32,.18,'paper',r2=.12);sphere('warm bulb',(x,y,z-.59),(.11,.11,.06),'yellow')

def chair(x,y,z=.3,green=True):
 c='green' if green else 'wood';box('chair upholstered seat',(x,y,z+.57),(.56,.53,.14),c,.075)
 box('chair back cushion',(x,y+.24,z+1.05),(.55,.13,.62),c,.065);rod('chair support',(x,y+.24,z+.5),(x,y+.24,z+1.15),.035,'slate');cyl('chair central post',(x,y,z+.27),.055,.54,'slate')
 for i in range(5):
  a=i*math.tau/5;rod('chair foot',(x,y,z+.11),(x+.38*math.cos(a),y+.38*math.sin(a),z+.07),.033,'slate');sphere('chair caster',(x+.38*math.cos(a),y+.38*math.sin(a),z+.045),(.065,.065,.065),'black',12,6)

def bookshelf(x,y,z,w=1.3,h=1.8):
 box('bookcase back',(x,y+.16,z+h/2),(w,.08,h),'wood')
 for s in [-1,1]:box('bookcase side',(x+s*w/2,y,z+h/2),(.09,.40,h),'darkwood')
 for i in range(5):
  zz=z+i*h/4;box('bookshelf',(x,y,zz),(w,.43,.06),'wood');
  if i<4:books(x-w*.40,y-.04,zz+.035,n=int(w*8))

def desk(x,y,z):
 box('desk top',(x,y,z+.84),(2.10,.90,.10),'wood',.04)
 for xx in [-.87,.87]:
  for yy in [-.32,.32]:box('desk leg',(x+xx,y+yy,z+.40),(.12,.12,.80),'wood',.02)
 box('desk drawer pedestal',(x+.61,y,z+.42),(.66,.76,.82),'wood',.025)
 for i in range(3):
  zz=z+.18+i*.25;box('desk drawer front',(x+.61,y-.393,zz),(.59,.06,.21),'floorwood',.015);rod('brass drawer handle',(x+.50,y-.44,zz),(x+.73,y-.44,zz),.017,'bell')
 books(x+.40,y+.20,z+.90,6)
 box('open notebook',(x-.15,y-.12,z+.903),(.55,.37,.018),'paper',.006,rot=(0,0,-.12))
 for i in range(5):box('notebook ruled line',(x-.16,y-.23+i*.045,z+.914),(.45,.006,.002),'bath')
 rod('pencil',(x-.2,y-.28,z+.94),(x+.12,y-.1,z+.94),.014,'yellow')
 cyl('pencil cup',(x+.15,y+.23,z+1.0),.07,.2,'blue')
 for i in range(5):rod('colored pencil',(x+.12+i*.014,y+.23,z+.97),(x+.11+i*.023,y+.24,z+1.21),.009,'book'+str(i))
 cyl('blue desk lamp base',(x-.72,y+.18,z+.93),.15,.055,'blue');rod('lamp lower arm',(x-.72,y+.18,z+.94),(x-.84,y+.18,z+1.28),.026,'blue');rod('lamp upper arm',(x-.84,y+.18,z+1.28),(x-.57,y+.18,z+1.48),.026,'blue');cyl('lamp shade',(x-.53,y+.18,z+1.45),.14,.20,'blue',r2=.07,rot=(0,-.5,0))
 chair(x-.16,y-.92,z)
 box('school bag',(x-1.01,y-.1,z+.41),(.16,.46,.52),'navy',.06);rod('bag strap',(x-1.04,y-.3,z+.5),(x-1.04,y+.1,z+.7),.028,'black')

def alarmclock(x,y,z):
 cyl('clock blue case',(x,y,z+.2),.22,.11,'blue',rot=(math.pi/2,0,0),vertices=32);cyl('clock ivory dial',(x,y-.067,z+.2),.185,.01,'paper',rot=(math.pi/2,0,0),vertices=32)
 for i in range(12):
  a=i*math.tau/12;sphere('hour mark',(x+.153*math.sin(a),y-.082,z+.2+.153*math.cos(a)),(.008,.009,.015),'darkwood',8,4)
 rod('clock minute hand',(x,y-.086,z+.2),(x+.07,y-.086,z+.3),.008,'black');rod('clock hour hand',(x,y-.09,z+.2),(x-.07,y-.09,z+.2),.012,'black')
 for s in [-1,1]:sphere('alarm bell',(x+s*.145,y,z+.41),(.11,.085,.05),'blue');rod('clock foot',(x+s*.1,y,z+.06),(x+s*.15,y,z-.015),.015,'slate')

print('MATERIALS AND PRIMITIVES READY',flush=True)
# ---------------- NOBI HOUSE / metre-scale two-floor interior ----------------
origin=Vector((-13,5,0));GROUP='home_ground'
box('stone foundation',(0,.2,.1),(10.4,10,.30),'concrete',.05)
box('first floor wooden deck',(0,.2,.31),(10,9.6,.15),'floorwood')
tatamiroom(-2.25,-2.25,.37,5.3,4.4);tatamiroom(-2.25,2.65,.37,5.3,4.5)
# Ground-floor facade is separate so dollhouse view can peel it away.
GROUP='home_front_ground'
roomwall(-2.25,-4.6,.40,5.45)
box('entry facade panel',(1.38,-4.6,1.87),(1.95,.20,2.94),'cream',solid=True)
box('entry right pillar',(4.8,-4.6,1.85),(.40,.24,2.94),'cream',solid=True)
box('entry lintel',(3.35,-4.6,3.08),(2.65,.22,.55),'wood')
# Door left open: genuine path from tiled genkan into the corridor.
box('open entrance door',(4.38,-3.88,1.54),(.10,1.45,2.28),'wood',.025)
box('entry door glass',(4.315,-3.88,1.84),(.018,.67,.66),'bath')
cyl('entry door handle',(4.30,-4.35,1.35),.035,.15,'bell',rot=(0,math.pi/2,0))
sign('野比',(4.83,-4.74,1.96),.60,.28)
GROUP='home_ground'
# side and back walls, cutout doorways on partitions
box('west plaster wall',(-5,.2,1.87),(.18,9.6,2.94),'cream',solid=True)
box('east plaster wall',(5,.2,1.87),(.18,9.6,2.94),'cream',solid=True)
roomwall(-2.25,5,.4,5.45);roomwall(2.7,5,.4,4.45)
for yy,dd in [(-3.85,1.5),(.3,2.6),(4.5,1.0)]:box('corridor partition',(.55,yy,1.85),(.15,dd,2.9),'cream',solid=True)
box('parents room divider',(-2.25,.05,1.85),(5.45,.13,2.9),'paper',solid=True)
# opening living-corridor at y -2.2; parents-corridor at y 2.7
for xx in [-4.9,.52,2.02,4.94]:box('structural post',(xx,-4.53,1.86),(.14,.14,2.96),'wood')
for yy in [-4.5,.1,4.92]:box('exposed ground beam',(0,yy,3.2),(10,.15,.17),'darkwood')
wallframe(-2.25,-2.25,.4,5.5,4.5);wallframe(-2.25,2.6,.4,5.5,4.8)
# living room
GROUP='furniture_ground'
table(-2.1,-2.25,.46,1.7,1.25,.52)
for x,y in [(-2.1,-3.4),(-2.1,-1.15),(-3.45,-2.25)]:box('indigo floor cushion',(x,y,.53),(.73,.66,.13),'navy',.08)
for x in [-2.55,-1.72]:cup(x,-2.1,1.04)
box('tea tray',(-2.18,-2.46,1.05),(.49,.35,.028),'darkwood',.035);cyl('dorayaki lower cake',(-2.2,-2.46,1.09),.12,.042,'wood');cyl('dorayaki filling',(-2.2,-2.46,1.116),.119,.019,'darkwood');sphere('dorayaki dome',(-2.2,-2.46,1.14),(.12,.12,.025),'floorwood')
box('television cabinet',(-4.38,-2.4,.67),(.57,1.55,.42),'wood',.03)
box('old television',(-4.35,-2.3,1.24),(.42,1.18,.80),'darkwood',.09)
box('television screen',(-4.112,-2.38,1.29),(.045,.90,.57),'slate',.065)
for z in [1.08,1.33]:cyl('TV rotary knob',(-4.10,-1.79,z),.052,.03,'black',rot=(0,math.pi/2,0))
pot(-4.4,-4,.45,.36)
table(-2.2,2.5,.46,1.1,1.1,.43);cup(-2.4,2.35,.96)
box('newspaper',(-2.07,2.55,.958),(.47,.33,.011),'paper')
box('green zabuton',(-2.2,1.42,.52),(.76,.68,.13),'green',.09)
shoji(-2.5,4.65,.48,3,2.4);bookshelf(-4.15,4.35,.48,.85,1.05);pot(-4.25,4.25,1.55,.23)
# Kitchen (north-east), bathroom, washroom, toilet.
GROUP='home_ground'
for yy in [-2.6,-.9,1.3]:
 box('wet room divider',(3.62,yy,1.85),(2.58,.12,2.9),'cream',solid=True)
for yy in [-3.58,-1.83,.12]:
 box('wet room door jamb',(2.26,yy-.45,1.85),(.14,.24,2.9),'wood',solid=True)
# Kitchen floor planks visible as fine seams
for i in range(20):box('kitchen floor joint',(2.78,1.6+i*.17,.403),(4.30,.008,.002),'wood')
GROUP='furniture_ground'
for xx in [2.30,3.22,4.15]:
 box('kitchen lower cabinet',(xx,4.45,.93),(.87,.80,1.04),'curtain',.025);box('cabinet wood front',(xx,4.018,.96),(.82,.04,.80),'paper',.015);rod('kitchen cabinet handle',(xx-.11,3.975,1.19),(xx+.11,3.975,1.19),.016,'slate')
box('kitchen counter',(3.2,4.43,1.49),(2.80,.93,.09),'white',.025)
box('sink silver basin',(3.30,4.40,1.54),(.62,.59,.035),'slate',.10);box('sink inside',(3.30,4.40,1.555),(.47,.43,.012),'bath',.08)
line('curved faucet',[(3.3,4.70,1.56),(3.3,4.70,1.88),(3.3,4.56,1.95),(3.3,4.41,1.88)],.025,'slate')
for yy in [4.2,4.64]:torus('stove burner',(2.23,yy,1.548),.135,.025,'black',rot=(0,0,0))
box('fridge',(4.4,2.1,1.36),(.92,.8,1.88),'white',.06)
for zz in [1.45,2.2]:rod('fridge handle',(4.10,1.67,zz-.1),(4.10,1.67,zz+.1),.022,'slate')
box('fridge seam',(4.4,1.687,1.68),(.88,.008,.017),'slate');box('fridge note',(4.45,1.67,1.22),(.25,.008,.27),'paper');sphere('fridge magnet',(4.45,1.65,1.38),(.027,.009,.027),'red')
table(2.1,2.63,.42,1.45,.88,.85)
for x,y in [(1.25,2.63),(2.95,2.63),(2.1,1.75)]:
 box('dining chair seat',(x,y,.85),(.50,.50,.08),'wood',.03)
 for s in [-1,1]:
  for t in [-1,1]:box('dining chair leg',(x+s*.18,y+t*.18,.64),(.055,.055,.45),'wood')
 box('dining chair back',(x,y-.22,1.18),(.5,.06,.60),'curtain',.025)
cup(2.25,2.6,1.32);cyl('fruit bowl',(1.8,2.7,1.37),.19,.10,'paper',r2=.23)
for i in range(3):sphere('mikan orange',(1.72+i*.08,2.7,1.44),(.08,.08,.08),'orange')
for yy in [-3.6,-1.7,.2]:
 box('wet area floor',(3.65,yy,.405),(2.52,1.78,.025),'bath')
 for i in range(8):box('tile grout',(2.45+i*.32,yy,.422),(.009,1.76,.004),'white')
 for j in range(6):box('tile grout',(3.65,yy-.8+j*.32,.423),(2.5,.009,.004),'white')
box('bath tub',(4.10,.14,.85),(1.25,1.70,.75),'white',.15)
box('bath water',(4.10,.14,1.237),(.96,1.40,.015),'water',.12)
line('shower pipe',[(4.70,.75,1.2),(4.70,.75,2.48),(4.42,.75,2.56)],.022,'slate');sphere('showerhead',(4.4,.75,2.56),(.11,.09,.04),'slate')
box('washing machine',(4.2,-1.75,.92),(.88,.83,1.01),'white',.045);torus('washer front ring',(4.2,-2.18,.92),.24,.045,'slate');cyl('washer glass',(4.2,-2.19,.92),.21,.02,'bath',rot=(math.pi/2,0,0))
sphere('toilet pedestal',(4.13,-3.77,.66),(.26,.32,.27),'white');sphere('toilet bowl',(4.13,-3.65,.91),(.35,.46,.15),'white');box('toilet cistern',(4.13,-4.05,1.15),(.58,.19,.57),'white',.07)
# entry shoes, umbrella stand, warm lamp
box('genkan lowered tile',(3.4,-3.67,.38),(2.65,1.82,.02),'concrete')
box('shoe cabinet',(2.33,-3.62,.88),(.44,1.32,.94),'wood',.025)
for yy in [-4.05,-3.68,-3.28]:
 for xx in [3.0,3.21]:sphere('slipper',(xx,yy,.44),(.08,.18,.045),'navy',12,8)
cyl('umbrella stand',(4.69,-4.14,.70),.13,.57,'slate')
for i in range(3):rod('umbrella',(4.66+i*.03,-4.14,.48),(4.64+i*.05,-4.12,1.47),.018,'book'+str(i))
# staircase: physically climbable, with a gap in upper slab
GROUP='stairs'
for i in range(16):
 top=.40+(i+1)*3.05/16;box('oak stair tread',(1.25,-.95+i*.245,top-.075),(1.26,.255,.15),'wood',.012)
for x in [.59,1.90]:
 rod('stair stringer',(x,-1.12,.43),(x,2.94,3.48),.10,'darkwood')
 for i in range(7):rod('stair baluster',(x,-.8+i*.57,.65+i*.43),(x,-.8+i*.57,1.40+i*.43),.023,'wood')
 rod('stair handrail',(x,-.95,1.35),(x,2.90,4.25),.055,'darkwood')
# Second floor: two tatami rooms either side of a central landing.
GROUP='home_upper'
box('upper west floor',(-2.85,.2,3.36),(4.3,9.6,.17),'floorwood')
box('upper east floor',(3.5,.2,3.36),(3.0,9.6,.17),'floorwood')
box('floor beside stair front',(1.55,-2.8,3.36),(.9,3.6,.17),'floorwood')
box('floor beside stair rear',(1.55,4,3.36),(.9,2,.17),'floorwood')
box('upper front landing',(.1,-3.35,3.36),(1.66,2.5,.17),'floorwood')
box('upper rear landing',(.6,3.82,3.36),(2.8,2.0,.17),'floorwood')
tatamiroom(-2.85,.2,3.44,4.12,9.4);tatamiroom(3.5,.2,3.44,2.84,9.4);tatamiroom(1.55,-2.85,3.44,.86,3.4);tatamiroom(1.55,4.0,3.44,.86,1.8)
box('upper west wall',(-5,.2,4.92),(.18,9.6,2.95),'cream',solid=True)
box('east wall lower',(5,.2,3.95),(.18,9.6,1),'cream',solid=True)
box('east wall upper',(5,.2,6.20),(.18,9.6,.5),'cream')
box('east wall rear',(5,2.25,5.12),(.18,5.50,1.50),'cream',solid=True)
box('east wall front',(5,-4.05,5.12),(.18,1.10,1.50),'cream',solid=True)
for yy in [-3.5,-2,-.5]:box('east window jamb',(5,yy,5.16),(.15,.065,1.50),'wood')
for zz in [4.43,5.16,5.88]:box('east window rail',(5,-2,zz),(.15,3.1,.065),'wood')
box('east window sill',(4.94,-2,4.42),(.38,3.2,.10),'wood',.015)
box('upper rear wall',(0,5,4.92),(10,.18,2.95),'cream',solid=True)
for xx in [-.73,1.1]:
 for yy,dd in ([(.75,6.3),(-4.25,.7)] if xx<0 else [(-1.75,1.3),(4.47,.84),(-4.25,.7)]):box('upper room corridor wall',(xx,yy,4.9),(.14,dd,2.9),'cream',solid=True)
wallframe(-2.85,.2,3.45,4.3,9.6);wallframe(3.06,.2,3.45,3.88,9.6)
GROUP='home_front_upper'
roomwall(-2.85,-4.6,3.45,4.30);roomwall(3.06,-4.6,3.45,3.88)
GROUP='furniture_upper'
# Hero desk looks toward the afternoon window; furniture rotates to face inward.
start=len(groups[GROUP]);desk(3.00,-3.92,3.54)
# desk must face the viewer from inside: south-facing standard desk is rotated 180 at its own centre
pivot=Vector((3,-3.92,0))+origin;R=Matrix.Rotation(math.pi,4,'Z')
for o in groups[GROUP][start:]:o.location=pivot+R.to_3x3()@(o.location-pivot);o.rotation_euler.rotate(R)
bookshelf(4.54,1.65,3.56,.65,2.0)
# a waist-high cabinet with iconic alarm clock and stacked comics
box('low bedroom cabinet',(1.56,-3.6,4.06),(.66,.62,.96),'wood',.02)
books(1.32,-3.92,4.56,3)
start=len(groups[GROUP]);alarmclock(1.54,-3.43,4.56)
pivot=Vector((1.54,-3.43,0))+origin;R=Matrix.Rotation(math.pi,4,'Z')
for o in groups[GROUP][start:]:o.location=pivot+R.to_3x3()@(o.location-pivot);o.rotation_euler.rotate(R)
box('blue book bin',(1.47,-3.55,4.26),(.45,.48,.25),'blue',.025)
box('zabuton bedroom',(2.74,-.35,3.59),(.7,.67,.12),'navy',.08,rot=(0,0,.28))
for i in range(3):box('manga on tatami',(2.0+i*.47,.75+random.uniform(-.2,.2),3.56),(.28,.38,.045),'book'+str(i),.008,rot=(0,0,random.uniform(-.4,.4)))
# closet depth, open sleeping berth and sliding fusuma door
box('closet back',(3.1,4.75,4.8),(3.65,.10,2.5),'darkwood')
for xx in [1.31,3.24,4.88]:box('closet upright',(xx,4.10,4.83),(.10,1.30,2.55),'wood')
for zz in [3.62,4.60,6.12]:box('closet shelf',(3.1,4.10,zz),(3.65,1.38,.09),'wood')
shoji(4.06,3.42,3.60,1.68,2.5)
box('Doraemon futon mattress',(2.28,4.09,4.73),(1.66,1.17,.17),'futon',.12)
box('folded white quilt',(2.3,4.43,4.9),(1.40,.46,.17),'paper',.10)
box('soft pillow',(2.30,3.87,4.86),(.58,.31,.10),'white',.07)
for i in range(4):box('closet comic stack',(4.10,4.0,3.7+i*.07),(.48,.63,.055),'book'+str(i),.006)
# west room and small writing alcove
table(-2.9,-.8,3.55,1.25,1.10,.48);cup(-2.8,-.8,4.09)
box('old room cushion',(-2.9,-2.0,3.63),(.78,.71,.12),'green',.08)
shoji(-3.06,4.30,3.55,3.45,2.5);bookshelf(-4.35,2.2,3.55,.8,1.1);pot(-4.35,2.2,4.69,.24)
# tokonoma, wall frames, globe and toy plane
for xx in [-4.82,4.82]:
 box('bedroom picture frame',(xx,.15,5.2),(.075,.70,.86),'wood');box('picture paper',(xx- .045 if xx>0 else xx+.045,.15,5.2),(.009,.56,.72),'paper')
sphere('geography globe',(4.59,1.65,5.85),(.23,.23,.23),'bath',24,16);torus('globe meridian',(4.59,1.65,5.85),.26,.012,'bell',rot=(math.pi/2,0,.3));cyl('globe stand',(4.59,1.65,5.59),.14,.06,'wood')
box('model plane fuselage',(1.65,-1.15,3.70),(.09,.58,.08),'yellow',.025,rot=(0,0,.4));box('model plane wing',(1.65,-1.15,3.70),(.60,.15,.036),'floorwood',.012,rot=(0,0,.4));box('model plane tail',(1.55,-1.34,3.75),(.22,.08,.035),'floorwood',.008)
# A real ceiling, individually laid boards, removable as a named game layer.
GROUP='home_ceiling'
box('plaster ceiling',(0,.2,6.49),(10,9.6,.10),'paper')
for xx in range(-5,6):box('ceiling timber grid',(xx,.2,6.375),(.065,9.6,.07),'wood')
for i in range(11):box('ceiling timber grid',(0,-4.6+i*.96,6.39),(10,.065,.07),'wood')
GROUP='furniture_upper';lamp(2.8,.1,6.40);lamp(-2.7,.1,6.40)
GROUP='furniture_ground';lamp(-2.2,-2,3.18);lamp(2.3,2.3,3.18)
GROUP='home_roof';roof(0,.20,6.53,11.25,10.8,2.08)
# Lower eaves on all street-side volumes.
GROUP='home_eaves';roof(-2.25,-5.76,3.18,6.35,3.65,.82)
roof(3.44,-5.30,3.08,3.30,2.25,.38)
GROUP='home_ground'
# guest room extension from reference floor plan
box('guest room platform',(-2.25,-6.05,.22),(5.35,2.84,.30),'floorwood')
box('guest west wall',(-4.92,-6.05,1.65),(.15,2.84,2.65),'cream',solid=True)
box('guest east wall',(.42,-6.05,1.65),(.15,2.84,2.65),'cream',solid=True)
GROUP='home_front_ground';roomwall(-2.25,-7.47,.38,5.35)
GROUP='furniture_ground'
box('guest sofa frame',(-2.23,-6.70,.69),(2.25,.72,.62),'wood',.06)
box('sofa seat',(-2.23,-6.62,.81),(1.96,.66,.23),'futon',.10)
box('sofa back',(-2.23,-6.95,1.18),(2.04,.20,.59),'futon',.08)
for s in [-1,1]:box('sofa arm',(-2.23+s*1.06,-6.60,1.02),(.20,.72,.38),'paper',.09)
table(-2.25,-5.68,.40,1.2,.65,.42);pot(-4.25,-6.60,.39,.36)
# Exterior garden, drainage, tiled entrance and block fence.
GROUP='garden'
box('Nobi garden lawn',(-.5,-8.70,.10),(13,3.0,.18),'leaf4',.12)
for i in range(9):box('entrance stepping stone',(3.45+math.sin(i)*.13,-5.0-i*.59,.18),(1.13,.52,.12),'concrete',.08,rot=(0,0,random.uniform(-.05,.05)))
for xx in [2.8,4.1]:
 for i in range(7):box('genkan ceramic tile',(xx,-5.1+i*.26,.405),(.28,.25,.02),'concrete',.01)
for x,y,r in [(-5.8,-7.8,.7),(-4.5,-8.8,.55),(-2.9,-9.1,.57),(-1.3,-8.7,.65),(1,-8.6,.6),(5.7,-6.0,.7),(5.6,-8.8,.6)]:shrub(x,y,r,flower=True)
tree(-5.5,-6.4,4.8,1.75);tree(5.9,3.7,4.0,1.4)
for x,y in [(2.25,-5),(4.72,-5),(1.1,-6),(5.4,-4.3)]:pot(x,y,.25,.36)
for y in [0,3,6]:shrub(-5.9,y,.62)
# Garden fence with staggered blocks and breeze-block openings.
for x1,x2 in [(-7,2.48),(4.48,7)]:
 for row in range(4):
  xx=x1
  while xx<x2-.04:
   ww=min(.8,x2-xx);box('boundary concrete block',(xx+ww/2,-10.2,.24+row*.28),(ww-.015,.25,.265),'concrete',.009);xx+=.8
 box('wall coping',((x1+x2)/2,-10.2,1.29),(x2-x1+.08,.36,.09),'edge',.025)
for xx in [2.48,4.48]:
 box('gate pillar',(xx,-10.2,.89),(.43,.47,1.65),'concrete',.025,solid=True);box('pillar cap',(xx,-10.2,1.74),(.53,.56,.12),'edge',.025)
sign('野比',(4.49,-10.454,1.20),.43,.25)
for side in [-1,1]:
 x=3.48+side*.98
 for j in range(7):rod('open black garden gate',(x,-10.2+j*.13,.30),(x,-10.2+j*.13,1.52),.018,'slate')
 for z in [.4,1.40]:rod('gate rail',(x,-10.20,z),(x,-9.40,z),.028,'slate')
for xx in [-7,7]:box('side boundary wall',(xx,-.90,.63),(.22,18.2,1.12),'concrete',.015,solid=True)
# Side bicycle, wheels, frame and basket
for yy in [-.65,.65]:torus('bicycle tire',(5.76,-3+yy,.54),.40,.039,'black',rot=(0,math.pi/2,0));torus('bicycle rim',(5.76,-3+yy,.54),.34,.016,'slate',rot=(0,math.pi/2,0))
line('red bicycle frame',[(5.76,-3.65,.54),(5.76,-3.25,1.05),(5.76,-2.65,1.0),(5.76,-3.0,.57),(5.76,-3.65,.54)],.035,'red');line('bicycle frame',[(5.76,-3.25,1.05),(5.76,-3,.57),(5.76,-2.35,.54),(5.76,-2.64,1.2)],.034,'red');box('bicycle saddle',(5.76,-3.30,1.12),(.23,.33,.075),'darkwood',.04);rod('handlebar',(5.5,-2.61,1.24),(6.0,-2.61,1.24),.025,'slate')
print('NOBI HOUSE COMPLETE',len(bpy.data.objects),flush=True)
# ---------------- NEIGHBORHOOD / layout inspired by the supplied map ----------------
origin=Vector((0,0,0));GROUP='town'
box('rounded miniature earth base',(0,2,-.8),(89,83,1.55),'soil',.7)
box('continuous green ground',(0,2,-.025),(88,82,.15),'leaf2',.5)
# Three continuous streets join all landmarks, with sidewalks and drains.
for road_index,(x,y,w,d) in enumerate([(0,-8,88,5),(1,6,5,67),(0,20,88,4.5),(0,-28,88,4.5),(-27,-.5,3.8,19),(27,-18,4,15)]):
 box('asphalt street',(x,y,.07+road_index*.002),(w,d,.12),'road',.025)
 if w>d:
  for yy in [y-d/2-.38,y+d/2+.38]:
   box('sidewalk',(x,yy,.17),(w,.76,.24),'concrete',.04)
   for xx in range(-42,43,2):box('sidewalk joint',(xx,yy,.293),(.012,.74,.004),'edge')
 else:
  for xx in [x-w/2-.38,x+w/2+.38]:box('sidewalk',(xx,y,.17),(.76,d,.24),'concrete',.04)
# painted crossing and quiet neighbourhood markings
for xx in [-5.6,6.6]:
 for i in range(6):box('zebra crossing',(xx,-9.65+i*.66,.138),(.38,.4,.009),'paper')
for xx in [-34,-17,14,33]:
 box('road edge paint',(xx,-10.03,.137),(4,.08,.01),'paper')
for x,y in [(1,-8),(1,20),(-27,-8),(27,-28)]:cyl('manhole cover',(x,y,.141),.32,.025,'slate',vertices=24)

def smallhouse(x,y,w=7,d=6,story=2,roofmat='slate',wall='cream',label=None):
 global GROUP
 h=2.9*story;box('house stone plinth',(x,y,.22),(w+.32,d+.3,.44),'concrete',.05)
 box('plaster house',(x,y,h/2+.4),(w,d,h),wall,.05,solid=True)
 old=GROUP;GROUP='roof_town';roof(x,y,h+.45,w+1.0,d+1.15,1.45,roofmat);GROUP=old
 for floor in range(story):
  for xx in [-w*.24,w*.24]:window(x+xx,y-d/2-.04,1.78+floor*2.9,w*.32,1.25)
  window(x+w/2+.03,y,1.75+floor*2.9,2.0,1.28,rot=math.pi/2)
 for s in [-1,1]:box('house corner trim',(x+s*(w/2-.04),y-d/2-.06,h/2+.4),(.13,.10,h),'wood')
 box('wood entrance door',(x+w*.26,y-d/2-.11,1.39),(1.10,.12,1.98),'wood',.025)
 box('entrance glass',(x+w*.26,y-d/2-.182,1.61),(.43,.023,.67),'bath')
 box('entry step',(x+w*.26,y-d/2-.50,.25),(1.58,.88,.33),'concrete',.04)
 if label:sign(label,(x+w*.43,y-d/2-.09,1.59),.55,.27)
 for xx in [-w/2,w/2]:
  rod('rainwater downpipe',(x+xx,y-d/2-.17,.35),(x+xx,y-d/2-.17,h+.35),.042,'slate')
 box('outdoor AC unit',(x-w*.28,y-d/2-.37,.68),(1.1,.49,.66),'paper',.04)
 for i in range(9):box('AC vent',(x-w*.28-.42+i*.105,y-d/2-.62,.68),(.025,.018,.46),'slate')
 for i in range(4):shrub(x-w*.45+i*w*.2,y-d/2-1.3,.48,flower=i%2==0)
 tree(x-w/2-1.25,y+1.0,4.2,1.3)
 for xx in [x-w/2-1.1,x+w/2+1.1]:box('residential wall',(xx,y,.64),(.20,d+3,1.10),'concrete',.02,solid=True)

# Far-left Gian's family shop; west-front Suneo; Shizuka south of Nobi.
smallhouse(-34,5,8.3,7.4,2,'roofBlue',label='剛田')
# store front replaces ground window impression with vivid striped awning and crates
for i in range(12):box('Goda grocery striped awning',(-37.55+i*.64,.65,2.7),(.64,1.52,.16),'paper' if i%2 else 'green',.02,rot=(.13,0,0))
sign('剛田商店',(-34,.98,3.0),5.8,.56)
for x in [-36,-34.9,-33.8]:
 box('produce crate',(x,.30,.53),(.90,.7,.55),'wood',.02)
 for i in range(9):sphere('shop produce',(x+random.uniform(-.3,.3),.30+random.uniform(-.22,.22),.88),(.11,.11,.1),'orange' if x==-36 else 'leaf4',10,6)
smallhouse(-33,-18,9.0,7.8,2,'roofGreen',label='骨川')
# Modern wing and balcony distinguish Suneo's larger house.
box('Suneo modern wing',(-27.75,-16.7,2.75),(3.6,4.6,5.1),'paper',.07,solid=True)
box('Suneo flat roof',(-27.75,-16.7,5.36),(3.95,4.93,.23),'concrete',.04)
box('balcony base',(-33,-22.65,3.18),(8.0,1.45,.20),'paper',.04)
for i in range(24):rod('balcony metal rail',(-36.8+i*.33,-23.3,3.2),(-36.8+i*.33,-23.3,4.18),.018,'paper')
rod('balcony top rail',(-36.8,-23.3,4.18),(-29.2,-23.3,4.18),.04,'paper')
smallhouse(-12,-18,7.5,7.0,2,'tile',label='源')
# gentle pink trim gives Shizuka's home a distinct identity
box('Shizuka entrance awning',(-10,-22.0,2.7),(2.3,1.1,.15),'pink',.04)
for x in [-15.1,-13.8,-12.5]:shrub(x,-23.4,.6,flower=True)
# north neighborhood and rear railway station
for args in [(-12,30,8,6,1,'roofBlue'),(-30,30,7,7,2,'tile'),(12,29,7,6,2,'roofGreen'),(32,29,8,7,1,'tile'),(34,-.5,7,7,2,'roofBlue'),(32,12,7,6,1,'roofGreen'),(-11,-35,8,5,1,'roofGreen'),(-33,-35,7,5,1,'tile')]:smallhouse(*args)
# vacant lot to the east of the Nobi block
box('vacant lot dry earth',(16,4,.13),(21,22,.16),'sand',.20)
for x in [6,26]:
 for y in range(-5,15,2):cyl('lot fence post',(x,y,.73),.07,1.22,'darkwood')
 for z in [.51,.94]:rod('lot fence rail',(x,-5,z),(x,15,z),.045,'wood')
for x in range(6,27,2):cyl('lot rear post',(x,15,.74),.07,1.2,'darkwood')
for z in [.51,.94]:rod('lot rear rail',(6,15,z),(26,15,z),.045,'wood')
# Iconic three open concrete drainage pipes, actual hollow interiors.
def pipe(x,y,z):
 n=40;vs=[];fs=[];r=.88;inner=.71;d=3.6
 for yy,rr in [(-d/2,r),(d/2,r),(-d/2,inner),(d/2,inner)]:
  for i in range(n):a=i*math.tau/n;vs.append((x+rr*math.cos(a),y+yy,z+rr*math.sin(a)))
 for i in range(n):
  j=(i+1)%n;fs.extend([(i,j,n+j,n+i),(2*n+i,3*n+i,3*n+j,2*n+j),(i,2*n+i,2*n+j,j),(n+i,n+j,3*n+j,3*n+i)])
 me=bpy.data.meshes.new('hollow concrete pipe');me.from_pydata(vs,[],fs);me.update();obj('stacked hollow pipe',me,material='concrete')
 for yy in [-1.8,1.8]:torus('pipe thick rim',(x,y+yy,z),.79,.09,'concrete')
pipe(14.25,8,1.07);pipe(16.05,8,1.07);pipe(15.15,8,2.64)
colliders.append({'x':15.15,'y':8,'z':1.7,'w':3.7,'d':3.8,'h':3.2,'group':'town'})
for x,y in [(8,12),(23,11),(22,1),(7,-2)]:tree(x,y,4.9,1.8)
for i in range(100):
 x=random.uniform(6,26);y=random.uniform(-5,14)
 if random.random()<.7 and 9<x<22 and -3<y<10:continue
 for k in range(3):rod('dry grass',(x,y,.22),(x+random.uniform(-.08,.08),y+random.uniform(-.08,.08),random.uniform(.30,.52)),.012,'leaf3')
sign('みんなの広場',(7,-4.8,1.5),1.7,.60)
# school in the south-east: L-shaped building, sports yard and gates.
box('school courtyard',(17,-21,.08),(24,20,.17),'sand')
for x,y,w,d in [(20,-32,27,5.2),(31,-23.94,5,10.8)]:
 box('elementary school',(x,y,3.8),(w,d,7.4),'paper',.06,solid=True)
 box('school flat roof',(x,y,7.6+(.024 if w<6 else 0)),(w+.5,d+.5,.24),'concrete',.025)
 for floor in range(3):
  for i in range(int(w/1.6)-1):window(x-w/2+1.5+i*1.6,y-d/2-.04,1.4+floor*2.25,1.14,1.23)
 # north face, visible from the neighborhood
 for floor in range(3):
  for i in range(int(w/1.65)-1):window(x-w/2+1.5+i*1.65,y+d/2+.06,1.4+floor*2.25,1.14,1.23,rot=math.pi)
sign('月見台小学校',(18,-34.68,7.0),5.3,.65)
for x in [7,28]:box('school gate pillar',(x,-12.5,1.0),(.7,.7,2.0),'concrete',.03)
# oval athletics track and football goal
for r in [6.4,6.8]:
 pts=[(17+math.cos(i*math.tau/80)*r, -21+math.sin(i*math.tau/80)*r*.6,.185) for i in range(81)];line('school running track',pts,.035,'paper')
line('goal frame',[(11,-24,.2),(11,-24,2.25),(14,-24,2.25),(14,-24,.2)],.048,'paper')
rod('flagpole',(29,-16,.1),(29,-16,8.7),.045,'slate');box('school flag',(29.60,-16,8.10),(1.2,.03,.75),'paper');sphere('flag red sun',(29.60,-16.021,8.10),(.19,.015,.19),'red')
# railway along the north, compact old station
box('railway embankment',(0,40,.28),(87,5.5,.50),'edge')
for yy in [39,40.6]:rod('steel rail',(-43,yy,.65),(43,yy,.65),.045,'slate')
for x in range(-43,44):box('railway sleeper',(x,39.8,.53),(.17,2.65,.16),'darkwood')
box('station platform',(0,35.80,.55),(17,3.9,1.1),'concrete',.07)
for x in [-7,-3,3,7]:box('station roof support',(x,35.8,2.2),(.13,.13,3.35),'wood')
GROUP='roof_town';roof(0,35.8,3.85,18.3,4.5,1.1,'roofBlue');GROUP='town';sign('月見台駅',(0,33.52,3.27),3.0,.56)
# local green-and-cream train, seats visible through dark blue windows
box('local train',(20,39.8,2.05),(14,2.40,2.55),'paper',.23)
box('train green belt',(20,38.58,1.52),(13.6,.06,.50),'green',.025)
for i in range(10):box('train window',(14.1+i*1.3,38.54,2.48),(.99,.05,.87),'slate',.08)
for x in [14,17,23,26]:cyl('train wheel',(x,38.90,.8),.43,.13,'black',rot=(math.pi/2,0,0))
# Electricity poles and sagging wires: the familiar Japanese streetscape.
for x,y in [(-23,-5),(-3,-5),(20,-5),(39,-5),(-23,17),(-3,17),(20,17)]:
 cyl('concrete utility pole',(x,y,4.2),.13,8.35,'concrete',r2=.095)
 for z in [7.15,7.80]:rod('utility crossarm',(x-.90,y,z),(x+.90,y,z),.053,'slate')
 for dx in [-.72,.72]:
  cyl('ceramic insulator',(x+dx,y,7.35),.085,.23,'paper');cyl('ceramic insulator',(x+dx,y,7.98),.085,.23,'paper')
 box('pole transformer',(x+.19,y,6.40),(.44,.49,.66),'slate',.07)
for y in [-5,17]:
 for x1,x2 in [(-23,-3),(-3,20),(20,39)]:
  for offset in [-.72,.72]:
   pts=[(x1+(x2-x1)*i/16+offset,y,7.95-.9*math.sin(i/16*math.pi)) for i in range(17)];line('sagging power line',pts,.014,'slate')
# edge greenery frames the miniature district without obstructing the hero building
for x,y in [(-41,33),(-41,15),(-41,-19),(-40,-34),(41,34),(41,18),(41,-16),(39,-34),(6,31),(24,31),(-20,14),(-19,-24)]:tree(x,y,random.uniform(4,6),1.65)
print('TOWN COMPLETE',len(bpy.data.objects),flush=True)
# ---------------- CHARACTERS / smooth dimensional interpretations ----------------
actor_origins={}
def doraemon(x,y,z,scale=1,name='doraemon'):
 global GROUP,origin
 GROUP='actor_'+name;origin=Vector((x,y,z));actor_origins[GROUP]=(x,y,z)
 start=len(groups[GROUP])
 sphere('Doraemon blue body',(0,0,.52),(.42,.30,.46),'blue',32,20)
 sphere('white tummy',(0,-.271,.53),(.33,.057,.32),'white',32,20)
 # pocket is a white hemisphere boundary, modelled as a curve on the belly
 pts=[(.22*math.cos(i*math.pi/24),-.337,.54-.19*math.sin(i*math.pi/24)) for i in range(25)];line('four-dimensional pocket seam',pts,.010,'slate');rod('pocket opening',(-.22,-.337,.54),(.22,-.337,.54),.010,'slate')
 for s in [-1,1]:
  sphere('white foot',(s*.23,-.12,.11),(.24,.31,.115),'white',24,16)
  rod('blue arm',(s*.32,0,.66),(s*.51,-.10,.43),.12,'blue');sphere('round white hand',(s*.53,-.12,.43),(.145,.145,.145),'white',24,16)
 sphere('round blue head',(0,0,1.16),(.57,.45,.53),'blue',40,28)
 sphere('white face',(0,-.354,1.13),(.48,.115,.419),'white',40,28)
 for s in [-1,1]:
  sphere('oval eye',(s*.112,-.421,1.445),(.119,.062,.162),'white',24,16)
  sphere('black eye pupil',(s*.081,-.479,1.429),(.024,.018,.057),'black',20,12)
  sphere('eye glint',(s*.081-.007,-.495,1.447),(.009,.005,.014),'white',12,8)
 sphere('red nose',(0,-.507,1.288),(.095,.082,.083),'red',24,16);sphere('nose glint',(-.025,-.573,1.321),(.018,.009,.016),'white',12,8)
 rod('nose centre line',(0,-.479,1.23),(0,-.479,.96),.01,'black')
 pts=[(.32*math.cos(i*math.pi/32),-.466,1.075-.19*math.sin(i*math.pi/32)) for i in range(33)];line('friendly smile',pts,.012,'black')
 for s in [-1,1]:
  for i in range(3):rod('whisker',(s*.22,-.473,1.14-i*.066),(s*.435,-.433,1.23-i*.13),.009,'black')
 torus('red collar',(0,0,.742),.359,.044,'red',rot=(0,0,0));sphere('golden bell',(0,-.399,.672),(.09,.07,.095),'bell',24,16);rod('bell stripe',(-.078,-.456,.684),(.078,-.456,.684),.01,'darkwood');sphere('bell hole',(0,-.468,.644),(.019,.007,.024),'black',12,8)
 sphere('red tail',(0,.345,.40),(.09,.09,.09),'red')
 if scale!=1:
  for o in groups[GROUP][start:]:o.location=origin+(o.location-origin)*scale;o.scale*=scale

def person(name,pos,shirt='yellow',height=1.55,glasses=False,girl=False,heavy=False,spiky=False,adult=False):
 global GROUP,origin
 GROUP='actor_'+name;origin=Vector(pos);actor_origins[GROUP]=pos
 start=len(groups[GROUP]);w=.26 if not heavy else .38;head=.32 if not heavy else .36
 # shoes, sock, knees and shorts
 for s in [-1,1]:
  sphere('dark shoe',(s*w*.57,-.08,.075),(.115,.21,.085),'navy',20,12)
  cyl('white sock',(s*w*.57,0,.24),.072,.23,'white')
  cyl('bare leg',(s*w*.57,0,.41),.073,.21,'skin')
  box('shorts leg',(s*w*.58,0,.565),(.22,.28,.20),'navy',.045)
 if girl:
  cyl('flared pink skirt',(0,0,.61),.29,.26,'pink',r2=.17,vertices=32)
 sphere('shirt body',(0,0,.82),(w,.185,.30),shirt,28,20)
 sphere('soft shirt hem',(0,0,.64),(w*.93,.176,.105),shirt,24,16)
 # white collar, real triangle meshes
 for s in [-1,1]:
  vs=[(s*.025,-.175,1.06),(s*.17,-.16,1.00),(s*.075,-.21,.91)];me=bpy.data.meshes.new('pointed collar');me.from_pydata(vs,[],[(0,1,2)]);obj('white collar',me,material='white')
  sphere('shirt sleeve',(s*(w+.035),-.01,.90),(.12,.14,.16),shirt)
  rod('skin forearm',(s*(w+.06),-.02,.83),(s*(w+.11),-.075,.64),.064,'skin');sphere('hand',(s*(w+.115),-.078,.62),(.086,.069,.096),'skin')
 cyl('neck',(0,0,1.085),.105,.14,'skin')
 sphere('head',(0,-.015,1.33),(head,.27,.325),'skin',40,28)
 for s in [-1,1]:sphere('ear',(s*(head-.005),-.01,1.30),(.072,.047,.09),'skin')
 # fitted upper hair cap, not an intersecting full sphere
 n=40;rows=12;vs=[];fs=[]
 for j in range(rows+1):
  t=j/rows
  for i in range(n):
   a=i*math.tau/n;phi=t*(1.18+.20*math.cos(a*3))
   vs.append((head*1.025*math.sin(phi)*math.cos(a),-.008+.274*math.sin(phi)*math.sin(a),1.33+.335*math.cos(phi)))
 for j in range(rows):
  for i in range(n):fs.append((j*n+i,j*n+(i+1)%n,(j+1)*n+(i+1)%n,(j+1)*n+i))
 me=bpy.data.meshes.new('sculpted hair cap');me.from_pydata(vs,[],fs);me.update()
 for p in me.polygons:p.use_smooth=True
 obj('sculpted hair',me,material='hair')
 for s in [-1,1]:
  eyeX=s*.125
  sphere('white eye',(eyeX,-.253,1.36),(.105,.047,.137),'white',24,16)
  sphere('pupil',(eyeX+s*.003,-.296,1.354),(.030,.014,.061),'black',20,12)
  sphere('eye light',(eyeX-.007,-.308,1.378),(.009,.005,.016),'white',12,6)
  rod('eyebrow',(eyeX-.073,-.258,1.515),(eyeX+.053,-.27,1.529),.015,'hair')
  if glasses:torus('round glasses',(eyeX,-.313,1.368),.116,.011,'black')
 if glasses:
  rod('glasses bridge',(-.016,-.32,1.381),(.016,-.32,1.381),.011,'black')
  for s in [-1,1]:rod('glasses side',(s*.24,-.302,1.385),(s*.31,-.02,1.385),.010,'black')
 sphere('little nose',(0,-.294,1.278),(.045,.045,.041),'skin',20,12)
 line('happy smile',[(-.086,-.272,1.203),(-.042,-.287,1.181),(0,-.293,1.176),(.044,-.287,1.183),(.086,-.272,1.205)],.009,'darkwood')
 if girl:
  for s in [-1,1]:
   sphere('pigtail',(s*.36,.09,1.19),(.13,.09,.23),'hair',20,12);sphere('hair ribbon',(s*.32,.055,1.34),(.065,.055,.042),'pink')
 if spiky:
  for i in range(3):
   vs=[(-.28+i*.13,-.12,1.56),(.12+i*.13,.10,1.58),(.50+i*.035,-.15,1.78-i*.055),(-.20+i*.10,.19,1.57)];me=bpy.data.meshes.new('Suneo hair spike');me.from_pydata(vs,[],[(0,1,2),(0,2,3),(3,2,1),(0,3,1)]);obj('swept pointed hair',me,material='hair')
 if heavy:box('Gian white shirt stripe',(0,-.183,.80),(w*1.8,.026,.14),'paper',.02)
 factor=height/1.66
 for o in groups[GROUP][start:]:o.location=origin+(o.location-origin)*factor;o.scale*=factor

person('nobita',(-9,-6.3,.20),'yellow',1.60,glasses=True)
doraemon(-11,-5.6,.20,1.05)
person('shizuka',(-9,-24,.22),'pink',1.58,girl=True)
person('gian',(17,2,.23),'orange',1.95,heavy=True)
person('suneo',(13,1,.23),'curtain',1.48,spiky=True)
person('tamako',(-15,7.8,.52),'pink',1.95,glasses=True,girl=True,adult=True)
person('nobisuke',(-16,3.0,.52),'paper',1.94,glasses=True,adult=True)
# mini Doraemon toy sits in the closet, with actual life-size berth left available
# A separate room prop avoids duplicating the interactive character.
doraemon(-10.72,9.10,4.88,.60,'closet_toy')
print('CHARACTERS COMPLETE',len(bpy.data.objects),flush=True)
# ---------------- MERGE BY SEMANTIC LAYER, KEEP EDITABLE SOURCE ----------------
origin=Vector((0,0,0))
# Save full editable assembly before optimizing export. Every tile and furniture part remains editable.
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.world.color=(.35,.42,.52)
scene.world.use_nodes=True;bg=scene.world.node_tree.nodes.get('Background');bg.inputs[0].default_value=(.68,.79,.91,1);bg.inputs[1].default_value=.65
# motivated soft afternoon sun
ld=bpy.data.lights.new('Warm afternoon sun','SUN');lo=bpy.data.objects.new('Warm afternoon sun',ld);scene.collection.objects.link(lo);lo.rotation_euler=Vector((22,38,-48)).to_track_quat('-Z','Y').to_euler();ld.energy=3.0;ld.angle=math.radians(5);ld.color=(1.0,.87,.66)
for name,loc,power,size in [('Soft sky',(-16,-10,18),1500,15),('Bedroom window bounce',(-10.1,.1,5.5),280,2.1),('Bedroom fill',(-10.0,6.4,5.8),100,3.0)]:
 ld=bpy.data.lights.new(name,'AREA');lo=bpy.data.objects.new(name,ld);scene.collection.objects.link(lo);lo.location=loc;ld.energy=power;ld.shape='DISK';ld.size=size;lo.rotation_euler=(Vector((-11,5,3))-lo.location).to_track_quat('-Z','Y').to_euler();ld.color=(1.0,.87,.69)
cd=bpy.data.cameras.new('Town delivery camera');cam=bpy.data.objects.new('Town delivery camera',cd);scene.collection.objects.link(cam);scene.camera=cam
cam.location=(36,-51,48);cam.rotation_euler=(Vector((-3,3,0))-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=69
scene.render.resolution_x=1600;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.1
# group collections improve native editing and preserve semantic layer names
for group,objects in groups.items():
 col=bpy.data.collections.new(group);scene.collection.children.link(col)
 for o in objects:
  for c in list(o.users_collection):c.objects.unlink(o)
  col.objects.link(o)
bpy.ops.wm.save_as_mainfile(filepath=DELIVER+'/哆啦A梦小镇.blend')
print('EDITABLE BLEND SAVED',flush=True)
# convert curves, merge objects per layer: fewer draw calls in real-time, all textures embedded
# Merge directly from mesh arrays, avoiding quadratic selection/dependency updates.
bpy.context.view_layer.update()
all_originals=[]
for group,objects in groups.items():
 vertices=[];faces=[];smooth=[];material_ids=[];uv_values=[];material_slots=[];slot_by_name={}
 pivot=Vector(actor_origins.get(group,(0,0,0)))
 for o in objects:
  eval_obj=None
  if o.type=='MESH':me=o.data
  else:eval_obj=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=eval_obj.to_mesh()
  offset=len(vertices);mw=o.matrix_world
  vertices.extend([tuple(mw@v.co-pivot) for v in me.vertices])
  uv=me.uv_layers.active.data if me.uv_layers.active else None
  for poly in me.polygons:
   faces.append(tuple(offset+v for v in poly.vertices));smooth.append(poly.use_smooth)
   material=me.materials[poly.material_index] if me.materials else mats['paper']
   if material.name not in slot_by_name:slot_by_name[material.name]=len(material_slots);material_slots.append(material)
   material_ids.append(slot_by_name[material.name])
   for li in poly.loop_indices:uv_values.extend(uv[li].uv[:] if uv else (0,0))
  if eval_obj:eval_obj.to_mesh_clear()
 me=bpy.data.meshes.new(group+'_mesh');me.from_pydata(vertices,[],faces);me.update()
 for material in material_slots:me.materials.append(material)
 me.polygons.foreach_set('material_index',material_ids);me.polygons.foreach_set('use_smooth',smooth)
 uv=me.uv_layers.new(name='UVMap');uv.data.foreach_set('uv',uv_values)
 o=bpy.data.objects.new(group,me);scene.collection.objects.link(o);o.location=pivot
 all_originals.extend(objects)
 print('MERGED',group,len(vertices),flush=True)
bpy.data.batch_remove(ids=all_originals)
with open(OUT+'/world.json','w') as f:json.dump({'colliders':colliders,'actors':actor_origins,'home':{'x':-13,'y':5},'units':'meters','sourceAxis':'Blender Z-up; convert to Three [x,z,-y]'},f,ensure_ascii=False)
bpy.ops.object.select_all(action='DESELECT')
for o in scene.objects:
 if o.type=='MESH':o.select_set(True)
bpy.ops.export_scene.gltf(filepath=OUT+'/town.glb',export_format='GLB',use_selection=True,export_apply=True,export_lights=False,export_cameras=False,export_yup=True,export_image_format='AUTO',export_materials='EXPORT',export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6)
# Preserve the color multipliers that the glTF exporter omits on linked Mix nodes.
import struct
with open(OUT+'/town.glb','rb') as f:blob=f.read()
n=struct.unpack_from('<I',blob,12)[0];doc=json.loads(blob[20:20+n]);binary=blob[20+n:]
for material in doc.get('materials',[]):
 v={'aged walnut':.34,'warm oak':.66,'honey floor':.85}.get(material.get('name'))
 if v:material['pbrMetallicRoughness']['baseColorFactor']=[v,v*.91,v*.82,1]
j=json.dumps(doc,separators=(',',':')).encode();j+=b' '*((-len(j))%4)
with open(OUT+'/town.glb','wb') as f:f.write(struct.pack('<III',0x46546c67,2,20+len(j)+len(binary))+struct.pack('<II',len(j),0x4e4f534a)+j+binary)
print('GLB EXPORTED',os.path.getsize(OUT+'/town.glb'),flush=True)
# Native rendered visual QA, independent of the browser.
scene.render.filepath=DELIVER+'/渲染预览/town-preview.png';bpy.ops.render.render(write_still=True)
print('TOWN RENDERED',flush=True)
cd.type='PERSP';cd.lens=22;cam.location=(-11.18,4.30,5.02);cam.rotation_euler=(Vector((-9.93,1.25,4.78))-cam.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1440;scene.render.resolution_y=1000;scene.render.filepath=DELIVER+'/渲染预览/bedroom-preview.png';bpy.ops.render.render(write_still=True)
print('BEDROOM RENDERED',flush=True)

cd.type='PERSP';cd.lens=52;cam.location=(-6.9,-10.6,2.75);cam.rotation_euler=(Vector((-10.3,-5.6,1.0))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.resolution_x=1300;scene.render.resolution_y=1000;scene.render.filepath=DELIVER+'/渲染预览/characters-preview.png';bpy.ops.render.render(write_still=True)
