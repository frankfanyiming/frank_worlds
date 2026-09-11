"""Blender authoring for the enclosed frog home; preserves existing furniture and rig."""
from pathlib import Path
import bpy, math, random
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

plaster = material('Home stone mortar', (.235, .265, .27))
ceiling = material('Home rough stone vault', (.30, .335, .345))
stones = [material(f'Home weathered limestone {i}', (.30+i*.012, .332+i*.012, .342+i*.011)) for i in range(6)]
wood = material('Home dark oak joinery', (.25, .16, .085))
panel = material('Home honey oak wainscot', (.38, .27, .15))
paper = material('Home diffused daylight panes', (.76, .77, .61), .38)

def mesh(name, vertices, faces, mat):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    if mat: obj.data.materials.append(mat)
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

# Continuous inward-facing wall, with the actual entrance kept open.
segments = 128
heights = [.08, 1.08, 2.82, 5.22]
vertices = [(cx+radius*math.cos(i*math.tau/segments), cy+radius*math.sin(i*math.tau/segments), z)
            for z in heights for i in range(segments)]
faces = []
for j in range(len(heights)-1):
    for i in range(segments):
        angle = (i+.5)*math.tau/segments
        if math.sin(angle)<-.966 and j<2: continue
        k, n = j*segments+i, j*segments+(i+1)%segments
        faces.append((k,k+segments,n+segments,n))
mesh('EnclosureWall', vertices, faces, plaster)

# Vaulted ceiling closes every sightline above the loft.
rings = [(radius,5.22),(4.15,5.67),(3.0,6.03),(.02,6.24)]
vertices = [(cx+r*math.cos(i*math.tau/segments),cy+r*math.sin(i*math.tau/segments),z)
            for r,z in rings for i in range(segments)]
faces = []
for j in range(len(rings)-1):
    for i in range(segments):
        k,n=j*segments+i,j*segments+(i+1)%segments
        faces.append((k,k+segments,n+segments,n))
faces.append(tuple(range((len(rings)-1)*segments,len(rings)*segments)))
mesh('EnclosureCeiling', vertices, faces, ceiling)

# Broad irregular stones, shallow worn edges and recessed mortar make the
# enclosure read as a stone house, including behind the furniture.
rng = random.Random(611)
for row in range(8):
    low = .09+row*.64
    high = min(5.23, low+.625)
    count = 22 if row%2 else 21
    offset = (row%2)*.47
    for index in range(count):
        start = (index+offset)*math.tau/count+.005
        end = (index+1+offset)*math.tau/count-.005
        if math.sin((start+end)*.5)<-.947 and low<2.82: continue
        angles = [start+(end-start)*j/4 for j in range(5)]
        depth = rng.uniform(.045,.075)
        verts = [(cx+r*math.cos(a),cy+r*math.sin(a),z) for r in [radius-depth,radius+.015] for z in [low,high] for a in angles]
        faces = []
        for j in range(4):
            faces.extend([(j,j+5,j+6,j+1),(j+10,j+11,j+16,j+15),(j,j+1,j+11,j+10),(j+5,j+15,j+16,j+6)])
        faces.extend([(0,10,15,5),(4,9,19,14)])
        obj = mesh('Home individual limestone',verts,faces,rng.choice(stones))
        bevel = obj.modifiers.new('Worn stone corners','BEVEL');bevel.width=.014;bevel.segments=2

# Wooden floor remains distinct from the enclosing rock walls.
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=radius, depth=.06, location=(cx,cy,.075))
bpy.context.object.name='EnclosureFloorUnderlay'
bpy.context.object.data.materials.append(wood)
beam('Home trunk into ceiling',(-15.64,12.2,5.05),(-15.60,12.2,6.22),.435,wood)

# The room-side door and threshold close the entrance visually. They disappear
# with this interior as the player crosses the doorstep back into the garden.
for i in range(8):
    box('Home inner door plank',(cx+(i-3.5)*.335,cy-radius+.30,1.43),(.33,.12,2.76),panel)
for z in [.40,2.25]:
    box('Home inner door crosspiece',(cx,cy-radius+.385,z),(2.69,.10,.14),wood)
for i in range(8):
    box('Home entrance floor',(cx+(i-3.5)*.32,cy-radius+.25,.125),(.315,1.50,.055),panel)

# Opaque, softly lit paper windows: daylight has a frame, never an outdoor cutaway.
for index,(angle,z,w,h) in enumerate([(2.15,4.03,1.35,1.70),(.33,2.30,1.40,2.00),(1.06,4.10,1.20,1.55)]):
    radial=Vector((math.cos(angle),math.sin(angle),0))
    tangent=Vector((-math.sin(angle),math.cos(angle),0))
    center=Vector((cx,cy,z))+radial*(radius-.13)
    rot=angle+math.pi/2
    box('Home window daylight',center,(w,.045,h),paper,rot)
    for sign in [-1,1]:
        box('Home window upright',center+tangent*(sign*w*.5)-radial*.065,(.085,.13,h+.14),wood,rot)
        box('Home window lintel',center+Vector((0,0,sign*h*.5))-radial*.07,(w+.15,.14,.085),wood,rot)
    for fraction in [-.25,0,.25]:
        box('Home window mullion',center+tangent*(fraction*w)-radial*.075,(.04,.10,h),wood,rot)
    box('Home window crossbar',center-radial*.085,(w,.10,.045),wood,rot)
    box('Home window sill',center+Vector((0,0,-h*.5-.075))-radial*.15,(w+.28,.40,.10),panel,rot)

bpy.ops.wm.save_as_mainfile(filepath=str(NATIVE/'frog-home-enclosure.blend'))
# Keep the editable timber pieces in the .blend; batch the runtime copy by
# material so the room does not add hundreds of browser draw calls.
groups = {}
for obj in list(bpy.context.scene.objects):
    if obj.type != 'MESH' or obj.name in {'EnclosureWall', 'EnclosureCeiling'}: continue
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
