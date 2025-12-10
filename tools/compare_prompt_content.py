"""
Quick comparison of original .md prompts vs V2 assembled prompt.
Shows actual content differences, not just token counts.
"""

from dotenv import load_dotenv
load_dotenv()

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import tiktoken
from src.extraction.json_extractor import JsonExtractor

# Initialize tokenizer
enc = tiktoken.get_encoding('cl100k_base')

# Load V2 assembled prompt
extractor = JsonExtractor()
v2_prompt = extractor.system_prompt

# Load original .md files (what V1 used to load)
import os

prompts_dir = "prompts/extraction"
files = {
    "grok_json_prompt.md": os.path.join(prompts_dir, "grok_json_prompt.md"),
    "entity_detection_rules.md": os.path.join(prompts_dir, "entity_detection_rules.md"),
    "entity_extraction_prompt.md": os.path.join(prompts_dir, "entity_extraction_prompt.md"),
}

original_parts = {}
original_total = ""

for name, path in files.items():
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        original_parts[name] = content
        original_total += content + "\n\n"

# Compare
print("="*80)
print("PROMPT CONTENT COMPARISON: Original .md vs V2 Assembled")
print("="*80)

print(f"\nORIGINAL (.md files concatenated):")
print(f"  Total chars:  {len(original_total):,}")
print(f"  Total lines:  {len(original_total.splitlines()):,}")
print(f"  Total tokens: {len(enc.encode(original_total)):,}")

print(f"\nV2 ASSEMBLED (extraction_v2/ + examples):")
print(f"  Total chars:  {len(v2_prompt):,}")
print(f"  Total lines:  {len(v2_prompt.splitlines()):,}")
print(f"  Total tokens: {len(enc.encode(v2_prompt)):,}")

print(f"\nREDUCTION:")
char_reduction = (1 - len(v2_prompt) / len(original_total)) * 100
line_reduction = (1 - len(v2_prompt.splitlines()) / len(original_total.splitlines())) * 100
token_reduction = (1 - len(enc.encode(v2_prompt)) / len(enc.encode(original_total))) * 100

print(f"  Chars:  {char_reduction:+.1f}%")
print(f"  Lines:  {line_reduction:+.1f}%")
print(f"  Tokens: {token_reduction:+.1f}%")

# Check for examples preservation
print(f"\n{'='*80}")
print("EXAMPLES SECTION CHECK")
print("="*80)

original_examples_marker = "Annotated RFP Examples:" in original_total
v2_examples_marker = "ANNOTATED EXAMPLES" in v2_prompt

print(f"\nOriginal has 'Annotated RFP Examples:' marker: {original_examples_marker}")
print(f"V2 has 'ANNOTATED EXAMPLES' marker: {v2_examples_marker}")

if original_examples_marker:
    orig_ex_start = original_total.find("Annotated RFP Examples:")
    orig_ex_end = original_total.find("---Real Data---") if "---Real Data---" in original_total else len(original_total)
    orig_examples = original_total[orig_ex_start:orig_ex_end]
    print(f"\nOriginal examples section: {len(orig_examples):,} chars, {len(orig_examples.splitlines())} lines")

if v2_examples_marker:
    v2_ex_start = v2_prompt.find("ANNOTATED EXAMPLES")
    v2_ex_end = v2_prompt.find("EXTRACTION TASK") if "EXTRACTION TASK" in v2_prompt else len(v2_prompt)
    v2_examples = v2_prompt[v2_ex_start:v2_ex_end]
    print(f"V2 examples section: {len(v2_examples):,} chars, {len(v2_examples.splitlines())} lines")

# Check for key intelligence patterns (case-insensitive, flexible matching)
print(f"\n{'='*80}")
print("INTELLIGENCE PATTERN CHECK")
print("="*80)

patterns = {
    "QASP split rule": ["split rule", "split_rule"],
    "Modal verb detection": ["shall", "mandatory", "modal_verb"],
    "Section L↔M linking": ["guides", "section l", "section m"],
    "Deliverable traceability": ["tracked_by", "tracked by", "deliverable"],
    "Strategic themes": ["strategic_theme", "strategic theme", "shipley"],
    "Workload drivers": ["labor_drivers", "labor drivers", "boe_category"],
    "Performance metrics": ["performance_metric", "performance objective", "qasp"],
    "Criticality levels": ["criticality", "mandatory", "important", "optional"],
    "Requirement types": ["requirement_type", "functional", "performance", "security"],
    "Evaluation factors": ["evaluation_factor", "subfactor", "factor_id"],
}

print(f"\n{'Pattern':<30s} Original  V2")
print("-"*50)
all_match = True
for name, pattern_list in patterns.items():
    # Check if ANY of the patterns match (case-insensitive)
    orig_has = any(p.lower() in original_total.lower() for p in pattern_list)
    v2_has = any(p.lower() in v2_prompt.lower() for p in pattern_list)
    
    # Only flag as warning if original HAD it but V2 LOST it
    if orig_has and not v2_has:
        status = "❌"
        all_match = False
    elif not orig_has and v2_has:
        status = "✨"  # V2 added something new
    else:
        status = "✅"
    
    print(f"{status} {name:<28s} {'YES' if orig_has else 'NO':>3s}     {'YES' if v2_has else 'NO':>3s}")

print(f"\n{'='*80}")
print("SUMMARY")
print("="*80)

if token_reduction > 0:
    print(f"\n✅ V2 achieves {token_reduction:.1f}% token reduction")
else:
    print(f"\n⚠️  V2 is {abs(token_reduction):.1f}% LARGER than original")

if v2_examples_marker and original_examples_marker:
    examples_retention = (len(v2_examples) / len(orig_examples)) * 100
    print(f"✅ Examples section preserved ({examples_retention:.1f}% of original)")
else:
    print(f"❌ Examples section MISSING")

if all_match:
    print(f"✅ All intelligence patterns preserved")
else:
    print(f"❌ Some intelligence patterns LOST in V2")

print()
