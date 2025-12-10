"""
Presence Parity Test for Compressed vs Original Prompts

Compares critical intelligence elements presence in the constructed system prompt
without invoking the LLM. Ensures compressed prompts preserve all core rules.
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.extraction.json_extractor import JsonExtractor

CRITICAL_STRINGS = [
    # Distinction & split rule
    "PERFORMANCE_METRIC",
    "REQUIREMENT",
    "MEASURED_BY",
    # Strategic theme
    "strategic_theme",
    "CUSTOMER_HOT_BUTTON",
    # Entity types
    "evaluation_factor",
    "submission_instruction",
    "deliverable",
    "clause",
    "statement_of_work",
    "performance_metric",
    "organization",
    "document",
    "section",
    "program",
    "equipment",
    "location",
    "person",
    "technology",
    "concept",
    # Naming normalization
    "FAR 52.212-1",
    "Section C.4",
    "CDRL A001",
    # Workload decomposition
    "labor_drivers",
    "material_needs",
    # Tables extraction
    "HAS_EQUIPMENT",
    "APPLIES_TO",
    "CHILD_OF",
    # JSON format
    "entities",
    "relationships",
    "entity_name",
    "entity_type",
]


def build_prompt(use_compressed: bool) -> str:
    os.environ["USE_COMPRESSED_PROMPTS"] = "true" if use_compressed else "false"
    # Ensure API key envs exist to allow JsonExtractor initialization
    os.environ.setdefault("LLM_BINDING_API_KEY", "test-dummy-key")
    os.environ.setdefault("XAI_API_KEY", "test-dummy-key")
    extractor = JsonExtractor()
    return extractor.system_prompt


def check_presence(prompt_text: str):
    missing = []
    for s in CRITICAL_STRINGS:
        if s not in prompt_text:
            missing.append(s)
    return missing


def main():
    print("Presence Parity Test: Original vs Compressed System Prompt")
    print("==========================================================")

    # Original
    orig_prompt = build_prompt(use_compressed=False)
    orig_missing = check_presence(orig_prompt)
    print(f"Original Prompt Length: {len(orig_prompt)} chars")
    print(f"Original Missing Count: {len(orig_missing)}")

    # Compressed
    comp_prompt = build_prompt(use_compressed=True)
    comp_missing = check_presence(comp_prompt)
    print(f"Compressed Prompt Length: {len(comp_prompt)} chars")
    print(f"Compressed Missing Count: {len(comp_missing)}")

    # Differential
    orig_set = set(CRITICAL_STRINGS) - set(orig_missing)
    comp_set = set(CRITICAL_STRINGS) - set(comp_missing)

    only_in_orig = sorted(list(orig_set - comp_set))
    only_in_comp = sorted(list(comp_set - orig_set))

    print("\nDelta Analysis")
    print("--------------")
    print(f"Present only in ORIGINAL: {only_in_orig}")
    print(f"Present only in COMPRESSED: {only_in_comp}")

    # Verdict
    if len(comp_missing) == 0 and len(orig_missing) == 0:
        print("\n✅ Parity achieved: All critical strings present in both prompts.")
        return 0
    elif len(comp_missing) == 0:
        print("\n✅ Compressed prompt preserves all critical strings.")
        return 0
    else:
        print("\n❌ Compressed prompt missing critical strings:")
        for s in comp_missing:
            print(f" - {s}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
