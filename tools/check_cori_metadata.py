import urllib.request,json
url='https://huggingface.co/api/models/rhasspy/piper-voices/tree/main/en/en_GB/cori/high?expand=true'
with urllib.request.urlopen(url,timeout=35) as response:value=json.load(response)
from pathlib import Path
Path('release/evidence/cori-upstream-tree.json').write_text(json.dumps({'source':url,'retrieved':'2026-10-18','files':value},indent=2),encoding='utf-8')
for item in value:print(json.dumps({k:item[k] for k in ('path','oid','lfs') if k in item}))
