import os
import tiktoken
from src.extraction.json_extractor import JsonExtractor

if __name__ == "__main__":
    # Ensure dummy keys for initializer without calls
    os.environ.setdefault("LLM_BINDING_API_KEY", "dummy-key")
    os.environ.setdefault("XAI_API_KEY", os.environ.get("LLM_BINDING_API_KEY", "dummy-key"))

    extractor = JsonExtractor()
    prompt = extractor.system_prompt
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = len(tokenizer.encode(prompt))
    print("Assembled System Prompt Measurement")
    print("==================================")
    print(f"Characters: {len(prompt)}")
    print(f"Tokens (cl100k_base): {tokens}")
