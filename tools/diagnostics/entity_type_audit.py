"""
Entity Type Audit Tool

Analyzes the knowledge graph to provide a complete breakdown of entity types
across all 18 types defined in the ontology schema.

Usage:
    python tools/diagnostics/entity_type_audit.py [--workspace WORKSPACE]

Default workspace: Uses WORKSPACE from .env or 'default'
"""

import os
import sys
import json
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment
load_dotenv(PROJECT_ROOT / ".env")

# Import canonical entity types from schema
from src.ontology.schema import VALID_ENTITY_TYPES

# 18 Entity Types from schema.py - use canonical source
SCHEMA_ENTITY_TYPES = list(VALID_ENTITY_TYPES)

# Entity type categories for analysis
ENTITY_CATEGORIES = {
    "RFP Structure": ["section", "document", "clause"],
    "Requirements & Performance": ["requirement", "performance_metric", "deliverable"],
    "Evaluation": ["evaluation_factor", "submission_instruction", "strategic_theme"],
    "Work Definition": ["statement_of_work", "program"],
    "Resources": ["organization", "person", "equipment", "technology", "location"],
    "Generic": ["concept", "event"],
}


def load_neo4j_entities(workspace: str) -> List[Dict[str, Any]]:
    """Load entities from Neo4j database."""
    try:
        from neo4j import GraphDatabase
        
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USERNAME", "neo4j")  # Note: NEO4J_USERNAME not NEO4J_USER
        password = os.getenv("NEO4J_PASSWORD", "password")
        database = os.getenv("NEO4J_DATABASE", "neo4j")
        
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        with driver.session(database=database) as session:
            # LightRAG stores workspace as a label on nodes
            # Query entities with the workspace label
            workspace_label = workspace.replace("-", "_").replace(" ", "_")
            
            # First try: workspace as label
            result = session.run(f"""
                MATCH (n:`{workspace_label}`)
                WHERE n.entity_type IS NOT NULL
                RETURN 
                    n.entity_name as entity_name,
                    n.entity_type as entity_type,
                    labels(n) as labels
            """)
            
            entities = [dict(record) for record in result]
            
            # If no results, try all entities (maybe single workspace)
            if not entities:
                result = session.run("""
                    MATCH (n)
                    WHERE n.entity_type IS NOT NULL
                    RETURN 
                        n.entity_name as entity_name,
                        n.entity_type as entity_type,
                        labels(n) as labels
                """)
                entities = [dict(record) for record in result]
        
        driver.close()
        return entities
        
    except ImportError:
        print("⚠️  Neo4j driver not installed, falling back to local storage")
        return []
    except Exception as e:
        print(f"⚠️  Neo4j connection failed: {e}")
        return []


def load_local_entities(workspace: str) -> List[Dict[str, Any]]:
    """Load entities from local RAG storage (JSON/GraphML files)."""
    entities = []
    
    # Check rag_storage directory
    rag_storage = PROJECT_ROOT / "rag_storage" / workspace
    
    if not rag_storage.exists():
        print(f"⚠️  Workspace directory not found: {rag_storage}")
        return entities
    
    # Try graph_chunk_entity_relation.json (LightRAG format)
    entity_file = rag_storage / "graph_chunk_entity_relation.json"
    if entity_file.exists():
        try:
            with open(entity_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # LightRAG stores entities with their properties
            if isinstance(data, dict):
                for entity_name, entity_data in data.items():
                    if isinstance(entity_data, dict):
                        entities.append({
                            "entity_name": entity_name,
                            "entity_type": entity_data.get("entity_type", "unknown"),
                            "source": "graph_chunk_entity_relation.json"
                        })
            print(f"✅ Loaded {len(entities)} entities from {entity_file.name}")
        except Exception as e:
            print(f"⚠️  Error loading {entity_file}: {e}")
    
    # Try kv_store_full_docs.json
    kv_file = rag_storage / "kv_store_full_docs.json"
    if kv_file.exists() and not entities:
        try:
            with open(kv_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"📄 Found kv_store_full_docs.json with {len(data)} entries")
        except Exception as e:
            print(f"⚠️  Error loading {kv_file}: {e}")
    
    # Try vdb_entities.json (vector DB)
    vdb_file = rag_storage / "vdb_entities.json"
    if vdb_file.exists():
        try:
            with open(vdb_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict) and "data" in data:
                vdb_entities = data["data"]
                print(f"📊 Found vdb_entities.json with {len(vdb_entities)} vector entries")
                
                # Extract entity info from vector DB
                for entry in vdb_entities:
                    if isinstance(entry, dict):
                        # VDB format: {"__id__": ..., "__vector__": [...], ...other fields}
                        entity_id = entry.get("__id__", "")
                        if entity_id and not entities:  # Only use if no other source
                            entities.append({
                                "entity_name": entity_id,
                                "entity_type": entry.get("entity_type", "unknown"),
                                "source": "vdb_entities.json"
                            })
        except Exception as e:
            print(f"⚠️  Error loading {vdb_file}: {e}")
    
    return entities


def analyze_entity_distribution(entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze entity type distribution against schema."""
    
    # Count entity types
    type_counts = Counter()
    unknown_types = Counter()
    entity_samples = defaultdict(list)
    
    for entity in entities:
        entity_type = entity.get("entity_type", "unknown")
        entity_name = entity.get("entity_name", "unnamed")
        
        if entity_type in SCHEMA_ENTITY_TYPES:
            type_counts[entity_type] += 1
            # Keep up to 3 samples per type
            if len(entity_samples[entity_type]) < 3:
                entity_samples[entity_type].append(entity_name)
        else:
            unknown_types[entity_type] += 1
    
    # Build analysis results
    results = {
        "total_entities": len(entities),
        "schema_types_found": len([t for t in SCHEMA_ENTITY_TYPES if type_counts[t] > 0]),
        "schema_types_missing": [t for t in SCHEMA_ENTITY_TYPES if type_counts[t] == 0],
        "type_distribution": dict(type_counts),
        "unknown_types": dict(unknown_types),
        "entity_samples": dict(entity_samples),
        "coverage_pct": len([t for t in SCHEMA_ENTITY_TYPES if type_counts[t] > 0]) / len(SCHEMA_ENTITY_TYPES) * 100
    }
    
    return results


def print_report(results: Dict[str, Any], workspace: str):
    """Print formatted audit report."""
    
    print("\n" + "=" * 80)
    print(f"📊 ENTITY TYPE AUDIT REPORT - Workspace: {workspace}")
    print("=" * 80)
    
    # Summary
    print(f"\n📈 SUMMARY")
    print(f"   Total Entities: {results['total_entities']}")
    print(f"   Schema Types Found: {results['schema_types_found']}/18 ({results['coverage_pct']:.1f}%)")
    print(f"   Schema Types Missing: {len(results['schema_types_missing'])}")
    
    # Type distribution (sorted by count)
    print(f"\n📊 ENTITY TYPE DISTRIBUTION (Sorted by Count)")
    print("-" * 60)
    
    sorted_types = sorted(
        results['type_distribution'].items(),
        key=lambda x: x[1],
        reverse=True
    )
    
    for entity_type, count in sorted_types:
        bar = "█" * min(count // 5, 30)  # Scale bar
        samples = results['entity_samples'].get(entity_type, [])
        sample_str = ""
        if samples and samples[0]:
            sample_str = f"  (e.g., {str(samples[0])[:40]}...)"
        print(f"   {entity_type:25} : {count:4} {bar}{sample_str}")
    
    # Missing types (CRITICAL)
    if results['schema_types_missing']:
        print(f"\n❌ MISSING ENTITY TYPES ({len(results['schema_types_missing'])})")
        print("-" * 60)
        
        for missing_type in results['schema_types_missing']:
            # Find which category this belongs to
            category = "Unknown"
            for cat_name, cat_types in ENTITY_CATEGORIES.items():
                if missing_type in cat_types:
                    category = cat_name
                    break
            print(f"   ❌ {missing_type:25} [{category}]")
    
    # Category analysis
    print(f"\n📂 COVERAGE BY CATEGORY")
    print("-" * 60)
    
    for category, types in ENTITY_CATEGORIES.items():
        found = sum(1 for t in types if results['type_distribution'].get(t, 0) > 0)
        total = len(types)
        count = sum(results['type_distribution'].get(t, 0) for t in types)
        status = "✅" if found == total else "⚠️" if found > 0 else "❌"
        print(f"   {status} {category:30} : {found}/{total} types ({count} entities)")
        
        # Show missing in this category
        missing_in_cat = [t for t in types if results['type_distribution'].get(t, 0) == 0]
        if missing_in_cat:
            print(f"      Missing: {', '.join(missing_in_cat)}")
    
    # Unknown types warning
    if results['unknown_types']:
        print(f"\n⚠️  UNKNOWN ENTITY TYPES (not in schema)")
        print("-" * 60)
        for unknown_type, count in results['unknown_types'].items():
            print(f"   ⚠️  {unknown_type}: {count}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS")
    print("-" * 60)
    
    if "performance_metric" in results['schema_types_missing']:
        print("   1. ❌ CRITICAL: No performance_metric entities detected")
        print("      → PWS Section 2.0 Service Summary likely has QASP metrics")
        print("      → Check if PO-X objectives extracted as 'requirement' instead")
        print("      → See Issue #9 for prompt enhancement")
    
    if "strategic_theme" in results['schema_types_missing']:
        print("   2. ⚠️  No strategic_theme entities detected")
        print("      → Customer hot buttons may be in evaluation factors")
        print("      → Review prompts for Shipley capture patterns")
    
    if "submission_instruction" in results['schema_types_missing']:
        print("   3. ⚠️  No submission_instruction entities detected")
        print("      → Check if non-UCF format detection is working")
        print("      → Verify pattern-based detection (not Section L specific)")
    
    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Audit entity types in knowledge graph")
    parser.add_argument("--workspace", "-w", default=None, help="Workspace name to audit")
    parser.add_argument("--source", "-s", choices=["neo4j", "local", "both"], default="both",
                        help="Data source to query")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    # Get workspace
    workspace = args.workspace or os.getenv("WORKSPACE", "default")
    
    print(f"\n🔍 Auditing workspace: {workspace}")
    print(f"   Data source: {args.source}")
    
    # Load entities
    entities = []
    
    if args.source in ["neo4j", "both"]:
        neo4j_entities = load_neo4j_entities(workspace)
        if neo4j_entities:
            entities.extend(neo4j_entities)
            print(f"✅ Loaded {len(neo4j_entities)} entities from Neo4j")
    
    if args.source in ["local", "both"] and not entities:
        local_entities = load_local_entities(workspace)
        if local_entities:
            entities.extend(local_entities)
    
    if not entities:
        print("❌ No entities found in workspace")
        print("   Check that:")
        print("   1. Neo4j is running and connected")
        print("   2. Workspace name is correct")
        print("   3. Documents have been processed")
        sys.exit(1)
    
    # Analyze
    results = analyze_entity_distribution(entities)
    
    # Output
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_report(results, workspace)


if __name__ == "__main__":
    main()
