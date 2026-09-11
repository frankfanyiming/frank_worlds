"""Blender authoring for the enclosed frog home; preserves existing furniture and rig."""
from pathlib import Path
import bpy, math, random
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
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = .92
    if emission:
        p.inputs['Emission Color'].default_value = (*color, 1)
        p.inputs['Emission Strength'].default_value = emission
    return m

# Packed mineral textures remain ordinary Blender materials in the editable file.
# Low-frequency mottling and a subtle normal map avoid a repeated masonry pattern.
def mineral_material(name, color, seed):
    mat = material(name, color)
    n = 512
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:n,0:n]/n
    field = np.zeros((n,n))
    for grid, weight in [(3,.48),(8,.28),(24,.16),(96,.08)]:
        values = rng.random((grid+1,grid+1))
        values[-1,:] = values[0,:]; values[:,-1] = values[:,0]
        gx,gy = xx*grid,yy*grid; ix,iy = gx.astype(int),gy.astype(int)
        u,v = gx-ix,gy-iy; u=u*u*(3-2*u); v=v*v*(3-2*v)
        field += weight*((1-v)*((1-u)*values[iy,ix]+u*values[iy,ix+1])+v*((1-u)*values[iy+1,ix]+u*values[iy+1,ix+1]))
    rgba = np.ones((n,n,4),dtype=np.float32)
    for channel, base in enumerate(color): rgba[:,:,channel] = base*(.80+field*.40)
    # PNG color samples are sRGB; keep the intended linear Blender albedo.
    rgba[:,:,:3]=np.where(rgba[:,:,:3]<=.0031308,rgba[:,:,:3]*12.92,1.055*np.power(rgba[:,:,:3],1/2.4)-.055)
    image = bpy.data.images.new(name+' mineral color',n,n); image.pixels.foreach_set(rgba.ravel()); image.pack()
    nodes,links = mat.node_tree.nodes,mat.node_tree.links
    shader = nodes.get('Principled BSDF')
    texture = nodes.new('ShaderNodeTexImage'); texture.image=image
    links.new(texture.outputs['Color'],shader.inputs['Base Color'])
    dy,dx = np.gradient(field)
    rgba[:,:,0]=.5-dx*2.5; rgba[:,:,1]=.5-dy*2.5; rgba[:,:,2]=1
    normal = bpy.data.images.new(name+' mineral normal',n,n); normal.colorspace_settings.name='Non-Color'
    normal.pixels.foreach_set(rgba.ravel()); normal.pack()
    texture=nodes.new('ShaderNodeTexImage'); texture.image=normal
    normal_map=nodes.new('ShaderNodeNormalMap'); normal_map.inputs['Strength'].default_value=.38
    links.new(texture.outputs['Color'],normal_map.inputs['Color']); links.new(normal_map.outputs['Normal'],shader.inputs['Normal'])
    return mat

rock = mineral_material('Home continuous warm grey rock',(.37,.355,.325),911)
ceiling = rock
seam = material('Home recessed rock fissures',(.235,.23,.211))
floor_mats = [mineral_material(f'Home flagstone {i}',(.315+i*.012,.328+i*.011,.314+i*.010),921+i) for i in range(4)]
floor_grout = material('Home flagstone joints',(.145,.158,.151))
wood = material('Home dark oak joinery', (.25, .16, .085))
panel = material('Home honey oak wainscot', (.38, .27, .15))
paper = material('Home diffused daylight panes', (.76, .77, .61), .38)

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
    return radius+.055+.070*math.sin(angle*5+z*.82)+.038*math.sin(angle*9-z*1.1)+.023*math.sin(angle*3+z*2.8)

segments = 64
heights = [.08,.58,1.10,1.67,2.21,2.82,3.37,3.99,4.61,5.22]
vertices=[]; uvs=[]; stride=segments+1
for row,z in enumerate(heights):
    for i in range(stride):
        a=i*math.tau/segments
        # Jitter each ring except the doorway edges and the vault junction.
        zz=z+(.065*math.sin(a*7+row*2.2) if row not in [0,5,9] else 0)
        r=wall_radius(a,zz)
        vertices.append((cx+r*math.cos(a),cy+r*math.sin(a),zz))
        uvs.append((a*radius/3.1,zz/3.1))
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
seeds=[(x*1.15+rng.uniform(-.36,.36),y*1.15+rng.uniform(-.36,.36)) for x in range(-5,6) for y in range(-5,6)]
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
    polygon=[(cx+center[0]+(x-center[0])*.975,cy+center[1]+(y-center[1])*.975) for x,y in polygon]
    count=len(polygon)
    top=.188+rng.uniform(-.001,.001)
    vertices=[(x,y,z) for z in [.143,top] for x,y in polygon]
    faces=[tuple(reversed(range(count))),tuple(range(count,2*count))]
    faces.extend([(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)])
    slab=mesh('Home irregular floor slab',vertices,faces,rng.choice(floor_mats),[(x/2.7,y/2.7) for x,y,z in vertices])
    bevel=slab.modifiers.new('Worn flagstone edges','BEVEL');bevel.width=.007;bevel.segments=2
beam('Home trunk into ceiling',(-15.64,12.2,5.05),(-15.60,12.2,6.22),.435,wood)

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
    mesh('Home round diffused window',disk,[(0,i+1,(i+1)%64+1) for i in range(64)],paper)
    verts=[];faces=[]
    for i in range(64):
        a=i*math.tau/64; across=tangent*math.cos(a)+up*math.sin(a)
        for j in range(10):
            b=j*math.tau/10
            verts.append(tuple(center+across*(rr+.065*math.cos(b))-radial*(.075+.065*math.sin(b))))
    for i in range(64):
        for j in range(10): faces.append((i*10+j,((i+1)%64)*10+j,((i+1)%64)*10+(j+1)%10,i*10+(j+1)%10))
    ring=mesh('Home round oak window frame',verts,faces,wood)
    for face in ring.data.polygons:face.use_smooth=True
    for offset in [-.30,0,.30]:
        reach=math.sqrt(rr*rr-offset*offset)-.035
        beam('Home round window upright',center+tangent*offset+up*.10-radial*.10,center+tangent*offset+up*reach-radial*.10,.018,wood)
    reach=math.sqrt(rr*rr-.10*.10)-.025
    beam('Home round window crossbar',center-tangent*reach+up*.10-radial*.10,center+tangent*reach+up*.10-radial*.10,.022,wood)

bpy.ops.wm.save_as_mainfile(filepath=str(NATIVE/'frog-home-enclosure.blend'))
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
    bpy.context.object.name = f'HomeDetails_{index:02}'
bpy.ops.export_scene.gltf(filepath=str(ASSETS/'home-enclosure.glb'),export_format='GLB',export_apply=True,export_animations=False,export_cameras=False,export_lights=False)
print('HOME_ENCLOSURE_EXPORTED', len(bpy.data.objects), (ASSETS/'home-enclosure.glb').stat().st_size)
