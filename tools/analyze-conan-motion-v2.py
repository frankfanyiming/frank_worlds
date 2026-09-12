"""Summarize real-controller capture without manufacturing animation poses."""
import json,math,sys
from pathlib import Path
p=Path(sys.argv[1]);r=json.loads(p.read_text());summary={'source':str(p.name),'engine':r['engine'],'controller':r['controller'],'checks':r['checks'],'phases':{},'feet':{},'material_textures':[m['texture'] for m in r['materials']]}
for phase in sorted({s['phase'] for s in r['samples']}):
 rows=[s for s in r['samples'] if s['phase']==phase];positions=[s['position'] for s in rows]
 distance=sum(math.hypot(b[0]-a[0],b[2]-a[2]) for a,b in zip(positions,positions[1:]));stable=rows[20:] or rows
 summary['phases'][phase]={'frames':len(rows),'distance_m':distance,'mean_stable_actual_speed':sum(s['actual_speed'] for s in stable)/len(stable),'grounded_fraction':sum(s['grounded'] for s in rows)/len(rows),'clips':sorted({s['animation'] for s in rows}),'mean_animation_rate':sum(s['animation_speed'] for s in stable)/len(stable)}
for phase,clip,duty in [('walk_forward','Walk',.60),('run_forward','Run',.44)]:
 rows=[s for s in r['samples'] if s['phase']==phase];duration=r['character_motion']['conan']['cycles'][clip]['seconds'];start=rows[0]['t'];result={}
 for side,offset in [('Left',0),('Right',.5)]:
  cycles={};cycle=0;last=None;clearances=[]
  for row in rows:
   ph=(row['animation_time']/duration+offset)%1
   if last is not None and ph<last-.5:cycle+=1
   last=ph
   if row['t']-start<.35 or row['animation']!=clip:continue
   f=row['feet'][side];clearances.append(f['sole_y']-row['position'][1])
   if .08<ph<duty-.08:cycles.setdefault(cycle,[]).append(f['center'])
  drift=[]
  for points in cycles.values():
   if len(points)<4:continue
   drift.append(max(math.hypot(a[0]-b[0],a[2]-b[2]) for a in points for b in points))
  result[side]={'max_observed_stance_drift_m':max(drift) if drift else None,'stance_segments':len(drift),'minimum_sole_relative_body_m':min(clearances),'maximum_lift_relative_body_m':max(clearances)}
  summary['checks'].append({'check':clip+'_'+side+'_foot_contact','passed':bool(drift) and max(drift)<.004 and min(clearances)>-.003,'drift_m':max(drift) if drift else None,'minimum_relative_sole_m':min(clearances)})
 summary['feet'][clip]=result
out=p.with_name('conan-motion-v2-summary.json');out.write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False,indent=2));sys.exit(0 if all(c['passed'] for c in summary['checks']) else 1)
