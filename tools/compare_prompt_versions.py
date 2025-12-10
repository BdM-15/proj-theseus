"""
Compare v1 vs v2 prompt token counts.
"""

import os
import tiktoken
from pathlib import Path

def measure_file(file_path: str) -> dict:
    """Measure token and character counts for a file."""
    if not os.path.exists(file_path):
        return {"tokens": 0, "chars": 0, "lines": 0, "exists": False}
    
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = len(enc.encode(content))
    chars = len(content)
    lines = len(content.split('\n'))
    
    return {
        "tokens": tokens,
        "chars": chars,
        "lines": lines,
        "exists": True
    }

def compare_prompts():
    """Compare v1 (extraction_optimized) vs v2 (extraction_v2) prompts."""
    base_path = Path.cwd()
    
    print("=" * 80)
    print("PROMPT COMPARISON: v1 (baseline) vs v2 (refactored)")
    print("=" * 80)
    
    # V1 files
    v1_files = {
        "system_prompt": base_path / "prompts/extraction_optimized/grok_json_prompt.txt",
        "detection_taxonomy": base_path / "prompts/extraction_optimized/entity_detection_rules.txt",
        "extraction_prompt": base_path / "prompts/extraction_optimized/entity_extraction_prompt.txt",
    }
    
    # V2 files
    v2_files = {
        "system_prompt": base_path / "prompts/extraction_v2/system_prompt.txt",
        "detection_taxonomy": base_path / "prompts/extraction_v2/detection_taxonomy.txt",
        "output_format": base_path / "prompts/extraction_v2/output_format.txt",
    }
    
    v1_total = 0
    v2_total = 0
    
    print("\nV1 PROMPTS (extraction_optimized):")
    print("-" * 80)
    for name, file_path in v1_files.items():
        metrics = measure_file(str(file_path))
        if metrics["exists"]:
            print(f"{name:25} {metrics['tokens']:6,} tokens  {metrics['chars']:8,} chars  {metrics['lines']:5,} lines")
            v1_total += metrics["tokens"]
        else:
            print(f"{name:25} FILE NOT FOUND")
    
    print(f"\n{'V1 TOTAL':25} {v1_total:6,} tokens")
    
    print("\n" + "=" * 80)
    print("\nV2 PROMPTS (extraction_v2):")
    print("-" * 80)
    for name, file_path in v2_files.items():
        metrics = measure_file(str(file_path))
        if metrics["exists"]:
            print(f"{name:25} {metrics['tokens']:6,} tokens  {metrics['chars']:8,} chars  {metrics['lines']:5,} lines")
            v2_total += metrics["tokens"]
        else:
            print(f"{name:25} FILE NOT FOUND")
    
    print(f"\n{'V2 TOTAL (current)':25} {v2_total:6,} tokens")
    
    # Calculate savings
    if v1_total > 0 and v2_total > 0:
        savings = v1_total - v2_total
        savings_pct = (savings / v1_total) * 100
        
        print("\n" + "=" * 80)
        print("ANALYSIS:")
        print(f"  Token reduction: {savings:,} tokens ({savings_pct:.1f}%)")
        
        if savings_pct >= 30:
            print(f"  ✅ EXCELLENT: Exceeded 30% target")
        elif savings_pct >= 20:
            print(f"  ✅ GOOD: Approaching target (20-30%)")
        elif savings_pct >= 10:
            print(f"  ⚠️ MODERATE: Some savings (10-20%)")
        else:
            print(f"  ❌ LOW: Below 10% reduction")
        
        # Note about missing components
        print("\n  NOTE: v2 still needs:")
        print("    - Entity-specific examples (consolidated)")
        print("    - Schema-mirror integration (18 entity files)")
        print("    - Cross-references to reduce redundancy")
    
    print("=" * 80)

if __name__ == "__main__":
    compare_prompts()
