# Changelog

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
