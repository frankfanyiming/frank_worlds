import {defineConfig} from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/postcss';
import {readdirSync,rmSync,statSync,writeFileSync,readFileSync} from 'node:fs';
import {resolve,relative} from 'node:path';
import {fileURLToPath,URL} from 'node:url';
import {MODEL_PARTS,STARTUP_PARTS} from './lib/town/model-manifest';
export default defineConfig({
 base:process.env.SITE_BASE || '/frank_worlds/',
 plugins:[react(),{name:'ship-runtime-assets-only',closeBundle(){
  const models=new Set(MODEL_PARTS.map(name=>name+'.glb'));models.add('world.json');
  rmSync(resolve('dist-pages/textures'),{recursive:true,force:true});
  const folder=resolve('dist-pages/models');
  const walk=(dir:string)=>{for(const name of readdirSync(dir)){const path=resolve(dir,name);if(statSync(path).isDirectory())walk(path);else if(!models.has(relative(folder,path)))rmSync(path);}};walk(folder);
  const sizes=[...models].map(name=>({name,bytes:statSync(resolve(folder,name)).size}));
  const startupNames=new Set([...STARTUP_PARTS.map(name=>name+'.glb'),'world.json']);
  const startupModelBytes=sizes.filter(v=>startupNames.has(v.name)).reduce((sum,v)=>sum+v.bytes,0);
  const totalModelBytes=sizes.reduce((sum,v)=>sum+v.bytes,0);
  const roomManifest=JSON.parse(readFileSync('dist-pages/bedroom-materials/manifest.json','utf8'));
  const roomMaterialBytes=roomManifest.files.reduce((sum:number,f:{bytes:number})=>sum+f.bytes,0);
  writeFileSync('dist-pages/asset-sizes.json',JSON.stringify({startupModelBytes,deferredModelBytes:totalModelBytes-startupModelBytes,totalModelBytes,roomMaterialBytes,totalModelAndMaterialBytes:totalModelBytes+roomMaterialBytes,models:sizes},null,2));
 }}],
 resolve:{alias:{'@':fileURLToPath(new URL('.',import.meta.url))}},
 css:{postcss:{plugins:[tailwindcss()]}},
 build:{outDir:'dist-pages',emptyOutDir:true},
});
