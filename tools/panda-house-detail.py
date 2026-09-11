"""Second material/detail pass executed by build-panda-home.py.

No NPC mesh or animation is authored here. Room layout, staircase, portal and
furniture footprints stay fixed. Architectural detail is genuine mesh geometry.
"""
from mathutils import noise as bnoise

def noise_field(n,seed,layers):
 rr=np.random.default_rng(seed);yy,xx=np.mgrid[0:n,0:n]/n;f=np.zeros((n,n))
 for grid,w in layers:
  a=rr.random((grid+1,grid+1));a[-1]=a[0];a[:,-1]=a[:,0];gx=xx*grid;gy=yy*grid;i=gx.astype(int);j=gy.astype(int);u=gx-i;v=gy-j;u=u*u*(3-2*u);v=v*v*(3-2*v)
  f+=w*((1-v)*((1-u)*a[j,i]+u*a[j,i+1])+v*((1-u)*a[j+1,i]+u*a[j+1,i+1]))
 return f

def image_map(name,pixels,color=False):
 n=pixels.shape[0];im=bpy.data.images.new(name,n,n)
 im.colorspace_settings.name='sRGB' if color else 'Non-Color'
 im.pixels.foreach_set(pixels.astype(np.float32).ravel())
 if color:
  # Runtime albedo may be JPEG; normal and roughness remain lossless data maps.
  td=NATIVE/'panda-textures';td.mkdir(exist_ok=True);fp=td/(name.replace('/','-')+'.jpg')
  im.filepath_raw=str(fp);im.file_format='JPEG';im.save();bpy.data.images.remove(im)
  im=bpy.data.images.load(str(fp));im.colorspace_settings.name='sRGB'
 im.pack();return im

surface_data_cache={}
def surface(material,kind,seed,display_color=None):
 n=512
 yy,xx=np.mgrid[0:n,0:n]/n;rr=np.random.default_rng(seed)
 broad=noise_field(n,seed,[(3,.44),(9,.27),(27,.18),(89,.11)])
 fine=noise_field(n,seed+37,[(21,.40),(67,.35),(191,.25)])
 speck=rr.random((n,n))
 if kind=='rock':
  # Mineral veins and fine chisel/granular relief, independent from macro facets.
  vein=np.exp(-np.square((broad-.48)*24))
  value=.80+.29*broad+.09*fine+.045*speck-.05*vein
  height=(broad-.5)*.022+(fine-.5)*.010+(speck-.5)*.0014
  rough=.72+.20*fine+.045*speck
 elif kind=='wood':
  warp=(broad-.5)*.075+.01*np.sin(yy*TAU*2)
  fibres=np.sin((xx+warp)*TAU*89+np.sin(yy*TAU*2)*.38)
  rings=np.sin((xx+warp*.6)*TAU*14)
  value=.84+.13*broad+.040*rings+.014*fibres
  height=.0007*rings+.00030*fibres+.0012*(fine-.5)
  rough=.67+.13*fine-.035*rings
 elif kind=='weave':
  pitch=54;u=(xx*pitch)%1;v=(yy*pitch)%1;parity=(np.floor(xx*pitch)+np.floor(yy*pitch))%2
  horizontal=np.sin(v*math.pi)**.65;vertical=np.sin(u*math.pi)**.65
  h=np.where(parity<.5,horizontal,vertical)
  twine=np.sin((xx+yy)*TAU*270)*.08
  value=.71+.23*h+.09*fine+.02*twine
  height=.0065*h+.00035*twine
  rough=.85+.11*fine
 else:
  value=.93+.10*fine; height=(fine-.5)*.0006;rough=.24+.13*fine
 if display_color is not None:
  linear=np.array([c/12.92 if c<.04045 else ((c+.055)/1.055)**2.4 for c in display_color])
 else:linear=np.array(material.diffuse_color[:3])
 material.diffuse_color=(*linear,1)
 nodes,links=material.node_tree.nodes,material.node_tree.links
 shader=next(n for n in nodes if n.type=='BSDF_PRINCIPLED');shader.inputs['Base Color'].default_value=(*linear,1)
 for node in list(nodes):
  if node.type in ['TEX_IMAGE','NORMAL_MAP']:nodes.remove(node)
 rgba=np.ones((n,n,4));rgba[:,:,:3]=np.maximum(.001,linear[None,None,:]*value[:,:,None]);rgb=rgba[:,:,:3]
 rgba[:,:,:3]=np.where(rgb<=.0031308,rgb*12.92,1.055*np.power(rgb,1/2.4)-.055)
 image=image_map(material.name+' detailed albedo',rgba,True);tex=nodes.new('ShaderNodeTexImage');tex.image=image;links.new(tex.outputs['Color'],shader.inputs['Base Color'])
 # Tangent-space normal image is exported, not a Blender-only procedural node.
 dy,dx=np.gradient(height);nx=-dx*n/1.6;ny=-dy*n/1.6;nz=np.ones_like(nx);mag=np.sqrt(nx*nx+ny*ny+nz*nz)
 rgba[:,:,:3]=np.stack((nx/mag*.5+.5,ny/mag*.5+.5,nz/mag*.5+.5),axis=-1)
 normal=surface_data_cache[kind][0] if kind in surface_data_cache else image_map(material.name+' detailed normal',rgba)
 tex=nodes.new('ShaderNodeTexImage');tex.image=normal;node=nodes.new('ShaderNodeNormalMap');node.inputs['Strength'].default_value=.75 if kind=='weave' else 1.0;links.new(tex.outputs['Color'],node.inputs['Color']);links.new(node.outputs['Normal'],shader.inputs['Normal'])
 rgba[:,:,:3]=np.clip(rough[:,:,None],.05,1)
 rough_image=surface_data_cache[kind][1] if kind in surface_data_cache else image_map(material.name+' detailed roughness',rgba)
 surface_data_cache[kind]=(normal,rough_image)
 tex=nodes.new('ShaderNodeTexImage');tex.image=rough_image;links.new(tex.outputs['Color'],shader.inputs['Roughness'])

# Hue variation remains subtle: individual stone slabs must not become a checkerboard.
surface(rock,'rock',125,(.52,.495,.44))
for i,m in enumerate(stone):surface(m,'rock',201+i,(.435+i*.009,.448+i*.008,.423+i*.008))
surface(wood,'wood',311,(.39,.275,.18));surface(edge,'wood',313,(.44,.315,.215));surface(bamboo,'wood',315,(.48,.365,.225))
for i,m in enumerate([green,straw,gold,cream]):surface(m,'weave',410+i)
surface(celadon,'ceramic',521,(.55,.66,.59))
node_mat.diffuse_color=(.10,.073,.040,1)
next(n for n in node_mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Base Color'].default_value=node_mat.diffuse_color
grain_dark=mat('Panda incised wood grain',(.055,.027,.012))
grain_light=mat('Panda worn raised wood edge',(.24,.135,.065))
thread=mat('Panda bamboo embroidery thread',(.060,.12,.035),rough=.94)
thread_cream=mat('Panda natural flax thread',(.34,.26,.14),rough=.98)
dark_clay=mat('Panda varied unglazed clay',(.115,.075,.044),rough=.87)

def make_uv_world(o,scale=1.6):
 if o.type!='MESH':return
 uv=o.data.uv_layers.active or o.data.uv_layers.new(name='UVMap')
 corners=[o.matrix_world@Vector(c) for c in o.bound_box];lengths=[max(v[i] for v in corners)-min(v[i] for v in corners) for i in range(3)];long_axis=max(range(3),key=lambda i:lengths[i])
 is_wood=any(m in [wood,edge,bamboo] for m in o.data.materials)
 for poly in o.data.polygons:
  normal=poly.normal;axis=max(range(3),key=lambda i:abs(normal[i]));indices=[i for i in range(3) if i!=axis]
  if is_wood and indices[0]==long_axis:indices.reverse()
  # Wooden surfaces use consistent lengthwise coordinates instead of a cube net.
  for loop_index in poly.loop_indices:
   co=o.matrix_world@o.data.vertices[o.data.loops[loop_index].vertex_index].co
   uv.data[loop_index].uv=(co[indices[0]]/scale,co[indices[1]]/scale)

# A continuous weathered rock surface, not a tessellation of masonry blocks.
# Broad nonperiodic relief changes the actual surface silhouette; a few fissures
# supply geological breaks while most of the bedrock stays continuous.
detail_rng=random.Random(20260912)
def inner_wall_r(a,z):
 r=5.03 if z<4.65 else 5.03-(z-4.65)*1.32
 return r+.075*math.sin(a*5+z*.4)+.035*math.sin(a*11-z)
def detailed_wall_r(a,z):
 p=Vector((math.cos(a)*3.1,math.sin(a)*3.1,z*.76))
 broad=bnoise.noise_vector(p,noise_basis='PERLIN_ORIGINAL').x
 medium=bnoise.noise_vector(p*2.17+Vector((2.3,4.1,.8)),noise_basis='PERLIN_ORIGINAL').y
 return inner_wall_r(a,z)-.055+(.20*broad+.064*medium)*(.45 if z<.55 else 1.0)
old=bpy.data.objects.get('EnclosureWall')
if old:bpy.data.objects.remove(old,do_unlink=True)
for o in list(bpy.context.scene.objects):
 if o.name.startswith('Panda tapered natural rock fissure'):bpy.data.objects.remove(o,do_unlink=True)
segments=112;levels=29;vv=[];uv=[]
for j in range(levels):
 z=.12+j*(6.2-.12)/(levels-1)
 for i in range(segments+1):
  a=i*TAU/segments;zz=z+(.07*math.sin(a*7+j*1.71) if j not in [0,levels-1] else 0);r=detailed_wall_r(a,zz)
  vv.append((r*math.cos(a),r*math.sin(a),zz));uv.append((a*5/1.6,zz/1.6))
ff=[]
for j in range(levels-1):
 for i in range(segments):
  a=(i+.5)*TAU/segments;z=.12+j*(6.2-.12)/(levels-1)
  if math.sin(a)<-.974 and z<2.22:continue
  k=j*(segments+1)+i;n=k+1;ff.extend([(k,k+segments+1,n+segments+1),(k,n+segments+1,n)])
ff.append(tuple(reversed(range((levels-1)*(segments+1),levels*(segments+1)))))
wall=mesh('EnclosureWall',vv,ff,rock,uv)
for face in wall.data.polygons:face.use_smooth=True
# Sparse branching mineral seams follow the deformed surface; no all-over grid.
for index in range(18):
 a=.31+index*TAU/18;z0=2.2+(index%5)*.65;length=.45+(index%4)*.17
 if math.sin(a)<-.94 and z0<3:continue
 v=[]
 for j in range(13):
  t=j/12;z=z0-t*length;angle=a+.034*math.sin(t*7+index)+t*.058
  for side in [-1,1]:
   aa=angle+side*.00075*math.sin(math.pi*t);r=detailed_wall_r(aa,z)-.011
   v.append((r*math.cos(aa),r*math.sin(aa),z))
 mesh('Panda delicate bedrock fracture',v,[(j*2,j*2+1,j*2+3,j*2+2) for j in range(12)],fissure_mat)
# A few worn layer lips read as natural rock flakes, not decorative stacked blocks.
for index in [1,3,6,8,11,14]:
 a=.23+index*TAU/17;z=2.45+(index%4)*.64;width=.43+(index%3)*.19
 v=[]
 for j in range(14):
  u=(j/13-.5)*width;aa=a+u/4.7;zz=z+.085*math.sin(u*6+index)
  for row in [0,1]:
   h=zz-row*(.052+.019*math.sin(j*.7));r=detailed_wall_r(aa,h)-(.025 if row==0 else .0)
   v.append((r*math.cos(aa),r*math.sin(aa),h))
 mesh('Panda thin weathered stone layer',v,[(j*2,j*2+2,j*2+3,j*2+1) for j in range(13)],rock,[(i//2/13,i%2*.045) for i in range(len(v))])

# Large overlapping shallow planes emerge from the SAME bedrock. Their outer
# boundaries sink into the continuous surface, so there is no closed dark joint
# around each patch. Only selected sloping fracture edges remain visible.
rock_patch_rng=random.Random(29121)
for index in range(46):
 a=rock_patch_rng.uniform(0,TAU);z=rock_patch_rng.uniform(.65,5.94)
 width=rock_patch_rng.uniform(1.90,3.75);height=rock_patch_rng.uniform(.90,2.14)
 if math.sin(a)<-.85 and z<2.7:continue
 # Keep window apertures, lattice and daylight unobstructed.
 if any((5*math.atan2(math.sin(a-wa),math.cos(a-wa)))**2/(width*.55+wr+.12)**2+(z-wz)**2/(height*.55+wr+.12)**2<1.0 for wa,wz,wr in [(math.pi/2,4.62,.88),(.28,3.52,.82),(2.87,1.75,.63)]):continue
 sides=rock_patch_rng.choice([6,7,8]);rotation=rock_patch_rng.uniform(-.48,.48);outline=[]
 for j in range(sides):
  t=j*TAU/sides+rock_patch_rng.uniform(-.16,.16);size=rock_patch_rng.uniform(.84,1.12)
  u=math.cos(t)*width*.5*size;v=math.sin(t)*height*.5*size
  outline.append((u*math.cos(rotation)-v*math.sin(rotation),u*math.sin(rotation)+v*math.cos(rotation)))
 depth=rock_patch_rng.uniform(.045,.105);tilt=rock_patch_rng.uniform(-.015,.015);verts=[];tex=[]
 for ring in [0,1]:
  for j,(u,v) in enumerate(outline):
   scale=1 if ring==0 else rock_patch_rng.uniform(.58,.77);uu=u*scale;vv=v*scale
   aa=a+uu/5;zz=max(.30,min(6.19,z+vv));base=detailed_wall_r(aa,zz)
   rr=base+(.14 if j%3 else .07) if ring==0 else base-depth+vv*tilt
   verts.append((rr*math.cos(aa),rr*math.sin(aa),zz));tex.append((aa*5/1.6,zz/1.6))
 faces=[]
 for j in range(sides):
  nj=(j+1)%sides;faces.append((j,nj,nj+sides,j+sides))
 faces.append(tuple(range(sides,2*sides)))
 o=mesh('Panda hewn rock face embedded layer',verts,[tuple(reversed(f)) for f in faces],rock,tex)
 bevel=o.modifiers.new('Weather softened rock edges','BEVEL');bevel.width=.018;bevel.segments=2
 # The broad front remains planar; uneven edge slopes form real shallow folds.
 for p in o.data.polygons:p.use_smooth=False

# Window glass, frame and fretwork stand in front of the new 5–17 cm stone relief.
for o in list(bpy.context.scene.objects):
 if o.name.startswith(('Panda luminous round window','Panda round bamboo window rim','Panda Chinese geometric lattice')):
  if o.type=='MESH':
   for v in o.data.vertices:
    r=Vector((v.co.x,v.co.y,0));v.co-=r.normalized()*.12
  elif o.type=='CURVE':
   for sp in o.data.splines:
    for p in sp.points:
     r=Vector((p.co.x,p.co.y,0));p.co.x-=r.normalized().x*.12;p.co.y-=r.normalized().y*.12
   if o.name.startswith('Panda Chinese'):o.data.bevel_depth=.032

# Pastel garden light behind the real thick window lattice gives depth without
# opening the entire room to the exterior. The enclosing rock remains intact.
n=512;yy,xx=np.mgrid[0:n,0:n]/n;sky=np.ones((n,n,4));tone=yy[:,:,None]
sky[:,:,:3]=np.array([.59,.69,.55])*(1-tone)+np.array([.86,.88,.79])*tone
for cx,cy,rx,ry in [(.1,.25,.18,.23),(.86,.14,.20,.17),(.36,.12,.12,.21)]:
 mask=np.exp(-((xx-cx)/rx)**2-((yy-cy)/ry)**2)[:,:,None]*.28
 sky[:,:,:3]=sky[:,:,:3]*(1-mask)+np.array([.32,.49,.27])*mask
glow=np.exp(-((xx-.68)/.34)**2-((yy-.72)/.31)**2)[:,:,None]*.22
sky[:,:,:3]=sky[:,:,:3]*(1-glow)+np.array([1,.94,.78])*glow
garden_image=image_map('Panda soft garden beyond round windows',sky,True)
window_mat=mat('Panda softly diffused garden daylight',(.70,.75,.57),rough=.94)
sh=next(n for n in window_mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');tn=window_mat.node_tree.nodes.new('ShaderNodeTexImage');tn.image=garden_image
window_mat.node_tree.links.new(tn.outputs['Color'],sh.inputs['Base Color']);window_mat.node_tree.links.new(tn.outputs['Color'],sh.inputs['Emission Color']);sh.inputs['Emission Strength'].default_value=.35
for o in bpy.context.scene.objects:
 if o.name.startswith('Panda luminous round window') and o.type=='MESH':
  o.visible_shadow=False
  o.data.materials.clear();o.data.materials.append(window_mat);uv=o.data.uv_layers.new(name='UVMap')
  for loop in o.data.loops:
   i=loop.vertex_index;uv.data[loop.index].uv=(.5,.5) if i==0 else (.5+.5*math.cos((i-1)*TAU/64),.5+.5*math.sin((i-1)*TAU/64))

# Smaller mixed-size hand-laid floor slabs with actual broken edges and thickness.
for o in list(bpy.context.scene.objects):
 if o.name.startswith('Panda hand-cut stone floor'):bpy.data.objects.remove(o,do_unlink=True)
floor_seeds=[]
for ix in range(-8,9):
 for iy in range(-8,9):
  if (ix+iy)%7==0:continue
  floor_seeds.append((ix*.68+detail_rng.uniform(-.23,.23),iy*.68+detail_rng.uniform(-.23,.23)))
for sx,sy in floor_seeds:
 if math.hypot(sx,sy)>5.7:continue
 poly=[(5.025*math.cos(a),5.025*math.sin(a)) for a in np.linspace(0,TAU,113)[:-1]]
 for tx,ty in floor_seeds:
  if (sx,sy)==(tx,ty):continue
  poly=clip(poly,tx-sx,ty-sy,(tx*tx+ty*ty-sx*sx-sy*sy)*.5)
  if len(poly)<3:break
 if len(poly)<3:continue
 cx=sum(x for x,y in poly)/len(poly);cy=sum(y for x,y in poly)/len(poly)
 small=[]
 for i,(x,y) in enumerate(poly):
  x=cx+(x-cx)*.994;y=cy+(y-cy)*.994;small.append((x,y))
  if i==1 and len(poly)<9:
   nx,ny=poly[(i+1)%len(poly)];px=x*.57+nx*.43;py=y*.57+ny*.43;small.append((px+(cx-px)*.040,py+(cy-py)*.040))
 top=.197+detail_rng.uniform(-.002,.005)
 o=extrude('Panda detailed layered flagstone',small,.105,top,stone[detail_rng.randrange(4)])
 bevel=o.modifiers.new('Small chipped flagstone edge','BEVEL');bevel.width=.009;bevel.segments=2
 # A shallow broken flake overlaps only the edge, avoiding large changes to foot height.
 if detail_rng.random()<.12 and len(small)>3:
  p,q=Vector((*small[0],top)),Vector((*small[1],top));c=Vector((cx,cy,top))
  verts=[tuple(p.lerp(q,.17)),tuple(p.lerp(q,.6)),tuple(p.lerp(q,.4).lerp(c,.13)+Vector((0,0,.006)))]
  mesh('Panda stone laminated edge chip',verts,[(0,1,2)],stone[1],[(p[0],p[1]) for p in verts])

# Visible joinery, irregular plank edges and thin carved grain in focal furniture.
for o in list(bpy.context.scene.objects):
 if o.type=='MESH' and o.name.startswith(('Panda individual loft board','Panda tea table bamboo slat','Panda stair tread','Panda low tea cabinet top')):
  for v in o.data.vertices:
   p=o.matrix_world@v.co
   if abs(v.co.z-max(vv.co.z for vv in o.data.vertices))<.01:v.co.z+=.003*math.sin(p.x*6+p.y*9)
  make_uv_world(o)
for x in [-3.5,-2.45,-1.35,-.25,.85,1.8]:
 beam('Panda exposed hardwood dowel',(x,1.108,2.84),(x,1.075,2.84),.040,grain_light,16)
for i in range(6):
 y=-.46+i*.185
 for j in range(2):
  pts=[(-.82+t*1.64,y+(j-.5)*.048+.007*math.sin(t*10+i),.807+.0006*math.sin(t*15)) for t in np.linspace(0,1,23)]
  curve('Panda tea tabletop carved grain',pts,.0018,grain_dark)
 for x in [-.76,.76]:beam('Panda tea table peg',(x,y,.801),(x,y,.817),.018,grain_dark,12)
for x in [-3.18,-2.65,-1.98,-1.36,-.74,.05,.68,1.37]:
 for j in range(2):curve('Panda loft fine worn grain',[(x+.018*math.sin(t*12+j),1.4+t*1.4,3.019) for t in np.linspace(0,1,20)],.0013,grain_dark)

# Real rope border and crossed jute strips. Fine fibers are provided by PBR normal maps.
for o in list(bpy.context.scene.objects):
 if o.name.startswith('Panda rug woven fringe'):bpy.data.objects.remove(o,do_unlink=True)
for i in range(57):
 x=-1.48+i*.0526;pts=[(x+.003*math.sin(j*math.pi),-1.53+j*.054,.247+.009*math.sin(j*math.pi/2+i*math.pi)) for j in range(51)]
 curve('Panda jute warp strand',pts,.0105,straw)
for j in range(51):
 y=-1.53+j*.054;pts=[(-1.48+i*.0526,y,.247-.009*math.sin(i*math.pi/2+j*math.pi)) for i in range(57)]
 curve('Panda jute weft strand',pts,.0105,straw)
for side in [-1,1]:
 curve('Panda bound woven rug side',[(side*1.54,y,.247) for y in np.linspace(-1.58,1.17,100)],.031,straw)
 for x in np.arange(-1.5,1.53,.05):curve('Panda knotted rug fringe',[(x,side*1.38-.22,.236),(x+.015,side*1.48-.22,.237),(x,side*1.53-.22,.23)],.011,straw)

def coiled_seat(name,pos,size):
 old=[o for o in bpy.context.scene.objects if o.name==name]
 for o in old:bpy.data.objects.remove(o,do_unlink=True)
 pillow(name,pos,size,straw)
 x,y,z=pos;rx,ry,h=size[0]/2,size[1]/2,size[2]/2;pts=[]
 for t in np.linspace(.02,1,820):
  a=t*TAU*18;r=t*.98;zz=z+h*math.sqrt(max(0,1-r*r))+.005
  pts.append((x+rx*r*math.cos(a),y+ry*r*math.sin(a),zz))
 curve('Panda braided round cushion coil',pts,.0095,straw)
 for a in np.linspace(0,TAU,9)[:-1]:
  curve('Panda cushion hand tied seam',[(x+rx*t*math.cos(a),y+ry*t*math.sin(a),z+h*math.sqrt(max(0,1-t*t))+.011) for t in np.linspace(.04,.9,20)],.004,thread_cream)
coiled_seat('Panda visitor cushion',(0,-1.17,.305),(.84,.79,.21))
coiled_seat('Panda host cushion',(-1.26,.18,.29),(.81,.76,.18))
coiled_seat('Panda loft woven stool',(.68,2.76,3.12),(.65,.58,.19))

# A draped, embroidered cloth replaces the flat rectangular board-like runner.
for o in list(bpy.context.scene.objects):
 if o.name=='Panda tea table sage runner':bpy.data.objects.remove(o,do_unlink=True)
ys=[(-.626,.36),(-.62,.50),(-.615,.67),(-.59,.81),(-.54,.823),(-.25,.823),(0,.823),(.25,.823),(.54,.823),(.59,.81),(.615,.65),(.62,.42)]
v=[]
for j,(y,z) in enumerate(ys):
 for i in range(13):
  x=.30+(i/12-.5)*.48;v.append((x,y+.007*math.sin(i*.9),z+.004*math.sin(i*1.1+j*.2)))
o=mesh('Panda sage draped woven tea cloth',v,[(j*13+i,j*13+i+1,(j+1)*13+i+1,(j+1)*13+i) for j in range(len(ys)-1) for i in range(12)],green,[(i%13/12*.30,i//13*.10) for i in range(len(v))]);solid=o.modifiers.new('Real woven cloth thickness','SOLIDIFY');solid.thickness=.005
for x in np.linspace(.065,.535,20):curve('Panda tea cloth tassel',[(x,-.627,.37),(x+.004,-.629,.31),(x-.004,-.627,.288)],.003,thread_cream)

def embroidered_bamboo(origin,h,plane='front'):
 x,y,z=origin
 def point(u,v):return (x+u,y-.006,z+v) if plane=='front' else (x+.006,y+u,z+v)
 curve('Panda stitched bamboo stem',[point(.022*math.sin(t*4),t*h) for t in np.linspace(0,1,23)],.004,thread)
 for v,sg in [(h*.22,-1),(h*.44,1),(h*.66,-1),(h*.83,1)]:
  curve('Panda stitched bamboo branch',[point(0,v),point(sg*.085,v+.046)],.003,thread)
  for off in [0,.04]:
   verts=[point(sg*(.035+off),v+.02),point(sg*(.13+off),v+.04),point(sg*(.076+off),v+.074)]
   mesh('Panda satin stitch bamboo leaf',verts,[(0,1,2)],thread)
  curve('Panda short bamboo stitch node',[point(-.011,v-.009),point(.014,v-.009)],.004,thread_cream)
embroidered_bamboo((.29,-.639,.37),.33)
# A small drape on the exposed cabinet front, preserving its collision footprint.
vv=[]
for j in range(17):
 for i in range(15):
  y=-.54+i/14*.58;z=.40+j/16*.72;x=-3.10+.012*math.sin(i*1.30)+.006*math.sin(j*.9);vv.append((x,y,z))
curtain=mesh('Panda cabinet embroidered linen curtain',vv,[(j*15+i,j*15+i+1,(j+1)*15+i+1,(j+1)*15+i) for j in range(16) for i in range(14)],cream,[(i%15/14*.4,i//15/16*.5) for i in range(len(vv))]);sol=curtain.modifiers.new('Linen curtain thickness','SOLIDIFY');sol.thickness=.007
embroidered_bamboo((-3.078,-.31,.44),.55,'side')
for y in np.linspace(-.51,.02,18):curve('Panda cabinet curtain fringe',[(-3.09,y,.408),(-3.085,y+.003,.354)],.004,thread_cream)

# Tea tins, rolled textiles, varied ceramic lids and dry herb bundles occupy shelves.
stored=[o for o in bpy.context.scene.objects if o.name.startswith('Panda stored tea jar')]
for i,o in enumerate(stored):
 # Mesh vertices were lathed directly in world space; vary each vessel about its center.
 pts=o.data.vertices;cx=sum(v.co.x for v in pts)/len(pts);cy=sum(v.co.y for v in pts)/len(pts);base=min(v.co.z for v in pts);top=max(v.co.z for v in pts)
 for v in pts:
  v.co.x=cx+(v.co.x-cx)*(.82+(i%3)*.12);v.co.y=cy+(v.co.y-cy)*(.82+(i%3)*.12);v.co.z=base+(v.co.z-base)*(.81+(i%4)*.09)
 height=max(v.co.z for v in pts)
 if i%2==0:
  o.data.materials.clear();o.data.materials.append(dark_clay)
 lathe('Panda individual ceramic lid',(cx,cy,height),[(0,0),(.145,0),(.15,.035),(.10,.065),(0,.07)],bamboo if i%3==0 else dark_clay)
 ball('Panda ceramic lid finial',(cx,cy,height+.09),(.036,.036,.024),dark_clay,16)
 if i%3==0:box('Panda handwritten tea tag',(cx,cy-.21,base+.20),(.13,.016,.16),cream,.009)
for i in range(7):
 x=1.47+i*.04;y=3.18+(i%2)*.025;z=2.52
 curve('Panda drying herb stem',[(x,y,z),(x+.03,y,z-.35),(x-.04,y-.03,z-.63)],.009,bamboo)
 for j in range(4):
  zz=z-.24-j*.09;leaf((x,y,zz),(x+(-1 if j%2 else 1)*.16,y-.04,zz-.10),.045,straw)
curve('Panda herb binding cord',[(1.45,3.17,2.48),(1.65,3.16,2.49),(1.66,3.17,2.53),(1.46,3.18,2.53)],.014,thread_cream)
for i in range(3):
 x=1.50+i*.07;beam('Panda rolled umbrella bamboo',(x,2.17,.34),(x+.03,2.18,1.00+i*.09),.018,bamboo)
plant((-3.95,1.88,.196),.92)
# More life around the pantry and loft; these stay inside existing wall/furniture zones.
box('Panda small plant wall shelf',(-2.77,3.57,2.21),(.55,.38,.09),edge)
plant((-2.78,3.56,2.26),.20)
for i in range(5):
 beam('Panda dry loft flower stalk',(1.72,3.48,3.52),(1.75+.20*math.sin(i*2),3.49+.14*math.cos(i),4.00+i*.025),.006,node_mat)
 end=(1.75+.20*math.sin(i*2),3.49+.14*math.cos(i),4.00+i*.025)
 for a in np.linspace(0,TAU,6)[:-1]:ball('Panda delicate dried flower',(end[0]+.029*math.cos(a),end[1]+.029*math.sin(a),end[2]),(.027,.018,.034),cream,12)

# A generated ink painting is an artwork texture on the real cloth scroll, not
# a room/image-plane stand-in. All furniture and rock still render as geometry.
art_path=NATIVE/'panda-ink-landscape.png'
if art_path.exists():
 art=mat('Panda original ink wash artwork',(.68,.60,.43),rough=.98)
 shader=next(n for n in art.node_tree.nodes if n.type=='BSDF_PRINCIPLED');node=art.node_tree.nodes.new('ShaderNodeTexImage')
 # Keep the original artwork unchanged; runtime uses a compressed color copy.
 original=bpy.data.images.load(str(art_path));original.pack();compressed=NATIVE/'panda-textures'/'panda-ink-landscape-runtime.jpg';original.filepath_raw=str(compressed);original.file_format='JPEG';original.save();bpy.data.images.remove(original)
 node.image=bpy.data.images.load(str(compressed));node.image.pack();art.node_tree.links.new(node.outputs['Color'],shader.inputs['Base Color'])
 for o in list(bpy.context.scene.objects):
  if o.name.startswith('Panda ink mountain silhouette'):bpy.data.objects.remove(o,do_unlink=True)
 mesh('Panda ink painting on linen scroll',[(-3.68,2.688,1.24),(-2.72,2.688,1.24),(-2.72,2.688,2.64),(-3.68,2.688,2.64)],[(0,1,2,3)],art,[(0,0),(1,0),(1,1),(0,1)])

# Apply consistent physical-scale UVs to previously untextured procedural meshes.
for o in list(bpy.context.scene.objects):
 if o.type=='MESH' and not o.name.startswith(('Panda ink painting','Panda sage draped','Panda cabinet embroidered','Panda hewn rock face')):
  if not o.data.uv_layers or o.name.startswith(('Panda tea table','Panda loft','Panda detailed layered')):make_uv_world(o)
print('PANDA_DETAIL_PASS_COMPLETE',len(bpy.context.scene.objects),flush=True)
