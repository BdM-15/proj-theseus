## Simplified Detection Rules (keep extraction robust)

These rules reduce brittleness. When uncertain, **use broader types**.

### Quick rules
- **Workload / volumes / frequencies / coverage / shifts / SLAs** → keep inside `rfp_requirement.description` (do NOT invent a separate entity type).
- **Page limits / formatting / due dates / delivery instructions / forms** → `compliance_item`.
- **Factors / subfactors / weights / importance / rating scheme** → `evaluation_criterion`.
- **CDRLs / reports / plans / schedules** → `deliverable`.
- **PWS/SOW tasks / CLIN scope buckets** → `work_scope`.
- **UCF sections and attachments** → `section`.
- **Referenced standards/manuals/specs** → `document`.
- **Explicit risks/concerns** → `risk`.
- **Win themes/hot buttons** → `win_theme`; discriminators/proof points → `discriminator`.

### Shipley phase tagging
Only use `shipley_phase` if the text explicitly indicates a pursuit decision, capture planning activity, proposal development activity, or a color review (pink/red/gold).

