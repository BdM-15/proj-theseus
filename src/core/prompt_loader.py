"""
Prompt Loader: External Markdown Prompt Management

Loads prompts from prompts/ directory as external data files,
enabling 5-second edit cycles without server restarts.

Philosophy: Prompts are training data, not code.
- 2M context windows enable detailed, example-rich prompts
- Version controlled separately from logic
- Continuous refinement without code changes
"""

from pathlib import Path
from typing import Dict
import logging

logger = logging.getLogger(__name__)

# Cache for loaded prompts (in-memory)
_prompt_cache: Dict[str, str] = {}


def load_prompt(prompt_name: str, use_cache: bool = True) -> str:
    """
    Load prompt from prompts/ directory.
    
    Args:
        prompt_name: Prompt path relative to prompts/ directory (without .md extension)
                    Example: "entity_extraction/entity_detection_rules"
        use_cache: Use in-memory cache (default True). Set False for development/testing.
    
    Returns:
        Prompt text as string
        
    Raises:
        FileNotFoundError: If prompt file doesn't exist
        
    Examples:
        >>> load_prompt("entity_extraction/entity_detection_rules")
        "SEMANTIC-FIRST ENTITY DETECTION RULES:\\n\\n1. EVALUATION_FACTOR:..."
        
        >>> load_prompt("relationship_inference/section_l_m_linking")
        "SECTION L↔M MAPPING RULES:\\n\\n..."
    """
    # Check cache first
    if use_cache and prompt_name in _prompt_cache:
        logger.debug(f"Loaded prompt from cache: {prompt_name}")
        return _prompt_cache[prompt_name]
    
    # Build file path
    prompt_path = Path("prompts") / f"{prompt_name}.md"
    
    if not prompt_path.exists():
        raise FileNotFoundError(
            f"Prompt not found: {prompt_path}\n"
            f"Expected path: {prompt_path.absolute()}\n"
            f"Available prompts: Use list_available_prompts() to see options"
        )
    
    # Load from disk
    try:
        prompt_text = prompt_path.read_text(encoding="utf-8")
        logger.info(f"Loaded prompt: {prompt_name} ({len(prompt_text)} chars)")
        
        # Cache for future use
        _prompt_cache[prompt_name] = prompt_text
        
        return prompt_text
        
    except Exception as e:
        logger.error(f"Error loading prompt {prompt_name}: {e}")
        raise


def list_available_prompts() -> Dict[str, list]:
    """
    List all available prompts in prompts/ directory.
    
    Returns:
        Dictionary mapping category to list of prompt names
        
    Example:
        {
            "entity_extraction": ["entity_detection_rules", "metadata_extraction", ...],
            "relationship_inference": ["section_l_m_linking", "annex_linking", ...]
        }
    """
    prompts_dir = Path("prompts")
    
    if not prompts_dir.exists():
        logger.warning(f"Prompts directory not found: {prompts_dir.absolute()}")
        return {}
    
    available = {}
    
    for category_dir in prompts_dir.iterdir():
        if category_dir.is_dir():
            category = category_dir.name
            prompts = [
                p.stem for p in category_dir.glob("*.md")
            ]
            available[category] = sorted(prompts)
    
    return available


def validate_prompts_exist(required_prompts: list) -> None:
    """
    Validate that all required prompts exist at startup.
    
    Args:
        required_prompts: List of prompt names (e.g., ["entity_extraction/entity_detection_rules"])
        
    Raises:
        FileNotFoundError: If any required prompt is missing
    """
    missing = []
    
    for prompt_name in required_prompts:
        prompt_path = Path("prompts") / f"{prompt_name}.md"
        if not prompt_path.exists():
            missing.append(prompt_name)
    
    if missing:
        raise FileNotFoundError(
            f"Missing {len(missing)} required prompts:\n" +
            "\n".join(f"  - {p}" for p in missing) +
            f"\n\nRun list_available_prompts() to see what's available."
        )
    
    logger.info(f"✓ Validated {len(required_prompts)} required prompts exist")


def clear_cache() -> None:
    """Clear in-memory prompt cache. Useful for development/testing."""
    global _prompt_cache
    count = len(_prompt_cache)
    _prompt_cache = {}
    logger.info(f"Cleared {count} cached prompts")


def get_cache_stats() -> Dict[str, int]:
    """Get statistics about cached prompts."""
    return {
        "cached_prompts": len(_prompt_cache),
        "total_size_chars": sum(len(p) for p in _prompt_cache.values())
    }
