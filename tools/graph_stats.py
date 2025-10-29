import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

class UnionFind:
    def __init__(self):
        self.parent = {}
        self.rank = {}

    def find(self, x):
        if self.parent.get(x, x) != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent.get(x, x)

    def union(self, a, b):
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return
        if self.rank.get(ra,0) < self.rank.get(rb,0):
            self.parent[ra] = rb
        else:
            self.parent[rb] = ra
            if self.rank.get(ra,0) == self.rank.get(rb,0):
                self.rank[ra] = self.rank.get(ra,0) + 1


base = Path('rag_storage/default')
graphml = base / 'graph_chunk_entity_relation.graphml'
if not graphml.exists():
    print('{"error": "graphml file not found", "path": "%s"}' % str(graphml))
    raise SystemExit(1)

# streaming parse
context = ET.iterparse(str(graphml), events=("start", "end"))
# skip root
_, root = next(context)

node_labels = {}
node_types = Counter()
degree = Counter()
uf = UnionFind()
edge_count = 0

for event, elem in context:
    if event == 'end' and elem.tag.endswith('}node') or (event == 'end' and elem.tag == 'node'):
        nid = elem.attrib.get('id')
        label = None
        ntype = None
        for data in elem.findall('.//'):
            # look for 'data' elements
            if data.tag.endswith('}data') or data.tag == 'data':
                key = data.attrib.get('key')
                text = (data.text or '').strip()
                # heuristics
                if key and ('label' in key.lower() or 'name' in key.lower() or 'text' in key.lower()):
                    if not label and text:
                        label = text
                if key and ('type' in key.lower() or 'entity' in key.lower() or 'class' in key.lower()):
                    if not ntype and text:
                        ntype = text
        node_labels[nid] = label
        if ntype:
            node_types[ntype]+=1
        elem.clear()
    elif event == 'end' and elem.tag.endswith('}edge') or (event == 'end' and elem.tag == 'edge'):
        src = elem.attrib.get('source')
        tgt = elem.attrib.get('target')
        if src is None or tgt is None:
            continue
        edge_count += 1
        degree[src] += 1
        degree[tgt] += 1
        uf.parent.setdefault(src, src)
        uf.parent.setdefault(tgt, tgt)
        uf.union(src, tgt)
        elem.clear()

# compute connected components sizes
comp_counter = Counter()
for n in uf.parent.keys():
    r = uf.find(n)
    comp_counter[r]+=1

# collect top stats
top_degrees = degree.most_common(20)
# map node ids to labels for top list
top_entities = []
for nid, deg in top_degrees:
    top_entities.append({'id': nid, 'label': node_labels.get(nid), 'degree': deg})

out = {
    'node_count': len(node_labels),
    'edge_count': edge_count,
    'unique_nodes_with_degree': len(degree),
    'avg_degree': sum(degree.values())/len(degree) if degree else 0,
    'connected_components': len(comp_counter),
    'largest_component_size': comp_counter.most_common(1)[0][1] if comp_counter else 0,
    'top_entities_by_degree': top_entities,
    'node_type_counts_top20': node_types.most_common(20),
}
import json
print(json.dumps(out, indent=2, ensure_ascii=False))
