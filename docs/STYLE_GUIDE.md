# Theseus UI Style Guide

> Single source of truth for visual styling in `src/ui/static/index.html` + `src/ui/static/styles/theseus.css`. Read this **before** adding or modifying any UI markup or CSS.

---

## 1. Architecture (one HTML, one CSS, no build)

| File | Role |
| --- | --- |
| `src/ui/static/index.html` | Single SPA: Tailwind CDN config + Alpine.js component `theseus()` + body markup. **No `<style>` block** — links to `theseus.css`. |
| `src/ui/static/styles/theseus.css` | All custom CSS: token `:root` block, base styles, components (`.card`, `.btn-*`, `.acc`, `.pill`, `.toast`, etc.). |
| `tailwind.config.js` (root) | **IDE-only mirror** of the inline Tailwind config in `index.html` — kept in sync so VS Code Tailwind IntelliSense works. Not loaded at runtime. |

**No build step.** Edits are picked up on hard-reload (`Ctrl+Shift+R`).

---

## 2. Hard rule: never use `@apply` in `theseus.css`

**Tailwind Play CDN does NOT process `@apply` directives in external CSS files.** It only resolves `@apply` inside an inline `<style>` block in HTML — and we no longer have one.

If you write `@apply` in `theseus.css`, the browser will silently ignore the directive and the element will be unstyled.

**Always use raw CSS** with the token variables defined in `:root` (Section 3), or the rgba triplet form for transparency (Section 4).

If you need a Tailwind utility, put it directly on the element in `index.html` as a class. If the utility is repeated across many elements, promote it to a CSS class in `theseus.css` using raw CSS.

---

## 3. Token system

All colors live as CSS custom properties at the top of `theseus.css`:

```css
:root {
  --neon-cyan: #00f0ff;
  --neon-magenta: #ff2bd6;
  --neon-lime: #00ff9c;
  --neon-amber: #ffb020;
  --neon-red: #ff3b6b;

  --ink-950: #05070d;  /* page background */
  --ink-900: #0a0e1a;
  --ink-850: #0f1422;
  --ink-800: #141a2b;
  --ink-700: #1c2338;
  --ink-600: #283151;
  --ink-card: #11172a;  /* card surface */

  --edge: #1f2a44;          /* default border */
  --edge-strong: #2c3a5e;   /* prominent border */

  --text-primary: #e6ecff;  /* body text */
  --text-300: #cbd5e1;      /* secondary */
  --text-400: #94a3b8;      /* tertiary */
  --text-500: #64748b;      /* muted */
}
```

**Naming conventions:**
- `--neon-*` — brand accent colors (high saturation, used sparingly for emphasis)
- `--ink-{950..600}` — dark surface scale (lower number = darker)
- `--edge`, `--edge-strong` — borders
- `--text-{primary,100..600,white}` — text scale (lower number = lighter)
- `--accent-purple`, `--accent-pink` — secondary accents
- `--*-soft`, `--*-bright` — variant tints of a brand color

**Usage:**
```css
.thing {
  background: var(--ink-card);
  color: var(--text-primary);
  border: 1px solid var(--edge-strong);
}
```

---

## 4. Transparency: use the `-rgb` triplet pattern

For `rgba()` values, every brand/ink color has a matching `--*-rgb` triplet variable:

```css
:root {
  --neon-cyan-rgb: 0, 240, 255;
  --neon-magenta-rgb: 255, 43, 214;
  --ink-900-rgb: 10, 14, 26;
  /* ... */
}
```

Use the triplet inside `rgba()`:

```css
.glow {
  background: rgba(var(--neon-cyan-rgb), 0.1);
  border: 1px solid rgba(var(--neon-cyan-rgb), 0.4);
  box-shadow: 0 0 18px rgba(var(--neon-cyan-rgb), 0.25);
}
```

This keeps a **single source of truth for the RGB value** — change the brand color in one place and every transparency variant updates.

**Do NOT** invent new hex literals for "lighter" or "transparent" versions of an existing brand color. Use the triplet + alpha.

---

## 5. Adding new CSS

### When to use Tailwind utilities (in `index.html`)
- One-off layout (flex, grid, spacing, sizing)
- Spacing tokens (`p-4`, `gap-2`, `mt-3`)
- Responsive variants (`sm:*`, `lg:*`)
- State variants (`hover:*`, `focus:*`) for simple cases

### When to write raw CSS (in `theseus.css`)
- Reusable components (any pattern used in 3+ places)
- Custom animations / keyframes
- Complex `box-shadow` stacks
- Anything involving brand color tokens (use `var(--*)`)
- Pseudo-elements (`::before`, `::after`)

### Adding a new color token
1. Add the variable to `:root` in `theseus.css`
2. Add the matching `--*-rgb` triplet if you'll use it in `rgba()`
3. Mirror the change in the `tailwind.config` script tag inside `index.html` (and `tailwind.config.js`) if you need a Tailwind utility for it
4. Document the semantic meaning in this file

---

## 6. Existing component patterns

| Pattern | Class | Notes |
| --- | --- | --- |
| Card surface | `.card` | Gradient + edge-strong border + soft shadow |
| Card with hover lift | `.card-hover` | Adds cyan glow + translateY on hover |
| Primary button | `.btn` + `.btn-primary` | Cyan-tinted bg, cyan border, glow on hover |
| Ghost button | `.btn` + `.btn-ghost` | Transparent, slate-300 text, white-on-hover |
| Soft button | `.btn` + `.btn-soft` | Edge-strong border, cyan-on-hover |
| Danger button | `.btn` + `.btn-danger` | Red-tinted |
| Warning button | `.btn` + `.btn-warn` | Amber-tinted |
| Accordion section | `details.acc` | Card surface + chevron rotation when `[open]` |
| Status pill | `.pill` | Small mono caps badge, gap-1.5, rounded-md |
| Icon container | `.icon-tile` | 40x40 square with subtle inner glow |
| Toast | `.toast` | Fixed top-right card with cyan glow |

When extending, follow the existing visual language: dark surfaces, neon accents (cyan primary, magenta secondary), glowing borders/shadows for emphasis.

---

## 7. Mojibake prevention

UI text containing non-ASCII characters (`·`, `→`, `↔`, `—`, smart quotes, ellipses) **must** be saved as UTF-8 without BOM round-tripping through Windows-1252.

**If you see `Â·`, `â†'`, `â€"` or similar in the rendered UI**, it means a tool re-encoded the file. To repair:

```python
# Targeted repair (preferred — surgical)
text = text.replace('\u00c2\u00b7', '\u00b7')      # · middle dot
text = text.replace('\u00e2\u2020\u2019', '\u2192') # → right arrow
text = text.replace('\u00e2\u20ac\u201d', '\u2014') # — em dash
# (full pattern list lived in fix_mojibake.py during Phase 1)
```

**Editor settings:** VS Code → save as UTF-8 (no BOM). PowerShell → `Out-File -Encoding utf8` always.

---

## 8. Quick reference: do / don't

| Do | Don't |
| --- | --- |
| `color: var(--neon-cyan)` | `color: #00f0ff` |
| `background: rgba(var(--neon-cyan-rgb), 0.4)` | `background: rgba(0, 240, 255, 0.4)` |
| Raw CSS in `theseus.css` | `@apply` in `theseus.css` |
| Tailwind utilities for layout | Custom CSS for one-off margins |
| Hard-reload after CSS edits | Restart server for CSS edits |
| UTF-8 (no BOM) | `Out-File` without `-Encoding utf8` |

---

_Last updated: Phase 2 (issue #86)_
