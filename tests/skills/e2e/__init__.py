"""End-to-end skill smoke tests.

Hits a running Theseus server's `/api/ui/skills/{name}/invoke` endpoint with
the active workspace pointed at a known-good processed RFP (default
``doj_mmwr_old_rfp``). Validates the full tool-calling loop, transcript
capture, and artifact emission.

Gated by ``RUN_SKILL_E2E=1`` AND a reachable server. Skips cleanly otherwise
so CI / fresh clones do not fail.

See ``README.md`` in this directory for setup.
"""
