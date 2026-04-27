# Volume Outline Template

```
VOLUME <#>: <Title>
  Page Limit: <n>
  Format: <font, margins, citation style>
  Submission: <how, when, to whom>

  Section <id>: <Title>   [L: <instruction id>] [M: <factor id>] [Pages: n]
    - Subsection <id>: <Title>   [L: ...] [M: ...] [Pages: n]
      - Bullet evidence: <entity_id refs>
      - Required exhibit: <name>

  Section <id>: <Title>   [L: ...] [M: ...] [Pages: n]
    ...
```

Every section heading must carry both `[L: ...]` and `[M: ...]` annotations referencing real workspace entities. Sections without an L-or-M anchor are "boilerplate" and must be moved to a non-evaluated front-matter section.
