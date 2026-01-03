"""
Diagnose why ADAB services and workload data aren't retrieved together.
Check entities, relationships, and chunk associations.
"""
import json
import os

def main():
    vdb_path = "rag_storage/swa_tas/vdb_entities.json"
    rel_path = "rag_storage/swa_tas/vdb_relationships.json"
    
    # Load entities
    with open(vdb_path, 'r', encoding='utf-8') as f:
        entities_data = json.load(f)
    
    entities = entities_data.get('data', [])
    
    print("=" * 70)
    print("ADAB-RELATED ENTITIES")
    print("=" * 70)
    
    adab_entities = []
    appendix_h_entities = []
    workload_entities = []
    
    for e in entities:
        name = e.get('entity_name', '').lower()
        content = e.get('content', '').lower()
        entity_type = e.get('entity_type', 'unknown')
        
        # Find ADAB related
        if 'adab' in name or 'al dhafra' in name.lower():
            adab_entities.append(e)
        # Find Appendix H related
        elif 'appendix h' in name or 'h.1' in name or 'h.2' in name:
            appendix_h_entities.append(e)
        # Find workload/forecast related
        elif any(term in name for term in ['workload', 'forecast', 'operations', 'aircraft']):
            workload_entities.append(e)
    
    print(f"\n[ADAB] Entities with ADAB in name: {len(adab_entities)}")
    for e in adab_entities[:10]:
        print(f"   - {e.get('entity_name', 'N/A')[:60]} [{e.get('entity_type', '?')}]")
    
    print(f"\n[APPENDIX H] Entities with Appendix H / H.x in name: {len(appendix_h_entities)}")
    for e in appendix_h_entities[:15]:
        print(f"   - {e.get('entity_name', 'N/A')[:60]} [{e.get('entity_type', '?')}]")
    
    print(f"\n[WORKLOAD] Entities with workload/forecast/operations in name: {len(workload_entities)}")
    for e in workload_entities[:15]:
        print(f"   - {e.get('entity_name', 'N/A')[:60]} [{e.get('entity_type', '?')}]")
    
    # Load relationships
    print("\n" + "=" * 70)
    print("RELATIONSHIPS CONNECTING ADAB/APPENDIX H ENTITIES")
    print("=" * 70)
    
    with open(rel_path, 'r', encoding='utf-8') as f:
        rel_data = json.load(f)
    
    relationships = rel_data.get('data', [])
    
    adab_rels = []
    for r in relationships:
        src = r.get('src_id', '').lower()
        tgt = r.get('tgt_id', '').lower()
        keywords = r.get('keywords', '').lower()
        
        if any(term in src or term in tgt for term in ['adab', 'appendix h', 'h.1', 'h.2', 'al dhafra']):
            adab_rels.append(r)
    
    print(f"\n[RELS] Relationships involving ADAB/Appendix H: {len(adab_rels)}")
    for r in adab_rels[:20]:
        src = r.get('src_id', 'N/A')[:30]
        tgt = r.get('tgt_id', 'N/A')[:30]
        kw = r.get('keywords', 'N/A')[:20]
        print(f"   {src} --[{kw}]--> {tgt}")
    
    # Check for CHILD_OF relationships specifically
    print("\n" + "=" * 70)
    print("CHILD_OF RELATIONSHIPS (Hierarchical Structure)")
    print("=" * 70)
    
    child_of_rels = [r for r in relationships if 'child' in r.get('keywords', '').lower()]
    print(f"\nTotal CHILD_OF relationships: {len(child_of_rels)}")
    
    adab_child_rels = [r for r in child_of_rels 
                       if any(term in r.get('src_id', '').lower() or term in r.get('tgt_id', '').lower() 
                              for term in ['adab', 'appendix h', 'h.1', 'h.2'])]
    
    print(f"CHILD_OF involving ADAB/Appendix H: {len(adab_child_rels)}")
    for r in adab_child_rels[:15]:
        src = r.get('src_id', 'N/A')[:40]
        tgt = r.get('tgt_id', 'N/A')[:40]
        print(f"   {src} --[CHILD_OF]--> {tgt}")

if __name__ == "__main__":
    main()
