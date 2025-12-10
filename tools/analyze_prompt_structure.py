"""
Analyze current prompt structure to identify key patterns and intelligence.
This helps us understand what to preserve during refactoring.
"""

import os
from pathlib import Path

def analyze_prompt_file(file_path: str):
    """Analyze a single prompt file for structure and patterns."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = content.split('\n')
    
    print(f"\n{'=' * 80}")
    print(f"FILE: {os.path.basename(file_path)}")
    print(f"{'=' * 80}")
    print(f"Total lines: {len(lines):,}")
    print(f"Total chars: {len(content):,}")
    
    # Find key sections (headers starting with specific patterns)
    sections = []
    current_section = None
    section_line = 0
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Look for section headers (various patterns)
        if any(stripped.startswith(p) for p in ['#', '==', '---', 'Rule', 'Example', 'CRITICAL:', '⚠️']):
            if current_section and i - section_line > 10:  # Only count substantial sections
                sections.append((current_section, i - section_line))
            current_section = stripped[:60]  # First 60 chars of header
            section_line = i
    
    if sections:
        print(f"\nKey sections found ({len(sections)}):")
        for section, line_count in sections[:15]:  # Show first 15
            print(f"  - {section[:70]:<70} ({line_count} lines)")
        if len(sections) > 15:
            print(f"  ... and {len(sections) - 15} more sections")
    
    # Count examples
    example_count = sum(1 for line in lines if 'example' in line.lower() and line.strip().startswith(('Example', '#', '-')))
    print(f"\nExample sections: ~{example_count}")
    
    # Count detection patterns
    pattern_indicators = ['trigger', 'pattern', 'detection', 'signal', 'if you see']
    pattern_lines = sum(1 for line in lines if any(p in line.lower() for p in pattern_indicators))
    print(f"Detection pattern references: ~{pattern_lines}")
    
    # Count entity type mentions
    entity_types = [
        'requirement', 'evaluation_factor', 'submission_instruction', 'strategic_theme',
        'clause', 'performance_metric', 'deliverable', 'document', 'section',
        'organization', 'concept', 'equipment', 'location', 'person', 'technology'
    ]
    entity_mentions = {}
    for entity_type in entity_types:
        count = content.lower().count(entity_type)
        if count > 3:  # Only show significant mentions
            entity_mentions[entity_type] = count
    
    if entity_mentions:
        print(f"\nEntity type mentions (>3):")
        for entity, count in sorted(entity_mentions.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  - {entity}: {count}")


def analyze_all_prompts():
    """Analyze all three main prompt files."""
    base_path = Path.cwd()
    prompts_dir = base_path / "prompts" / "extraction_optimized"
    
    files = [
        prompts_dir / "grok_json_prompt.txt",
        prompts_dir / "entity_detection_rules.txt",
        prompts_dir / "entity_extraction_prompt.txt",
    ]
    
    print("=" * 80)
    print("PROMPT STRUCTURE ANALYSIS")
    print("=" * 80)
    
    for file_path in files:
        if file_path.exists():
            analyze_prompt_file(str(file_path))
        else:
            print(f"\n❌ File not found: {file_path}")
    
    print(f"\n{'=' * 80}")
    print("ANALYSIS COMPLETE")
    print(f"{'=' * 80}\n")


if __name__ == "__main__":
    analyze_all_prompts()
