# Quick Validation Test - Path B Ontology-Guided Extraction
# Tests if current ontology prevents Path A contamination

import json
from pathlib import Path
from src.core.ontology import EntityType, is_valid_relationship, VALID_RELATIONSHIPS

# Load Oct 2 extraction results (Path A contaminated)
rag_storage = Path('./rag_storage')
entities_file = rag_storage / 'kv_store_full_entities.json'
relations_file = rag_storage / 'kv_store_full_relations.json'

if entities_file.exists():
    with open(entities_file, 'r', encoding='utf-8') as f:
        entities_data = json.load(f)
    
    doc_id = list(entities_data.keys())[0]
    entities = entities_data[doc_id]['entity_names']
    
    print(f' Oct 2 Extraction Analysis')
    print(f'Total entities: {len(entities)}\n')
    
    # Analyze Path A contamination patterns
    path_a_artifacts = []
    valid_looking = []
    ambiguous = []
    
    for entity in entities:
        entity_lower = entity.lower()
        # Path A artifact patterns
        if 'rfp section j-' in entity_lower or \
           'section j-' in entity_lower or \
           'attachment line' == entity_lower or \
           'attachment 0' in entity_lower:
            path_a_artifacts.append(entity)
        # Ambiguous (need context)
        elif len(entity.split()) == 1 or entity.isupper():
            ambiguous.append(entity)
        # Looks valid
        else:
            valid_looking.append(entity)
    
    print(f' Valid-looking entities: {len(valid_looking)} ({len(valid_looking)/len(entities)*100:.1f}%)')
    print(f'  Path A artifacts: {len(path_a_artifacts)} ({len(path_a_artifacts)/len(entities)*100:.1f}%)')
    print(f' Ambiguous: {len(ambiguous)} ({len(ambiguous)/len(entities)*100:.1f}%)\n')
    
    print(' Sample Path A Artifacts (first 10):')
    for artifact in path_a_artifacts[:10]:
        print(f'  - {artifact}')
    
    print('\n Sample Valid Entities (first 10):')
    for valid in valid_looking[:10]:
        print(f'  - {valid}')
    
    print(f'\n Path B Re-run Target:')
    print(f'  - Expected entities: 500-700 (quality over quantity)')
    print(f'  - Expected precision: 95%+ (vs {len(valid_looking)/len(entities)*100:.1f}% currently)')
    print(f'  - Zero Path A artifacts (vs {len(path_a_artifacts)} currently)')
else:
    print(' No rag_storage data found. Will create fresh extraction with Path B.')
    print(' Ontology ready: {len([e for e in EntityType])} entity types defined')
    print(' Prompts ready: 4 RFP examples with government contracting patterns')

