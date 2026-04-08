# Kirkouski Typographic Keyboard Layout v0.1

> **[Interactive Layout Preview & Downloads](https://polish-typographic-keyboard-layout.pages.dev/)** — explore the layout, download installers, and read installation guides.

Custom keyboard layouts for **Windows** and **macOS** that add typographic symbols (em dash, curly quotes, copyright, euro, etc.) accessible via AltGr (Right Alt) on top of standard Polish Programmers and Russian ЙЦУКЕН layouts.

Based on [Ilya Birman's Typography Layout](https://ilyabirman.ru/typography-layout/). Typographic symbols are in the same positions across both language variants — switch between Polish and Russian without relearning symbol locations.

## Layouts

### Polish Typographic

![Polish Typographic Layout](screenshots/polish_layout.png)

### Russian Typographic

![Russian Typographic Layout](screenshots/russian_layout.png)

### Legend

| Position | Color | Meaning |
|----------|-------|---------|
| Bottom-left | grey | Base character |
| Top-left | dim grey | Shift |
| Bottom-right | red | AltGr (Right Alt) |
| Top-right | orange | Shift + AltGr |
| Bottom-right | green | Polish diacritics (AltGr) |
| Bottom-right | blue | Russian-specific (AltGr) |
| Top-right | purple | Dead keys (accent combiners) |

## Quick Install

### Windows

1. Download `pltypo.dll` (or `rutypo.dll`) and `install.ps1` from the latest release
2. Place both files in the same folder
3. Right-click `install.ps1` > **Run with PowerShell** (it will auto-elevate to admin)
4. Restart, then go to **Settings > Time & Language > Language & Region > Keyboard** and add the new layout

**Uninstall:** Run `.\install.ps1 -Uninstall` and restart. Use `-Layout polish` or `-Layout russian` to uninstall selectively.

**Apply to login screen & new users:** After installing and switching to the new layout, open `intl.cpl` (Win+R > `intl.cpl`) > **Administrative** tab > **Copy settings** > check both **"Welcome screen and system accounts"** and **"New user accounts"** > OK. This ensures the login screen and any new user accounts use your layout instead of the default.

**Broken install?** Run `.\install.ps1 -HardCleanup` to remove all traces (registry, DLLs, preload entries).

> **Note:** Do not use MSKLC (Microsoft Keyboard Layout Creator) to build from `.klc` files — its generated DLLs crash Windows Explorer on Windows 11. Use the direct DLL pipeline instead.

### macOS

1. Copy `dist/polish_typographic.keylayout` (or `russian_typographic.keylayout`) to `~/Library/Keyboard Layouts/` (current user) or `/Library/Keyboard Layouts/` (all users — requires `sudo`)
2. Log out and back in
3. **System Settings > Keyboard > Input Sources > + > Add** the new layout

**For the login screen:** Install to `/Library/Keyboard Layouts/` (system-wide) instead of `~/Library/Keyboard Layouts/` (user-only). The login screen only sees system-wide layouts.

## Building from Source

### Prerequisites

| Tool | Required for | Install |
|------|-------------|---------|
| Python 3.10+ | All build scripts | [python.org](https://www.python.org/downloads/) |
| Visual Studio Build Tools | Windows DLL compilation | [visualstudio.microsoft.com](https://visualstudio.microsoft.com/visual-cpp-build-tools/) |
| Windows SDK | Headers for kbd.h | Included with VS Build Tools |
| NSIS 3.x | Windows .exe installer | `winget install NSIS.NSIS` |
| Node.js 18+ / pnpm | Web frontend (optional) | [nodejs.org](https://nodejs.org/) |

When installing VS Build Tools, select the **"Desktop development with C++"** workload. This provides `cl.exe`, `link.exe`, `rc.exe`, and the Windows SDK.

NSIS is optional — if not installed, `build.py` skips the .exe installer and produces only the zip.

No external Python packages are required — the toolchain uses only the Python standard library.

### Build Commands

```bash
# Build everything (Windows DLLs + macOS keylayouts + KLC files)
python build.py

# Build specific platform
python build.py windows          # DLLs + install.ps1
python build.py macos            # .keylayout files
python build.py klc              # .klc files (for MSKLC)

# Build specific layout
python build.py windows polish
python build.py macos russian
```

### What the pipeline does

```
              build_kbd_c.py     compile_kbd.py        NSIS
Windows:  JSON ────────────> C ──────────────> DLL ──────────> setup.exe
                                                 \
                                                  └──> zip (DLLs + install.ps1)

macOS:    JSON (full) ──> build_keylayout.py ──> .keylayout ──> .pkg (macOS only)
                                                       \
                                                        └──> zip
```

### Output

`python build.py` produces everything in `dist/`:

| File | Description |
|------|-------------|
| `kirkouski-typographic-v0.1-windows-setup.exe` | NSIS installer (Add/Remove Programs, UAC) |
| `kirkouski-typographic-v0.1-windows.zip` | DLLs + install.ps1 for manual install |
| `kirkouski-typographic-v0.1-macos.zip` | .keylayout files for manual install |
| `kirkouski-typographic-v0.1-macos.pkg` | macOS installer (built on macOS only) |
| `windows-v0.1/` | Loose Windows files |
| `macos-v0.1/` | Loose macOS files |

## Project Structure

```
build.py                # Build orchestrator (single entry point)
build_kbd_c.py          # JSON -> C source generator (Windows DLL pipeline)
compile_kbd.py          # MSVC compiler wrapper (C -> DLL)
build_klc.py            # JSON -> KLC generator
build_keylayout.py      # JSON -> keylayout generator (macOS)
installer.nsi           # NSIS installer script
install.ps1             # Windows PowerShell installer/uninstaller

extract_base.py         # One-time: extract full layout from Birman originals

polish_typographic.json       # Polish layout definition (overlay)
russian_typographic.json      # Russian layout definition (overlay)
polish_typographic_full.json  # Complete macOS layout structure
russian_typographic_full.json # Complete macOS layout structure

visualizer.html         # Standalone keyboard layout viewer (legacy)
web/                    # Vue 3 frontend app (visualizer, downloads, i18n)
screenshots/            # Layout preview images
dist/                   # Build outputs (organized by platform)
build/                  # Intermediate C/obj files (gitignored)
```

## Web Frontend

The `web/` directory contains a Vue 3 + TypeScript app with an interactive keyboard visualizer, download links, install guides, and i18n (English, Polish, Russian).

```bash
cd web
pnpm install
pnpm dev        # dev server at http://localhost:5173
pnpm build      # production build to web/dist/
```

The app loads layout JSONs from the project root (via a Vite plugin in dev, copied to `public/` at build time).

## Regenerating Full JSONs

The `*_full.json` files contain the complete macOS keylayout structure extracted from the original Birman `.keylayout` files with our changes applied on top. To regenerate them:

1. Download the original layouts from [ilyabirman.ru/typography-layout](https://ilyabirman.ru/typography-layout/)
2. Place `English – Ilya Birman Typography.keylayout` and `Russian – Ilya Birman Typography.keylayout` in the project root
3. Run: `python extract_base.py`

This is only needed if you modify the overlay JSONs and want to update the macOS output.

## Troubleshooting

### Windows: Explorer crashes after install

1. Boot into Safe Mode or switch to a standard keyboard layout
2. Open `regedit` as Administrator
3. Delete the layout's registry key under `HKLM\SYSTEM\CurrentControlSet\Control\Keyboard Layouts\` (look for keys starting with `a0` whose `Layout File` matches `pltypo.dll` or `rutypo.dll`)
4. Also check and clean: `HKCU\Keyboard Layout\Preload` and `HKCU\Keyboard Layout\Substitutes`
5. Delete `C:\Windows\System32\pltypo.dll` (or `rutypo.dll`)
6. Restart

### Windows: "Layout name already in use"

Previous install left ghost registry entries. Run `.\install.ps1 -Uninstall` as admin first, restart, then reinstall.

### Windows: MSKLC won't build

Use the direct DLL pipeline instead (`python build.py windows`). It doesn't need MSKLC.

## Credits

Layout concept by [Ilya Birman](https://ilyabirman.ru/typography-layout/). Polish/Russian adaptation and open-source toolchain by Andrew Kirkouski.

## License

MIT License — see [LICENSE](LICENSE).
