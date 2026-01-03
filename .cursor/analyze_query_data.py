import json
import re
import collections
from pathlib import Path

p = Path(".cursor/tmp_query_data.json")
obj = json.loads(p.read_text(encoding="utf-8"))
d = obj.get("data", {})
chunks = d.get("chunks", [])
entities = d.get("entities", [])
relationships = d.get("relationships", [])

print("entities", len(entities), "relationships", len(relationships), "chunks", len(chunks))

fp_counts = collections.Counter(c.get("file_path", "") for c in chunks)
print("top_files")
for fp, n in fp_counts.most_common(8):
    print(" ", n, fp)

def count_pat(pat: str) -> int:
    r = re.compile(pat, re.IGNORECASE)
    return sum(1 for c in chunks if r.search(c.get("content", "") or ""))

print("chunks_with_F.1.3", count_pat(r"\bF\.1\.3\b"))
print("chunks_with_F.1.4", count_pat(r"\bF\.1\.4\b"))
print("chunks_with_F.1.5", count_pat(r"\bF\.1\.5\b"))
print("chunks_with_F.1.6", count_pat(r"\bF\.1\.6\b"))
print("chunks_with_PWS_1.x", count_pat(r"\b1\.0\b|\b1\.1\b|\b1\.2\b"))
print("chunks_with_scope", count_pat(r"\bscope\b"))

want = re.compile(r"\b1\.0\b|\b1\.1\b|\b1\.2\b|\bscope\b|\bpws\b\s*(section|paragraph)\s*1", re.IGNORECASE)
found = [c for c in chunks if want.search(c.get("content", "") or "")]
print("narrative_like_chunks", len(found))

for c in found[:5]:
    snip = re.sub(r"\s+", " ", c.get("content", "") or "")[:260]
    print("---")
    print("file:", c.get("file_path"))
    print("ref:", c.get("reference_id"), "chunk:", c.get("chunk_id"))
    print("snip:", snip)
