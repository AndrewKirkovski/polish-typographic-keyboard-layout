# Szpargalka Sans — browser font injectors

Three ways to force Szpargalka Sans (Polish → Cyrillic pronunciation hints)
onto any webpage, ranked from easiest to most featured.

| Path | What you install | Effort | Best for |
|---|---|---|---|
| [Stylus user CSS](./stylus/) | Stylus extension + one user-style click | 1 min | Anyone who already uses Stylus |
| [Tampermonkey user script](./tampermonkey/) | Tampermonkey + one script install | 2 min | Power users who already have Tampermonkey |
| [Chrome MV3 extension](./chrome-mv3/) | Unpacked Chrome extension (not published to store) | 5 min | Standalone install with a popup toggle and per-site overrides |

All three do the same thing at their core: inject an `@font-face` declaration
that loads Szpargalka Sans, then apply it via `* { font-family: ... !important }`
with code/icon-font exclusions so page chrome stays legible.

## Toggle model

All three variants are **strictly manual on/off**. Earlier revisions tried to
auto-detect Polish pages via `<html lang>` sniffing and letter-density checks,
but in practice the false positives and mis-identified mixed-language pages
made the font feel intrusive. The current rule is simpler: you flip it on
when you want pronunciation hints, and flip it off otherwise.

| Variant | Toggle mechanism |
|---|---|
| Stylus | Stylus's own popup toggle enables or disables the installed user-style. No custom UI inside the style itself. |
| Tampermonkey | Single menu entry via `GM_registerMenuCommand` — ships disabled, one click flips to enabled and reloads. |
| Chrome extension | Popup with a binary `On / Off` global toggle (default **Off**) and an optional per-site override showing the active tab's hostname. |

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
2. Open `stylus/szpargalka-sans.user.css` in your browser — Stylus auto-detects
   the `==UserStyle==` header and offers to install. Or copy the contents and
   paste them into Stylus → *Manage* → *Write new style* → *Save*.
3. The user-style ships enabled after install. Click it off in the Stylus
   popup whenever you don't want it; Stylus's own on/off is the toggle —
   there's no custom UI inside the style.

### Tampermonkey

1. Install the [Tampermonkey extension](https://www.tampermonkey.net/).
2. Open `tampermonkey/szpargalka-sans.user.js` in your browser — Tampermonkey
   auto-detects the `==UserScript==` header and offers to install.
3. The script ships **disabled**. Click the Tampermonkey icon → hover
   *Szpargalka Sans* → click the menu entry to flip it on; click again to
   flip it off. The menu entry shows the current state (`✓ On` / `  Off`)
   and reloads the tab on change.

### Chrome extension (unpacked)

1. If `chrome-mv3/font-data.js` isn't already present (it's committed to
   the repo so it usually is), regenerate it from `dist/SzpargalkaSans-Regular.ttf`:
   ```bash
   node extensions/chrome-mv3/build-font.mjs
   ```
2. Open `chrome://extensions` → enable **Developer mode** (top right) →
   click **Load unpacked** → select the `extensions/chrome-mv3/` folder.
3. Click the extension's toolbar icon. The popup has two sections:
   - **This site** — per-site override showing the active tab's
     hostname. Toggle *Default / Force on / Force off* to override the
     global setting for just this site. "Default" clears the override
     and falls back to the global toggle below.
   - **Global default** — a binary `On / Off` radio (defaulting to **Off**).
     The extension ships silent so flipping it on is an explicit opt-in.
   Both changes re-apply in the active tab immediately — no reload.

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
