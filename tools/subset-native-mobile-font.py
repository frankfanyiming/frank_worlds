"""Subset only an isolated mobile runtime font; preserve all project UI glyphs."""
from pathlib import Path
import sys,json,hashlib
from fontTools import subset
from fontTools.ttLib import TTFont
project=Path(sys.argv[1]).resolve()
if 'native-mobile24' not in str(project):raise SystemExit('Use an isolated native-mobile24 project')
font_path=project/'ui-font.otf';original=font_path.read_bytes()
text=''.join(chr(n) for n in range(32,256))+'←↑→↓↗↘↙↖…·◉↔×☰☀☾♧♥✓'
for path in project.rglob('*'):
 if path.suffix in ['.gd','.json','.tscn','.tres'] and '.godot' not in path.parts:text+=path.read_text(errors='replace')
font=TTFont(font_path);options=subset.Options();options.recommended_glyphs=True;options.notdef_outline=True
sub=subset.Subsetter(options=options);sub.populate(text=text);sub.subset(font)
font.save(font_path)
report={'before':len(original),'after':font_path.stat().st_size,'requestedCharacters':len(set(text)),'originalSha256':hashlib.sha256(original).hexdigest(),'sha256':hashlib.sha256(font_path.read_bytes()).hexdigest()}
(project/'mobile-font-report.json').write_text(json.dumps(report,indent=2)+'\n');print(project.name,report)
