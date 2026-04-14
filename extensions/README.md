# Szpargalka Sans — browser font injectors

Three ways to force Szpargalka Sans (Polish → Cyrillic pronunciation hints)
onto any webpage, ranked from easiest to most featured.

| Path | What you install | Effort | Best for |
|---|---|---|---|
| [Stylus user CSS](./stylus/) | Stylus extension + one user-style click | 1 min | Anyone who already uses Stylus |
| [Tampermonkey user script](./tampermonkey/) | Tampermonkey + one script install | 2 min | Power users who already have Tampermonkey |
| [Chrome MV3 extension](./chrome-mv3/) | Unpacked Chrome extension (not published to store) | 5 min | Standalone install with a popup toggle |

All three do the same thing at their core: inject an `@font-face` declaration
that loads Szpargalka Sans, then apply it via `* { font-family: ... !important }`
with code/icon-font exclusions so page chrome stays legible.

## Detection modes

All three variants support some form of "only activate on Polish pages"
behaviour. Szpargalka Sans is a *pedagogical* font — its OpenType ligatures
replace Polish digraphs (`sz`, `cz`, `rz`, `szcz`, …) with Cyrillic glyphs
for pronunciation hints — so leaving it on for English, German, or code sites
is noise. The default is **Polish pages only**.

| Variant | Toggle mechanism |
|---|---|
| Stylus | Two separate user-styles (install whichever you want): `szpargalka-sans-polish.user.css` or `szpargalka-sans-everywhere.user.css` |
| Tampermonkey | In-menu toggle via `GM_registerMenuCommand` — 3-way switch |
| Chrome extension | Popup with a 3-way radio: *Polish only / Everywhere / Off* |

## How "Polish" is detected

- **Primary signal**: `<html lang="pl">` (matches `pl`, `pl-PL`, `pl_PL`, etc.)
- **Secondary** (Tampermonkey / Chrome only — not available in CSS): text-density
  sniff — count occurrences of the nine uniquely-Polish letters `ą ć ę ł ń ó ś ź ż`
  in the visible body text. If they make up >2% of characters, it's Polish.
  This catches sites like Reddit and X that don't set `lang` correctly.

## Ignored elements

All three variants preserve:

- `<code>`, `<pre>`, `<kbd>`, `<samp>`, `<tt>` — monospace for source code
- FontAwesome (`[class*="fa-"]`), Material Icons (`.material-icons`,
  `.material-symbols-outlined`), Bootstrap Icons (`i.bi`), Glyphicons,
  GitHub Octicons — icon fonts stay intact

If you spot a site where icons break, open an issue with a screenshot and
we'll add the selector.

## The font

All three reference the same TTF file hosted at
<https://polish-typographic.com/fonts/SzpargalkaSans-Regular.ttf>. Stylus
and Tampermonkey fetch it once over HTTPS (Tampermonkey then caches it
locally as base64 forever). The Chrome extension ships with the font
embedded as a base64 data URI inside `font-data.js` — no network round-trip,
works offline.

## Install

### Stylus

1. Install the [Stylus extension](https://chromewebstore.google.com/detail/stylus/clngdbkpkpeebahjckkjfobafhncgmne).
2. Open `stylus/szpargalka-sans-polish.user.css` or
   `stylus/szpargalka-sans-everywhere.user.css` in your editor, copy the
   contents, then in the Stylus popup → *Manage* → *Write new style* →
   paste → *Save*. Polish-only and Everywhere are separate styles; install
   whichever fits, or both and toggle between them.

### Tampermonkey

1. Install the [Tampermonkey extension](https://www.tampermonkey.net/).
2. Open `tampermonkey/szpargalka-sans.user.js` in your browser — Tampermonkey
   auto-detects the `==UserScript==` header and offers to install.
3. Click the Tampermonkey icon → `Szpargalka Sans — ...` menu to toggle
   between *Polish pages only* / *Everywhere* / *Off*. The menu entries
   show a ✓ next to the current mode.

### Chrome extension (unpacked)

1. If `chrome-mv3/font-data.js` isn't already present (it's committed to
   the repo so it usually is), regenerate it from `dist/SzpargalkaSans-Regular.ttf`:
   ```bash
   node extensions/chrome-mv3/build-font.mjs
   ```
2. Open `chrome://extensions` → enable **Developer mode** (top right) →
   click **Load unpacked** → select the `extensions/chrome-mv3/` folder.
3. Click the extension's toolbar icon. The popup shows a 3-way radio:
   *Polish pages only / Everywhere / Off*. Pick one and the active tab
   re-applies immediately — no reload needed.

## Known quirks

- **`letter-spacing` disables OpenType ligatures.** Any non-zero
  letter-spacing tells the text shaper to stop combining glyphs, which
  kills the `sz` → `ш` substitutions that are the entire point. All three
  variants force `letter-spacing: 0 !important` on the overridden elements
  to restore ligature shaping.
- **Icon fonts and `<code>` blocks are preserved.** FontAwesome, Material
  Icons, Bootstrap Icons, Octicons, and monospace code containers keep
  their original font-family via `revert !important` in the exclusion
  selector list.
- **Strict `font-src` CSP sites** may block the embedded data URI in the
  Chrome extension (~5% of the web — banks, some enterprise portals). The
  Stylus and Tampermonkey variants load the font over HTTPS from
  `polish-typographic.com` and are not affected.
- **Canvas-rendered text** (Google Docs, Figma, Sheets) cannot be
  overridden by any of these — those apps rasterise text into bitmaps
  before the font layer even sees it.
- **Closed shadow DOM** — a handful of sites with web-component UIs use
  closed shadow roots that content scripts can't inject CSS into. Rare in
  the wild.
