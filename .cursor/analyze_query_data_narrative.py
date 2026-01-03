import json
import re
from pathlib import Path

p = Path(".cursor/tmp_query_data.json")
obj = json.loads(p.read_text(encoding="utf-8"))
chunks = obj.get("data", {}).get("chunks", [])

# Filter to real text chunks (exclude multimodal table analysis wrappers)
def is_table_analysis(text: str) -> bool:
    return text.strip().startswith("Table Analysis:")

def norm_snip(text: str, n: int = 320) -> str:
    return re.sub(r"\s+", " ", text).strip()[:n]

narr_terms = re.compile(r"\bscope\b|\bpurpose\b|\bgeneral\b|\boverview\b|\bdescription\b|\bapplicab|\bcontractor\s+shall\b|\bperformance work statement\b|\bthis\s+pws\b", re.I)
po_terms = re.compile(r"\bPO-\d\b|\bperformance objective\b|\bF\.1\.(3|4|5|6)\b", re.I)

cands = []
for c in chunks:
    txt = c.get("content", "") or ""
    if is_table_analysis(txt):
        continue
    fp = c.get("file_path", "") or ""
    # Prefer PWS PDF narrative
    score = 0
    if "Attachment 1" in fp and fp.lower().endswith(".pdf"):
        score += 2
    if narr_terms.search(txt):
        score += 2
    # De-prioritize PO-heavy chunks for this analysis
    if po_terms.search(txt):
        score -= 1
    if score >= 3:
        cands.append((score, fp, c.get("reference_id"), c.get("chunk_id"), norm_snip(txt)))

cands.sort(key=lambda t: (-t[0], t[1] or ""))

out = [
    f"candidate_narrative_chunks={len(cands)}",
    "",
]
for score, fp, ref, chunk_id, snip in cands[:12]:
    out.append(f"score={score} file={fp} ref={ref} chunk={chunk_id}")
    out.append(snip)
    out.append("")

Path(".cursor/query_data_narrative_candidates.txt").write_text("\n".join(out), encoding="utf-8")
print("wrote .cursor/query_data_narrative_candidates.txt")
