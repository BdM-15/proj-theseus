"""Check GraphML structure and propose LLM-powered post-processing"""
import xml.etree.ElementTree as ET
import json

# Parse GraphML
tree = ET.parse('rag_storage/graph_chunk_entity_relation.graphml')
root = tree.getroot()
ns = {'g': 'http://graphml.graphdrawing.org/xmlns'}

# Get nodes and edges
nodes = root.findall('.//g:node', ns)
edges = root.findall('.//g:edge', ns)

print(f"GraphML Structure:")
print(f"  Total nodes: {len(nodes)}")
print(f"  Total edges: {len(edges)}")

# Extract node details
node_data = []
for node in nodes[:10]:
    node_id = node.get('id')
    data_elements = node.findall('.//g:data', ns)
    data = {}
    for d in data_elements:
        key = d.get('key')
        data[key] = d.text
    node_data.append({'id': node_id, 'data': data})

print(f"\nFirst 10 nodes:")
for n in node_data:
    print(f"  {n['id']}")
    for k, v in list(n['data'].items())[:3]:
        print(f"    {k}: {v[:80] if v and len(str(v)) > 80 else v}")

# Find annex nodes
annex_nodes = []
section_nodes = []

for node in nodes:
    node_id = node.get('id')
    entity_type = None
    
    for d in node.findall('.//g:data', ns):
        if d.get('key') == 'entity_type':
            entity_type = d.text
            break
    
    if entity_type == 'ANNEX' or (node_id and ('J-' in node_id or 'Annex' in node_id or 'Attachment' in node_id)):
        annex_nodes.append(node_id)
    
    if entity_type == 'SECTION' or (node_id and 'Section' in node_id):
        section_nodes.append(node_id)

print(f"\n{'='*80}")
print(f"ANNEX & SECTION ANALYSIS")
print(f"{'='*80}")
print(f"Annex-like nodes found: {len(annex_nodes)}")
print(f"Section nodes found: {len(section_nodes)}")

print(f"\nFirst 20 annex nodes:")
for a in annex_nodes[:20]:
    print(f"  {a}")

print(f"\nSection nodes:")
for s in section_nodes[:10]:
    print(f"  {s}")

# Check edges for these nodes
annex_edges = []
for edge in edges:
    source = edge.get('source')
    target = edge.get('target')
    
    if source in annex_nodes or target in annex_nodes:
        annex_edges.append((source, target))

print(f"\nEdges involving annex nodes: {len(annex_edges)}")
if len(annex_edges) > 0:
    print(f"First 5 edges:")
    for src, tgt in annex_edges[:5]:
        print(f"  {src} → {tgt}")
else:
    print(f"  ❌ NO EDGES FOUND - Annexes are completely isolated!")

print(f"\n{'='*80}")
print(f"RECOMMENDATION: LLM-Powered Relationship Inference")
print(f"{'='*80}")
print(f"""
Instead of regex patterns, we should:

1. Load all {len(annex_nodes)} annex entities and {len(section_nodes)} section entities
2. Batch them into groups (e.g., 50 annexes + all sections per batch)
3. Ask Grok LLM:
   
   "You are analyzing a government RFP knowledge graph. Given these annex/attachment 
   entities and these section entities, determine which annexes belong to which sections
   based on:
   - Naming conventions (J-XXXXX belongs to Section J)
   - Content similarity
   - Logical document structure
   - Standard government contracting organization patterns
   
   Output JSON with relationships."

4. Benefits:
   - Agency-agnostic (handles ANY naming convention)
   - Understands context (not just prefix patterns)
   - Adapts to non-standard structures
   - Uses phase6_prompts.py as guidance
   - Leverages 2M context window effectively

5. Implementation:
   - Read from graph_chunk_entity_relation.graphml (has full entity details)
   - Use Grok for semantic understanding
   - Save relationships back to graphml + kv_store files
""")
