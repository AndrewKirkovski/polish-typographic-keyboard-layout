# Keyboard Layout Development Checklist

Reference checklist for building production-ready keyboard layouts for Windows and macOS.
Derived from real issues encountered during development of Kirkouski Typographic layouts.

---

## Layout Design

- [ ] All key positions documented (base, shift, AltGr, Shift+AltGr)
- [ ] Conflict analysis between source layouts complete (e.g., Polish diacritics vs Birman typographic)
- [ ] Displaced characters relocated to mnemonic or logical positions
- [ ] Dead keys defined with full composition tables (every base char + space terminator)
- [ ] Ligatures defined for multi-character outputs (e.g., fraction sequences ½ ⅓ ¼)
- [ ] CapsLock behavior specified per key:
  - Letters: CAPLOK (CapsLock = Shift for base/shift)
  - AltGr diacritics: CAPLOKALTGR (CapsLock also affects AltGr layer — e.g., CapsLock+AltGr+E = Ę)
  - Non-letters: no CapsLock effect
- [ ] No unintentional duplicate characters across shift states (e.g., $ on both Shift+4 and AltGr+4)
- [ ] AltGr/Shift+AltGr chars that match base/shift are intentional or removed
- [ ] All characters verified as valid Unicode (no PUA, no unassigned codepoints)
- [ ] Dead key accent + Space produces the accent character itself

## JSON Source Files

- [ ] Overlay JSON has all 4 layers: `base`, `shift`, `altgr`, `shift_altgr`
- [ ] Dead keys encoded as `"dk:name"` (not raw Unicode)
- [ ] Ligatures are multi-char strings (e.g., `"¹⁄₂"`)
- [ ] Null entries mean "no mapping" (key produces nothing in that layer)
- [ ] Full JSON (macOS) contains complete structure: all 9 keyMap indices, all actions, terminators
- [ ] Base/shift layers use plain strings; altgr/shift_altgr use `{char, name, source}` objects

## Windows — KLC Generation (build_klc.py)

- [ ] Output is UTF-16 LE with BOM
- [ ] Line endings are `\r\n`
- [ ] Tabs separate columns (not spaces)
- [ ] SHIFTSTATE section defines states 0, 1, 2, 6, 7
- [ ] Ctrl column (state 2) is `-1` for all keys (Windows handles Ctrl+letter internally)
- [ ] Dead keys marked with `@` suffix in LAYOUT section
- [ ] Each dead key has a matching DEADKEY section
- [ ] DEADKEY sections include `0020` (space) terminator entry
- [ ] Characters outside ASCII use 4-digit hex (`00f3` not `ó`)
- [ ] KEYNAME, KEYNAME_EXT, KEYNAME_DEAD sections complete
- [ ] KBD short name ≤ 8 chars, no spaces (becomes DLL filename)
- [ ] LOCALEID matches target language (0415=Polish, 0419=Russian)

## Windows — C Source Generation (build_kbd_c.py)

- [ ] `#define KBD_TYPE 4` before includes
- [ ] Includes: `windows.h`, `kbd.h`, `dontuse.h`
- [ ] Scancode-to-VK table covers 0x00-0x7F (128 entries)
- [ ] All standard VK names used (VK_OEM_1 through OEM_8, not raw numbers)
- [ ] VK_OEM_102 (ISO extra key, scancode 0x56) included with key name
- [ ] E0-prefix extended scancodes table (Return, Ctrl, arrows, etc.)
- [ ] E1-prefix scancodes table (Pause key)
- [ ] MODIFIERS table: 4 active states (base=0, shift=1, AltGr=2, Shift+AltGr=3)
- [ ] SHFT_INVALID for unused modifier combos (Ctrl, Alt, Shift+Ctrl, Shift+Alt)
- [ ] `wMaxModBits = 7` (covers 3-bit range)
- [ ] VK_TO_WCHARS grouped by column count (VK_TO_WCHARS2, VK_TO_WCHARS4)
- [ ] Dead key entries use `WCH_DEAD` in the character column
- [ ] Dead key continuation row: VK=0xFF, single row even if multiple columns are dead
- [ ] Ligature entries use `WCH_LGTR`, matched in LIGATURE table
- [ ] LIGATURE max size ≤ 5 (LIGATURE1 through LIGATURE5 defined in kbd.h)
- [ ] `DEADTRANS(base_char, dead_char, composed_char, flags)` — argument order matches macro
- [ ] DEADTRANS table null-terminated with `{0, 0, 0}`
- [ ] KBDTABLES field order matches kbd.h exactly (16 fields)
- [ ] `fLocaleFlags = MAKELONG(KLLF_ALTGR, KBD_VERSION)` — mandatory for AltGr layouts
- [ ] `dwType = 4`, `dwSubType = 0`
- [ ] `KbdLayerDescriptor` exported via `__declspec(dllexport)` and .def file
- [ ] String resources in .rc file (layout name, language ID)
- [ ] Special keys (Space, Backspace, Escape, Return, Cancel) in VK_TO_WCHARS

## Windows — DLL Compilation (compile_kbd.py)

- [ ] MSVC Build Tools discovered via vswhere.exe
- [ ] Windows SDK discovered (Include/um for kbd.h)
- [ ] Compiler flags: `/GS-` (no buffer security), `/Zl` (no CRT), `/O1` (size), `/utf-8`
- [ ] Linker flags: `/noentry` (no DllMain), `/dll`
- [ ] Section merging: `/merge:.rdata=.data /merge:.bss=.data /merge:.text=.data`
- [ ] Section attributes: `/section:.data,re` (read + execute)
- [ ] `/ignore:4254` (suppress section merge warning)
- [ ] No CRT dependency in final DLL
- [ ] DLL exports only `KbdLayerDescriptor`
- [ ] Output DLL is 5-10 KB (typical size for keyboard layout)
- [ ] .exp and .lib byproducts cleaned up

## Windows — Installation (install.ps1)

- [ ] Admin elevation check at script start
- [ ] DLL copied to `%SystemRoot%\System32`
- [ ] Registry key created under `HKLM\...\Keyboard Layouts\a00XLLLL`
- [ ] Registry values set: Layout File, Layout Text, Layout Display Name, Layout Id
- [ ] Layout Display Name stored as REG_EXPAND_SZ (not REG_SZ) for `%SystemRoot%` expansion
- [ ] Layout Id is unique, in range 0x00C0-0x0FFF (values > 0x0FFF crash Explorer)
- [ ] Layout Id allocated by scanning all existing layouts (not just same language)
- [ ] Already-installed detection (check Layout File value, not just key name)
- [ ] DLL copy wrapped in try/catch (file may be locked if layout is active)
- [ ] Uninstall cleans: registry key, DLL, Preload entries, Substitutes entries
- [ ] Preload entries renumbered after deletion (no gaps)
- [ ] Both HKCU and HKU\.DEFAULT preload/substitutes cleaned on uninstall
- [ ] Success message only shown when layouts were actually installed
- [ ] Restart reminder after install/uninstall

## Windows — Known Pitfalls

- [ ] MSKLC-generated DLLs crash Explorer on Windows 11 — use direct C compilation instead
- [ ] Ghost registry entries from failed installs cause "name already in use" errors
- [ ] Layout Id above 0x0FFF causes Explorer crash/freeze
- [ ] Missing Layout Id on custom layouts (a-prefix registry keys) causes Explorer crash
- [ ] 32-bit apps need a separate DLL in SysWOW64 (WOW64 compatibility)
- [ ] Duplicate characters across shift states trigger MSKLC validation warnings
- [ ] Ctrl column with explicit control characters triggers "redundant" warnings — use -1

## macOS — Keylayout Generation

- [ ] XML 1.1 declaration (required for control character references like `&#x000D;`)
- [ ] DOCTYPE references Apple's KeyboardLayout DTD
- [ ] Control chars encoded as `&#xNNNN;` references, NOT literal bytes
- [ ] PUA placeholder encoding only for actual control chars (< 0x20, == 0x7F)
- [ ] Printable ASCII chars (`'`, `"`, `&`, `<`, `>`) NOT PUA-encoded
- [ ] TAB (0x09), CR (0x0D), LF (0x0A) encoded as `&#x` refs in output attributes
- [ ] All 9 keyMap indices present (base, shift, caps, option, shift+option, caps+option, option+command, control, shift+option+command)
- [ ] Secondary keyMapSet (994) for ISO/JIS keyboards included
- [ ] Actions section: dead key entry actions with `<when state="none" next="..."/>`
- [ ] Actions section: base character actions with `<when state="none" output="..."/>` + dead key state responses
- [ ] Terminators for every dead key state
- [ ] Caps+Option layer produces uppercase variants (not copied from Option)
- [ ] `maxout` attribute matches original (3 for Birman-based layouts)
- [ ] `keyboard group`, `id` attributes set
- [ ] Total key entries, actions, when clauses match the original source layout

## macOS — Installation

- [ ] .keylayout file placed in `~/Library/Keyboard Layouts/` (user) or `/Library/Keyboard Layouts/` (system)
- [ ] User must log out and back in after installing
- [ ] Layout appears in System Settings > Keyboard > Input Sources

## Visualizer / Frontend

- [ ] All keys rendered with correct base/shift/AltGr/Shift+AltGr characters
- [ ] AltGr chars that duplicate base are hidden (e.g., AltGr+[ = [ same as base)
- [ ] Shift+AltGr chars that duplicate shift are hidden
- [ ] Dead keys displayed as diacritical symbols (˜ ˆ ´ etc.), not text names
- [ ] Dead key symbol map covers all dead keys in the layout
- [ ] Tooltips show full Unicode character names
- [ ] Color coding: base (grey), AltGr (red), Polish (green), Russian (blue), dead keys (purple)
- [ ] Layout JSON loaded dynamically (not hardcoded)
- [ ] Russian layout shows Cyrillic base characters
- [ ] Modifier keys show Mac equivalents (⌘ ⌥ ⌃ ⇧)

## Testing

- [ ] Build pipeline runs end-to-end: `python build.py`
- [ ] Windows DLL installs and appears in Settings
- [ ] All Polish diacritics type correctly (ą ć ę ł ń ó ś ź ż)
- [ ] All typographic symbols type correctly (— – € © ® ™ § × « » „ " " ' ' …)
- [ ] Dead keys produce composed characters (dk:acute + e = é)
- [ ] Dead key + Space produces the accent itself
- [ ] CapsLock works with base letters
- [ ] CapsLock + AltGr produces uppercase diacritics (Ą Ć Ę etc.)
- [ ] Layout switch (Win+Space) works without issues
- [ ] Explorer does not crash after install
- [ ] Uninstall removes layout cleanly
- [ ] macOS .keylayout installs and works
- [ ] Visualizer renders both layouts correctly
