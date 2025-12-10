"""
Convert markdown prompts to clean .txt format.

Strips ALL markdown formatting while preserving 100% of intelligence content.
Expected ~40% token reduction from formatting removal alone.
"""

import re
import os
import tiktoken
from pathlib import Path


def strip_markdown_to_txt(md_content: str) -> str:
    """
    Strip ALL markdown formatting while preserving 100% of intelligence content.
    
    Removes:
    - Header markers (# ## ### etc.)
    - Bold/italic markers (** * __ _)
    - Code fence markers (```) 
    - Inline code backticks
    - Horizontal rules (--- ***)
    - HTML tags
    - Excessive blank lines
    
    Preserves:
    - All actual text content
    - Bullet points (- *) converted to plain dashes
    - Numbered lists
    - Indentation structure
    - JSON/code content (just without fences)
    """
    lines = md_content.split('\n')
    result = []
    in_code_block = False
    
    for line in lines:
        # Track code blocks - skip the fence markers but keep content
        stripped = line.strip()
        if stripped.startswith('```'):
            in_code_block = not in_code_block
            continue
        
        # Skip horizontal rules (---, ***, ___)
        if re.match(r'^[\-\*_]{3,}\s*$', stripped):
            continue
        
        # Strip header markers (# ## ### etc.) but keep text
        line = re.sub(r'^#{1,6}\s+', '', line)
        
        # Strip bold markers (**text** or __text__)
        line = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)
        line = re.sub(r'__([^_]+)__', r'\1', line)
        
        # Strip italic markers (*text* or _text_) - careful with underscores in names
        line = re.sub(r'(?<![a-zA-Z0-9])\*([^*\n]+)\*(?![a-zA-Z0-9])', r'\1', line)
        
        # Strip inline code backticks
        line = re.sub(r'`([^`]+)`', r'\1', line)
        
        # Convert markdown bullets to plain dashes
        line = re.sub(r'^(\s*)\*\s+', r'\1- ', line)
        
        # Strip HTML tags
        line = re.sub(r'<[^>]+>', '', line)
        
        result.append(line)
    
    # Join and collapse multiple blank lines
    text = '\n'.join(result)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def count_tokens(text: str) -> int:
    """Count tokens using cl100k_base encoding."""
    enc = tiktoken.get_encoding('cl100k_base')
    return len(enc.encode(text))


def convert_file(input_path: str, output_path: str) -> dict:
    """Convert a single .md file to .txt format."""
    with open(input_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    txt_content = strip_markdown_to_txt(md_content)
    
    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(txt_content)
    
    # Calculate stats
    md_chars = len(md_content)
    txt_chars = len(txt_content)
    md_tokens = count_tokens(md_content)
    txt_tokens = count_tokens(txt_content)
    
    return {
        'input': input_path,
        'output': output_path,
        'md_chars': md_chars,
        'txt_chars': txt_chars,
        'md_tokens': md_tokens,
        'txt_tokens': txt_tokens,
        'char_reduction': (1 - txt_chars/md_chars) * 100,
        'token_reduction': (1 - txt_tokens/md_tokens) * 100,
    }


def main():
    base_dir = Path(__file__).parent.parent / 'prompts'
    
    # Files to convert
    conversions = [
        # Extraction prompts
        ('extraction/grok_json_prompt.md', 'extraction_optimized/grok_json_prompt.txt'),
        ('extraction/entity_detection_rules.md', 'extraction_optimized/entity_detection_rules.txt'),
        ('extraction/entity_extraction_prompt.md', 'extraction_optimized/entity_extraction_prompt.txt'),
        # Relationship inference prompts
        ('relationship_inference/attachment_section_linking.md', 'relationship_inference_optimized/attachment_section_linking.txt'),
        ('relationship_inference/clause_clustering.md', 'relationship_inference_optimized/clause_clustering.txt'),
        ('relationship_inference/deliverable_traceability.md', 'relationship_inference_optimized/deliverable_traceability.txt'),
        ('relationship_inference/document_hierarchy.md', 'relationship_inference_optimized/document_hierarchy.txt'),
        ('relationship_inference/document_section_linking.md', 'relationship_inference_optimized/document_section_linking.txt'),
        ('relationship_inference/evaluation_hierarchy.md', 'relationship_inference_optimized/evaluation_hierarchy.txt'),
        ('relationship_inference/instruction_evaluation_linking.md', 'relationship_inference_optimized/instruction_evaluation_linking.txt'),
        ('relationship_inference/orphan_resolution.md', 'relationship_inference_optimized/orphan_resolution.txt'),
        ('relationship_inference/requirement_evaluation.md', 'relationship_inference_optimized/requirement_evaluation.txt'),
        ('relationship_inference/semantic_concept_linking.md', 'relationship_inference_optimized/semantic_concept_linking.txt'),
        ('relationship_inference/sow_deliverable_linking.md', 'relationship_inference_optimized/sow_deliverable_linking.txt'),
        ('relationship_inference/system_prompt.md', 'relationship_inference_optimized/system_prompt.txt'),
        ('relationship_inference/workload_enrichment.md', 'relationship_inference_optimized/workload_enrichment.txt'),
    ]
    
    print("=" * 80)
    print("MARKDOWN TO TXT CONVERSION - Intelligence Preserved, Formatting Stripped")
    print("=" * 80)
    print()
    
    total_md_tokens = 0
    total_txt_tokens = 0
    
    for input_rel, output_rel in conversions:
        input_path = base_dir / input_rel
        output_path = base_dir / output_rel
        
        if not input_path.exists():
            print(f"SKIP: {input_rel} (not found)")
            continue
        
        stats = convert_file(str(input_path), str(output_path))
        total_md_tokens += stats['md_tokens']
        total_txt_tokens += stats['txt_tokens']
        
        print(f"{Path(input_rel).name}:")
        print(f"  Chars: {stats['md_chars']:,} -> {stats['txt_chars']:,} ({stats['char_reduction']:.1f}% reduction)")
        print(f"  Tokens: {stats['md_tokens']:,} -> {stats['txt_tokens']:,} ({stats['token_reduction']:.1f}% reduction)")
        print(f"  Output: {output_rel}")
        print()
    
    print("=" * 80)
    print(f"TOTAL: {total_md_tokens:,} -> {total_txt_tokens:,} tokens")
    print(f"OVERALL TOKEN REDUCTION: {(1 - total_txt_tokens/total_md_tokens)*100:.1f}%")
    print("=" * 80)


if __name__ == '__main__':
    main()
