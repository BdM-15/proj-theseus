import json, re
from pathlib import Path
obj=json.loads(Path('.cursor/q_scope_query_data_with_chunks.json').read_text(encoding='utf-8'))
chunks=obj.get('data',{}).get('chunks',[])

def count(pat):
    r=re.compile(pat,re.I)
    return sum(1 for c in chunks if r.search(c.get('content','') or ''))

for pat in [r'\bG\.1\.', r'\bH\.1\.', r'\bI\.1\.', r'\bJ\.1\.', r'\bK\.1\.', r'\bL\.1\.']:
    print(pat, count(pat))

# show first hit for G.1
r=re.compile(r'\bG\.1\.',re.I)
for c in chunks:
    txt=c.get('content','') or ''
    if r.search(txt):
        snip=re.sub(r'\s+',' ',txt)[:320]
        print('HIT',c.get('file_path'),c.get('reference_id'),snip)
        break
