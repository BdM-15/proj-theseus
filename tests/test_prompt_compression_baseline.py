"""
Baseline Measurement Script for Prompt Compression

Measures exact token counts and extraction quality BEFORE compression.
This establishes the baseline for comparing optimized prompts.

Run this BEFORE making any prompt changes to establish:
1. Token counts per prompt file (using tiktoken)
2. Baseline extraction quality on test chunk
3. Entity type distribution
4. Relationship counts
5. Processing time

Usage:
    python tests/test_prompt_compression_baseline.py
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import tiktoken

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def count_tokens(text: str) -> int:
    """Count tokens using tiktoken (cl100k_base encoding for GPT-4)."""
    tokenizer = tiktoken.get_encoding("cl100k_base")
    return len(tokenizer.encode(text))


def measure_prompt_files() -> Dict[str, Any]:
    """
    Measure token counts for all prompt files.
    
    Returns:
        Dict with file paths, character counts, and token counts
    """
    prompts_dir = Path("prompts")
    
    measurements = {
        "extraction": {},
        "relationship_inference": {},
        "total_tokens": 0,
        "total_chars": 0
    }
    
    # Measure extraction prompts
    extraction_dir = prompts_dir / "extraction"
    for prompt_file in extraction_dir.glob("*.md"):
        content = prompt_file.read_text(encoding="utf-8")
        tokens = count_tokens(content)
        chars = len(content)
        
        measurements["extraction"][prompt_file.name] = {
            "chars": chars,
            "tokens": tokens,
            "path": str(prompt_file)
        }
        measurements["total_tokens"] += tokens
        measurements["total_chars"] += chars
    
    # Measure relationship inference prompts
    rel_inf_dir = prompts_dir / "relationship_inference"
    for prompt_file in rel_inf_dir.glob("*.md"):
        content = prompt_file.read_text(encoding="utf-8")
        tokens = count_tokens(content)
        chars = len(content)
        
        measurements["relationship_inference"][prompt_file.name] = {
            "chars": chars,
            "tokens": tokens,
            "path": str(prompt_file)
        }
        measurements["total_tokens"] += tokens
        measurements["total_chars"] += chars
    
    return measurements


def print_measurements(measurements: Dict[str, Any]):
    """Print formatted measurement results."""
    
    logger.info("=" * 80)
    logger.info("BASELINE PROMPT TOKEN MEASUREMENTS")
    logger.info("=" * 80)
    
    logger.info("\nEXTRACTION PROMPTS:")
    logger.info("-" * 80)
    for filename, data in sorted(measurements["extraction"].items()):
        logger.info(f"{filename:40s} {data['chars']:>8,} chars  {data['tokens']:>8,} tokens")
    
    extraction_tokens = sum(d["tokens"] for d in measurements["extraction"].values())
    logger.info(f"{'SUBTOTAL (Extraction)':40s} {sum(d['chars'] for d in measurements['extraction'].values()):>8,} chars  {extraction_tokens:>8,} tokens")
    
    logger.info("\nRELATIONSHIP INFERENCE PROMPTS:")
    logger.info("-" * 80)
    for filename, data in sorted(measurements["relationship_inference"].items()):
        logger.info(f"{filename:40s} {data['chars']:>8,} chars  {data['tokens']:>8,} tokens")
    
    rel_inf_tokens = sum(d["tokens"] for d in measurements["relationship_inference"].values())
    logger.info(f"{'SUBTOTAL (Relationship Inference)':40s} {sum(d['chars'] for d in measurements['relationship_inference'].values()):>8,} chars  {rel_inf_tokens:>8,} tokens")
    
    logger.info("\n" + "=" * 80)
    logger.info(f"{'TOTAL SYSTEM PROMPT':40s} {measurements['total_chars']:>8,} chars  {measurements['total_tokens']:>8,} tokens")
    logger.info("=" * 80)
    
    # Calculate cost at $0.20/1M input tokens (xAI Grok pricing)
    cost_per_chunk = (measurements['total_tokens'] / 1_000_000) * 0.20
    logger.info(f"\nCost per chunk (at $0.20/1M input tokens): ${cost_per_chunk:.4f}")
    logger.info(f"Cost for 32-chunk RFP: ${cost_per_chunk * 32:.2f}")
    
    # Compression targets
    logger.info("\n" + "=" * 80)
    logger.info("COMPRESSION TARGETS (Grok 4 Recommended: 30-50%)")
    logger.info("=" * 80)
    for percent in [30, 40, 50]:
        target_tokens = int(measurements['total_tokens'] * (1 - percent/100))
        target_reduction = measurements['total_tokens'] - target_tokens
        savings_per_rfp = cost_per_chunk * 32 * (percent / 100)
        logger.info(f"{percent}% reduction: {target_tokens:>8,} tokens (remove {target_reduction:>8,}) - Save ${savings_per_rfp:.2f}/RFP")


async def test_extraction_quality():
    """
    Test extraction quality on a small chunk to establish baseline.
    
    This would run actual extraction, but for now just logs the plan.
    """
    logger.info("\n" + "=" * 80)
    logger.info("EXTRACTION QUALITY BASELINE")
    logger.info("=" * 80)
    logger.info("\nTo establish extraction baseline:")
    logger.info("1. Create test fixture: tests/fixtures/compression_test_chunk.txt")
    logger.info("2. Run extraction with ORIGINAL prompts")
    logger.info("3. Record: entity counts by type, relationship counts, processing time")
    logger.info("4. Save results for comparison after compression")
    logger.info("\nSkipping actual extraction in this initial baseline script.")


def main():
    """Run baseline measurements."""
    logger.info("Starting baseline measurements for prompt compression...\n")
    
    # Measure prompt token counts
    measurements = measure_prompt_files()
    print_measurements(measurements)
    
    # Log extraction quality plan
    asyncio.run(test_extraction_quality())
    
    logger.info("\n" + "=" * 80)
    logger.info("NEXT STEPS:")
    logger.info("=" * 80)
    logger.info("1. Review token counts above")
    logger.info("2. Create test fixture if needed")
    logger.info("3. Begin Phase 2: Compress grok_json_prompt.md (lines 1-200)")
    logger.info("4. Run validation after each 100-200 line batch")
    logger.info("\nBaseline measurement complete!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
