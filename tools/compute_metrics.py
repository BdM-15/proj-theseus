import json
from collections import Counter
from pathlib import Path

base = Path('rag_storage/default')
kv_entities_path = base / 'kv_store_full_entities.json'
kv_relations_path = base / 'kv_store_full_relations.json'
vdb_entities_path = base / 'vdb_entities.json'
vdb_relationships_path = base / 'vdb_relationships.json'

out = {}

# KV entities: sum counts and sample names
if kv_entities_path.exists():
    with open(kv_entities_path, 'r', encoding='utf-8') as f:
        kv = json.load(f)
    total = 0
    samples = []
    for doc, payload in kv.items():
        c = payload.get('count') or len(payload.get('entity_names', []))
        total += c
        for name in payload.get('entity_names', [])[:25]:
            samples.append({'doc': doc, 'name': name})
    out['kv_total_entities'] = total
    out['kv_doc_count'] = len(kv)
    out['kv_samples'] = samples[:25]
else:
    out['kv_total_entities'] = None

# Relations: count occurrence of lines that start a pair by scanning file
if kv_relations_path.exists():
    count = 0
    samples = []
    # We'll scan the file line by line and count lines that contain only '[' (optionally with spaces)
    with open(kv_relations_path, 'r', encoding='utf-8') as f:
        inside_pairs = False
        for line in f:
            # count lines that are an opening of a pair: line with only '[' or with '  ['
            s = line.strip()
            if s == '[':
                # this is an opening bracket for a pair or array; need to check context
                # lookahead is hard; instead, count occurrences of pattern '  [' with quotes on next line
                pass
            # count lines that start a pair: a line with '[' followed by next non-empty line with a quoted string
            # Simpler heuristic: count occurrences of '\n      [' inside the raw file
            # We'll do a raw read for this
            continue
    # fallback: raw bytes count
    try:
        data = kv_relations_path.read_bytes()
        # count occurrences of b"\n      [" which matches the opening bracket lines seen in the file
        pair_marker = b"\n      ["
        count = data.count(pair_marker)
        # Extract first 25 pairs by naive JSON load of the top-level object but only first doc to avoid memory
        with open(kv_relations_path, 'r', encoding='utf-8') as f:
            j = json.load(f)
            for doc, payload in j.items():
                pairs = payload.get('relation_pairs', [])
                for a,b in pairs[:25]:
                    samples.append({'doc': doc, 'a': a, 'b': b})
                break
        out['kv_total_relations_estimate'] = count
        out['kv_relation_samples'] = samples[:25]
    except Exception as e:
        out['kv_total_relations_estimate'] = None
        out['kv_relation_samples'] = []

# VDB entities: attempt to load and extract types
if vdb_entities_path.exists():
    try:
        with open(vdb_entities_path, 'r', encoding='utf-8') as f:
            vdb = json.load(f)
        entries = []
        if isinstance(vdb, dict):
            for k, v in vdb.items():
                if isinstance(v, dict):
                    entries.append(v)
                elif isinstance(v, list):
                    entries.extend(v)
        elif isinstance(vdb, list):
            entries = vdb
        type_counter = Counter()
        samples = []
        for e in entries:
            t = e.get('type') or e.get('entity_type') or e.get('label') or 'UNKNOWN'
            type_counter[t] += 1
            if len(samples) < 25:
                samples.append({'id': e.get('_id') or e.get('id') or None, 'type': t, 'name': e.get('name') or e.get('text')})
        out['vdb_entity_count'] = len(entries)
        out['vdb_top_types'] = type_counter.most_common(20)
        out['vdb_samples'] = samples
    except Exception as e:
        out['vdb_entity_count'] = None

# Try to load vdb_relationships.json and count entries; fallback to heuristic
if vdb_relationships_path.exists():
    try:
        with open(vdb_relationships_path, 'r', encoding='utf-8') as f:
            rels = json.load(f)
        if isinstance(rels, list):
            out['vdb_relationship_count'] = len(rels)
        elif isinstance(rels, dict):
            out['vdb_relationship_count'] = len(rels)
        else:
            out['vdb_relationship_count'] = None
    except Exception:
        try:
            b = vdb_relationships_path.read_bytes()
            est = b.count(b"\n  {")
            out['vdb_relationship_count_estimate'] = est
        except Exception:
            out['vdb_relationship_count_estimate'] = None

print(json.dumps(out, indent=2, ensure_ascii=False))
