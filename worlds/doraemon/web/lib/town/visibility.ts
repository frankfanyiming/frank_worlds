import * as THREE from 'three';

/** Preserve gameplay/visibility flags while keeping distant geometry out of room passes. */
export class TownVisibility {
 private meshes=new Set<THREE.Mesh>();
 private sphere=new THREE.Sphere();
 culled=0;
 constructor(private mobile:boolean){}
 unregister(root:THREE.Object3D){root.traverse(o=>{if(o instanceof THREE.Mesh)this.meshes.delete(o);});}
 register(root:THREE.Object3D){
  if(!this.mobile)return;
  root.updateWorldMatrix(true,true);
  root.traverse(o=>{
   if(!(o instanceof THREE.Mesh))return;
   if(o instanceof THREE.SkinnedMesh){
    // Bind-pose bounds are unsafe for animated limbs. Keep a generous envelope
    // around the actual posed mesh; the character root still moves normally.
    o.skeleton.update();o.computeBoundingSphere();
    if(o.boundingSphere)o.boundingSphere.radius*=2;
    o.frustumCulled=true;
   }else if(!o.geometry.boundingSphere)o.geometry.computeBoundingSphere();
   this.meshes.add(o);
  });
 }
 update(center:THREE.Vector3,roomView:boolean,overview=false){
  if(!this.mobile)return;
  this.culled=0;
  for(const mesh of this.meshes){
   const bounds=mesh instanceof THREE.SkinnedMesh?mesh.boundingSphere:mesh.geometry.boundingSphere;
   if(!bounds)continue;
   this.sphere.copy(bounds).applyMatrix4(mesh.matrixWorld);
   // The near neighbourhood stays visible through windows. The distant forest
   // is completely occluded by the house at these interior camera positions.
   const hidden=!overview&&this.sphere.distanceToPoint(center)>(roomView?24:48);
   mesh.layers.set(hidden?1:0);if(hidden)this.culled++;
  }
 }
}
