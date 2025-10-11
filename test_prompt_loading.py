"""
Quick validation script to test that all prompts load correctly.

This should be run BEFORE starting the server to catch any missing prompts early.
"""

from src.core.prompt_loader import validate_prompts_exist, list_available_prompts

def main():
    print("=" * 80)
    print("Prompt Loading Validation Test")
    print("=" * 80)
    
    # Define all required prompts
    required_prompts = [
        # Entity extraction
        "entity_extraction/entity_extraction_prompt",
        
        # Relationship inference (5 algorithms)
        "relationship_inference/document_section_linking",
        "relationship_inference/clause_clustering",
        "relationship_inference/section_l_m_mapping",
        "relationship_inference/requirement_evaluation",
        "relationship_inference/sow_deliverable_linking",
        
        # System prompt
        "relationship_inference/system_prompt",
    ]
    
    print(f"\n✅ Testing {len(required_prompts)} required prompts...\n")
    
    try:
        # Validate all prompts exist
        validate_prompts_exist(required_prompts)
        print("✅ All required prompts validated successfully!")
        
        # Show available prompts
        print("\n" + "=" * 80)
        print("Available Prompts by Category")
        print("=" * 80)
        available = list_available_prompts()
        for category, prompts in sorted(available.items()):
            print(f"\n📁 {category}/ ({len(prompts)} prompts)")
            for prompt in prompts:
                print(f"   • {prompt}")
        
        return True
        
    except FileNotFoundError as e:
        print(f"\n❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
