/** Only these versioned models are shipped and requested by the game. */
export const MODEL_PARTS: string[] = ['world-v11','neighborhood-v21','nobi-home-v27','bedroom-v12','vegetation-v3-lite','terrain-v6','streets-v7-lite','surface-v11-lite','details/house-v11','details/connector-v9-lite',...['terrain','river-bridge','trees-west','trees-east','groundcover'].map(id=>'expansion/expansion-'+id+(id==='groundcover'?'-lite':'')),...['nobita','doraemon','shizuka','gian','suneo','tamako','nobisuke'].map(id=>'actors/'+id+(id==='doraemon'?'-v11':'')),'fauna/cat','fauna/sparrow','fauna/sparrow_ash','vehicles/kei_hatchback-v11','vehicles/kei_truck-v11','gadgets/bamboo','gadgets/door','gadgets/drawer','gadgets/time-machine','gadgets/season-extras'];
export const BEDROOM_PART='bedroom-v12';
export const WORLD_DATA_FILE='world-v27.json';
export const NOBI_ASSET_VERSION='20260913-nobi27';
export const STARTUP_PARTS=MODEL_PARTS.filter(part=>part!==BEDROOM_PART);
// Bump only when asset bytes change; app-only releases reuse the same cache.
export const ASSET_VERSION='20260910-12';
// Mobile derivatives keep the source scene hierarchy, doors, UVs and coordinates.
export const MOBILE_ASSET_VERSION='20260913-mobile23';
export const MOBILE_MODEL_PARTS=new Set(MODEL_PARTS.filter(p=>!p.startsWith('actors/')&&!p.startsWith('fauna/')&&!p.startsWith('vehicles/')&&!p.startsWith('gadgets/')));
export const MOBILE_ACTOR_VERSION='20260913-mobile24';
export const MOBILE_ACTOR_PARTS=new Set(MODEL_PARTS.filter(p=>p.startsWith('actors/')||p.startsWith('fauna/')||p.startsWith('vehicles/')));
export const SHIPPED_MODEL_PARTS=[...MODEL_PARTS,...[...MOBILE_MODEL_PARTS].map(p=>(p==='nobi-home-v27'?'mobile-v27/':'mobile-v23/')+p),...[...MOBILE_ACTOR_PARTS].map(p=>'mobile-v24/'+p)];
export function modelFile(part:string,mobile=false){return mobile&&part==='nobi-home-v27'?'mobile-v27/'+part:mobile&&MOBILE_ACTOR_PARTS.has(part)?'mobile-v24/'+part:mobile&&MOBILE_MODEL_PARTS.has(part)?'mobile-v23/'+part:part;}
export function modelVersion(part:string,mobile=false){return part==='nobi-home-v27'?NOBI_ASSET_VERSION:mobile&&MOBILE_ACTOR_PARTS.has(part)?MOBILE_ACTOR_VERSION:mobile&&MOBILE_MODEL_PARTS.has(part)?MOBILE_ASSET_VERSION:ASSET_VERSION;}
