"""Check for CHILD_OF relationships in VDB and show sample."""
import json

with open('rag_storage/swa_tas/vdb_relationships.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

rels = data.get('data', [])

# Find CHILD_OF in keywords
child_ofs = [r for r in rels if 'child' in r.get('keywords', '').lower()]

print(f"Total relationships in VDB: {len(rels)}")
print(f"CHILD_OF relationships (in keywords): {len(child_ofs)}")
print()

if child_ofs:
    print("Sample CHILD_OF relationships:")
    for r in child_ofs[:15]:
        src = r.get('src_id', 'N/A')[:50]
        tgt = r.get('tgt_id', 'N/A')[:50]
        kw = r.get('keywords', '')[:30]
        print(f"  {src}")
        print(f"    --[{kw}]--> {tgt}")
        print()
else:
    print("No CHILD_OF relationships found in keywords")
    print("\nChecking what keywords exist:")
    keyword_samples = set()
    for r in rels[:100]:
        kw = r.get('keywords', '')
        if kw:
            keyword_samples.add(kw[:50])
    for kw in list(keyword_samples)[:20]:
        print(f"  - {kw}")
