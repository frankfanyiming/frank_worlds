"""Revision 02 natural-rock enclosure; furniture authored separately in build-frog-furnishings.py."""
from pathlib import Path
import bpy, math, random, json
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'worlds/frog/source/assets'
NATIVE = ROOT / 'worlds/frog/blender'
NATIVE.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
cx, cy, radius = -15.0, 12.0, 4.72

def material(name, color, emission=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    p = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = .92
    if emission:
        p.inputs['Emission Color'].default_value = (*color, 1)
        p.inputs['Emission Strength'].default_value = emission
    return m

# Packed mineral textures remain ordinary Blender materials in the editable file.
# Low-frequency mottling and a subtle normal map avoid a repeated masonry pattern.
def mineral_material(name, color, seed, size=512, scale=2.5):
    """Portable PBR: multiscale minerals + actual tangent-space micro relief.
    Pixel buffer is 8-bit sRGB for color, Non-Color for normal/roughness.
    """
    mat=material(name,color);n=size;rng=np.random.default_rng(seed)
    yy,xx=np.mgrid[0:n,0:n]/n
    def noise(grid):
        v=rng.random((grid+1,grid+1));v[-1,:]=v[0,:];v[:,-1]=v[:,0]
        gx,gy=xx*grid,yy*grid;ix,iy=gx.astype(int),gy.astype(int);u,vv=gx-ix,gy-iy;u=u*u*(3-2*u);vv=vv*vv*(3-2*vv)
        return (1-vv)*((1-u)*v[iy,ix]+u*v[iy,ix+1])+vv*((1-u)*v[iy+1,ix]+u*v[iy+1,ix+1])
    broad=noise(4);mid=noise(19);grain=noise(110);micro=noise(245)
    # Directional mineral lips and tiny pits, not a regular masonry pattern.
    ridge=np.abs(np.sin((xx*.6+yy)*26+mid*5+broad*3))
    fine_cracks=np.maximum(0,.045-ridge)/.045
    pits=np.maximum(0,.22-grain)*3
    height=.034*(broad-.5)+.015*(mid-.5)+.0038*(grain-.5)+.0014*(micro-.5)-fine_cracks*.0028-pits*.0025
    field=.70+.39*broad+.18*mid+.08*(grain-.5)
    rgba=np.ones((n,n,4),dtype=np.float32)
    for c,base in enumerate(color):rgba[:,:,c]=np.clip(base*field*(1-fine_cracks*.09-pits*.13),.001,1)
    rgba[:,:,:3]=np.where(rgba[:,:,:3]<=.0031308,rgba[:,:,:3]*12.92,1.055*np.power(rgba[:,:,:3],1/2.4)-.055)
    image=bpy.data.images.new(name+' mineral color',n,n);image.pixels.foreach_set(rgba.ravel());image.pack()
    nodes,links=mat.node_tree.nodes,mat.node_tree.links;shader=next(n for n in nodes if n.type=='BSDF_PRINCIPLED')
    texture=nodes.new('ShaderNodeTexImage');texture.image=image;links.new(texture.outputs['Color'],shader.inputs['Base Color'])
    dy,dx=np.gradient(height,scale/n);norm=np.dstack((-dx,-dy,np.ones_like(dx)));norm/=np.sqrt(np.sum(norm*norm,axis=2))[...,None]
    rgba[:,:,:3]=norm*.5+.5
    normal=bpy.data.images.new(name+' mineral normal',n,n);normal.colorspace_settings.name='Non-Color';normal.pixels.foreach_set(rgba.ravel());normal.pack()
    texture=nodes.new('ShaderNodeTexImage');texture.image=normal;nm=nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=.78
    links.new(texture.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs['Normal'],shader.inputs['Normal'])
    rgba[:,:,:3]=np.repeat(np.clip(.78+.15*grain+.04*mid,.65,1)[...,None],3,axis=2)
    rough=bpy.data.images.new(name+' roughness',n,n);rough.colorspace_settings.name='Non-Color';rough.pixels.foreach_set(rgba.ravel());rough.pack()
    texture=nodes.new('ShaderNodeTexImage');texture.image=rough;links.new(texture.outputs['Color'],shader.inputs['Roughness'])
    return mat

rock = mineral_material('Home continuous warm grey rock',(.255,.238,.208),911,1024,2.5)
ceiling = rock
seam = material('Home recessed rock fissures',(.116,.105,.085))
floor_mats = [mineral_material(f'Home flagstone {i}',(.275+i*.014,.253+i*.012,.210+i*.010),921+i,512,1.8) for i in range(3)]
floor_grout = material('Home flagstone joints',(.162,.147,.119))
wood = material('Home dark oak joinery', (.25, .16, .085))
panel = material('Home honey oak wainscot', (.38, .27, .15))
paper = material('Home distant garden through glazing', (.50,.56,.44), .055)
# Opaque garden vista is contained inside the window: depth and colour without
# making the room walls transparent or loading the full exterior stage.
n=512;yy,xx=np.mgrid[:n,:n]/(n-1);pixels=np.ones((n,n,4),dtype=np.float32)
sky=np.array((.37,.47,.51));low=np.array((.49,.54,.35))
blend=np.clip(yy[...,None],0,1);rgb=low*(1-blend)+sky*blend
cloud=np.exp(-((xx-.24)**2/.036+(yy-.77)**2/.005))*.33+np.exp(-((xx-.7)**2/.13+(yy-.83)**2/.012))*.20
rgb=rgb*(1-cloud[...,None])+np.array((.70,.71,.59))*cloud[...,None]
forest=.31+.07*np.sin(xx*11)+.06*np.sin(xx*23+1.6)
mask=1/(1+np.exp((yy-forest)*38))
leafvariation=.5+.22*np.sin(xx*29+yy*19)+.16*np.sin(yy*53-xx*13)
forest_color=np.dstack((.10+.11*leafvariation,.20+.13*leafvariation,.065+.065*leafvariation))
rgb=rgb*(1-mask[...,None])+forest_color*mask[...,None]
sun=np.exp(-((xx-.74)**2+(yy-.71)**2)/.007)*.65
rgb=rgb*(1-sun[...,None])+np.array((.88,.79,.51))*sun[...,None]
pixels[:,:,:3]=np.where(rgb<=.0031308,rgb*12.92,1.055*np.power(rgb,1/2.4)-.055)
im=bpy.data.images.new('Soft distant garden window color',n,n);im.pixels.foreach_set(pixels.ravel());im.pack()
shader=next(n for n in paper.node_tree.nodes if n.type=='BSDF_PRINCIPLED');tex=paper.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;paper.node_tree.links.new(tex.outputs['Color'],shader.inputs['Base Color']);shader.inputs['Roughness'].default_value=.45
window_metadata=[]

def mesh(name, vertices, faces, mat, uvcoords=None):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    if mat: obj.data.materials.append(mat)
    if uvcoords:
        uv = data.uv_layers.new(name='UVMap')
        for loop in data.loops: uv.data[loop.index].uv=uvcoords[loop.vertex_index]
    return obj

def box(name, pos, size, mat, rotation=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    o = bpy.context.object
    o.name = name
    o.dimensions = size
    o.rotation_euler.z = rotation
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(mat)
    bevel = o.modifiers.new('Soft timber edges', 'BEVEL')
    bevel.width = .018
    bevel.segments = 2
    return o

def beam(name, a, b, thickness, mat):
    a, b = Vector(a), Vector(b)
    bpy.ops.mesh.primitive_cylinder_add(vertices=12, radius=thickness, depth=(b-a).length, location=(a+b)*.5)
    o = bpy.context.object
    o.name = name
    o.rotation_euler = (b-a).to_track_quat('Z', 'Y').to_euler()
    o.data.materials.append(mat)
    return o

# A single sculpted rock surface: broad irregular planes, no horizontal courses.
def wall_radius(angle, z):
    return radius+.065+.105*math.sin(angle*5+z*.82)+.053*math.sin(angle*9-z*1.1)+.032*math.sin(angle*3+z*2.8)

segments = 96
heights = [.08,.47,.96,1.51,2.12,2.82,3.42,4.05,4.67,5.22]
vertices=[]; uvs=[]; stride=segments+1
for row,z in enumerate(heights):
    for i in range(stride):
        a=i*math.tau/segments
        # Jitter each ring except the doorway edges and the vault junction.
        zz=z+(.065*math.sin(a*7+row*2.2) if row not in [0,5,9] else 0)
        r=wall_radius(a,zz)
        vertices.append((cx+r*math.cos(a),cy+r*math.sin(a),zz))
        uvs.append((a*radius/2.5,zz/2.5))
faces=[]
for j in range(len(heights)-1):
    for i in range(segments):
        angle = (i+.5)*math.tau/segments
        if math.sin(angle)<-.966 and heights[j]<2.82: continue
        k=j*stride+i; n=k+1
        faces.extend([(k,k+stride,n+stride),(k,n+stride,n)])
wall=mesh('EnclosureWall',vertices,faces,rock,uvs)
for polygon in wall.data.polygons: polygon.use_smooth=True

# Vaulted ceiling closes every sightline above the loft.
rings = [(radius,5.22),(4.15,5.67),(3.0,6.03),(.02,6.24)]
vertices=[]
for ring,(r,z) in enumerate(rings):
    for i in range(segments):
        a=i*math.tau/segments
        rr=wall_radius(a,z) if ring==0 else r
        vertices.append((cx+rr*math.cos(a),cy+rr*math.sin(a),z))
faces = []
for j in range(len(rings)-1):
    for i in range(segments):
        k,n=j*segments+i,j*segments+(i+1)%segments
        faces.append((k,k+segments,n+segments,n))
faces.append(tuple(range((len(rings)-1)*segments,len(rings)*segments)))
roof=mesh('EnclosureCeiling',vertices,faces,ceiling,[(x/3.1,y/3.1) for x,y,z in vertices])
for polygon in roof.data.polygons: polygon.use_smooth=True

# A few tapered, uneven fissures follow the rock, never forming a tile grid.
rng = random.Random(611)
for index in range(15):
    a=(index+.3)*math.tau/15; start=rng.uniform(1.6,5.0); length=rng.uniform(.45,1.15)
    if math.sin(a)<-.93:continue
    vertices=[]
    for i in range(7):
        t=i/6; z=start-t*length
        angle=a+t*.085+.018*math.sin(t*5+index)
        half=.0014*math.sin(math.pi*t)
        for side in [-1,1]:
            aa=angle+side*half; r=wall_radius(aa,z)-.012
            vertices.append((cx+r*math.cos(aa),cy+r*math.sin(aa),z))
    mesh('Home natural hairline fissure',vertices,[(i*2,i*2+2,i*2+3,i*2+1) for i in range(6)],seam)

# Voronoi flagstones form the ground floor; the original timber loft is retained.
def clip_polygon(polygon, nx, ny, distance):
    out=[]
    for first,second in zip(polygon,polygon[1:]+polygon[:1]):
        fa=first[0]*nx+first[1]*ny-distance; fb=second[0]*nx+second[1]*ny-distance
        if fa<=0:out.append(first)
        if (fa<0)!=(fb<0):
            t=fa/(fa-fb);out.append((first[0]+t*(second[0]-first[0]),first[1]+t*(second[1]-first[1])))
    return out

bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=4.94, depth=.065, location=(cx,cy,.145))
bpy.context.object.name='EnclosureFloorUnderlay'
bpy.context.object.data.materials.append(floor_grout)
seeds=[]
for _ in range(2500):
    x,y=rng.uniform(-5.7,5.7),rng.uniform(-5.7,5.7)
    minimum=.53 if rng.random()<.28 else .86
    if all(math.hypot(x-a,y-b)>minimum for a,b in seeds):seeds.append((x,y))
    if len(seeds)>=105:break
boundary=[(4.94*math.cos(i*math.tau/96),4.94*math.sin(i*math.tau/96)) for i in range(96)]
for sx,sy in seeds:
    if math.hypot(sx,sy)>5.55:continue
    polygon=boundary[:]
    for tx,ty in seeds:
        if (sx,sy)==(tx,ty):continue
        polygon=clip_polygon(polygon,tx-sx,ty-sy,(tx*tx+ty*ty-sx*sx-sy*sy)*.5)
        if len(polygon)<3:break
    if len(polygon)<3:continue
    center=(sum(x for x,y in polygon)/len(polygon),sum(y for x,y in polygon)/len(polygon))
    polygon=[(cx+center[0]+(x-center[0])*.983,cy+center[1]+(y-center[1])*.983) for x,y in polygon]
    # Break long straight outlines with shallow natural chips; shared joints stay narrow.
    chipped=[]
    for first,second in zip(polygon,polygon[1:]+polygon[:1]):
        chipped.append(first)
        if math.dist(first,second)>.25:
            t=rng.uniform(.35,.65);mx=first[0]*(1-t)+second[0]*t;my=first[1]*(1-t)+second[1]*t
            dx=cx+center[0]-mx;dy=cy+center[1]-my;L=math.hypot(dx,dy);chip=rng.uniform(.008,.023)
            chipped.append((mx+dx/L*chip,my+dy/L*chip))
    polygon=chipped
    count=len(polygon)
    top=.188+rng.uniform(-.001,.001)
    vertices=[(x,y,z) for z in [.143,top] for x,y in polygon]
    faces=[tuple(reversed(range(count))),tuple(range(count,2*count))]
    faces.extend([(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)])
    slab=mesh('Home irregular floor slab',vertices,faces,rng.choice(floor_mats),[(x/1.8,y/1.8) for x,y,z in vertices])
    bevel=slab.modifiers.new('Worn flagstone edges','BEVEL');bevel.width=.016;bevel.segments=3
# Broad irregular natural rock planes: a continuous cave skin, not brick courses.
# Cells occupy the unwrapped wall and make shallow angled facets. They retain
# closed backing and are joined to EnclosureWall for the same real collision mesh.
wall_cells=[];half=radius*math.pi
rrng=random.Random(913);wall_seeds=[]
for _ in range(6000):
    u,v=rrng.uniform(-half,half),rrng.uniform(.10,5.20)
    if all(math.hypot(u-a,(v-b)*1.05)>1.08 for a,b in wall_seeds):wall_seeds.append((u,v))
    if len(wall_seeds)>=65:break
for idx,(su,sv) in enumerate(wall_seeds):
    poly=[(-half,.08),(half,.08),(half,5.22),(-half,5.22)]
    for tu,tv in wall_seeds:
        if (su,sv)==(tu,tv):continue
        poly=clip_polygon(poly,tu-su,tv-sv,(tu*tu+tv*tv-su*su-sv*sv)*.5)
        if len(poly)<3:break
    if len(poly)<3:continue
    # Keep front door opening undisturbed.
    a=su/radius
    if math.sin(a)<-.87 and sv<3.0:continue
    cu=sum(p[0] for p in poly)/len(poly);cv=sum(p[1] for p in poly)/len(poly)
    depth=rrng.uniform(.052,.145)
    verts=[];uv=[];count=len(poly)
    for inset in [0,.30]:
        for u,v in poly:
            uu=u*(1-inset)+cu*inset;vv=v*(1-inset)+cv*inset;aa=uu/radius
            inward=.013 if inset==0 else depth*(.75+.25*math.sin(aa*7+vv*3))
            rad=wall_radius(aa,vv)-inward
            verts.append((cx+rad*math.cos(aa),cy+rad*math.sin(aa),vv));uv.append((uu/2.5,vv/2.5))
    fs=[]
    for i in range(count):fs.append((i,(i+1)%count,(i+1)%count+count,i+count))
    fs.append(tuple(range(count,count*2)))
    fs=[tuple(reversed(face)) for face in fs]
    o=mesh('Natural cave broad rock face %02d'%idx,verts,fs,rock,uv)
    # Weighted bevel softens edges while keeping wide readable planes.
    mod=o.modifiers.new('Subtle softened rock arris','BEVEL');mod.width=.013;mod.segments=2
    wall_cells.append(o)
# Fine branches occasionally accent a broad plane; avoid a tiled outline on every face.
for idx in range(24):
    a=rrng.uniform(-math.pi,math.pi);z=rrng.uniform(.7,5.15)
    if math.sin(a)<-.9:continue
    vertices=[]
    for j in range(8):
        t=j/7;aa=a+.03*math.sin(t*4+idx)+.038*t;zz=z-t*rrng.uniform(.6,1.2)
        rad=wall_radius(aa,zz)-.020
        for side in [-1,1]:
            aw=aa+side*.0012*math.sin(math.pi*t)
            vertices.append((cx+rad*math.cos(aw),cy+rad*math.sin(aw),zz))
    mesh('Natural forked fissure',vertices,[(j*2,j*2+2,j*2+3,j*2+1) for j in range(7)],seam)

# The slimmer left trunk is authored with the new furnishings.

# The room-side door and threshold close the entrance visually. They disappear
# with this interior as the player crosses the doorstep back into the garden.
for i in range(8):
    box('Home inner door plank',(cx+(i-3.5)*.335,cy-radius+.30,1.43),(.33,.12,2.76),panel)
for z in [.40,2.25]:
    box('Home inner door crosspiece',(cx,cy-radius+.385,z),(2.69,.10,.14),wood)
box('Home stone threshold',(cx,cy-radius+.25,.155),(2.76,1.50,.07),floor_mats[0])

# Opaque, softly lit paper windows: daylight has a frame, never an outdoor cutaway.
for index,(angle,z,w,h) in enumerate([(2.15,4.03,1.35,1.70),(.33,2.30,1.40,2.00),(1.06,4.10,1.20,1.55)]):
    radial=Vector((math.cos(angle),math.sin(angle),0))
    tangent=Vector((-math.sin(angle),math.cos(angle),0))
    center=Vector((cx,cy,z))+radial*(wall_radius(angle,z)-.20)
    rr=w*.54; up=Vector((0,0,1))
    disk=[tuple(center)]+[tuple(center+tangent*(rr*math.cos(i*math.tau/64))+up*(rr*math.sin(i*math.tau/64))) for i in range(64)]
    mesh('FrogWindowBackground',disk,[(0,i+1,(i+1)%64+1) for i in range(64)],paper,[(.5,.5)]+[(.5+.5*math.cos(i*math.tau/64),.5+.5*math.sin(i*math.tau/64)) for i in range(64)])
    # A cut-stone reveal and substantial oak ring give the window real depth.
    reveal_vertices=[]
    for rr2,depth in [(rr+.23,.00),(rr+.13,-.15),(rr+.055,-.09)]:
        for i in range(64):
            aa=i*math.tau/64;across=tangent*math.cos(aa)+up*math.sin(aa)
            reveal_vertices.append(tuple(center+across*rr2+radial*depth))
    reveal_faces=[]
    for layer in range(2):
        for i in range(64):
            q=layer*64+i;r=layer*64+(i+1)%64;reveal_faces.append((q,r,r+64,q+64))
    # Angular-first strip winding faces the rock; flip the reveal toward the room.
    mesh('Home thick stone window reveal',reveal_vertices,[tuple(reversed(face)) for face in reveal_faces],rock,[(i/64,j) for j in range(3) for i in range(64)])
    sx,sy,sz=5.6/4.72,4.9/4.72,(6.6-.2)/(6.24-.2)
    p=[cx+(center.x-cx)*sx,.2+(center.z-.2)*sz,-cy-(center.y-cy)*sy]
    inward=Vector((-radial.x/sx,0,radial.y/sy)).normalized()
    window_metadata.append({'name':'FrogWindow%d'%index,'position':[round(v,5) for v in p],'inward_normal':[round(v,5) for v in inward],'width':round(2*rr*math.hypot(math.sin(angle)*sx,math.cos(angle)*sy),4),'height':round(2*rr*sz,4)})
    verts=[];faces=[]
    for i in range(64):
        a=i*math.tau/64; across=tangent*math.cos(a)+up*math.sin(a)
        for j in range(10):
            b=j*math.tau/10
            verts.append(tuple(center+across*(rr+.090*math.cos(b))-radial*(.075+.090*math.sin(b))))
    for i in range(64):
        for j in range(10): faces.append((i*10+j,((i+1)%64)*10+j,((i+1)%64)*10+(j+1)%10,i*10+(j+1)%10))
    # The (around, tube) parameter order points inward; reverse only the torus.
    # Window bars/door joinery share this material but already face outward.
    ring=mesh('Home round oak window frame',verts,[tuple(reversed(face)) for face in faces],wood)
    for face in ring.data.polygons:face.use_smooth=True
    for offset in [-.30,0,.30]:
        reach=math.sqrt(rr*rr-offset*offset)-.035
        beam('Home round window upright',center+tangent*offset+up*.10-radial*.10,center+tangent*offset+up*reach-radial*.10,.018,wood)
    reach=math.sqrt(rr*rr-.10*.10)-.025
    beam('Home round window crossbar',center-tangent*reach+up*.10-radial*.10,center+tangent*reach+up*.10-radial*.10,.022,wood)

# Increase room moderately (10.37 frog heights across), preserving floor height.
# Enclosure meshes are centered in Blender coordinates (-15,12,0); glTF maps
# these to Godot (-15,0,-12). The exterior keeps its independent entry portal.
from mathutils import Matrix
for obj in list(bpy.context.scene.objects):
    if obj.type != 'MESH': continue
    bpy.context.view_layer.objects.active=obj
    for modifier in list(obj.modifiers): bpy.ops.object.modifier_apply(modifier=modifier.name)
    mw=obj.matrix_world.copy()
    inv=mw.inverted()
    for v in obj.data.vertices:
        p=mw@v.co
        p.x=cx+(p.x-cx)*(5.6/4.72)
        p.y=cy+(p.y-cy)*(4.9/4.72)
        if p.z>.20:p.z=.20+(p.z-.20)*(6.6-.20)/(6.24-.20)
        v.co=inv@p
# Include visible sculpted rock planes in the wall collision object. Inner
# relief remains below 0.16 units; walking route and staircase stay unchanged.
bpy.ops.object.select_all(action='DESELECT')
wall.select_set(True)
for o in wall_cells:o.select_set(True)
bpy.context.view_layer.objects.active=wall;bpy.ops.object.join();wall.name='EnclosureWall'

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

bpy.ops.wm.save_as_mainfile(filepath=str(NATIVE/'frog-home-enclosure.blend'))
runtime_colour_jpegs()
# Keep the editable timber pieces in the .blend; batch the runtime copy by
# material so the room does not add hundreds of browser draw calls.
groups = {}
for obj in list(bpy.context.scene.objects):
    if obj.type != 'MESH' or obj.name in {'EnclosureWall', 'EnclosureCeiling', 'EnclosureFloorUnderlay'}: continue
    bpy.context.view_layer.objects.active = obj
    for modifier in list(obj.modifiers): bpy.ops.object.modifier_apply(modifier=modifier.name)
    groups.setdefault(obj.data.materials[0].name, []).append(obj)
for index, objects in enumerate(groups.values()):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects: obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    bpy.context.object.name = 'FrogWindowBackground' if bpy.context.object.data.materials[0]==paper else f'HomeDetails_{index:02}'
bpy.ops.export_scene.gltf(filepath=str(ASSETS/'home-enclosure.glb'),export_format='GLB',export_apply=True,export_animations=False,export_cameras=False,export_lights=False)
(ASSETS/'home-window-lighting.json').write_text(json.dumps(window_metadata,ensure_ascii=False,indent=2)+'\n')
print('HOME_ENCLOSURE_EXPORTED', len(bpy.data.objects), (ASSETS/'home-enclosure.glb').stat().st_size)
