# Project: Kirkouski Typographic Keyboard Layout

## Architecture

JSON-driven build pipeline that takes Ilya Birman's Typography Layout as a
base, applies per-language overlay changes (Polish diacritics, Russian-specific
symbols, moved typographic characters), and produces installable keyboard
layouts for Windows and macOS.

### Data flow

All platform outputs derive from the same `*_full.json` — the single source
of merged layout data.

```
SOURCE OF TRUTH (committed, manually edited):
  Birman .keylayout files (upstream baseline)
  *_typographic.json (overlay — what Kirkouski changes)

MERGE STEP:
  extract_base.py  →  *_typographic_full.json (generated, tracked)

ALL PLATFORM OUTPUTS READ *_full.json:
  build_keylayout.py   →  dist/*.keylayout (macOS)
  build_macos_bundle.py →  build/macos/*.bundle
  build_kbd_c.py        →  build/*.c  (Windows DLL, via layout_adapter.py)
  compile_kbd.py        →  dist/windows/*.dll
  build_klc.py          →  dist/*.klc (MSKLC legacy, via layout_adapter.py)
```

`build.py` orchestrates all of the above. For development, individual scripts
can be run standalone.

## Python scripts (repo root)

### Build pipeline

| Script | Purpose | Input | Output |
|--------|---------|-------|--------|
| `build.py` | Top-level orchestrator | command-line args | everything in `dist/` |
| `extract_base.py` | Parse Birman keylayouts + apply overlay JSONs | `*_typographic.json` + Birman `.keylayout` | `*_typographic_full.json` |
| `build_keylayout.py` | Generate macOS keylayout XML | `*_full.json` | `dist/*.keylayout` |
| `build_macos_bundle.py` | Package keylayouts + icons into macOS bundle | `dist/*.keylayout` + icons | `.bundle` |
| `build_kbd_c.py` | Generate C source for Windows DLL | `*_full.json` (via `layout_adapter.py`) | `build/*.c` |
| `compile_kbd.py` | Compile C source to DLL via MSVC | `build/*.c` | `dist/windows/*.dll` |
| `build_klc.py` | Generate Windows KLC files (legacy) | `*_full.json` (via `layout_adapter.py`) | `dist/*.klc` |
| `layout_adapter.py` | Shared module: convert macOS-centric full JSON to flat Windows layers + dead key tables | (imported by build_kbd_c.py, build_klc.py) | — |

### Dev/QA tools

| Script | Purpose | Usage |
|--------|---------|-------|
| `diff_keylayouts.py` | Compare two keylayout files (XML or JSON), decode keycodes to key labels | `python diff_keylayouts.py <file_a> <file_b> [--layer N] [--keys-only] [--json]` |
| `validate_keylayout.py` | Check for orphan dead keys, missing terminators, multi-char leaks, undefined actions | `python validate_keylayout.py dist/*.keylayout` |
| `polish_liga.py` | Generate pronunciation fonts with Cyrillic or IPA hints above Polish digraphs. Input: `NotoSans-Regular.ttf` (bundled in `scripts/assets/fonts/`). Output: `dist/SzpargalkaSans-Regular.ttf` (Cyrillic), `dist/PolishPhoneticsSans-Regular.ttf` (IPA). Requires `fonttools`. | `python polish_liga.py --variant cyrillic\|ipa --input scripts/assets/fonts/NotoSans-Regular.ttf [--output path.ttf] [--dry-run]` |
| `build_pdf.py` | Render printable A4 landscape PDF reference sheets showing all four layers on each key. Requires `reportlab`; optional `qrcode` for QR code. | `python build_pdf.py [--layout polish\|russian] [--style color\|bw]` |

## Key data files

| File | Role | Tracked? |
|------|------|----------|
| `polish_typographic.json` | Polish overlay — defines which keys differ from Birman | Yes |
| `russian_typographic.json` | Russian overlay — defines which keys differ from Birman | Yes |
| `polish_typographic_full.json` | Complete merged layout (regenerable artifact) | Yes |
| `russian_typographic_full.json` | Complete merged layout (regenerable artifact) | Yes |
| `English ... Ilya Birman Typography.keylayout` | Birman upstream (base for Polish) | Yes |
| `Russian ... Ilya Birman Typography.keylayout` | Birman upstream (base for Russian) | Yes |
| `VERSION` | Single version source — propagates to all build outputs | Yes |

## Overlay JSON format

Each overlay JSON has `layers.altgr`, `layers.shift_altgr`, `layers.base`,
`layers.shift`. Each entry is either:

- **Object** `{"char": "...", "name": "...", "source": "..."}` — override this
  key with the given character. Source values: `"BI"` (Birman original, kept
  as-is), `"PL"` / `"RU"` (language-native), `"MOVE"` (relocated from another
  position), `"KI"` (Kirkouski addition).
- **`null`** — intentionally unassigned. The key is removed from that layer
  (pressing it does nothing). Used in Russian for positions where Polish has
  native diacritics.
- Dead keys use `"char": "dk:state_name"` prefix.

### caps+altgr (km=5) derivation

Birman's caps+altgr layer is an independent Latin-typographic layer, NOT a
mirror of shift+altgr. The extractor only overrides km=5 for keys with
non-`"BI"` source in shift_altgr. For `"BI"` entries and `null` entries,
Birman's original km=5 values are preserved.

## Common build commands

```bash
# Full pipeline rebuild (after editing overlay JSONs)
python extract_base.py
python build_keylayout.py
python build_macos_bundle.py

# Validate generated files
python validate_keylayout.py dist/*.keylayout

# Compare against Birman baseline
python diff_keylayouts.py <birman.keylayout> dist/russian_typographic.keylayout

# Build everything for release
python build.py

# Web frontend
cd web && pnpm dev      # dev server
cd web && pnpm build    # production build
```

## Known gotchas

- **Apple's keylayout parser is not a compliant XML parser.** Named entities
  (`&lt;`, `&gt;`) in attribute values are NOT decoded — use numeric char refs
  (`&#x003C;`). `build_keylayout.py` handles this.
- **XML 1.1 declaration** — Python's stdlib `xml.etree` cannot parse XML 1.1.
  The parsers in `diff_keylayouts.py` and `validate_keylayout.py` downgrade to
  1.0 and handle control-char placeholders manually.
- **Orphan dead key states** crash macOS layout registration silently. The
  `validate_keylayout.py` script catches these. Always validate before
  deploying to Mac.
- **`str.upper()` on `ß` returns `"SS"` (two chars).** The extractor
  previously used `.upper()` to derive caps+altgr — now it copies from the
  explicit `shift_altgr` layer instead. Never use `.upper()` for key output
  derivation.
- **Birman keylayout filenames contain en-dashes** (`–` U+2013) which get
  mojibaked on Windows (displayed as `ÔÇô`). Use `os.listdir()` + startswith
  filtering instead of hardcoding filenames.

## Version bump checklist

When bumping VERSION, follow this exact sequence:

1. **Edit `VERSION`** file (single source of truth)
2. **Search for old version** — `grep -rn "v0.X" --include="*.json" --include="*.py" --include="*.iss" --include="*.md" .`
   Update any hardcoded fallback versions (e.g., `installer.iss` default VERSION define,
   overlay JSON `name` fields)
3. **Rebuild everything:**
   ```bash
   python extract_base.py
   python build_keylayout.py
   python build_macos_bundle.py
   python build_kbd_c.py
   python compile_kbd.py
   python build_klc.py
   pip install reportlab qrcode fonttools
   python build_pdf.py --layout all --style all
   python polish_liga.py --variant cyrillic --input scripts/assets/fonts/NotoSans-Regular.ttf
   python polish_liga.py --variant ipa --input scripts/assets/fonts/NotoSans-Regular.ttf
   python validate_keylayout.py dist/*.keylayout
   cd scripts/assets && pnpm build    # icons, OG images, diagrams
   cd web && pnpm build               # web frontend + prerender
   ```
4. **Verify no old version remains** — repeat the grep from step 2
5. **Commit, tag, push** — `git commit`, `git tag -a vX.Y`, `git push --tags`
6. **Verify release** — check GitHub Actions builds, release artifacts

## Layout identifiers (macOS)

- Bundle ID: `com.kirkouski.keyboardlayout.typographic`
- Polish keyboard ID: `-19876`
- Russian keyboard ID: `-19877`
- Birman Russian ID: `-31553` (no conflict)
