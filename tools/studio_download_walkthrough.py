"""148 — Studio download/edit-loop walkthrough probe.

Hits each of the three artifact format families currently in the active
workspace (json, md, docx) via the same download endpoint the Studio UI
uses, and verifies the response carries the correct ``Content-Type``,
``Content-Disposition`` (attachment, server-supplied filename), and a
non-empty body. Designed to be called against a running Theseus server
on http://localhost:9621.

Not registered as a pytest case yet — it needs a live server. Becomes
``tests/skills/test_studio_download_smoke.py`` (Playwright/HTTP) once
148 confirms the click sequence is stable.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen

BASE = "http://localhost:9621"
INDEX_URL = f"{BASE}/api/ui/studio"


def fetch(url: str) -> tuple[int, dict[str, str], bytes]:
    req = Request(url)
    with urlopen(req, timeout=10) as resp:
        return resp.status, dict(resp.headers), resp.read()


def main() -> int:
    status, _, body = fetch(INDEX_URL)
    if status != 200:
        print(f"FAIL: index endpoint returned {status}")
        return 1
    payload = json.loads(body)
    rows = payload["deliverables"]
    print(f"workspace={payload['workspace']} count={payload['count']}")

    # One sample per extension
    seen: dict[str, dict] = {}
    for row in rows:
        ext = row["filename"].rsplit(".", 1)[-1].lower()
        seen.setdefault(ext, row)

    failures = 0
    for ext, row in seen.items():
        url = (
            f"{BASE}/api/ui/skills/{row['skill']}"
            f"/runs/{row['run_id']}/artifacts/{row['filename']}"
        )
        try:
            st, hdrs, content = fetch(url)
        except Exception as exc:  # noqa: BLE001
            print(f"[FAIL] .{ext}: GET raised {exc!r}")
            failures += 1
            continue

        ct = hdrs.get("Content-Type") or hdrs.get("content-type") or ""
        cd = hdrs.get("Content-Disposition") or hdrs.get("content-disposition") or ""
        cl = int(hdrs.get("Content-Length") or hdrs.get("content-length") or "0")
        expected = row["mime"]
        ok_mime = ct.split(";")[0].strip().lower() == expected.lower()
        ok_disp = "attachment" in cd.lower() and row["filename"] in cd
        ok_body = len(content) == row["size"] and len(content) > 0

        flag = "PASS" if (ok_mime and ok_disp and ok_body) else "FAIL"
        print(f"[{flag}] .{ext:6s} {row['skill']}/{row['filename']}")
        print(f"        status={st} ct={ct!r}")
        print(f"        cd={cd!r}")
        print(f"        bytes={cl} expected={row['size']} body={len(content)}")
        if not (ok_mime and ok_disp and ok_body):
            failures += 1
            if not ok_mime:
                print(f"        -> mime mismatch (expected {expected!r})")
            if not ok_disp:
                print("        -> Content-Disposition missing 'attachment' or filename")
            if not ok_body:
                print("        -> body length mismatch")

    print(f"--- {len(seen) - failures}/{len(seen)} formats passed ---")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
