import sys
from pathlib import Path

try:
    import tiktoken
except ImportError:
    print("tiktoken not installed. Please install it to run this measurement.")
    sys.exit(1)

root = Path(__file__).parent.parent
orig = root / "prompts" / "extraction" / "entity_detection_rules.md"
opt = root / "prompts" / "extraction_optimized" / "entity_detection_rules.txt"

enc = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    return len(enc.encode(text))

orig_text = orig.read_text(encoding="utf-8")
opt_text = opt.read_text(encoding="utf-8")

orig_chars = len(orig_text)
opt_chars = len(opt_text)
orig_tokens = count_tokens(orig_text)
opt_tokens = count_tokens(opt_text)

delta_chars = orig_chars - opt_chars
pct_chars = (delta_chars / orig_chars * 100) if orig_chars else 0

delta_tokens = orig_tokens - opt_tokens
pct_tokens = (delta_tokens / orig_tokens * 100) if orig_tokens else 0

print("Entity Detection Rules Token Measurement")
print("========================================")
print(f"Original: {orig_chars} chars, {orig_tokens} tokens")
print(f"Optimized: {opt_chars} chars, {opt_tokens} tokens")
print(f"Delta: -{delta_chars} chars ({pct_chars:.1f}%), -{delta_tokens} tokens ({pct_tokens:.1f}%)")

# Simple success heuristic: token reduction >= 20% while presence parity holds (validated separately)
if pct_tokens >= 20.0:
    print("\n✅ Success: Token reduction meets threshold (>=20%).")
    sys.exit(0)
else:
    print("\n⚠️ Reduction below 20% threshold; review further compression opportunities.")
    sys.exit(2)
