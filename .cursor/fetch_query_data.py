import json
from pathlib import Path
import httpx

def fetch(query: str, out_path: str):
    payload = {
        "query": query,
        "mode": "mix",
        "top_k": 100,
        "chunk_top_k": 100,
        "include_chunk_content": False,
        "only_need_context": True,
    }
    r = httpx.post("http://localhost:9621/query/data", json=payload, timeout=120.0)
    r.raise_for_status()
    Path(out_path).write_text(r.text, encoding="utf-8")

fetch(
  "What can you tell me about the scope of this solicitation and requirements. Focus on quality and not brevity.",
  ".cursor/q_scope_query_data.json",
)
fetch(
  "Elaborate on the service areas and what needs to be accomplished in order to be successful. Be educational and do not speak in shorthand.",
  ".cursor/q_service_query_data.json",
)
print("wrote .cursor/q_scope_query_data.json and .cursor/q_service_query_data.json")
