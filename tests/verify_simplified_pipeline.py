import asyncio
import os
import logging
from src.extraction.json_extractor import JsonExtractor
from src.ontology.schema import VALID_ENTITY_TYPES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEST_TEXT = """
SECTION C - PERFORMANCE WORK STATEMENT

1.0 BACKGROUND
The Department of Homeland Security has a requirement for claims processing support.

2.0 SCOPE
The Contractor shall provide all personnel, equipment, and facilities to process claims.

3.0 TASKS
3.1 Claims Processing
The Contractor shall process a minimum of 5,000 medical claims per month. The volume is expected to increase by 10% annually.
Each claim must be adjudicated within 5 business days.

3.2 Reporting
The Contractor shall submit a Monthly Status Report (CDRL A001) by the 10th of each month.
"""

async def test_extraction():
    print("Initializing JsonExtractor...")
    extractor = JsonExtractor()
    
    print("Extracting entities...")
    result = await extractor.extract(TEST_TEXT, chunk_id="test_chunk")
    
    print(f"Extracted {len(result.entities)} entities and {len(result.relationships)} relationships.")
    
    found_workload = False
    found_deliverable = False
    
    for entity in result.entities:
        print(f"\nEntity: {entity.entity_name} ({entity.entity_type})")
        print(f"Description: {entity.description}")
        if entity.metadata:
            print(f"Metadata: {entity.metadata}")
            
        # Check for workload
        if "5,000" in entity.description or "5,000" in str(entity.metadata):
            found_workload = True
            print(">>> SUCCESS: Found workload volume!")
            
        if entity.entity_type == "deliverable" and "A001" in entity.entity_name:
            found_deliverable = True
            print(">>> SUCCESS: Found deliverable!")
            
    if found_workload and found_deliverable:
        print("\n✅ Verification PASSED: Extracted workload and deliverable using simplified ontology.")
    else:
        print("\n❌ Verification FAILED: Missing key details.")

if __name__ == "__main__":
    asyncio.run(test_extraction())
