"""
Fresh Extraction Assessment - Post Output Prompt Removal
Analyzes entity extraction quality after deleting output prompts
"""
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter, defaultdict

# Parse GraphML
graphml_path = Path("rag_storage/default/graph_chunk_entity_relation.graphml")
tree = ET.parse(graphml_path)
root = tree.getroot()

# XML namespace
ns = {'ns0': 'http://graphml.graphdrawing.org/xmlns'}

print("\n" + "="*80)
print("FRESH EXTRACTION ASSESSMENT - Post Output Prompt Removal")
print("="*80)

# Track entity types
entity_counts = Counter()
total_entities = 0

# Count all entities
for node in root.findall('.//ns0:node', ns):
    entity_type = None
    for data in node.findall('ns0:data', ns):
        if data.get('key') == 'd1':  # entity_type
            entity_type = data.text
            break
    if entity_type:
        entity_counts[entity_type] += 1
        total_entities += 1

# Count relationships
total_relationships = 0
phase6_patterns = {
    'EVALUATED_BY': 0,
    'GUIDES': 0,
    'ATTACHMENT_OF': 0,
    'CHILD_OF': 0,
    'PARENT_CLAUSE': 0
}

for edge in root.findall('.//ns0:edge', ns):
    total_relationships += 1
    # Check description for Phase 6 relationship types
    for data in edge.findall('ns0:data', ns):
        if data.get('key') == 'd7' and data.text:  # description field
            desc = data.text.lower()
            for pattern in phase6_patterns.keys():
                if pattern.lower() in desc:
                    phase6_patterns[pattern] += 1

print(f"\n📊 ENTITY EXTRACTION SUMMARY")
print(f"Total Entities: {total_entities:,}")
print(f"\nEntity Type Distribution (Top 15):")
for entity_type, count in entity_counts.most_common(15):
    print(f"  {entity_type:30s}: {count:4,}")

print(f"\n🔗 RELATIONSHIP SUMMARY")
print(f"Total Relationships: {total_relationships:,}")

print(f"\n📈 PHASE 6 INFERENCE (Semantic Relationships):")
for rel_type, count in phase6_patterns.items():
    status = "✅" if count > 0 else "❌"
    print(f"  {status} {rel_type:20s}: {count:4,} occurrences")

print(f"\n🎯 CRITICAL ENTITY TYPES (Government Contracting Specific):")
critical_types = [
    'evaluation_factor',
    'submission_instruction', 
    'requirement',
    'clause',
    'deliverable',
    'statement_of_work'
]

for entity_type in critical_types:
    count = entity_counts.get(entity_type, 0)
    status = "✅" if count > 0 else "❌"
    print(f"  {status} {entity_type:30s}: {count:4,}")

print(f"\n📋 COMPARISON TO BASELINE:")
print(f"  Previous extraction: 4,394 entities, 5,248 relationships")
print(f"  Current extraction:  {total_entities:,} entities, {total_relationships:,} relationships")

if total_entities < 4000:
    print(f"  ⚠️  WARNING: Entity count lower than baseline")
elif total_entities > 5000:
    print(f"  ✅ IMPROVEMENT: More entities extracted")
else:
    print(f"  ✅ SIMILAR: Entity count comparable to baseline")

print(f"\n🔍 NEXT STEP: Test query to validate strategic reasoning depth")
print(f"  Query: 'Based on proposal instructions, provide outline addressing pain points'")
print(f"  Expected: Strategic language ('to gain favor', 'earning Outstanding rating')")

print("\n" + "="*80)
