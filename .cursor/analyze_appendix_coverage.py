import json
import re
from pathlib import Path

obj = json.loads(Path('.cursor/q_scope_query_data_with_chunks.json').read_text(encoding='utf-8'))
chunks = obj.get('data', {}).get('chunks', [])

def count(pat):
    r = re.compile(pat, re.I)
    return sum(1 for c in chunks if r.search(c.get('content','') or ''))

print('chunks', len(chunks))
for pat in [r'Appendix\s+G', r'Appendix\s+H', r'Appendix\s+I', r'Appendix\s+J', r'Appendix\s+K', r'Appendix\s+L', r'\bAUAB\b', r'\bADAB\b', r'\bAASAB\b', r'\bMSAB\b', r'\bPSAB\b', r'\bAJAB\b']:
    print(pat, count(pat))

# show up to 2 snippets per appendix term
for pat in [r'Appendix\s+G', r'Appendix\s+H', r'Appendix\s+I', r'Appendix\s+J', r'Appendix\s+K', r'Appendix\s+L']:
    r = re.compile(pat, re.I)
    hits=[]
    for c in chunks:
        txt=c.get('content','') or ''
        if r.search(txt):
            snip=re.sub(r'\s+',' ',txt).strip()[:280]
            hits.append((c.get('file_path'), c.get('reference_id'), snip))
    print('\n', pat, 'examples', len(hits))
    for fp, ref, snip in hits[:2]:
        print(' -', fp, 'ref', ref, snip)
