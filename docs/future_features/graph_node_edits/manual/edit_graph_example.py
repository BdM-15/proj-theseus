"""
Example: Using LightRAG's Edit API to manually enhance the knowledge graph

This demonstrates how to:
1. Fix extraction errors
2. Add missing relationships
3. Inject custom domain knowledge
4. Merge duplicate entities
"""

import asyncio
from pathlib import Path
from lightrag import LightRAG
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.llm.openai import gpt_4o_mini_complete, openai_embed

WORKING_DIR = "./rag_storage"


async def main():
    # Initialize LightRAG instance
    rag = LightRAG(
        working_dir=WORKING_DIR,
        embedding_func=openai_embed,
        llm_model_func=gpt_4o_mini_complete,
    )
    await rag.initialize_storages()
    await initialize_pipeline_status()
    
    print("📝 Example 1: Fix Entity Type Error")
    print("=" * 60)
    # Check if entity exists first
    entity_info = await rag.aget_entity("Department of Veterans Affairs VA")
    if entity_info:
        print(f"Before: {entity_info['entity_type']}")
        
        # Fix entity type from incorrect extraction
        updated = await rag.aedit_entity(
            entity_name="Department of Veterans Affairs VA",
            updated_data={
                "entity_type": "organization",
                "description": "Department of Veterans Affairs (VA) - Federal agency providing mandatory supplies for contract"
            },
            allow_rename=False
        )
        print(f"After: {updated['entity_type']}")
        print("✅ Entity type corrected!\n")
    
    print("📝 Example 2: Add Missing Relationship")
    print("=" * 60)
    # Phase 6.1 might have missed a specific L↔M mapping
    try:
        new_rel = await rag.acreate_relation(
            source_entity="L.4 Proposal Format",
            target_entity="Factor 1 - Technical Approach",
            relation_data={
                "description": "Proposal format instructions guide how Technical Approach is submitted and evaluated",
                "keywords": "guides submission evaluation",
                "weight": 0.9,
                "relationship_type": "GUIDES"
            }
        )
        print(f"✅ Created relationship: L.4 → Factor 1")
        print(f"   Description: {new_rel['description']}\n")
    except Exception as e:
        print(f"Note: {e}\n")
    
    print("📝 Example 3: Add Custom Domain Knowledge")
    print("=" * 60)
    # Inject your company's past performance
    try:
        company_entity = await rag.acreate_entity(
            entity_name="Our Company - Navy BOS Portfolio",
            entity_data={
                "entity_type": "organization",
                "description": "Company portfolio of Navy Base Operations Support contracts worth $500M since 2015, including similar MCSF-BI work",
                "source_id": "company_domain_knowledge"
            }
        )
        print(f"✅ Created entity: {company_entity['entity_name']}")
        
        # Link to evaluation factor
        link_rel = await rag.acreate_relation(
            source_entity="Our Company - Navy BOS Portfolio",
            target_entity="Factor 6 - Past Performance",
            relation_data={
                "description": "Company's Navy BOS portfolio directly supports Past Performance evaluation",
                "keywords": "supports demonstrates qualifies",
                "weight": 1.0,
                "relationship_type": "SUPPORTS"
            }
        )
        print(f"✅ Linked to Factor 6 - Past Performance\n")
    except Exception as e:
        print(f"Note: {e}\n")
    
    print("📝 Example 4: Rename Entity (Merge)")
    print("=" * 60)
    # If LightRAG extracted "MCSF" and "MCSF-BI" separately, merge them
    try:
        renamed = await rag.aedit_entity(
            entity_name="MCSF",
            updated_data={
                "entity_name": "MCSF-BI",
                "description": "Marine Corps Support Facility Blount Island - primary facility for this contract"
            },
            allow_rename=True  # This merges relationships
        )
        print(f"✅ Renamed MCSF → MCSF-BI (relationships preserved)\n")
    except Exception as e:
        print(f"Note: {e}\n")
    
    print("📝 Example 5: Check Entity Exists Before Creating")
    print("=" * 60)
    entity_name = "Section L.4"
    exists = await rag.aget_entity(entity_name)
    if exists:
        print(f"✅ Entity '{entity_name}' exists:")
        print(f"   Type: {exists['entity_type']}")
        print(f"   Description: {exists['description'][:100]}...")
    else:
        print(f"❌ Entity '{entity_name}' not found - safe to create")
    
    await rag.finalize_storages()
    print("\n🎉 Done! All edits saved to knowledge graph.")


if __name__ == "__main__":
    asyncio.run(main())
