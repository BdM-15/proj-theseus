# Black-Hat One-Pager — canonical structure (Phase 4d)

Use this template once per competitor (incumbent + top 3 likely). Every
non-trivial claim cites either an `award_id` (USAspending
`generated_internal_id`) or a `chunk_id` (Theseus KG). Anything you cannot
cite goes in `claim_gaps`, NOT in the body.

```
COMPETITOR: <recipient name>
ROLE: incumbent | likely-1 | likely-2 | likely-3
RECIPIENT_HASH: <from get_recipient_profile>
PARENT_RECIPIENT: <parent name or "self">
BUSINESS_TYPES: <e.g. "Large Business, For-Profit Organization">

LAST 3 WINS IN THIS NAICS / AGENCY:
  1. <agency> · $<amount> · <pop_end> · [award:<id>]
  2. ...
  3. ...

PREDICTED THEMES (anchored to award history):
  1. <verb-led theme> — evidence: [award:<id>], [award:<id>]
  2. <verb-led theme> — evidence: [award:<id>]
  3. ...

CLAIM GAPS (what we cannot verify with USAspending alone):
  - CPARS performance ratings — no MCP source yet
  - Protest history — no MCP source yet
  - Recent news / leadership changes — no MCP source yet
  - Teaming intent on this specific opportunity — qualitative, requires capture-team intel

GHOST LANGUAGE HOOKS (for proposal-generator):
  - <hook 1 — short, evaluator-friendly phrase>
  - <hook 2>

NOTES FOR USER (manual research):
  - <thing the user should look up before red team>
```

Fill ONLY the fields you have evidence for. Drop the line entirely if
empty rather than emit a "TBD" — `proposal-generator` consumes this and
treats placeholder strings as content.
