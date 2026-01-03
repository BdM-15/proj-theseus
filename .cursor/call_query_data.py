import json
from pathlib import Path
import httpx

url = "http://localhost:9621/query/data"
payload = {
    "query": "Elaborate on the service areas and what needs to be accomplished in order to be successful. Be educational and do not speak in shorthand.",
    "mode": "mix",
    "top_k": 100,
    "chunk_top_k": 100,
    "include_chunk_content": True,
    "only_need_context": True,
}

resp = httpx.post(url, json=payload, timeout=120.0)
print("status", resp.status_code)
print(resp.text[:400])
Path(".cursor/tmp_query_data.json").write_text(resp.text, encoding="utf-8")
