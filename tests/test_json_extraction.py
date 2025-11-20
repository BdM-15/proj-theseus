import asyncio
import os
import sys
from dotenv import load_dotenv

# Add root to path
sys.path.append(os.getcwd())

# Load environment variables
load_dotenv()

from src.extraction.json_extractor import JsonExtractor

SAMPLE_RFP_TEXT = """
SECTION L - INSTRUCTIONS TO OFFERORS

L.1.0 GENERAL INSTRUCTIONS
The Offeror shall submit a Technical Volume limited to 25 pages, 12-point Times New Roman font.
This volume must address Factor 1 (Technical Approach) and Factor 2 (Management).

SECTION M - EVALUATION FACTORS

M.2.1 Factor 1: Technical Approach (Most Important, 40%)
The Government will evaluate the Offeror's understanding of the PWS requirements.

M.2.2 Factor 2: Management Approach (Important, 30%)
The Government will evaluate the staffing plan and key personnel.

SECTION C - PERFORMANCE WORK STATEMENT

C.3.1 System Administration
The Contractor shall provide 24/7 system administration support for the Red Hat Linux environment.
The Contractor should maintain 99.9% system availability.
The Contractor may use open-source automation tools.

C.3.2 Cybersecurity
The Contractor shall comply with FAR 52.204-21 and DFARS 252.204-7012.
"""

async def test_extraction():
    print("Initializing JsonExtractor...")
    try:
        extractor = JsonExtractor()
    except Exception as e:
        print(f"Failed to initialize extractor: {e}")
        return

    print("Running extraction on sample text...")
    try:
        result = await extractor.extract(SAMPLE_RFP_TEXT)
        
        print("\n=== EXTRACTION SUCCESS ===")
        print(f"Total Entities: {len(result.entities)}")
        
        print("\n--- Entities ---")
        for entity in result.entities:
            print(f"[{entity.entity_type.upper()}] {entity.entity_name} ({type(entity).__name__})")
            if isinstance(entity, type(result.entities[0].__class__.__base__.__subclasses__()[0])): # Hacky way to check Requirement? No.
                 pass

            if entity.entity_type == "requirement" and hasattr(entity, 'criticality'):
                print(f"   Criticality: {entity.criticality}")
                print(f"   Modal: {entity.modal_verb}")
                if entity.labor_drivers:
                    print(f"   Labor Drivers: {entity.labor_drivers}")
                if entity.material_needs:
                    print(f"   Material Needs: {entity.material_needs}")
            elif entity.entity_type == "evaluation_factor" and hasattr(entity, 'weight'):
                print(f"   Weight: {entity.weight}")
                print(f"   Importance: {entity.importance}")
            elif entity.entity_type == "submission_instruction" and hasattr(entity, 'page_limit'):
                print(f"   Page Limit: {entity.page_limit}")
            print(f"   Desc: {entity.description[:100]}...")
            print("")
            
        print("\n--- Relationships ---")
        for rel in result.relationships:
            print(f"[{rel.relationship_type}] {rel.source_entity} -> {rel.target_entity}")
            print(f"   Desc: {rel.description}")
            print("")
            
    except Exception as e:
        print(f"\n=== EXTRACTION FAILED ===")
        print(f"Error: {e}")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_extraction())
