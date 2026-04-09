# Kirkouski Typographic Keyboard Layout

> **[Interactive Layout Preview & Downloads](https://polish-typographic-keyboard-layout.pages.dev/)** — explore the layout, download installers, and read installation guides.

Custom keyboard layouts for **Windows** and **macOS** that add typographic symbols (em dash, curly quotes, copyright, euro, etc.) accessible via AltGr (Right Alt) on top of standard Polish Programmers and Russian ЙЦУКЕН layouts.

**Want Polish typographic symbols but keep English as your system language?** The **US+POL Typographic** variant gives you the same layout registered under English (US), so you don't need to add Polish as an input language in Windows.

Based on [Ilya Birman's Typography Layout](https://ilyabirman.ru/typography-layout/). Typographic symbols are in the same positions across both language variants — switch between Polish and Russian without relearning symbol locations.

## Layouts

### Polish Typographic

![Polish Typographic Layout](screenshots/polish_layout.png)

### Russian Typographic

![Russian Typographic Layout](screenshots/russian_layout.png)

### US+POL Typographic (Windows only)

Same as Polish Typographic, but registered under the English (US) locale. Use this if you want to keep English as your Windows system language while having all Polish typographic characters available via AltGr. The key mappings are identical — only the language association differs.

> **Note:** On macOS, keyboard layouts aren't tied to a system language, so the Polish Typographic keylayout already works regardless of your system language. The US+POL variant is only needed on Windows.

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

1. Download `pltypo.dll` (or `rutypo.dll`, or `ustypo.dll` for English system language) and `install.ps1` from the latest release
2. Place both files in the same folder
3. Right-click `install.ps1` > **Run with PowerShell** (it will auto-elevate to admin)
4. **🛑 REBOOT YOUR COMPUTER before using the new layout.** Your PC is fine to keep using right now — just don't switch to the Kirkouski Typographic layout until after a restart. If you do, Windows Explorer will crash because it still holds the old keyboard state in memory. The DLL is registered but cannot take effect until the next boot.
5. After reboot, go to **Settings > Time & Language > Language & Region > Keyboard** and add the new layout

**Uninstall:** Run `.\install.ps1 -Uninstall`, then **🛑 REBOOT** (same reason — required to release the DLL). Use `-Layout polish`, `-Layout russian`, or `-Layout us` to uninstall selectively.

**Apply to login screen & new users:** After installing and switching to the new layout, open `intl.cpl` (Win+R > `intl.cpl`) > **Administrative** tab > **Copy settings** > check both **"Welcome screen and system accounts"** and **"New user accounts"** > OK. This ensures the login screen and any new user accounts use your layout instead of the default.

**Broken install?** Run `.\install.ps1 -HardCleanup` to remove all traces (registry, DLLs, preload entries).

> **Note:** Do not use MSKLC (Microsoft Keyboard Layout Creator) to build from `.klc` files — its generated DLLs crash Windows Explorer on Windows 11. Use the direct DLL pipeline instead.

### macOS

The recommended path is the **`Kirkouski Typographic.bundle`** that ships in the macOS zip — it has proper icons, localized names, and lands in the right language category instead of "Others".

1. Download `kirkouski-typographic-vX.Y-macos.zip` from the latest release and unzip it
2. Move `Kirkouski Typographic.bundle` into `~/Library/Keyboard Layouts/` (current user) or `/Library/Keyboard Layouts/` (all users — needs `sudo`)
3. **Clear the quarantine xattr** that macOS adds to anything downloaded via a browser — without this the bundle may silently fail to load:
   ```bash
   xattr -dr com.apple.quarantine ~/Library/Keyboard\ Layouts/Kirkouski\ Typographic.bundle
   ```
4. **Log out and log back in** (a full logout — not just the lock screen). macOS only re-scans the keyboard layout directory at login.
5. **System Settings > Keyboard > Input Sources > + > Polish / Russian** — pick the **Kirkouski Typographic** entries.

**Login screen on macOS Sequoia (15+):** Sequoia only loads keyboard layouts from `/Library/Keyboard Layouts/` for the login screen — `~/Library/…` is ignored at the lock screen even though it works after login. If you need the layout at the login screen, install system-wide with `sudo`.

**Manual / loose `.keylayout` install:** the zip also contains `polish-typographic-kirkouski-vX.Y.keylayout` and `russian-typographic-kirkouski-vX.Y.keylayout` as a fallback. Drop them into `~/Library/Keyboard Layouts/` if you want the legacy install style — but the bundle is the supported path.

## Building from Source

### Prerequisites

| Tool | Required for | Install |
|------|-------------|---------|
| Python 3.10+ | All build scripts | [python.org](https://www.python.org/downloads/) |
| Visual Studio Build Tools | Windows DLL compilation | [visualstudio.microsoft.com](https://visualstudio.microsoft.com/visual-cpp-build-tools/) |
| Windows SDK | Headers for kbd.h | Included with VS Build Tools |
| NSIS 3.x | Windows .exe installer | `winget install NSIS.NSIS` |
| Node.js 18+ / pnpm | Web frontend + asset pipeline | [nodejs.org](https://nodejs.org/) |

When installing VS Build Tools, select the **"Desktop development with C++"** workload. This provides `cl.exe`, `link.exe`, `rc.exe`, and the Windows SDK.

NSIS is optional — if not installed, `build.py` skips the .exe installer and produces only the zip.

No external Python packages are required — the toolchain uses only the Python standard library.

### Build Commands

```bash
# Build everything (Windows DLLs + macOS keylayouts + KLC files)
python build.py

# Build specific platform
python build.py windows          # DLLs + install.ps1 + NSIS .exe
python build.py macos            # .keylayout files + .bundle
python build.py klc              # .klc files (for MSKLC)
python build.py assets           # icons, web favicons, OG image (needs pnpm)

# Build specific layout
python build.py windows polish
python build.py windows us
python build.py macos russian
```

The `assets` target shells out to `pnpm --dir scripts/assets build`. Outputs (icons, favicons, OG image) are committed to the repo, so this only needs to run when fonts, colours, the OG template, or `VERSION` change.

### What the pipeline does

**Windows** — JSON layout → C source → MSVC-compiled DLL → NSIS installer + manual ZIP:

![Windows pipeline](assets/diagrams/pipeline-windows.svg)

**macOS** — Layout JSON + committed `.icns` icons → `.keylayout` → `.bundle` → `.pkg` (macOS-only) + ZIP:

![macOS pipeline](assets/diagrams/pipeline-macos.svg)

**Assets pipeline (Node)** — One source font becomes a vector SVG, then rasterizes into every icon variant the project needs. Playwright handles the OG image separately because the template is HTML, not SVG:

![Assets pipeline](assets/diagrams/pipeline-assets.svg)

### Output

`python build.py` produces everything in `dist/` (where `vX.Y` is the value in the repo-root `VERSION` file):

| File | Description |
|------|-------------|
| `kirkouski-typographic-vX.Y-windows-setup.exe` | NSIS installer (Add/Remove Programs, UAC) |
| `kirkouski-typographic-vX.Y-windows.zip` | DLLs + install.ps1 for manual install |
| `kirkouski-typographic-vX.Y-macos.zip` | `.bundle` (primary) + loose `.keylayout` files (fallback) |
| `kirkouski-typographic-vX.Y-macos.pkg` | macOS installer (built on macOS only) |
| `windows-vX.Y/` | Loose Windows files |
| `macos-vX.Y/Kirkouski Typographic.bundle/` | macOS bundle — primary install artifact |
| `macos-vX.Y/*.keylayout` | Loose macOS keylayout files (fallback) |

## Project Structure

```
VERSION                 # Single source of truth — bumping this propagates everywhere
build.py                # Build orchestrator (single entry point)
build_kbd_c.py          # JSON -> C source generator (Windows DLL pipeline)
compile_kbd.py          # MSVC compiler wrapper (C -> DLL)
build_klc.py            # JSON -> KLC generator
build_keylayout.py      # JSON -> keylayout generator (macOS), overrides keyboard id+name
build_macos_bundle.py   # Wrap .keylayout + .icns into Kirkouski Typographic.bundle
installer.nsi           # NSIS installer script (reads VERSION via /DVERSION)
install.ps1             # Windows PowerShell installer/uninstaller

extract_base.py         # One-time: extract full layout from Birman originals

polish_typographic.json       # Polish layout definition (overlay)
russian_typographic.json      # Russian layout definition (overlay)
polish_typographic_full.json  # Complete macOS layout structure
russian_typographic_full.json # Complete macOS layout structure

assets/icons/           # Generated icon assets (committed; rebuilt by scripts/assets)
scripts/assets/         # Node/Playwright pipeline for icons + favicons + OG image
  ├── fonts/            #   DMSerifDisplay-Italic.ttf (OFL-1.1, committed)
  ├── templates/        #   og-template.html
  └── src/              #   build pipeline modules (variants, glyph extract, packers)

visualizer.html         # Standalone keyboard layout viewer (legacy)
web/                    # Vue 3 frontend app (visualizer, downloads, i18n)
screenshots/            # Layout preview images
dist/                   # Build outputs (organized by platform)
build/                  # Intermediate C/obj/bundle files (gitignored)
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

🛑 **You activated the new layout before rebooting.** This is **expected** if you switched to the Kirkouski Typographic layout in Win+Space (or via Settings) without restarting first — see step 4 of the Windows install instructions above. The DLL is registered but Explorer still holds the old keyboard state and crashes the moment you try to use the freshly-registered layout. **Restart your computer** and the layout will work normally on next boot.

If Explorer keeps crashing **even after a full reboot**, run the hard cleanup:

```powershell
.\install.ps1 -HardCleanup
```

This removes all traces of Kirkouski layouts (registry keys, DLLs, preload entries) so you can start fresh.

### Windows: "Layout name already in use"

Previous install left ghost registry entries. Run `.\install.ps1 -Uninstall` as admin first, restart, then reinstall.

## Support

If you find this useful, consider:

- **[Support on Ko-fi](https://ko-fi.com/ryotsuke)** — buy me a coffee
- **Star this repo** — helps others discover the project

## Credits

Layout concept by [Ilya Birman](https://ilyabirman.ru/typography-layout/). Polish/Russian adaptation and open-source toolchain by Andrew Kirkouski.

## License

MIT License — see [LICENSE](LICENSE).
