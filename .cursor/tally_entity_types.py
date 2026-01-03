import json
import collections
from pathlib import Path

def analyze(path: str, label: str):
    obj = json.loads(Path(path).read_text(encoding="utf-8"))
    d = obj.get("data", {})
    ents = d.get("entities", [])
    rels = d.get("relationships", [])
    chunks = d.get("chunks", [])

    etypes = [e.get("entity_type") for e in ents if e.get("entity_type")]
    counts = collections.Counter(etypes)

    pm = counts.get("performance_metric", 0)
    total = len(etypes)
    pm_pct = (pm / total * 100.0) if total else 0.0

    print("\n===", label, "===")
    print("entities", len(ents), "relationships", len(rels), "chunks", len(chunks))
    print(f"performance_metric: {pm}/{total} ({pm_pct:.1f}%)")
    print("top_entity_types:")
    for t, n in counts.most_common(10):
        print(f"  {n:4d}  {t}")

analyze('.cursor/q_scope_query_data.json', 'Query A: scope + requirements')
analyze('.cursor/q_service_query_data.json', 'Query B: service areas + success')
