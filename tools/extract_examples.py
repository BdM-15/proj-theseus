"""
Extract examples from v1 prompts and consolidate them for v2.

Strategy:
1. Parse existing examples from entity_extraction_prompt.txt
2. Identify unique intelligence (avoid duplicates)
3. Create consolidated example file with cross-references
4. Organize by entity type for easy reference
"""

import os
import re
from pathlib import Path
from typing import List, Dict

def extract_examples_from_file(file_path: str) -> List[Dict]:
    """Extract example sections from a prompt file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    examples = []
    
    # Find example sections (various patterns)
    # Pattern 1: "Example N: Title"
    pattern1 = r'Example \d+:([^\n]+)'
    matches1 = re.finditer(pattern1, content)
    
    for match in matches1:
        title = match.group(1).strip()
        start_pos = match.start()
        
        # Find the end of this example (next "Example" or major section)
        next_match = re.search(r'\n\s*(Example \d+:|---[A-Z]|^[A-Z][A-Z\s]+\n)', 
                              content[start_pos + 100:], re.MULTILINE)
        
        if next_match:
            end_pos = start_pos + 100 + next_match.start()
        else:
            end_pos = start_pos + 2000  # Default chunk size
        
        example_text = content[start_pos:end_pos]
        
        # Try to detect entity types mentioned
        entity_types = []
        for entity_type in ['requirement', 'evaluation_factor', 'submission_instruction',
                           'strategic_theme', 'clause', 'performance_metric', 'deliverable',
                           'document', 'section']:
            if entity_type in example_text.lower():
                entity_types.append(entity_type)
        
        examples.append({
            'title': title,
            'content': example_text,
            'entity_types': entity_types,
            'line_count': len(example_text.split('\n'))
        })
    
    return examples

def categorize_examples(examples: List[Dict]) -> Dict[str, List[Dict]]:
    """Group examples by primary entity type."""
    categorized = {
        'qasp_performance_metrics': [],
        'section_l_m_mapping': [],
        'requirements_workload': [],
        'clauses': [],
        'deliverables': [],
        'strategic_themes': [],
        'mixed': []
    }
    
    for example in examples:
        title_lower = example['title'].lower()
        
        if any(k in title_lower for k in ['qasp', 'performance', 'metric', 'po-']):
            categorized['qasp_performance_metrics'].append(example)
        elif any(k in title_lower for k in ['section l', 'section m', 'evaluation', 'submission']):
            categorized['section_l_m_mapping'].append(example)
        elif any(k in title_lower for k in ['requirement', 'pws', 'sow', 'workload']):
            categorized['requirements_workload'].append(example)
        elif 'clause' in title_lower or 'far' in title_lower or 'dfars' in title_lower:
            categorized['clauses'].append(example)
        elif 'deliverable' in title_lower or 'cdrl' in title_lower:
            categorized['deliverables'].append(example)
        elif 'strategic' in title_lower or 'theme' in title_lower or 'hot button' in title_lower:
            categorized['strategic_themes'].append(example)
        else:
            categorized['mixed'].append(example)
    
    return categorized

def main():
    """Extract and analyze examples from v1 prompts."""
    base_path = Path.cwd()
    
    # Extract from main prompt file (contains most examples)
    main_prompt = base_path / "prompts/extraction_optimized/entity_extraction_prompt.txt"
    
    print("=" * 80)
    print("EXAMPLE EXTRACTION ANALYSIS")
    print("=" * 80)
    
    if not main_prompt.exists():
        print(f"❌ File not found: {main_prompt}")
        return
    
    examples = extract_examples_from_file(str(main_prompt))
    
    print(f"\nFound {len(examples)} examples in entity_extraction_prompt.txt\n")
    
    categorized = categorize_examples(examples)
    
    for category, items in categorized.items():
        if items:
            print(f"\n{category.upper().replace('_', ' ')} ({len(items)} examples):")
            for item in items:
                print(f"  - {item['title'][:60]:<60} ({item['line_count']} lines)")
    
    # Calculate total lines
    total_lines = sum(ex['line_count'] for ex in examples)
    print(f"\n{'=' * 80}")
    print(f"Total example content: ~{total_lines:,} lines")
    print(f"Average per example: ~{total_lines // len(examples) if examples else 0} lines")
    print(f"{'=' * 80}")
    
    # Estimate token count (rough: 1 line ≈ 20-30 tokens)
    estimated_tokens = total_lines * 25
    print(f"\nEstimated example tokens: ~{estimated_tokens:,}")
    print(f"This represents ~{(estimated_tokens / 40327) * 100:.1f}% of v1 extraction prompts")
    
    print(f"\n{'=' * 80}")
    print("CONSOLIDATION STRATEGY:")
    print("=" * 80)
    print("""
1. PRIORITY EXAMPLES (keep in full):
   - QASP/Performance Metrics (most critical error)
   - Section L↔M Mapping (evaluation/submission link)
   - Requirements with Workload Drivers (labor/material extraction)
   
2. REFERENCE EXAMPLES (cross-reference to Priority):
   - PWS Appendix Structure → Reference Requirements example
   - Clause Extraction → Separate small example
   - Strategic Themes → Inline in detection_taxonomy.txt
   
3. CONSOLIDATION TARGETS:
   - Reduce from ~{total_lines:,} lines to ~1,500 lines (60% reduction)
   - Focus on canonical patterns, not exhaustive coverage
   - Use cross-references: "See Example 1, lines 45-52"
    """)

if __name__ == "__main__":
    main()
