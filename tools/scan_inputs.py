"""
CLI helper for the /scan-rfp endpoint.

Usage:
    # Scan the server's current workspace
    python tools/scan_inputs.py

    # Scan a specific workspace's inputs/<workspace>/ folder
    python tools/scan_inputs.py --workspace afcapv_bos_i_t12

    # Point at a non-default server
    python tools/scan_inputs.py --host http://localhost:9621

What it does:
    POSTs to /scan-rfp on the running Theseus server. The server walks
    inputs/<workspace>/ for supported files, skips anything already in
    "processed" status, and processes the rest through the standard
    multimodal + semantic post-processing pipeline.

The server returns immediately with a track_id. Tail the server log to
watch progress (filter on `[scan <track_id>]`).
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser(description="Trigger /scan-rfp on Theseus server.")
    parser.add_argument(
        "--workspace",
        default=None,
        help="Workspace whose inputs/<workspace>/ folder to scan. "
             "Defaults to the server's current workspace.",
    )
    parser.add_argument(
        "--host",
        default="http://localhost:9621",
        help="Theseus server base URL (default: http://localhost:9621).",
    )
    args = parser.parse_args()

    url = f"{args.host.rstrip('/')}/scan-rfp"
    if args.workspace:
        url += "?" + urllib.parse.urlencode({"workspace": args.workspace})

    req = urllib.request.Request(url, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"❌ Request to {url} failed: {e}", file=sys.stderr)
        return 1

    print(json.dumps(payload, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
