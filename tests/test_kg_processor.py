"""
Test GovconKGProcessor three-phase pipeline
"""
import sys
import os
import logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Configure logging to see processor output
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

from src.processors.govcon_kg_processor import GovconKGProcessor

# Sample extraction data (simulating what routes.py will provide)
text_chunks = [
    (
        "chunk_0",
        [
            {"entity_name": "User Training", "entity_type": "requirement", "description": "Training requirement", "source_id": "doc1", "file_path": "test.pdf"},
            {"entity_name": "User Training", "entity_type": "requirement", "description": "Duplicate training", "source_id": "doc1", "file_path": "test.pdf"},
            {"entity_name": "Security Clearance", "entity_type": "clause", "description": "Security requirement", "source_id": "doc1", "file_path": "test.pdf"}
        ],
        [
            {"src_id": "User Training", "tgt_id": "Security Clearance", "description": "requires", "keywords": "requires", "weight": 1.0, "source_id": "doc1"}
        ]
    ),
    (
        "chunk_1",
        [
            {"entity_name": "User Training", "entity_type": "requirement", "description": "Another duplicate", "source_id": "doc1", "file_path": "test.pdf"},
            {"entity_name": "Deliverables", "entity_type": "deliverable", "description": "Training deliverable", "source_id": "doc1", "file_path": "test.pdf"}
        ],
        [
            {"src_id": "User Training", "tgt_id": "Deliverables", "description": "produces", "keywords": "produces", "weight": 1.0, "source_id": "doc1"}
        ]
    )
]

multimodal_items = [
    (
        "table_page_5",
        [
            {"entity_name": "Table 1: Requirements Matrix", "entity_type": "table", "description": "Requirements table", "source_id": "doc1", "file_path": "test.pdf"}
        ],
        []
    )
]

# Initialize processor
processor = GovconKGProcessor()

# Run three-phase pipeline
print("\n" + "="*80)
print("TESTING GOVCON KG PROCESSOR")
print("="*80)

custom_kg = processor.process_document(
    text_chunks=text_chunks,
    multimodal_items=multimodal_items
)

print("\n" + "="*80)
print("RESULTS")
print("="*80)
print(f"Entities: {len(custom_kg['entities'])}")
print(f"Relationships: {len(custom_kg['relationships'])}")

print("\n--- Entity Names ---")
for entity in custom_kg['entities']:
    print(f"  - {entity['entity_name']} ({entity['entity_type']})")

print("\n--- Relationships ---")
for rel in custom_kg['relationships']:
    print(f"  - {rel['source_id']} → {rel['target_id']} ({rel['description']})")

print("\n✅ Test complete - check logs for three-phase logging")
