"""
Repair GraphML file with conflicting key definitions.

Problem: Phase 7 used d10/d11 for node metadata, but LightRAG reserves d0-d5 for nodes
and d6-d11 for edges. This caused NetworkX to try parsing string values as integers.

Solution: Remap d10→d12, d11→d13 for all node data elements, add proper key definitions.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

graphml_path = Path("./rag_storage/default/graph_chunk_entity_relation.graphml")

print("🔧 Repairing GraphML key conflicts...")

# Parse the file
tree = ET.parse(graphml_path)
root = tree.getroot()

ns = {'graphml': 'http://graphml.graphdrawing.org/xmlns'}
graphml_ns = 'http://graphml.graphdrawing.org/xmlns'

# Key remapping (old_key → new_key)
# d10 (metadata_weight) → d12
# d11 (metadata_importance) → d13
# d12 (metadata_subfactors) → d14
# d13 (metadata_page_limit) → d15
# d14 (metadata_format) → d16
# d15 (metadata_addressed_factors) → d17
# d16 (metadata_criticality) → d18
# d17 (metadata_modal_verb) → d19
# d18 (metadata_subject) → d20
key_remap = {
    'd10': 'd12',
    'd11': 'd13',
    'd12': 'd14',
    'd13': 'd15',
    'd14': 'd16',
    'd15': 'd17',
    'd16': 'd18',
    'd17': 'd19',
    'd18': 'd20',
}

# Remap data elements in nodes
nodes_remapped = 0
data_elements_remapped = 0

for node in root.findall('.//graphml:node', ns):
    for data in node.findall('.//graphml:data', ns):
        old_key = data.get('key')
        if old_key in key_remap:
            data.set('key', key_remap[old_key])
            data_elements_remapped += 1
    if any(d.get('key') in key_remap.values() for d in node.findall('.//graphml:data', ns)):
        nodes_remapped += 1

print(f"  ✅ Remapped {data_elements_remapped} data elements in {nodes_remapped} nodes")

# Remove old conflicting key definitions (d12-d18)
graph_elem = root.find('.//graphml:graph', ns)
keys_removed = []

for key_elem in root.findall('.//graphml:key', ns):
    key_id = key_elem.get('id')
    key_for = key_elem.get('for')
    # Remove old metadata key definitions that are now remapped
    if key_id in ['d12', 'd13', 'd14', 'd15', 'd16', 'd17', 'd18'] and key_for == 'node':
        root.remove(key_elem)
        keys_removed.append(key_id)

if keys_removed:
    print(f"  ✅ Removed old key definitions: {', '.join(keys_removed)}")

# Add new key definitions with correct IDs
new_keys = {
    'd12': ('metadata_weight', 'node', 'Evaluation factor weight (percentage or points)'),
    'd13': ('metadata_importance', 'node', 'Relative importance hierarchy'),
    'd14': ('metadata_subfactors', 'node', 'List of subfactors with weights'),
    'd15': ('metadata_page_limit', 'node', 'Page limit for submission'),
    'd16': ('metadata_format', 'node', 'Format requirements (font, margins, spacing)'),
    'd17': ('metadata_addressed_factors', 'node', 'Evaluation factors addressed by instruction'),
    'd18': ('metadata_criticality', 'node', 'Requirement criticality (MANDATORY/IMPORTANT/OPTIONAL)'),
    'd19': ('metadata_modal_verb', 'node', 'Modal verb used (shall/should/may)'),
    'd20': ('metadata_subject', 'node', 'Subject with obligation (Contractor/Offeror/Government)'),
}

keys_added = []
for key_id, (attr_name, for_type, description) in new_keys.items():
    # Check if key already exists
    existing = root.find(f'.//graphml:key[@id="{key_id}"][@for="{for_type}"]', ns)
    if existing is None:
        key_elem = ET.Element(f'{{{graphml_ns}}}key')
        key_elem.set('id', key_id)
        key_elem.set('for', for_type)
        key_elem.set('attr.name', attr_name)
        key_elem.set('attr.type', 'string')
        
        desc_elem = ET.SubElement(key_elem, f'{{{graphml_ns}}}desc')
        desc_elem.text = description
        
        # Insert before graph element
        root.insert(list(root).index(graph_elem), key_elem)
        keys_added.append(key_id)

if keys_added:
    print(f"  ✅ Added {len(keys_added)} new key definitions: {', '.join(keys_added)}")

# Save the repaired file
tree.write(graphml_path, encoding='utf-8', xml_declaration=True)

print(f"\n✅ GraphML file repaired: {graphml_path}")
print(f"   Nodes affected: {nodes_remapped}")
print(f"   Data elements remapped: {data_elements_remapped}")
print(f"   Keys added: {len(keys_added)}")
print(f"\n🔍 Verifying repair by loading with NetworkX...")

try:
    import networkx as nx
    G = nx.read_graphml(graphml_path)
    print(f"✅ SUCCESS! Graph loaded: {len(G.nodes())} nodes, {len(G.edges())} edges")
    
    # Check metadata attributes
    metadata_counts = {
        'metadata_weight': 0,
        'metadata_importance': 0,
        'metadata_subfactors': 0,
        'metadata_page_limit': 0,
        'metadata_criticality': 0,
    }
    
    for _, data in G.nodes(data=True):
        for key in metadata_counts:
            if key in data:
                metadata_counts[key] += 1
    
    print(f"\n📊 Metadata attribute counts:")
    for key, count in metadata_counts.items():
        if count > 0:
            print(f"   {key}: {count} nodes")
            
except Exception as e:
    print(f"❌ ERROR: {e}")
    print("   Graph file may still have issues")
