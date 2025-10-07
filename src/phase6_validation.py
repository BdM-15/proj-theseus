"""
Phase 6 Validation Script

Quick validation checks for Phase 6 implementation results.
Run after processing a document to measure success metrics.

Usage:
    python src/phase6_validation.py

Outputs:
    - Entity counts (total, by type)
    - Relationship counts (total, by type)
    - L↔M relationship count (target: ≥5)
    - Annex linkage percentage (target: 100%)
    - Clause clustering percentage
    - Comparison to baseline (if baseline data available)
"""

import json
from pathlib import Path
from collections import Counter
import sys


def load_knowledge_graph(rag_storage_path: str = "./rag_storage"):
    """Load entities and relationships from knowledge graph."""
    entities_path = Path(rag_storage_path) / "kv_store_full_entities.json"
    relations_path = Path(rag_storage_path) / "kv_store_full_relations.json"
    
    if not entities_path.exists():
        print(f"❌ Knowledge graph not found in {rag_storage_path}")
        print(f"   Please process a document first using /insert_multimodal endpoint")
        sys.exit(1)
    
    with open(entities_path, 'r', encoding='utf-8') as f:
        entities = json.load(f)
    
    with open(relations_path, 'r', encoding='utf-8') as f:
        relationships = json.load(f)
    
    return entities, relationships


def analyze_entities(entities: dict):
    """Analyze entity types and counts."""
    print("\n" + "=" * 80)
    print("📊 ENTITY ANALYSIS")
    print("=" * 80)
    
    # Count by type
    entity_types = []
    for entity in entities.values():
        if isinstance(entity, dict):
            entity_types.append(entity.get('entity_type', 'UNKNOWN'))
    
    type_counts = Counter(entity_types)
    
    print(f"\n  Total Entities: {len(entity_types)}")
    print(f"\n  By Type:")
    for entity_type, count in sorted(type_counts.items()):
        print(f"    {entity_type:30s}: {count:4d}")
    
    # Check for Phase 6 new types
    phase6_types = ['SUBMISSION_INSTRUCTION', 'STRATEGIC_THEME', 'ANNEX', 'STATEMENT_OF_WORK']
    print(f"\n  Phase 6 New Entity Types:")
    for entity_type in phase6_types:
        count = type_counts.get(entity_type, 0)
        status = "✅" if count > 0 else "❌"
        print(f"    {status} {entity_type:30s}: {count:4d}")
    
    return type_counts


def analyze_relationships(relationships: dict, entities: dict):
    """Analyze relationship types and counts."""
    print("\n" + "=" * 80)
    print("🔗 RELATIONSHIP ANALYSIS")
    print("=" * 80)
    
    # Count by type
    rel_types = []
    phase6_rels = []
    
    for rel in relationships.values():
        if isinstance(rel, dict):
            rel_type = rel.get('relationship_type', 'UNKNOWN')
            rel_types.append(rel_type)
            
            # Check if Phase 6 post-processing relationship
            if rel.get('source') == 'phase6_post_processing':
                phase6_rels.append(rel)
    
    type_counts = Counter(rel_types)
    
    print(f"\n  Total Relationships: {len(rel_types)}")
    print(f"\n  By Type:")
    for rel_type, count in sorted(type_counts.items()):
        print(f"    {rel_type:30s}: {count:4d}")
    
    # Phase 6 relationships
    print(f"\n  Phase 6 Post-Processing Relationships: {len(phase6_rels)}")
    
    # L↔M relationships (SUBMISSION_INSTRUCTION → GUIDES → EVALUATION_FACTOR)
    lm_rels = [r for r in relationships.values() if isinstance(r, dict) and r.get('relationship_type') == 'GUIDES']
    print(f"\n  L↔M Relationships (GUIDES): {len(lm_rels)}")
    if len(lm_rels) >= 5:
        print(f"    ✅ Target achieved (≥5)")
    else:
        print(f"    ❌ Below target ({len(lm_rels)} < 5)")
    
    return type_counts, len(phase6_rels), len(lm_rels)


def analyze_linkage(entities: dict, relationships: dict):
    """Analyze annex linkage and clause clustering."""
    print("\n" + "=" * 80)
    print("🔗 LINKAGE ANALYSIS")
    print("=" * 80)
    
    # Get annexes and clauses
    annexes = [e for e in entities.values() if isinstance(e, dict) and e.get('entity_type') == 'ANNEX']
    clauses = [e for e in entities.values() if isinstance(e, dict) and e.get('entity_type') == 'CLAUSE']
    
    # Count CHILD_OF relationships
    child_of_rels = {}
    for rel in relationships.values():
        if isinstance(rel, dict) and rel.get('relationship_type') == 'CHILD_OF':
            src_id = rel.get('src_id')
            if src_id:
                child_of_rels[src_id] = rel
    
    # Annex linkage
    annexes_linked = sum(1 for annex in annexes if annex.get('entity_name') in child_of_rels)
    annex_linkage_pct = (annexes_linked / len(annexes) * 100) if annexes else 0
    
    print(f"\n  Annex Linkage:")
    print(f"    Total annexes: {len(annexes)}")
    print(f"    Linked to parent: {annexes_linked}")
    print(f"    Linkage rate: {annex_linkage_pct:.1f}%")
    if annex_linkage_pct == 100:
        print(f"    ✅ Target achieved (100%)")
    else:
        print(f"    🔨 Below target ({annex_linkage_pct:.1f}% < 100%)")
    
    # Clause clustering
    clauses_linked = sum(1 for clause in clauses if clause.get('entity_name') in child_of_rels)
    clause_clustering_pct = (clauses_linked / len(clauses) * 100) if clauses else 0
    
    print(f"\n  Clause Clustering:")
    print(f"    Total clauses: {len(clauses)}")
    print(f"    Linked to parent: {clauses_linked}")
    print(f"    Clustering rate: {clause_clustering_pct:.1f}%")
    if clause_clustering_pct > 80:
        print(f"    ✅ Good clustering rate")
    else:
        print(f"    🔨 Could improve ({clause_clustering_pct:.1f}%)")
    
    return annex_linkage_pct, clause_clustering_pct


def compare_baseline(entity_count: int, rel_count: int, lm_count: int):
    """Compare results to Navy MBOS baseline."""
    print("\n" + "=" * 80)
    print("📈 BASELINE COMPARISON")
    print("=" * 80)
    
    baseline_entities = 594
    baseline_rels = 584
    baseline_lm = 0
    
    entity_increase = ((entity_count - baseline_entities) / baseline_entities * 100) if baseline_entities else 0
    rel_increase = ((rel_count - baseline_rels) / baseline_rels * 100) if baseline_rels else 0
    
    print(f"\n  Entities:")
    print(f"    Baseline: {baseline_entities}")
    print(f"    Phase 6:  {entity_count}")
    print(f"    Change:   {entity_increase:+.1f}%")
    if entity_increase >= 10:
        print(f"    ✅ Target achieved (+10%)")
    else:
        print(f"    🔨 Below target ({entity_increase:+.1f}% < +10%)")
    
    print(f"\n  Relationships:")
    print(f"    Baseline: {baseline_rels}")
    print(f"    Phase 6:  {rel_count}")
    print(f"    Change:   {rel_increase:+.1f}%")
    if rel_increase >= 30:
        print(f"    ✅ Target achieved (+30%)")
    else:
        print(f"    🔨 Below target ({rel_increase:+.1f}% < +30%)")
    
    print(f"\n  L↔M Relationships:")
    print(f"    Baseline: {baseline_lm}")
    print(f"    Phase 6:  {lm_count}")
    if lm_count >= 5:
        print(f"    ✅ Target achieved (≥5)")
    else:
        print(f"    ❌ Below target ({lm_count} < 5)")


def generate_summary(entity_count: int, rel_count: int, phase6_rel_count: int, 
                     lm_count: int, annex_linkage: float, clause_clustering: float):
    """Generate executive summary."""
    print("\n" + "=" * 80)
    print("🎯 PHASE 6 VALIDATION SUMMARY")
    print("=" * 80)
    
    # Count successes
    successes = []
    improvements = []
    
    if lm_count >= 5:
        successes.append("L↔M relationships ≥5")
    else:
        improvements.append(f"L↔M relationships ({lm_count} < 5)")
    
    if annex_linkage == 100:
        successes.append("100% annex linkage")
    else:
        improvements.append(f"Annex linkage ({annex_linkage:.1f}% < 100%)")
    
    if clause_clustering > 80:
        successes.append(f"Clause clustering {clause_clustering:.1f}%")
    else:
        improvements.append(f"Clause clustering ({clause_clustering:.1f}%)")
    
    if phase6_rel_count > 0:
        successes.append(f"{phase6_rel_count} relationships added by post-processing")
    
    print(f"\n  ✅ Successes ({len(successes)}):")
    for success in successes:
        print(f"    - {success}")
    
    if improvements:
        print(f"\n  🔨 Improvements Needed ({len(improvements)}):")
        for improvement in improvements:
            print(f"    - {improvement}")
    
    print(f"\n  📊 Key Metrics:")
    print(f"    Total entities: {entity_count}")
    print(f"    Total relationships: {rel_count}")
    print(f"    Phase 6 relationships: {phase6_rel_count}")
    print(f"    L↔M relationships: {lm_count}")
    print(f"    Annex linkage: {annex_linkage:.1f}%")
    print(f"    Clause clustering: {clause_clustering:.1f}%")
    
    # Overall status
    print(f"\n  Overall Status: ", end="")
    if len(successes) >= 3 and not improvements:
        print("✅ EXCELLENT - All targets met")
    elif len(successes) >= 2:
        print("✅ GOOD - Most targets met")
    elif len(successes) >= 1:
        print("🔨 FAIR - Some targets met")
    else:
        print("❌ NEEDS WORK - Few targets met")


def main():
    """Main validation function."""
    print("=" * 80)
    print("🔍 Phase 6 Implementation Validation")
    print("=" * 80)
    print("\nLoading knowledge graph from ./rag_storage...")
    
    # Load knowledge graph
    entities, relationships = load_knowledge_graph()
    
    # Run analyses
    entity_counts = analyze_entities(entities)
    rel_counts, phase6_rel_count, lm_count = analyze_relationships(relationships, entities)
    annex_linkage, clause_clustering = analyze_linkage(entities, relationships)
    
    # Compare to baseline
    compare_baseline(len(entities), len(relationships), lm_count)
    
    # Generate summary
    generate_summary(
        len(entities), 
        len(relationships), 
        phase6_rel_count, 
        lm_count, 
        annex_linkage, 
        clause_clustering
    )
    
    print("\n" + "=" * 80)
    print("✅ Validation complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
