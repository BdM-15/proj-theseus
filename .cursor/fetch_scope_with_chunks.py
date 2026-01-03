import json
from pathlib import Path
import httpx

q = "What can you tell me about the scope of this solicitation and requirements. Focus on quality and not brevity."
payload = {
    "query": q,
    "mode": "mix",
    "top_k": 100,
    "chunk_top_k": 100,
    "include_chunk_content": True,
    "only_need_context": True,
}
resp = httpx.post("http://localhost:9621/query/data", json=payload, timeout=180.0)
print("status", resp.status_code)
Path(".cursor/q_scope_query_data_with_chunks.json").write_text(resp.text, encoding="utf-8")
print("wrote .cursor/q_scope_query_data_with_chunks.json")
