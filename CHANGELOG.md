# Changelog

## v0.3

### Fixed: macOS layouts now actually appear in System Settings

The biggest fix in this release. v0.1 and v0.2 shipped loose `.keylayout` files that silently failed to register on Sonoma / Sequoia for two reasons:

1. **ID collision with the upstream Birman layouts.** Our generated keylayouts inherited Birman's `<keyboard id>` values (`-9876`, `-31553`) directly from the source JSON. macOS caches keyboard layouts by id — if Birman was ever installed, ours got dropped as duplicates. Now overridden at build time to `-19876` (Polish) and `-19877` (Russian).
2. **No `.bundle` wrapping.** Loose `.keylayout` files in `~/Library/Keyboard Layouts/` are unreliable on modern macOS, land in the "Others" category, and have no icon or localized name. v0.3 ships a proper `Kirkouski Typographic.bundle` with `Info.plist` (`KLInfo_*` per layout), `version.plist`, and `en.lproj/InfoPlist.strings` — matching Apple's canonical structure (verified against the Ilya Birman reference bundle).

### New: cross-platform asset pipeline (`scripts/assets/`)

Added a Node-based pipeline that generates every visual asset in the project from a single source of truth:

- **macOS icons** — three `.icns` files (Polish red, Russian blue, US+POL darker red), one per variant. The italic "K" glyph is extracted at build time from `DMSerifDisplay-Italic.ttf` (committed under `scripts/assets/fonts/`, OFL-1.1) and baked into the SVG as a vector path. Zero font dependency at render time. SVG → PNG via `@resvg/resvg-js`, packed into `.icns` via a hand-rolled writer.
- **Web favicons** — `favicon.svg`, `favicon.ico` (16/32/48), `favicon.png` (32), `apple-touch-icon.png` (180), all rebuilt from the canonical Polish brand icon. Hand-rolled `.ico` writer (no fragile npm packers).
- **OG image** — `og-template.html` moved into the repo (`scripts/assets/templates/`), parameterised by version, rendered via Playwright at retina (`deviceScaleFactor: 2`).

Run with `pnpm --dir scripts/assets build` or `python build.py assets`.

### New: single source of truth for version

The repo-root `VERSION` file is now the only place to bump versions. `build.py`, `build_kbd_c.py`, `build_macos_bundle.py`, `extract_base.py`, `installer.nsi` (via `/DVERSION`), `web/vite.config.ts` (via `transformIndexHtml` + `define __APP_VERSION__`) all read it.

### Other

- Loose `.keylayout` files still ship in `dist/macos-vX.Y/` as a fallback for users who prefer manual install.
- README install steps rewritten for the bundle path, with the `xattr -dr com.apple.quarantine` clear and the Sequoia login-screen caveat documented.

## v0.2

### New: US+POL Typographic variant (Windows)

Added a new keyboard layout variant — **US+POL Typographic by Kirkouski** (`ustypo.dll`) — that registers under the English (US) locale instead of Polish.

This is for users who want Polish typographic characters (em dashes, curly quotes, Polish diacritics via AltGr, etc.) but prefer to keep English as their Windows system language. The key mappings are identical to the Polish Typographic layout — only the language association differs.

- **DLL:** `ustypo.dll`
- **Locale:** English (US) — `en-US` / `0409`
- **Key mappings:** Same as Polish Typographic (`pltypo.dll`)
- **Platform:** Windows only (macOS keylayouts aren't tied to a system language, so the existing Polish Typographic keylayout already works regardless)

### Website

- Compact hero section — keyboard layout is now visible above the fold
- Share buttons (X, Facebook, LinkedIn, Reddit, copy link) with native Web Share API support
- Ko-fi support link and GitHub stars call-to-action

### Other changes

- Updated installer (`install.ps1`, `installer.nsi`) to support the new variant
- Build pipeline now accepts `us` as a layout target (`python build.py windows us`)

## v0.1

Initial release.

- Polish Typographic and Russian Typographic keyboard layouts
- Windows DLL build pipeline (JSON → C → MSVC → DLL)
- macOS .keylayout build pipeline
- KLC fallback generator
- NSIS installer for Windows
- PowerShell installer/uninstaller (`install.ps1`)
- Vue 3 web frontend with interactive layout explorer
- i18n support (English, Polish, Russian)
