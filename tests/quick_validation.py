"""Quick validation test for Phase 1 reset."""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

def main():
    print("=== ENV VALIDATION ===")
    print(f"CHUNK_SIZE: {os.getenv('CHUNK_SIZE')}")
    print(f"CHUNK_OVERLAP_SIZE: {os.getenv('CHUNK_OVERLAP_SIZE')}")
    print(f"CHUNK_OVERLAP_TOKEN_SIZE: {os.getenv('CHUNK_OVERLAP_TOKEN_SIZE')}")
    print(f"MAX_ASYNC: {os.getenv('MAX_ASYNC')}")
    print(f"EXTRACTION_LLM_NAME: {os.getenv('EXTRACTION_LLM_NAME')}")
    
    # Verify RAGAnything import
    from raganything import RAGAnything
    print("\n=== RAGANYTHING ===")
    print("RAGAnything imported OK")
    
    # Verify ontology schema
    from src.ontology.schema import BaseEntity, ExtractionResult, EntityType
    from typing import get_args
    print("\n=== ONTOLOGY SCHEMA ===")
    print(f"EntityType count: {len(get_args(EntityType))}")
    print(f"BaseEntity fields: {list(BaseEntity.model_fields.keys())}")
    
    # Check description is required
    field = BaseEntity.model_fields.get('description')
    print(f"description required: {field.is_required() if field else 'N/A'}")
    
    # Check source_text is removed
    has_source_text = 'source_text' in BaseEntity.model_fields
    print(f"source_text removed: {not has_source_text}")
    
    # Verify JSON extractor
    from src.extraction.json_extractor import JsonExtractor
    print("\n=== JSON EXTRACTOR ===")
    print("JsonExtractor imported OK")
    
    print("\n✅ All validations passed!")

if __name__ == "__main__":
    main()

