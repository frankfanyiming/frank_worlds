// Create an isolated runtime derivative. Geometry, collision, UVs, skeletons,
// animations and desktop source files stay byte-identical.
import {createRequire} from 'node:module';
import {readFile,writeFile,readdir,mkdir,cp,stat} from 'node:fs/promises';
import {resolve,relative,join} from 'node:path';
import {createHash} from 'node:crypto';
const require=createRequire(resolve(process.env.MOBILE_ASSET_TOOLS||'tools/mobile-assets','package.json'));
const sharp=require('sharp');sharp.concurrency(2);
const world=process.argv[2];if(!['frog','conan'].includes(world))throw Error('Choose frog or conan');
const source=resolve('worlds',world,world==='frog'?'source':'web-project'),dest=resolve(process.argv[3]||`../native-mobile24/${world}`);
if(dest===source||dest.startsWith(source+'/'))throw Error('Use a separate derivative directory');
await mkdir(dest,{recursive:true});
await cp(source,dest,{recursive:true,filter:p=>!relative(source,p).split('/').some(s=>s==='.godot'||s==='.DS_Store')});
const report={world,source,dest,sourceFilesPreserved:true,geometryAndAnimationPreserved:true,images:[],glbs:[]};
const sha=b=>createHash('sha256').update(b).digest('hex');
async function image(input,limit){
 const meta=await sharp(input).metadata();if(!meta.width||!meta.height)return null;
 const p=sharp(input).resize(limit,limit,{fit:'inside',withoutEnlargement:true});
 const alpha=meta.hasAlpha&&!(await sharp(input).stats()).isOpaque;
 const bytes=await (alpha?p.png({compressionLevel:9}):p.jpeg({quality:86,chromaSubsampling:'4:4:4'})).toBuffer();
 return{bytes,mime:alpha?'image/png':'image/jpeg',width:meta.width,height:meta.height};
}
async function walk(dir){
 for(const entry of await readdir(dir,{withFileTypes:true})){
  const path=join(dir,entry.name);if(entry.isDirectory()){await walk(path);continue;}
  const rel=relative(dest,path);
  if(/\.glb$/i.test(path)){
   const raw=await readFile(path);if(raw.readUInt32LE(0)!==0x46546c67)throw Error('Invalid GLB '+rel);
   const jsonLength=raw.readUInt32LE(12),doc=JSON.parse(raw.subarray(20,20+jsonLength).toString()),bin=raw.subarray(28+jsonLength),views=doc.bufferViews||[];
   const images=new Map();for(const im of doc.images||[])if(im.bufferView!==undefined)images.set(im.bufferView,im);
   if(!images.size)continue;
   const buffers=[];let offset=0,count=0;
   for(let i=0;i<views.length;i++){
    const view=views[i];let bytes=bin.subarray(view.byteOffset||0,(view.byteOffset||0)+view.byteLength);
    if(images.has(i)){
     const limit=/^(?:conan|frog|panda|agasa|kogoro|ran|haibara)\.glb$/.test(entry.name)?1024:512;
     const next=await image(bytes,limit);if(next){bytes=next.bytes;images.get(i).mimeType=next.mime;count++;}
    }
    const pad=(4-offset%4)%4;if(pad){buffers.push(Buffer.alloc(pad));offset+=pad;}
    view.byteOffset=offset;view.byteLength=bytes.length;buffers.push(bytes);offset+=bytes.length;
   }
   const binary=Buffer.concat(buffers);doc.buffers[0].byteLength=binary.length;
   const text=Buffer.from(JSON.stringify(doc)),json=Buffer.concat([text,Buffer.alloc((4-text.length%4)%4,32)]),data=Buffer.concat([binary,Buffer.alloc((4-binary.length%4)%4)]);
   const header=Buffer.alloc(20);header.writeUInt32LE(0x46546c67);header.writeUInt32LE(2,4);header.writeUInt32LE(28+json.length+data.length,8);header.writeUInt32LE(json.length,12);header.writeUInt32LE(0x4e4f534a,16);
   const bh=Buffer.alloc(8);bh.writeUInt32LE(data.length);bh.writeUInt32LE(0x004e4942,4);const output=Buffer.concat([header,json,bh,data]);
   await writeFile(path,output);report.glbs.push({file:rel,before:raw.length,after:output.length,images:count,sourceSha256:sha(raw),sha256:sha(output)});
  }
  // External maps are resized by the importer, preserving file names and UVs.
  if(/\.(png|jpe?g|webp)\.import$/i.test(path)){
   let text=await readFile(path,'utf8');const limit=/Color|albedo|diffuse/i.test(entry.name)?768:512;
   text=text.replace(/^process\/size_limit=.*$/m,'process/size_limit='+limit).replace(/^mipmaps\/generate=.*$/m,'mipmaps/generate=true');
   await writeFile(path,text);report.images.push({file:rel,maxDimension:limit});
  }
 }
}
await walk(dest);
let preset=await readFile(join(dest,'export_presets.cfg'),'utf8');preset=preset.replace('vram_texture_compression/for_desktop=true','vram_texture_compression/for_desktop=false');await writeFile(join(dest,'export_presets.cfg'),preset);
// The same stable user-data identity preserves existing saves on this device.
const project=join(dest,'project.godot');let settings=await readFile(project,'utf8');settings=settings.replace('anti_aliasing/quality/msaa_3d=2','anti_aliasing/quality/msaa_3d=1').replace(/lights_and_shadows\/directional_shadow\/size=\d+/, 'lights_and_shadows/directional_shadow/size=1024').replace(/lights_and_shadows\/positional_shadow\/atlas_size=\d+/, 'lights_and_shadows/positional_shadow/atlas_size=1024');await writeFile(project,settings);
await writeFile(join(dest,'render_budget.gd'),await readFile('tools/native-render-budget.gd'));
const evidence=resolve('docs/evidence/performance-revision24');await mkdir(evidence,{recursive:true});await writeFile(join(evidence,world+'-mobile-assets.json'),JSON.stringify(report,null,2)+'\n');
console.log('MOBILE PREPARED',world,report.glbs.length,'embedded texture sets',report.images.length,'external maps');
