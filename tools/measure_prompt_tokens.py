"""
Measure token counts for prompt files.
Used for baseline measurement and v2 comparison.
"""

import os
import tiktoken
from pathlib import Path

def measure_prompts(prompts_dir: str, output_file: str = None):
    """Measure token counts for all prompt files."""
    enc = tiktoken.get_encoding("cl100k_base")
    
    # Extraction prompts (v1 - optimized)
    extraction_files = [
        "prompts/extraction_optimized/grok_json_prompt.txt",
        "prompts/extraction_optimized/entity_detection_rules.txt",
        "prompts/extraction_optimized/entity_extraction_prompt.txt",
    ]
    
    results = []
    total_extraction = 0
    
    print("=" * 80)
    print("BASELINE PROMPT TOKEN COUNTS (v1 - extraction_optimized)")
    print("=" * 80)
    
    for file_path in extraction_files:
        full_path = os.path.join(prompts_dir, "..", file_path)
        if os.path.exists(full_path):
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            tokens = len(enc.encode(content))
            chars = len(content)
            lines = len(content.split('\n'))
            
            file_name = os.path.basename(file_path)
            print(f"\n{file_name}:")
            print(f"  Tokens: {tokens:,}")
            print(f"  Chars:  {chars:,}")
            print(f"  Lines:  {lines:,}")
            
            total_extraction += tokens
            results.append({
                "file": file_name,
                "tokens": tokens,
                "chars": chars,
                "lines": lines
            })
        else:
            print(f"\n❌ File not found: {file_path}")
    
    print(f"\n{'=' * 80}")
    print(f"TOTAL EXTRACTION PROMPTS: {total_extraction:,} tokens")
    print(f"{'=' * 80}")
    
    # Relationship inference prompts
    rel_files = [
        "system_prompt.txt",
        "evaluation_hierarchy.txt",
        "document_hierarchy.txt",
        "deliverable_traceability.txt",
        "clause_clustering.txt",
        "instruction_evaluation_linking.txt",
        "attachment_section_linking.txt",
        "sow_deliverable_linking.txt",
        "semantic_concept_linking.txt",
        "requirement_evaluation.txt",
        "orphan_resolution.txt",
        "workload_enrichment.txt",
        "document_section_linking.txt",
    ]
    
    rel_dir = os.path.join(prompts_dir, "..", "prompts/relationship_inference_optimized")
    total_rel = 0
    
    if os.path.exists(rel_dir):
        print(f"\n{'=' * 80}")
        print("RELATIONSHIP INFERENCE PROMPTS")
        print("=" * 80)
        
        for file_name in rel_files:
            file_path = os.path.join(rel_dir, file_name)
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                tokens = len(enc.encode(content))
                print(f"{file_name}: {tokens:,} tokens")
                total_rel += tokens
        
        print(f"\n{'=' * 80}")
        print(f"TOTAL RELATIONSHIP INFERENCE: {total_rel:,} tokens")
        print(f"{'=' * 80}")
    
    print(f"\n{'=' * 80}")
    print(f"GRAND TOTAL (ALL PROMPTS): {total_extraction + total_rel:,} tokens")
    print(f"{'=' * 80}")
    
    # Save results if output file specified
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"Baseline Token Counts\n")
            f.write(f"=====================\n\n")
            f.write(f"Extraction Prompts: {total_extraction:,} tokens\n")
            f.write(f"Relationship Inference: {total_rel:,} tokens\n")
            f.write(f"Grand Total: {total_extraction + total_rel:,} tokens\n")
        print(f"\n✅ Results saved to {output_file}")
    
    return {
        "extraction_tokens": total_extraction,
        "relationship_tokens": total_rel,
        "total_tokens": total_extraction + total_rel,
        "files": results
    }

if __name__ == "__main__":
    # Run from project root
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(base_dir)
    
    results = measure_prompts(
        prompts_dir=os.path.join(base_dir, "prompts"),
        output_file=os.path.join(base_dir, "docs/implementation_plans/baseline_token_counts.txt")
    )
