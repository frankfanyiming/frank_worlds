"""Terrain-fitted timber approaches for the existing creek bridge (Blender).

The bridge's original .325m end was above the adjoining meadow. Full-footprint
navigation correctly rejected that abrupt edge. Author a continuous physical
approach, retaining collision checks and the original central bridge surface.
"""
import sys, math, importlib.util, shutil
from pathlib import Path
import numpy as np
import bpy
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools/conan'))
import reference_geometry as g
spec=importlib.util.spec_from_file_location('glb',ROOT/'tools/conan/patch-street-context.py')
lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)
src=lib.GLB(ROOT/'worlds/frog/source/assets/woodland.glb')
node=next(n for n in src.d['nodes'] if n.get('name')=='Landscape_Moss_meadow')
triangles=[]
for p in src.d['meshes'][node['mesh']]['primitives']:
    triangles.extend(src.acc(p['attributes']['POSITION'])[src.acc(p['indices']).reshape(-1,3)])
tri=np.asarray(triangles)
def terrain(x,z):
    a=tri[:,0];b=tri[:,1]-a;c=tri[:,2]-a
    den=b[:,0]*c[:,2]-b[:,2]*c[:,0]
    ok=abs(den)>1e-8;den=np.where(ok,den,1)
    u=((x-a[:,0])*c[:,2]-(z-a[:,2])*c[:,0])/den
    v=(b[:,0]*(z-a[:,2])-b[:,2]*(x-a[:,0]))/den
    hits=ok&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1.000001)
    if not hits.any():raise ValueError((x,z,'outside meadow'))
    return float((a[:,1]+b[:,1]*u+c[:,1]*v)[hits].max())
def bridge(x):
    xs=np.linspace(10.7,17.4,28)
    return float(np.interp(x,xs,.325+.75*np.sin(np.linspace(0,math.pi,28))))+.008
g.init();g.OUT=ROOT/'worlds/frog/blender';g.GROUP='BridgeApproach-col'
wood=g.mat('Bridge approach honey timber','bba471',.94)
joint=g.mat('Bridge approach fine board joint','9c885e',.98)
for side,(ground,end) in enumerate([(9.65,11.08),(18.45,17.02)]):
    vs=[];N=16
    for i in range(N+1):
        t=i/N;x=ground+(end-ground)*t;half=.94*(1-t)+.755*t
        for z in [-9-half,-9+half]:
            h=(terrain(ground,z)+.006)*(1-t)+bridge(end)*t
            vs.append((x,h,z))
    top=len(vs);vs.extend((x,y-.075,z) for x,y,z in vs[:])
    fs=[]
    for i in range(N):
        a=i*2;b=(i+1)*2
        fs += [(a,b,b+1,a+1),(a+top,a+1+top,b+1+top,b+top),
               (a,a+top,b+top,b),(a+1,b+1,b+1+top,a+1+top)]
    fs += [(0,1,1+top,top),(2*N,2*N+top,2*N+1+top,2*N+1)]
    g.mesh('Terrain-fitted timber approach '+str(side),vs,fs,wood,recalc=True)
    for i in range(2,N,2):
        a,b=vs[2*i:2*i+2]
        g.rod('Approach plank joint',(a[0],a[1]+.003,a[2]+.015),
              (b[0],b[1]+.003,b[2]-.015),.004,joint,group='ApproachJoinery')
g.export_asset('bridge-approaches')
bpy.ops.wm.save_as_mainfile(filepath=str(g.OUT/'bridge-approaches22.blend'))
shutil.copy2(g.OUT/'bridge-approaches.glb',ROOT/'worlds/frog/source/assets/bridge-approaches.glb')
print('BRIDGE_APPROACHES_READY')
