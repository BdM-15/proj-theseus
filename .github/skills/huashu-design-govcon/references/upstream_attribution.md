# Upstream Attribution — alchaincyf/huashu-design

This skill is **adapted** from the open-source `huashu-design` project at <https://github.com/alchaincyf/huashu-design>.

## What we kept

- The **Junior Designer in a senior agency** workflow framing
- The **layout-first, color-last** discipline
- The **anti-AI-slop pre-export checklist** concept
- The conversion-script idea: `html2pptx`, `html2pdf`, `render_video`
- The self-critique pass after generation

## What we changed for federal GovCon

| Upstream                   | GovCon Edition                                                   |
| -------------------------- | ---------------------------------------------------------------- |
| Vibrant marketing palettes | Conservative navy/slate/bone palette + single gold accent        |
| Hero illustrations         | Tables and bullet evidence (federal evaluators read)             |
| Brand-driven typography    | Source Serif 4 + Source Sans 3 (PDF-embeddable, royalty-free)    |
| Generic content templates  | Compliance matrix, theme card, FAB chain templates               |
| Free-form input            | Auto-injected entity slices from the active Theseus workspace KG |
| English/Chinese bilingual  | English-only with FAR/DFARS clause handling                      |

## Scripts

The `scripts/` directory ships our own thin re-implementations of `html2pptx.js`, `html2pdf.sh`, and `render_video.py`. They are not byte-equivalent to the upstream — they are adapted to:

- Read entity payloads from a `build/context.json` written by the Theseus runtime
- Embed only royalty-free fonts
- Default to letter-size, 0.75" margins, slate-on-bone palette

## License

Upstream is MIT. Our adaptation is also MIT. See repo root `LICENSE`.
