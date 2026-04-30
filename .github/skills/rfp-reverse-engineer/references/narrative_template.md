# RFP Reverse-Engineer — Capture-Team Narrative Template

**Purpose:** Lower the degree of freedom in step 10 of `SKILL.md`. The model fills in this exact bullet skeleton. Every bullet is one of two forms:

- **Class A bullet** (factual): ends with `[see <jsonpath>.source_chunk_ids]` (cheapest), `[chunk-xxxx]`, `[entity: <Name>]`, or `[per references/<file>.md]`.
- **Class B bullet** (judgment): begins with one of the visible-judgment markers — `**Our read:**`, `**In our capture experience,**`, `**Likely …**`, `**Classic … pattern —**`, `**Rule of thumb:**`.

**No paragraphs.** **No bullet without one of those tail-anchors or lead-markers.** If you cannot honestly anchor or honestly frame as judgment, drop the bullet.

The `<jsonpath>` form is the cheapest and the audit trusts it because the JSON envelope is on disk with `source_chunk_ids` arrays on every entry. Use it whenever you are summarizing something the JSON already cited.

---

## Template (fill literally)

```markdown
# RFP Reverse-Engineering Brief — <solicitation_id>

## 1. Inferred contract type & posture
- The CO published a <SOW|PWS> — <one-line signal> [see inferred_intake_answers.sow_or_pws.source_chunk_ids].
- Contract type is <FFP|T&M|CR|hybrid> — <one-line signal> [see inferred_intake_answers.contract_type.source_chunk_ids].
- Commercial status: <commercial|non-commercial> [see inferred_intake_answers.commercial_status.source_chunk_ids].
- **Our read:** <2-line judgment on what this posture rewards in our cost stack and bid strategy.>

## 2. Top hot buttons (max 5)
- HB-001 <label> [see hot_buttons[0].source_chunk_ids] — discriminator: <one-line play>.
- HB-002 <label> [see hot_buttons[1].source_chunk_ids] — discriminator: <one-line play>.
- HB-003 <label> [see hot_buttons[2].source_chunk_ids] — discriminator: <one-line play>.
- **In our capture experience,** <one-line pattern that ties HB-001..003 together.>

## 3. Top discriminator hooks (max 5)
- DH-001 on <evaluation_factor> — hook phrase "<phrase>" [see discriminator_hooks[0].source_chunk_ids] — proposal play: <one-line>.
- DH-002 on <evaluation_factor> — hook phrase "<phrase>" [see discriminator_hooks[1].source_chunk_ids] — proposal play: <one-line>.
- **Our read:** <one-line on which hook is the highest-leverage win-theme anchor.>

## 4. Top ghost-language risks (max 5)
- GL-001 "<phrase>" in <section> [see ghost_language[0].source_chunk_ids] — risk: <one-line>; Q&A action: <one-line>.
- GL-002 "<phrase>" in <section> [see ghost_language[1].source_chunk_ids] — risk: <one-line>; Q&A action: <one-line>.
- **Likely** the CO will <one-line on which gap they will close themselves vs leave open.>

## 5. CO errors detected
- FAR 52.237-2 trap: <status> [see key_personnel_clause_check] — recommended clause: <agency-appropriate alternative>.
- CPFF form ambiguity: <status> [see cpff_form_signal] — Q&A action: <one-line>.
- QASP↔CPARS confusion: <status> [see qasp_cpars_check] — recommended remedy: <one-line>.
- **Our read:** <one-line on what these errors signal about CO sophistication and amendment likelihood.>

## 6. Missing-section signals
- Section <N> absent — likely meaning: <one-line per the catalog inference table> [see missing_sections[0]].
- Section <N> absent — likely meaning: <one-line> [see missing_sections[1]].

## 7. Top clarification questions to file
- Q1: <one-line question> [see clarification_questions[0]].
- Q2: <one-line question> [see clarification_questions[1]].
- Q3: <one-line question> [see clarification_questions[2]].
- Q4: <one-line question> [see clarification_questions[3]].
- Q5: <one-line question> [see clarification_questions[4]].

## 8. Hand-off to proposal-generator
- Decision tree blocks 1–6 ready in `artifacts/rfp_reverse_engineering.json` [see decision_tree_reconstruction].
- Hot buttons + discriminator hooks ready to seed win themes [see hot_buttons, discriminator_hooks].
- Open clarifications flagged for the next Q&A round [see clarification_questions].
- **Our read:** <one-line on what proposal-generator should prioritize first when consuming this envelope.>
```

---

## Self-audit regex (apply mentally before returning)

Each line that begins with `- ` (bullet) MUST satisfy ONE of:

1. Ends with `]` (anchor tag — `[see …]`, `[chunk-…]`, `[entity: …]`, `[per references/…]`)
2. Begins with `- **Our read:**`, `- **In our capture experience,**`, `- **Likely`, `- **Classic`, `- **Rule of thumb:**`

If neither matches: rewrite to add an anchor (look up the path in the JSON envelope) OR demote to a Class B bullet with a marker OR delete the bullet. **Do not** invent chunk ids. **Do not** add a marker to a sentence that is actually a Class A fact (transparent and produces a worse brief).

Headings (`#`, `##`) and code fences are exempt.
