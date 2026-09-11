"""Revision 02: original Travel Frog furniture, real shared scene and layout contract.
Blender Z-up authoring; runtime metadata is Godot Y-up. No new frog model is generated.
Run build-frog-home.py first, then this script with Blender --background --python.
"""
from pathlib import Path
import bpy, math, json, random, numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'worlds/frog/source/assets'
NATIVE=ROOT/'worlds/frog/blender'
RENDERS=NATIVE/'revision-02-renders'; RENDERS.mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for m in list(bpy.data.materials):bpy.data.materials.remove(m)
rng=random.Random(912);cx,cy=-15.,12.;FLOOR=.188;LOFT=3.25
furniture=[];collisions=[];stairs=[];route=[]
def world(p):return (cx+p[0],cy+p[1],p[2])
def godot(p):return [round(cx+p[0],5),round(p[2],5),round(-cy-p[1],5)]
def mat(name,c1,c2=None,kind='noise',rough=.84,emission=0):
 m=bpy.data.materials.new('R02 '+name);m.use_nodes=True;m.diffuse_color=(*c1,1)
 bs=next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(*c1,1);bs.inputs['Roughness'].default_value=rough
 if emission:bs.inputs['Emission Color'].default_value=(*c1,1);bs.inputs['Emission Strength'].default_value=emission
 if c2:
  n=1024 if kind=='bark' else 512;yy,xx=np.mgrid[:n,:n]/n;nr=np.random.default_rng(len(bpy.data.materials)*19)
  def value_noise(grid):
   a=nr.random((grid+1,grid+1));a[-1,:]=a[0,:];a[:,-1]=a[:,0]
   gx,gy=xx*grid,yy*grid;ix,iy=gx.astype(int),gy.astype(int);u,v=gx-ix,gy-iy;u=u*u*(3-2*u);v=v*v*(3-2*v)
   return (1-v)*((1-u)*a[iy,ix]+u*a[iy,ix+1])+v*((1-u)*a[iy+1,ix]+u*a[iy+1,ix+1])
  micro=nr.random((n,n));coarse=value_noise(5);detail=value_noise(19)
  if kind=='wood':
   phase=xx*51+2*np.sin(yy*7+xx*3)+.6*np.sin(yy*29)
   f=.49+.14*np.sin(phase)+.09*np.sin(phase*2.7)+.035*micro
   h=.018*f+.0009*micro
  elif kind=='bark':
   phase=xx*math.tau*28+.60*np.sin(yy*math.tau*2)+.35*np.sin(yy*math.tau*7)+.48*detail
   grooves=np.maximum(0,.16-np.abs(np.sin(phase)))/.16
   f=np.clip(.29+.31*coarse+.24*detail-grooves*.20+.035*micro,0,1)
   h=.010*coarse+.003*detail-grooves*.0045+.00055*micro
  elif kind=='cloth':
   wx=.5+.5*np.sin(xx*math.tau*72);wy=.5+.5*np.sin(yy*math.tau*72)
   over=np.sin(xx*math.pi*72)*np.sin(yy*math.pi*72)
   f=.46+.09*wx+.09*wy+.035*over+.028*micro;h=.0024*(wx+wy)+.00045*micro
  elif kind=='felt':
   fine=value_noise(95)
   f=.36+.26*coarse+.18*detail+.12*micro;h=.0018*fine+.00075*micro
  elif kind=='rings':
   rad=np.sqrt(((xx-.47)*1.03)**2+((yy-.51)*.96)**2)
   f=.52+.12*np.sin(rad*171+np.sin(xx*21)*.9+np.sin(yy*9)*.8)+.045*micro
   h=.008*f+.001*micro
  elif kind=='pottery':
   glaze=np.clip((.6*coarse+.4*detail-.34)*2.3,0,1)
   f=.22+.62*glaze+.025*micro;h=.0008*micro+.00035*np.sin(yy*math.tau*41)+.001*detail
  elif kind=='limestone':
   f=.24+.46*coarse+.27*detail+.035*micro;h=.012*coarse+.003*detail+.0006*micro
  else:
   f=.30+.42*coarse+.22*detail+.04*micro;h=.007*coarse+.002*detail+.0005*micro
  rgb=np.array(c1)[None,None,:]*(1-f[...,None])+np.array(c2)[None,None,:]*f[...,None]
  px=np.ones((n,n,4),dtype=np.float32);px[:,:,:3]=np.where(rgb<=.0031308,12.92*rgb,1.055*np.power(rgb,1/2.4)-.055)
  im=bpy.data.images.new(m.name+' color',n,n);im.pixels.foreach_set(px.ravel());im.pack()
  node=m.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;m.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color'])
  dy,dx=np.gradient(h,1.5/n);normal_vectors=np.dstack((-dx,-dy,np.ones_like(dx)));normal_vectors/=np.sqrt(np.sum(normal_vectors**2,axis=2))[...,None];px[:,:,:3]=normal_vectors*.5+.5
  im=bpy.data.images.new(m.name+' normal',n,n);im.colorspace_settings.name='Non-Color';im.pixels.foreach_set(px.ravel());im.pack()
  node=m.node_tree.nodes.new('ShaderNodeTexImage');node.image=im;normal=m.node_tree.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.84
  m.node_tree.links.new(node.outputs['Color'],normal.inputs['Color']);m.node_tree.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
 return m
wood=mat('Honey wood',(.18,.089,.032),(.34,.195,.077),'wood')
bark=mat('Chestnut trunk',(.105,.048,.016),(.235,.12,.040),'bark')
cut=mat('Stump endgrain',(.35,.22,.082),(.54,.37,.17),'rings')
mushroom_under=mat('Warm grey mushroom gills',(.29,.255,.19),(.48,.42,.305),'limestone')
mushroom=mat('Cream shelf mushroom',(.50,.365,.195),(.75,.625,.405),'rings')
blue=mat('Blue sleeping quilt',(.12,.25,.34),(.22,.38,.48),'cloth')
rose=mat('Rose woven mat',(.36,.13,.14),(.56,.27,.25),'cloth')
linen=mat('Oat linen',(.60,.53,.38),(.78,.71,.55),'cloth')
leafmat=mat('Moss leaf cloth',(.125,.20,.028),(.255,.345,.075),'felt')
leaflight=mat('Soft moss patches',(.15,.23,.035),(.30,.38,.085),'felt')
leafdark=mat('Deep green leaves',(.075,.18,.045),(.18,.30,.08))
vein=mat('Leaf veins',(.41,.47,.18))
clay=mat('Cream pottery',(.30,.225,.135),(.63,.56,.405),'pottery',rough=.58)
terra=mat('Earth pottery',(.155,.072,.030),(.34,.19,.075),'pottery',rough=.72)
hearthstone=mat('Warm carved hearth stone',(.31,.265,.19),(.53,.465,.34),'limestone',rough=.94)
charcoal=mat('Hearth charcoal',(.048,.056,.042),rough=.92)
parchment=mat('Map parchment',(.72,.65,.47))
mapink=mat('Map faded moss ink',(.29,.33,.16))
rope=mat('Flax binding',(.39,.31,.16))
brass=mat('Aged brass',(.36,.27,.087),rough=.45)
flame=mat('Candle flame',(.98,.55,.10),rough=.5,emission=3)
white=mat('Wax and pages',(.81,.77,.62))

def uv(o):
 if o.type!='MESH':return
 d=o.data
 if not d.uv_layers:d.uv_layers.new(name='UVMap')
 for face in d.polygons:
  axis=max(range(3),key=lambda a:abs(face.normal[a]));axes=[a for a in range(3) if a!=axis]
  for i in face.loop_indices:
   p=d.vertices[d.loops[i].vertex_index].co;d.uv_layers.active.data[i].uv=(p[axes[0]]*.7,p[axes[1]]*.7)
def tag(o,name,m):
 o.name=name
 if m:o.data.materials.append(m)
 furniture.append(o);return o
def smooth(o):
 for p in o.data.polygons:p.use_smooth=True
 return o
def mesh(name,pts,faces,m,uvcoords=None):
 d=bpy.data.meshes.new(name);d.from_pydata([world(p) for p in pts],[],faces);d.update();o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);tag(o,name,m);uv(o)
 if uvcoords:
  for loop in d.loops:d.uv_layers.active.data[loop.index].uv=uvcoords[loop.vertex_index]
 return o
def box(name,p,size,m,bevel=.035,rot=0):
 bpy.ops.mesh.primitive_cube_add(size=1,location=world(p));o=tag(bpy.context.object,name,m);o.dimensions=size;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);uv(o);o.rotation_euler.z=rot
 if bevel:
  mod=o.modifiers.new('Worn edges','BEVEL');mod.width=bevel;mod.segments=3
 return o
def sphere(name,p,size,m,seg=24,rings=12):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,radius=1,location=world(p));o=tag(bpy.context.object,name,m);o.scale=size;return smooth(o)
def beam(name,a,b,r,m,r2=None,seg=16):
 d=Vector(b)-Vector(a);bpy.ops.mesh.primitive_cone_add(vertices=seg,radius1=r,radius2=r if r2 is None else r2,depth=d.length,location=world((Vector(a)+Vector(b))*.5));o=tag(bpy.context.object,name,m);o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return smooth(o)
def tube(name,pts,r,m):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.resolution_u=5;d.bevel_depth=r;d.bevel_resolution=1
 sp=d.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
 for b,p in zip(sp.bezier_points,pts):b.co=world(p);b.handle_left_type='AUTO';b.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);return tag(o,name,m)
def ring(name,p,r,t,m,axis='Z'):
 bpy.ops.mesh.primitive_torus_add(major_radius=r,minor_radius=t,major_segments=40,minor_segments=8,location=world(p));o=tag(bpy.context.object,name,m)
 if axis=='Y':o.rotation_euler.x=math.pi/2
 if axis=='X':o.rotation_euler.y=math.pi/2
 return smooth(o)
def collision(name,p,size,yaw=0):collisions.append({'name':name,'position':godot(p),'size':[size[0],size[2],size[1]],'yaw':-yaw})
def slab(name,poly,z,h,m):
 n=len(poly);o=mesh(name,[(x,y,zz) for zz in [z-h,z] for x,y in poly],[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],m)
 mod=o.modifiers.new('Worn slab edge','BEVEL');mod.width=.017;mod.segments=2;return o

# Rear loft, a clipped deck with individual floorboards and slim supporting posts.
loft_poly=[(-4.04,1.35),(3.63,1.35),(3.66,2.78),(2.2,4.27),(-2.2,4.27),(-3.9,3.06)]
def clip(poly,nx,ny,d):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  fa=a[0]*nx+a[1]*ny-d;fb=b[0]*nx+b[1]*ny-d
  if fa<=0:out.append(a)
  if (fa<0)!=(fb<0):
   t=fa/(fa-fb);out.append((a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t))
 return out
for i in range(21):
 x=-4.08+i*.38;p=clip(clip(loft_poly,1,0,x+.363),-1,0,-x)
 if len(p)>2:slab('Loft individual plank %02d'%i,p,LOFT,.15,wood)
box('Loft front timber',(-.2,1.43,3.08),(7.62,.22,.25),wood,.04)
for x in [-1.9,3.34]:
 beam('Loft slim post',(x,1.52,FLOOR),(x,1.52,3.08),.10,wood,.085)
 collision('Loft post',(x,1.52,1.65),(.21,.21,2.93))
# Low original rope rail. Left landing stays open for the mushroom stair.
for x in [-2.35,-1.35,-.3,.75,1.8,2.85,3.4]:beam('Loft short baluster',(x,1.40,LOFT),(x,1.40,3.71),.047,wood)
for z in [3.47,3.65]:tube('Loft rope guardrail',[(-2.35,1.40,z),(-1.0,1.38,z-.04),(.65,1.40,z),(2,1.38,z-.035),(3.4,1.4,z)],.025,rope)
# Slim tree on the left retains original identity without blocking the room centre.
tx,ty=-3.55,.45
verts=[];faces=[];trunk_uv=[];ns,nz=64,42
for j in range(nz):
 z=FLOOR+j*(6.23-FLOOR)/(nz-1)
 for i in range(ns+1):
  a=i*math.tau/ns
  ripple=.054*math.sin(a*11+z*1.15)+.028*math.sin(a*27-z*3.7)+.017*math.sin(a*19+z*9)
  dent=0
  for ka,kz in [(4.6,1.7),(5.35,3.6),(3.9,4.6)]:
   da=math.atan2(math.sin(a-ka),math.cos(a-ka));dent+=.050*math.exp(-(da/.19)**2-((z-kz)/.22)**2)
  r=(.355-.038*z/6.23)*(1+ripple)-dent
  verts.append((tx+math.cos(a)*r+.026*math.sin(z),ty+math.sin(a)*r,z));trunk_uv.append((i/ns*1.5,z/2.3))
for j in range(nz-1):
 for i in range(ns):k=j*(ns+1)+i;faces.append((k,k+1,k+ns+2,k+ns+1))
smooth(mesh('Left chestnut trunk with sculpted bark',verts,faces,bark,trunk_uv));collision('Slim tree trunk',(tx,ty,3.2),(.70,.70,6.05))
# Relief rings around shallow eye knots follow the same sculpted bark surface.
for ka,kz in [(4.6,1.7),(5.35,3.6),(3.9,4.6)]:
 for extent in [.08,.12,.17]:
  pts=[]
  for i in range(21):
   a=i*math.tau/20;angle=ka+math.cos(a)*extent;zz=kz+math.sin(a)*extent*1.55;r=.339-.011*(extent/.17)
   pts.append((tx+math.cos(angle)*r+.026*math.sin(zz),ty+math.sin(angle)*r,zz))
  tube('Bark eye knot',pts,.008,bark)
for i in range(6):
 a=i*math.tau/6;tube('Small trunk root',[(tx,ty,FLOOR+.23),(tx+.46*math.cos(a),ty+.46*math.sin(a),FLOOR+.035)],.052,bark)
# 21 broad mushroom treads rise 3.06 units in 510 degrees. One revolution gives
# 2.06 units headroom, safely above the 1.08-unit frog before adding a collider.
step_count=21;start=-math.pi/2;end=start+math.radians(510)
for i in range(step_count):
 a=start+(end-start)*i/(step_count-1);top=FLOOR+(LOFT-FLOOR)*(i+1)/step_count
 px=tx+1.04*math.cos(a);py=ty+1.04*math.sin(a)
 o=sphere('Mushroom tread %02d'%i,(px,py,top-.078),(.69,.39,.087),mushroom,32,10);o.rotation_euler.z=a
 for vert in o.data.vertices:
  aa=math.atan2(vert.co.y,vert.co.x);factor=1+.020*math.sin(aa*9+i*.37)+.012*math.sin(aa*15);vert.co.x*=factor;vert.co.y*=factor
 for loop in o.data.loops:
  co=o.data.vertices[loop.vertex_index].co;o.data.uv_layers.active.data[loop.index].uv=(co.x*.5+.5,co.y*.5+.5)
 under=sphere('Mushroom warm layered underside',(px,py,top-.122),(.677,.379,.071),mushroom_under,28,10);under.rotation_euler.z=a
 beam('Mushroom woody stem',(tx+.28*math.cos(a),ty+.28*math.sin(a),top-.12),(px,py,top-.10),.065,bark)
 # Rippled cap rim and a few fine radial gills underneath.
 ringpts=[]
 for j in range(33):
  q=j*math.tau/32;u=.665*math.cos(q);v=.374*math.sin(q);ringpts.append((px+u*math.cos(a)-v*math.sin(a),py+u*math.sin(a)+v*math.cos(a),top-.07+.008*math.sin(q*5)))
 tube('Mushroom cream rim',ringpts,.012,cut)
 for q in [-.6,-.3,0,.3,.6]:
  tube('Mushroom underside gill',[(tx+.38*math.cos(a+q*.3),ty+.38*math.sin(a+q*.3),top-.13),(px+.48*math.cos(a+q),py+.48*math.sin(a+q),top-.10)],.008,cut)
 stairs.append({'name':'MushroomTread%02d'%i,'position':godot((px,py,top-.08)),'size':[1.27,.16,.70],'yaw':-a,'top':round(top,5)})
 route.append(godot((px,py,top)))
# A real landing meets the shared rear deck.
# The last mushroom meets the existing deck polygon; no coplanar landing plate.
# Front loft collider is rectangular; rear polygon is provided for a trimesh.
# Root may create the whole loft polygon collider, avoiding a box outside stone walls.

# Stump dining set and visible endgrain.
def stump(name,x,y,z,r,h):
 n=48;v=[];u=[];faces=[]
 for j,t in enumerate([0,.11,.5,.92,1]):
  for i in range(n+1):
   a=i*math.tau/n;rr=r*(1-.035*t+.033*math.sin(a*13)+.02*math.sin(a*23+t*2));v.append((x+rr*math.cos(a),y+rr*math.sin(a),z+h*t));u.append((i/n,z+h*t))
 for j in range(4):
  for i in range(n):q=j*(n+1)+i;faces.append((q,q+1,q+n+2,q+n+1))
 smooth(mesh(name+' uneven bark',v,faces,bark,u))
 rim=[]
 for i in range(n):rim.append(v[4*(n+1)+i])
 for i in range(n):
  a=i*math.tau/n;rim.append((x+math.cos(a)*r*.943,y+math.sin(a)*r*.943,z+h))
 mesh(name+' irregular bark top rim',rim,[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],cut)
 cap=beam(name+' endgrain',(x,y,z+h-.025),(x,y,z+h),r*.945,cut,seg=64)
 for loop in cap.data.loops:
  co=cap.data.vertices[loop.vertex_index].co
  cap.data.uv_layers.active.data[loop.index].uv=(co.x/(2*r*.945)+.5,co.y/(2*r*.945)+.5)
 for k in range(5):
  a=k*math.tau/5+.32;tube(name+' radial drying split',[(x+math.cos(a)*r*.74,y+math.sin(a)*r*.74,z+h+.006),(x+math.cos(a+.04)*r*.87,y+math.sin(a+.04)*r*.87,z+h+.006),(x+math.cos(a+.035)*r*.94,y+math.sin(a+.035)*r*.94,z+h-.01)],.0016,bark)
 collision(name,(x,y,z+h*.5),(r*1.9,r*1.9,h))
stump('Round stump table',.58,-1.33,FLOOR,.86,.50)
stump('Left guest stool',-.70,-1.60,FLOOR,.30,.29)
stump('Right guest stool',1.73,-1.15,FLOOR,.32,.29)
stump('Front stump stool',.65,-2.60,FLOOR,.31,.29)
# Low leaf/moss rug: scalloped perimeter and subtle radial leaf veins.
pts=[]
for i in range(96):
 a=i*math.tau/96;r=1+.032*math.sin(a*11)+.023*math.sin(a*19);pts.append((.52+2.12*r*math.cos(a),-1.42+1.73*r*math.sin(a)))
slab('Moss scalloped carpet',pts,FLOOR+.018,.013,leaflight)
# Each leaf is a padded cloth form with wrinkled edges, stitched veins and felt tufts.
for i,(x,y,ang,L,w) in enumerate([(-.75,-2.3,-.15,2.0,.70),(.55,-2.65,1.00,2.2,.75),(.88,-.95,2.0,1.8,.7),(-.52,-.85,2.7,1.65,.68)]):
 d=Vector((math.cos(ang),math.sin(ang),0));side=Vector((-d.y,d.x,0));a=Vector((x,y,FLOOR+.035));v=[];f=[];uvc=[];lengths=25;across=15
 def point(t,s):
  c=a+d*t*L;ww=math.sin(math.pi*t)**.72*w
  p=c+side*ww*s;p.z+=.043*math.sin(math.pi*t)*(1-s*s)+.003*math.sin(t*67+s*23)+.008*abs(s)**4*math.sin(t*48+i)
  return p
 for k in range(lengths):
  t=k/(lengths-1)
  for j in range(across):
   ss=-1+2*j/(across-1);v.append(tuple(point(t,ss)));uvc.append((t*1.6,(ss+1)*.65))
 for k in range(lengths-1):
  for j in range(across-1):q=k*across+j;f.append((q,q+1,q+across+1,q+across))
 f=[tuple(reversed(face)) for face in f]
 o=smooth(mesh('Padded moss leaf rug %d'%i,v,f,leafmat,uvc));m=o.modifiers.new('Soft leaf thickness','SOLIDIFY');m.thickness=.018
 tube('Leaf rug stitched centre',[tuple(point(t,0)+Vector((0,0,.008))) for t in [0,.12,.25,.4,.55,.7,.85,1]],.010,vein)
 for t in [.19,.32,.46,.60,.74,.85]:
  for side_sign in [-1,1]:tube('Leaf rug stitched branch',[tuple(point(t+q*.08,side_sign*q)+Vector((0,0,.007))) for q in [0,.3,.6,.90]],.0045,vein)
# Soft moss silhouette, with a small number of genuine geometry tufts.
for k in range(240):
 a=rng.random()*math.tau;r=1+.032*math.sin(a*11)+.023*math.sin(a*19)+rng.uniform(-.018,.021);x=.52+2.10*r*math.cos(a);y=-1.42+1.71*r*math.sin(a)
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=world((x,y,FLOOR+.024)))
 o=tag(bpy.context.object,'Soft carpet edge tuft',leaflight);o.scale=(.018+rng.random()*.039,.016+rng.random()*.031,.014+rng.random()*.023)
# Short curled fibre tufts lie within the moss area rather than blocking walking.
for k in range(140):
 a=rng.random()*math.tau;r=math.sqrt(rng.random());x=.52+2.00*r*math.cos(a);y=-1.42+1.57*r*math.sin(a);z=FLOOR+.040
 tube('Moss felt curl',[(x,y,z),(x+.018,y+.012,z+.02),(x+.035,y-.004,z+.01)],.003,leaflight)

# Blue bedding, small bedside books, rose mat, original wall map.
bx,by=.85,2.80
box('Sleeping low frame',(bx,by,LOFT+.12),(2.12,1.60,.20),wood,.065)
sphere('Soft sleeping mattress',(bx,by,LOFT+.255),(1.045,.775,.13),linen,40,18)
v=[];f=[];nx,ny=38,28
for j in range(ny):
 for i in range(nx):
  u=i/(nx-1);t=j/(ny-1);z=LOFT+.44+.035*math.sin(u*23+t*7)+.019*math.sin(u*44-t*9)-.14*abs(2*u-1)**8-.10*(1-t)**6
  v.append((bx-1.04+u*2.08,by-.78+t*1.19,z))
for j in range(ny-1):
 for i in range(nx-1):k=j*nx+i;f.append((k,k+1,k+nx+1,k+nx))
quilt=smooth(mesh('Blue quilt broad soft folds',v,f,blue));s=quilt.modifiers.new('Quilt hem thickness','SOLIDIFY');s.thickness=.035
sphere('Cream pillow',(bx,by+.46,LOFT+.49),(.64,.25,.125),linen,32,16)
for x in [bx-1.09,bx+1.09]:beam('Bed branch rail',(x,by-.76,LOFT+.24),(x,by+.76,LOFT+.33),.04,bark)
collision('Blue bed',(bx,by,LOFT+.30),(2.12,1.6,.60))
box('Rose bedside mat',(-.99,2.49,LOFT+.023),(.65,1.63,.031),rose,.018)
for i in range(11):
 for s in [-1,1]:tube('Rose mat fringe',[(-1.29+i*.06,2.49+s*.81,LOFT+.03),(-1.28+i*.06,2.49+s*.95,LOFT+.02)],.006,linen)
box('Bedside stack base',(-1.93,3.23,LOFT+.16),(.95,.70,.30),wood,.04)
for k in range(5):
 x=-1.93;y=3.22;z=LOFT+.34+k*.092;rot=.055*(k-2)
 box('Book cover %d'%k,(x,y,z),(.69,.47,.032),[leafdark,rose,linen,blue,cut][k],.008,rot)
 box('Book pages',(x,y,z+.038),(.65,.435,.050),white,.006,rot)
box('Map hanging parchment',(.78,4.04,4.87),(1.70,.055,1.20),parchment,.025)
for z in [4.25,5.49]:beam('Map wood scroll',(-.17,3.987,z),(1.73,3.987,z),.044,wood)
# Organic map contour silhouettes instead of meaningless pseudo text.
for i,(x,z,s) in enumerate([(.15,4.84,.18),(.43,4.99,.24),(.63,4.73,.23),(.88,4.65,.16),(1.2,4.72,.22),(.96,5.13,.23)]):
 poly=[(x+s*math.cos(k*math.tau/15)*(1+.18*math.sin(k*2.1)),3.995-i*.003,z+s*.7*math.sin(k*math.tau/15)) for k in range(15)]
 mesh('Map ink island',poly,[tuple(range(15))],mapink)
tube('Map dotted travel route',[(-.03,3.965,4.51),(.38,3.965,4.63),(.67,3.965,4.90),(1.15,3.965,5.15),(1.49,3.965,5.08)],.009,terra)
# Framed picture postcards pinned near books.
for k,(x,z) in enumerate([(-.76,4.89),(-1.38,4.72),(-.95,5.35)]):
 box('Travelling postcard',(x,3.965,z),(.44,.025,.32),white,.008,0)
 box('Postcard landscape',(x,3.944,z+.018),(.34,.016,.22),[leafdark,blue,mapink][k],.006)
 sphere('Postcard brass pin',(x,3.923,z+.145),(.015,.012,.015),brass,12,8)

# Pots have actual hollow necks and separate lids, plus a low larder below loft.
def jar(name,x,y,z,r=.16,h=.37,m=terra,lid=False):
 style=(int(abs(x)*11+abs(y)*7+z*3))%5
 profiles=[[(0,0),(.70,0),(.91,.06),(1,.25),(.94,.52),(.62,.74),(.56,.89),(.66,.91),(.66,.99),(.50,.99),(.48,.85)],
 [(0,0),(.68,0),(.90,.1),(1,.38),(.93,.70),(.74,.85),(.70,.94),(.78,.96),(.77,1),(.62,1),(.62,.83)],
 [(0,0),(.78,0),(.96,.10),(1,.32),(.94,.62),(.60,.72),(.48,.92),(.58,.96),(.58,1),(.42,1),(.42,.83)],
 [(0,0),(.60,0),(.91,.16),(1,.36),(.85,.59),(.57,.73),(.53,.95),(.60,.98),(.60,1),(.45,1),(.43,.83)],
 [(0,0),(.78,0),(.94,.11),(1,.43),(.91,.70),(.85,.84),(.81,.94),(.87,.96),(.87,1),(.73,1),(.72,.85)]]
 profile=profiles[style];pts=[];faces=[];uvc=[];n=32
 for rr,zz in profile:
  for i in range(n+1):
   a=i*math.tau/n;irr=1+.014*math.sin(a*7+zz*5);pts.append((x+rr*r*math.cos(a)*irr,y+rr*r*math.sin(a)*irr,z+zz*h));uvc.append((i/n,zz))
 for j in range(len(profile)-1):
  for i in range(n):k=j*(n+1)+i;faces.append((k,k+1,k+n+2,k+n+1))
 smooth(mesh(name,pts,faces,m,uvc))
 if lid:
  lip=profile[-4][0]*r
  sphere(name+' handturned lid',(x,y,z+h+.016),(lip*1.08,lip*1.08,h*.055),m,24,12);sphere(name+' lid knob',(x,y,z+h+.055),(r*.14,r*.14,r*.12),m,12,8)
  if style==2:
   ring(name+' neck twine',(x,y,z+h*.83),r*.55,.012,rope)
   tube(name+' twine tie',[(x,y-r*.58,z+h*.84),(x+r*.20,y-r*.64,z+h*.74),(x+r*.13,y-r*.69,z+h*.61)],.008,rope)
 if style in [1,4] and r>.12:
  # Two separate handles keep silhouettes distinct from copied bottles.
  for sign in [-1,1]:tube(name+' ear handle',[(x+sign*r*.84,y,z+h*.70),(x+sign*r*1.15,y,z+h*.55),(x+sign*r*.92,y,z+h*.36)],.023,m)
 return z+h

def wicker_tube(name,pts,r,m):
 verts=[];faces=[];n=6
 for i,p in enumerate(pts):
  d=Vector(pts[min(i+1,len(pts)-1)])-Vector(pts[max(i-1,0)]);d.normalize();side=d.cross(Vector((0,0,1)))
  if side.length<.01:side=d.cross(Vector((0,1,0)))
  side.normalize();up=d.cross(side).normalized()
  for k in range(n):verts.append(tuple(Vector(p)+r*(side*math.cos(k*math.tau/n)+up*math.sin(k*math.tau/n))))
 for i in range(len(pts)-1):
  for k in range(n):q=i*n+k;faces.append((q,i*n+(k+1)%n,(i+1)*n+(k+1)%n,q+n))
 return smooth(mesh(name,verts,faces,m))
def basket(name,x,y,z,r=.30,h=.30):
 # Closed weave backing removes the wire-cage appearance while preserving every interlaced strand.
 lining=[]
 for t in [0,1]:
  for i in range(48):
   aa=i*math.tau/48;rr=r*(.75+.23*t);lining.append((x+rr*math.cos(aa),y+rr*math.sin(aa),z+.02+t*(h-.035)))
 mesh(name+' close woven inner wall',lining,[(i,(i+1)%48,(i+1)%48+48,i+48) for i in range(48)],wood)
 # Genuine interlaced willow ribbons: thin horizontal rings and over-under uprights.
 for row in range(11):
  zz=z+.018+row*h/10;rr=r*(.76+.24*row/10);pts=[]
  for i in range(65):
   a=i*math.tau/64;rad=rr+.005*math.sin(a*20+row*math.pi);pts.append((x+rad*math.cos(a),y+rad*math.sin(a),zz))
  wicker_tube(name+' willow course',pts,.011,wood if row%3 else cut)
 for i in range(24):
  a=i*math.tau/24;pts=[]
  for row in range(13):
   t=row/12;rr=r*(.76+.24*t)+.012*math.sin(t*math.pi*12+i*math.pi);pts.append((x+rr*math.cos(a),y+rr*math.sin(a),z+t*h))
  wicker_tube(name+' interlaced upright',pts,.013,rope)
 ring(name+' rolled woven rim',(x,y,z+h),r,.025,cut)
 beam(name+' bottom',(x,y,z),(x,y,z+.026),r*.77,wood,seg=32)
 return z+h
for x in [-.98,1.55]:beam('Pantry shelf post',(x,3.14,FLOOR),(x,3.14,2.85),.055,wood)
for row,z in enumerate([.68,1.44,2.20]):
 box('Pantry shelf',(.28,3.18,z),(2.72,.60,.09),wood,.025)
 if row==0:
  basket('Pantry low wicker basket',-.52,3.12,z+.05,.26,.28)
  jar('Low ochre storage jar',.22,3.12,z+.05,.20,.35,terra,True)
  basket('Pantry folded cloth basket',.97,3.12,z+.05,.25,.27)
  box('Folded linen in basket',(.97,3.12,z+.29),(.33,.28,.11),linen,.04)
 else:
  for i,x in enumerate([-.75,-.14,.52,1.19]):
   h=[.42,.32,.49,.36][(i+row)%4];r=[.17,.21,.18,.15][i]
   jar('Pantry varied handglazed vessel',x,3.12,z+.05,r,h,[clay,terra,clay,leafdark][(i+row)%4],True)
# Rope lashings on actual shelf joints and an open storage basket beneath.
for x in [-.98,1.55]:
 for z in [.68,1.44,2.20]:
  for k in range(3):ring('Pantry rope lashing',(x,3.14,z-.032+k*.022),.064,.012,rope)
basket('Ground harvest basket',.12,3.09,FLOOR,.31,.42)
collision('Pantry shelving',(.28,3.18,1.5),(2.82,.70,2.68))
# Rounded two-mouth stove, oriented toward the player and under right window.
sx,sy=3.38,1.12
stove=box('Rounded carved double stove',(sx,sy,FLOOR+.43),(1.60,1.13,.86),hearthstone,.20)
bpy.context.view_layer.objects.active=stove
for mod in list(stove.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
for xx in [sx-.40,sx+.40]:
 cutout=sphere('Temporary stove cave cutter',(xx,sy-.44,FLOOR+.29),(.27,.49,.30),charcoal,32,18)
 bpy.context.view_layer.objects.active=cutout;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 bpy.context.view_layer.objects.active=stove;mod=stove.modifiers.new('Carved arched fire chamber','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutout;bpy.ops.object.modifier_apply(modifier=mod.name)
 furniture.remove(cutout);bpy.data.objects.remove(cutout,do_unlink=True)
uv(stove)
for x in [sx-.40,sx+.40]:
 # Arched fire mouth is dark inset backed by stone, with low timber inside.
 sphere('Stove dark arch',(x,sy-.10,FLOOR+.29),(.22,.018,.23),charcoal,28,14)
 box('Stove arch flat base',(x,sy-.12,FLOOR+.11),(.38,.025,.14),charcoal,.04)
 beam('Stove hotplate',(x,sy,FLOOR+.861),(x,sy,FLOOR+.878),.245,charcoal,seg=32)
 ring('Stove top rim',(x,sy,FLOOR+.883),.247,.027,hearthstone)
 for k in range(3):beam('Hearth kindling',(x-.16+k*.13,sy-.56,FLOOR+.07),(x-.16+k*.13,sy-.16,FLOOR+.12),.06,wood)
collision('Double stove',(sx,sy,FLOOR+.43),(1.64,1.15,.86))
jar('Dark cooking pot',sx-.4,sy,FLOOR+.90,.235,.27,charcoal,True)
ring('Cooking pot left handle',(sx-.65,sy,FLOOR+1.06),.085,.027,charcoal,'Y')
ring('Cooking pot right handle',(sx-.15,sy,FLOOR+1.06),.085,.027,charcoal,'Y')
jar('Water jug by stove',4.38,.83,FLOOR,.19,.45,terra,False)
# Hanging herbs sit beside shelf; no indoor vegetation giant enough to be trees.
def leaf(name,a,b,w,m):
 a=Vector(a);b=Vector(b);d=b-a;side=Vector((-d.y,d.x,0))
 if side.length<.001:side=Vector((1,0,0))
 side.normalize();v=[];f=[]
 for i in range(9):
  t=i/8;c=a+d*t;c.z+=math.sin(math.pi*t)*w*.22
  for s in [-1,0,1]:v.append(tuple(c+side*(math.sin(math.pi*t)**.7*w*s)))
 for i in range(8):
  for j in range(2):q=i*3+j;f.append((q,q+1,q+4,q+3))
 o=smooth(mesh(name,v,f,m));mod=o.modifiers.new('Leaf thickness','SOLIDIFY');mod.thickness=.007;return o
# Slim bamboo ladder is a background household prop beside the pantry, not the walking staircase.
for x in [-1.83,-1.35]:
 beam('Pantry bamboo ladder side',(x,2.74,FLOOR),(x,3.0,2.86),.040,wood,seg=16)
 for j in range(8):
  z=FLOOR+j*.37;yy=2.74+(z-FLOOR)/(2.86-FLOOR)*.26;ring('Bamboo ladder joint',(x,yy,z),.042,.010,cut)
for j in range(8):
 z=FLOOR+.18+j*.32;yy=2.74+(z-FLOOR)/(2.86-FLOOR)*.26
 beam('Pantry bamboo ladder rung',(-1.86,yy,z),(-1.32,yy,z),.028,wood,seg=14)
 for x in [-1.82,-1.36]:
  for k in range(2):ring('Ladder rung rope binding',(x,yy,z-.014+k*.025),.044,.009,rope)
collision('Background bamboo ladder',(-1.59,2.9,1.51),(.59,.38,2.65))
# Rolled maps and linen sack fill the left pantry margin without entering the stair route.
box('Pantry folded cloth sack',(-1.52,3.01,FLOOR+.40),(.38,.38,.77),linen,.12)
for k in range(5):
 beam('Stored rolled field map',(-1.67+k*.07,3.00,FLOOR+.65),(-1.70+k*.075,3.02,FLOOR+1.22+.08*math.sin(k)),.041,parchment,seg=14)
# Fresh leaves in the floor basket and small dried flower heads by the hanging herbs.
for k in range(11):
 a=k*math.tau/11;leaf('Harvest basket leaf',(.12,3.09,FLOOR+.32),(.12+.34*math.cos(a),3.09+.28*math.sin(a),FLOOR+.70+.16*math.sin(k)),.12,leafdark if k%2 else leafmat)
for k in range(4):
 x=2.12+k*.16;z=2.48-k*.08
 tube('Dry flower cord',[(x,2.74,3.06),(x,2.72,z)],.008,rope)
 for j in range(3):
  sphere('Papery dried seed pod',(x+(j-1)*.08,2.72,z-.10-j*.04),(.042,.040,.063),linen,12,8)
# A small woven hearth mat and scattered river pebbles are kept under the stove edge.
box('Blue woven pantry mat',(.4,2.29,FLOOR+.023),(1.15,.52,.024),blue,.017)
for k in range(17):
 a=k*math.tau/17;x=.4+.65*math.cos(a);y=2.29+.33*math.sin(a)
 sphere('Pantry mat smooth pebble',(x,y,FLOOR+.032),(.055,.043,.032),[clay,terra,cut][k%3],12,8)

for k in range(4):
 x=2.0+k*.22;z=2.80-k*.06;tube('Hanging herb string',[(x,2.70,3.04),(x,2.70,z-.17)],.008,rope)
 for j in range(5):leaf('Dried hanging leaf',(x,2.7,z-j*.10),(x+.17*(-1)**j,2.65,z-.20-j*.10),.075,[leafdark,leafmat][k%2])
# Little flowers and stems in a loft vase.
jar('Loft flower vase',-2.50,2.96,LOFT,.20,.55,clay)
for k in range(6):
 a=k*math.tau/6;tip=(-2.50+math.cos(a)*.36,2.96+math.sin(a)*.25,LOFT+1.1+rng.random()*.25)
 tube('Flower stalk',[(-2.50,2.96,LOFT+.40),(-2.48,2.94,LOFT+.80),tip],.014,leafdark)
 for q in range(5):sphere('Pale flower petal',(tip[0]+.07*math.cos(q*math.tau/5),tip[1]+.07*math.sin(q*math.tau/5),tip[2]),(.055,.04,.06),linen,12,8)
 sphere('Flower ochre centre',tip,(.037,.037,.037),cut,12,8)
# Closed travel chest and leaf coat stand near the entrance.
box('Travel chest base',(-3.22,-2.20,FLOOR+.26),(1.15,.73,.52),wood,.065)
box('Travel chest domed lid',(-3.22,-2.20,FLOOR+.57),(1.19,.77,.15),cut,.07)
for x in [-3.60,-2.84]:
 box('Travel chest strap',(x,-2.584,FLOOR+.30),(.075,.027,.49),bark,.007)
 box('Travel chest brass clasp',(x,-2.612,FLOOR+.38),(.09,.035,.16),brass,.012)
collision('Travel chest',(-3.22,-2.20,FLOOR+.33),(1.20,.80,.67))
jar('Packed travel flask',-3.45,-2.2,FLOOR+.66,.14,.30,leafdark,True)
box('Cloth lunch parcel',(-2.97,-2.2,FLOOR+.77),(.35,.29,.18),linen,.075)
beam('Leaf hat stand',(-3.35,-1.30,FLOOR),(-3.35,-1.30,1.91),.052,bark)
for a in [0,2.1,4.2]:beam('Hat stand foot',(-3.35,-1.30,FLOOR+.14),(-3.35+.25*math.cos(a),-1.30+.25*math.sin(a),FLOOR+.015),.037,wood)
leaf('Hanging leaf travel hat',(-3.35,-1.28,1.80),(-3.35,-1.62,1.03),.42,leafdark)
tube('Travel leaf hat midrib',[(-3.35,-1.30,1.79),(-3.35,-1.48,1.49),(-3.35,-1.65,1.06)],.013,vein)
for t in [.26,.43,.60,.75]:
 z=1.80-.77*t;y=-1.28-.34*t-.02
 for sign in [-1,1]:tube('Travel leaf hat lateral vein',[(-3.35,y,z),(-3.35+sign*.30*math.sin(t*math.pi),y-.045,z-.10)],.006,vein)
berry=mat('Leaf hat red berries',(.46,.060,.022),rough=.52)
for x,y,z in [(-3.29,-1.40,1.76),(-3.38,-1.41,1.73),(-3.32,-1.44,1.68)]:sphere('Travel hat red berry',(x,y,z),(.047,.039,.044),berry,16,10)
# Leaf curtain stays near the left wall above stairs instead of across main camera.
v=[];f=[]
for j in range(21):
 t=j/20;z=2.25+t*3.70;x=-4.77+.18*math.sin(t*math.pi)
 for i in range(13):
  u=i/12;y=.12+(u-.5)*1.32*(.62+.38*abs(t-.2));v.append((x+.055*math.sin(u*7*math.pi),y,z))
for j in range(20):
 for i in range(12):k=j*13+i;f.append((k,k+1,k+14,k+13))
smooth(mesh('Green leaf curtain drape',v,f,leafmat));tube('Leaf curtain tie',[(-4.66,-.26,3.05),(-4.49,.12,3.00),(-4.66,.48,3.05)],.025,rope)
# Tea cup, plate, bowl, wax candle and a few rice grains on the small round table.
tabletop=FLOOR+.51
jar('Green tea cup',.98,-1.18,tabletop,.095,.17,leafdark)
beam('Visible tea',(.98,-1.18,tabletop+.142),(.98,-1.18,tabletop+.148),.048,charcoal,seg=24)
beam('Candle saucer',(.26,-1.12,tabletop),(.26,-1.12,tabletop+.035),.17,leafdark,seg=32)
beam('Table candle wax',(.26,-1.12,tabletop+.035),(.26,-1.12,tabletop+.26),.059,white,seg=24)
sphere('Candle flame',(.26,-1.12,tabletop+.32),(.029,.029,.073),flame,16,10)
jar('Round rice bowl',.64,-1.75,tabletop,.20,.095,cut)
for k in range(14):sphere('Rice grain',(.64+rng.uniform(-.13,.13),-1.75+rng.uniform(-.1,.1),tabletop+.075),(.021,.031,.011),white,10,6)
box('Blue woven entry mat',(.05,-3.80,FLOOR+.027),(1.38,.76,.035),blue,.025)
for i in range(17):
 for s in [-1,1]:tube('Entry mat fringe',[(-.60+i*.08,-3.80+s*.38,FLOOR+.03),(-.60+i*.08,-3.80+s*.49,FLOOR+.025)],.005,linen)

route.insert(0,godot((tx,-1.03,FLOOR)))
route.append(godot((-3.03,2.02,LOFT)))
layout={
 'version':2,'revision':'approved-concept-02','authoring':'Blender scenery / original Tripo frog unchanged',
 'detail_revision':'natural-rock-felt-willow-01',
 'windows':json.loads((ASSETS/'home-window-lighting.json').read_text()),
 'coordinate_system':'Godot Y-up; authored Blender(-15,12,0) maps to Godot(-15,0,-12)',
 'frog_height':1.08,'center':[-15,0,-12],'floor_y':FLOOR,
 'entry_spawn':[-15,.20,-8.18],'exit_z':-7.40,
 'qa_ground_route':[godot(p) for p in [(0,-3.82,.20),(-.95,-3.05,.20),(-1.80,-2.35,.20),(-1.80,-.70,.20),(-3.55,-1.03,.20)]],
 'qa_loft_route':[godot(p) for p in [(-3.03,2.02,3.26),(-2.65,2.02,3.26),(-1.40,2.02,3.26),(-.80,1.85,3.26)]],
 'qa_wall_route':[godot(p) for p in [(0,-3.82,.20),(2.10,-3.32,.20),(3.20,-2.80,.20),(4.2,-1.8,.20)]],
 'qa_wall_start':godot((4.2,-1.8,.20)),'qa_wall_direction':[1,0,0],
 'room_bounds':{'min':[-20.6,.188,-16.9],'max':[-9.4,6.6,-7.1]},
 'bounds':{'type':'ellipse','radius_x':5.6,'radius_z':4.9,'ceiling_y':6.6},
 'door':{'position':[-15,.188,-7.30],'inside_spawn':[-15,.20,-8.18],'width':2.60,'height':2.90,'exit_direction':[0,0,1]},
 'loft':{'top':LOFT,'thickness':.15,'polygon':[godot((x,y,LOFT)) for x,y in loft_poly]},
 'furniture_collisions':collisions,'stair_steps':stairs,'stair_route':route,
 'stair_width':.90,'stair_collision_recommendation':'Continuous ribbon between stair_route points. Do not add vertical AABB risers, so CharacterBody walks without artificial jumping.',
 'camera_views':{
  'entry':{'position':godot((.60,-4.25,3.98)),'target':godot((-.05,1.10,2.16)),'vertical_fov':66},
  'main':{'position':godot((1.00,-4.10,4.70)),'target':godot((-.25,.55,2.22)),'vertical_fov':70},
  'loft':{'position':godot((1.1,-2.9,5.48)),'target':godot((-.25,2.60,3.77)),'vertical_fov':63},
  'details':{'position':godot((1.0,-3.0,2.1)),'target':godot((-.2,.30,1.03)),'vertical_fov':55},
  'frog_eye':{'position':godot((.15,-2.95,.90)),'target':godot((.3,1.5,1.48)),'vertical_fov':68}},
 'interactions':{'pack':godot((-3.22,-2.2,.5)),'book':godot((-1.9,2.8,3.5)),'tea':godot((.58,-1.33,.7))},
 'verification_targets':{'walk_approach_stairs':godot((-3.55,-1.05,.20)),'table_approach':godot((-.30,-.40,.20)),'loft_walk_end':godot((-1.10,2.0,3.26))}
}
# Convert curves, apply transforms/modifiers before exporting. Retain every
# individual editable object in the source .blend; batch only the runtime copy.
bpy.ops.object.select_all(action='DESELECT')
for o in furniture:o.select_set(True)
bpy.context.view_layer.objects.active=furniture[0];bpy.ops.object.convert(target='MESH')
furniture=list(bpy.context.selected_objects)
for o in furniture:
 bpy.context.view_layer.objects.active=o
 for m in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)

# Runtime uses opaque JPEG base colours only; keep authoring PNGs and lossless
# Non-Color normal/roughness maps. Encoding was checked with an sRGB grey chip.
def runtime_colour_jpegs():
 folder=NATIVE/'runtime-textures';folder.mkdir(parents=True,exist_ok=True)
 bpy.context.scene.render.image_settings.quality=95
 replacements={}
 for material in bpy.data.materials:
  if not material.use_nodes:continue
  for node in material.node_tree.nodes:
   if node.type!='TEX_IMAGE' or not node.image:continue
   original=node.image
   if original.colorspace_settings.name!='sRGB':continue
   if original.name not in replacements:
    path=folder/(original.name.replace('/','_')+'.jpg')
    original.file_format='JPEG';original.filepath_raw=str(path);original.save()
    replacement=bpy.data.images.load(str(path),check_existing=False);replacement.pack()
    replacements[original.name]=replacement
   node.image=replacements[original.name]
 return len(replacements)

bpy.ops.wm.save_as_mainfile(filepath=str(NATIVE/'frog-home-furnishings.blend'))
runtime_colour_jpegs()
# Export joined material groups into GLB, then reopen authoring source for renders.
groups={}
for o in furniture:groups.setdefault(o.data.materials[0].name,[]).append(o)
for i,objects in enumerate(groups.values()):
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();bpy.context.object.name='HomeFurniture_%02d'%i
bpy.ops.export_scene.gltf(filepath=str(ASSETS/'home-furnishings.glb'),export_format='GLB',export_apply=True,export_animations=False,export_cameras=False,export_lights=False)
layout['export']={'furnishing_materials':len(groups),'furnishing_meshes':len([o for o in bpy.context.scene.objects if o.type=='MESH']),'furnishing_bytes':(ASSETS/'home-furnishings.glb').stat().st_size}
(ASSETS/'home-layout.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2)+'\n')
(NATIVE/'frog-home-layout.json').write_text(json.dumps(layout,ensure_ascii=False,indent=2)+'\n')
print('FROG_LAYOUT_WRITTEN',json.dumps(layout['export']),flush=True)
bpy.ops.wm.open_mainfile(filepath=str(NATIVE/'frog-home-furnishings.blend'))
# Same physical enclosure for both views, no disappearing walls or ceiling.
with bpy.data.libraries.load(str(NATIVE/'frog-home-enclosure.blend'),link=False) as (data_from,data_to):data_to.objects=data_from.objects
for o in data_to.objects:
 if o:bpy.context.collection.objects.link(o)
# Import unchanged runtime Tripo frog and pose Idle first frame at table.
before=set(bpy.context.scene.objects);bpy.ops.import_scene.gltf(filepath=str(ASSETS/'frog.glb'))
added=set(bpy.context.scene.objects)-before
frog_pivot=bpy.data.objects.new('Review original Tripo frog pivot',None);bpy.context.collection.objects.link(frog_pivot)
for o in added:
 if o.parent not in added:o.parent=frog_pivot
frog_pivot.location=world((-.45,-.95,FLOOR+.02));frog_pivot.rotation_euler.z=math.radians(155)
# Rendering sources contain the same runtime GLB frog, never a substitute.
scene=bpy.context.scene;scene.frame_set(1)
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.render.resolution_x=1400;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.world.color=(.13,.14,.12)
scene.world.use_nodes=True;next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND').inputs[0].default_value=(.56,.59,.54,1);next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND').inputs[1].default_value=.38
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=-.25
for name,loc,target,power,size,color in [
 ('Main warm window',(4.80,.30,3.5),(-1,-.7,.8),650,2.3,(1,.87,.66)),
 ('Loft window',(-2.40,3.7,4.9),(1.0,2.25,3.5),420,1.8,(1,.89,.70)),
 ('Front soft fill',(0,-3.8,4.3),(0,1.0,2.0),520,4.0,(.86,.91,1)),
 ('Ceiling bounce',(0,.0,6.10),(0,0,.3),300,3.2,(1,.93,.80))]:
 bpy.ops.object.light_add(type='AREA',location=world(loc));o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.data.color=color;o.rotation_euler=(Vector(world(target))-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.light_add(type='POINT',location=world((.26,-1.12,1.09)));bpy.context.object.data.energy=8;bpy.context.object.data.color=(1,.65,.21);bpy.context.object.data.shadow_soft_size=.14
for name,key in [('01-main','main'),('02-loft','loft'),('03-entry','entry'),('04-details','details')]:
 view=layout['camera_views'][key];p=view['position'];t=view['target'];bpy.ops.object.camera_add(location=(p[0],-p[2],p[1]));cam=bpy.context.object;cam.name='Review '+name;cam.data.type='PERSP';cam.data.lens_unit='FOV';cam.data.sensor_fit='VERTICAL';cam.data.angle=math.radians(view['vertical_fov']);cam.data.clip_start=.04
 cam.rotation_euler=(Vector((t[0],-t[2],t[1]))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
 scene.render.filepath=str(RENDERS/(name+'.png'))
 if name=='01-main':bpy.ops.wm.save_as_mainfile(filepath=str(NATIVE/'frog-home-review.blend'))
 bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(NATIVE/'frog-home-review.blend'))
print('FROG_HOME_DONE',flush=True)
