# Planned Data Sources (competitive-intel)

| Source                    | Auth               | Coverage                            | Rate limit               |
| ------------------------- | ------------------ | ----------------------------------- | ------------------------ |
| SAM.gov Opportunities API | API key (free)     | Active and historical solicitations | ~1000/hr                 |
| SAM.gov Entity API        | API key (free)     | Vendor registration data            | ~1000/hr                 |
| USAspending API           | None (public)      | Award amounts, recipients, NAICS    | Unrestricted (be polite) |
| FPDS-NG ATOM              | None (public)      | Procurement actions, modifications  | ~10/sec                  |
| GSA eLibrary scraping     | None (public, ToS) | Schedule contractors, SINs          | Throttle 1 req/sec       |
| CPARS (gated)             | DoD CAC + role     | Performance ratings                 | N/A — manual export only |

## Implementation Notes (TODO)

- Cache aggressively — daily refresh is fine for awards >30 days old.
- Strip PII before storing.
- Never call from a user-facing thread; queue to a background worker.
