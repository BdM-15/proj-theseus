"""Quick inspection: what L↔M edges does the post-processing actually produce?"""
import json, sys
from collections import Counter
ws = sys.argv[1] if len(sys.argv) > 1 else "afcap6_drfp"
e = json.load(open(f"rag_storage/{ws}/vdb_entities.json", encoding="utf-8"))["data"]
d = json.load(open(f"rag_storage/{ws}/vdb_relationships.json", encoding="utf-8"))["data"]
t = {(x.get("entity_name") or x.get("entity_id")): (x.get("entity_type") or "").lower() for x in e}
print(f"=== {ws} ===")
print(f"proposal_instruction: {sum(1 for v in t.values() if v=='proposal_instruction')}")
print(f"evaluation_factor:    {sum(1 for v in t.values() if v=='evaluation_factor')}")
print(f"subfactor:            {sum(1 for v in t.values() if v=='subfactor')}")
print(f"deliverable:          {sum(1 for v in t.values() if v=='deliverable')}")
fwd, rev = Counter(), Counter()
for r in d:
    s, tg = r.get("src_id"), r.get("tgt_id")
    st, tt = t.get(s, "?"), t.get(tg, "?")
    kw = (r.get("keywords") or r.get("relationship_type") or "").upper()
    if st == "proposal_instruction" and tt in ("evaluation_factor", "subfactor"):
        fwd[kw] += 1
    if tt == "proposal_instruction" and st in ("evaluation_factor", "subfactor"):
        rev[kw] += 1
print("instruction → factor edges:", dict(fwd))
print("factor → instruction edges:", dict(rev))
# Also: deliverable→factor and instruction→deliverable
ifd, dff = Counter(), Counter()
for r in d:
    s, tg = r.get("src_id"), r.get("tgt_id")
    st, tt = t.get(s, "?"), t.get(tg, "?")
    kw = (r.get("keywords") or "").upper()
    if st == "proposal_instruction" and tt == "deliverable":
        ifd[kw] += 1
    if st == "deliverable" and tt in ("evaluation_factor", "subfactor"):
        dff[kw] += 1
print("instruction → deliverable:", dict(ifd))
print("deliverable → factor:     ", dict(dff))
