"""Build orchestrator for Kirkouski Typographic Keyboard Layouts.

Unified entry point for building all platform outputs.

Usage:
    python build.py                     # build everything
    python build.py windows             # Windows DLLs only
    python build.py macos               # macOS keylayouts only
    python build.py klc                 # Windows KLC files only (for MSKLC fallback)
    python build.py windows polish      # specific platform + layout
    python build.py macos russian       # specific platform + layout
"""
import subprocess
import sys
import os
import shutil

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _read_version():
    """Read project version from the repo-root VERSION file (single source of truth)."""
    with open(os.path.join(SCRIPT_DIR, "VERSION"), encoding="utf-8") as f:
        return f.read().strip()


VERSION = _read_version()

# Nice filenames for distribution (DLL names stay short for Windows registry)
# Format: lang-variation-author-version
NICE_NAMES = {
    "polish": "polish-typographic-kirkouski",
    "russian": "russian-typographic-kirkouski",
    "us": "us-pol-typographic-kirkouski",
}


def run(cmd, desc):
    """Run a Python script, forwarding output."""
    print(f"\n{'='*60}")
    print(f"  {desc}")
    print(f"{'='*60}\n")
    result = subprocess.run(
        [sys.executable] + cmd,
        cwd=SCRIPT_DIR,
        env={**os.environ, "PYTHONUNBUFFERED": "1", "PYTHONIOENCODING": "utf-8"},
    )
    if result.returncode != 0:
        print(f"\nFAILED: {desc}")
        sys.exit(result.returncode)


def build_windows(layouts):
    """Build Windows keyboard layout DLLs."""
    # Step 1: Generate C source
    run(["build_kbd_c.py"] + layouts, "Generating C source files")

    # Step 2: Compile to DLL (outputs to dist/ temporarily)
    run(["compile_kbd.py"] + layouts, "Compiling DLLs with MSVC")


def build_macos(layouts):
    """Build macOS .keylayout files and wrap them into a .bundle.

    The bundle wraps BOTH layouts in one artifact, so a partial
    `python build.py macos polish` cannot produce a valid bundle on its own.
    For partial builds we still rebuild every keylayout the bundle expects,
    then wrap — that way the bundle is always coherent and we never ship a
    stale copy of the layout the user didn't ask for.
    """
    run(["build_keylayout.py"], "Building macOS .keylayout files")
    run(["build_macos_bundle.py"], "Wrapping into macOS .bundle")
    if layouts:
        print(f"  (note: macos build always rebuilds both layouts to keep the bundle coherent)")


def build_assets():
    """Run the JS asset pipeline (icons, web favicons, OG image).

    Shells out to pnpm in scripts/assets/. Outputs are committed to the repo
    so this only needs to run when fonts, colours, or the OG template change.
    """
    print(f"\n{'='*60}")
    print("  Building assets (icons, favicons, OG image)")
    print(f"{'='*60}\n")
    pnpm = shutil.which("pnpm") or shutil.which("pnpm.cmd")
    if not pnpm:
        print("SKIP: pnpm not found on PATH. Install Node + pnpm to regenerate assets.")
        return
    result = subprocess.run(
        [pnpm, "build"],
        cwd=os.path.join(SCRIPT_DIR, "scripts", "assets"),
    )
    if result.returncode != 0:
        print("\nFAILED: assets build")
        sys.exit(result.returncode)


def build_klc(layouts):
    """Build Windows .klc files (MSKLC fallback)."""
    run(["build_klc.py"] + layouts, "Building .klc files for MSKLC")



def build_inno():
    """Build Inno Setup Windows installer (.exe)."""
    iss_file = os.path.join(SCRIPT_DIR, "installer.iss")
    if not os.path.isfile(iss_file):
        print("SKIP: installer.iss not found")
        return

    iscc = None
    for path in [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Inno Setup 6", "ISCC.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "Inno Setup 6", "ISCC.exe"),
        os.path.join(os.environ.get("ProgramFiles", ""), "Inno Setup 6", "ISCC.exe"),
    ]:
        if os.path.isfile(path):
            iscc = path
            break

    if not iscc:
        print("SKIP: Inno Setup 6 not installed. Download from https://jrsoftware.org/isdl.php")
        return

    print(f"\n{'='*60}")
    print("  Building Inno Setup installer")
    print(f"{'='*60}\n")

    result = subprocess.run(
        [iscc, f"/DVERSION={VERSION}", iss_file],
        cwd=SCRIPT_DIR,
    )
    if result.returncode != 0:
        print("\nFAILED: Inno Setup compilation")
        sys.exit(result.returncode)


def build_pkg():
    """Build macOS .pkg installer (macOS only).

    Wraps the .bundle (not loose .keylayout files) so PackageKit installs
    a complete bundle with icons + Info.plist into ~/Library/Keyboard Layouts/.
    `pkgbuild` is a macOS-only tool — silently skip on other platforms.
    """
    # Indirect through `str()` so static analysers don't narrow sys.platform
    # to the host literal and mark the macOS body as unreachable.
    current_platform: str = str(sys.platform)
    if current_platform != "darwin":
        print("SKIP: .pkg can only be built on macOS")
        return
    _build_pkg_darwin()


def _build_pkg_darwin():
    dist_dir = os.path.join(SCRIPT_DIR, "dist")
    pkg_out = os.path.join(dist_dir, f"kirkouski-typographic-v{VERSION}-macos.pkg")
    bundle_src = os.path.join(SCRIPT_DIR, "build", "macos", "Kirkouski Typographic.bundle")
    if not os.path.isdir(bundle_src):
        print(f"SKIP: bundle not built — run `python build.py macos` first ({bundle_src})")
        return

    # Stage payload: /Library/Keyboard Layouts/Kirkouski Typographic.bundle
    payload_root = os.path.join(SCRIPT_DIR, "build", "pkg-payload")
    payload_target = os.path.join(payload_root, "Library", "Keyboard Layouts", "Kirkouski Typographic.bundle")
    if os.path.isdir(payload_root):
        shutil.rmtree(payload_root)
    os.makedirs(os.path.dirname(payload_target), exist_ok=True)
    shutil.copytree(bundle_src, payload_target)

    print(f"\n{'='*60}")
    print("  Building macOS .pkg installer")
    print(f"{'='*60}\n")

    result = subprocess.run([
        "pkgbuild",
        "--root", payload_root,
        "--identifier", "com.kirkouski.keyboardlayout.typographic",
        "--version", VERSION,
        "--install-location", "/",
        pkg_out,
    ])
    if result.returncode != 0:
        print("\nFAILED: pkgbuild")
        sys.exit(result.returncode)
    print(f"  -> {pkg_out}")

    shutil.rmtree(payload_root, ignore_errors=True)


def build_zips():
    """Create distribution zip files."""
    dist_dir = os.path.join(SCRIPT_DIR, "dist")

    win_dir = os.path.join(dist_dir, f"windows-v{VERSION}")
    mac_dir = os.path.join(dist_dir, f"macos-v{VERSION}")

    if os.path.isdir(win_dir):
        zip_path = os.path.join(dist_dir, f"kirkouski-typographic-v{VERSION}-windows")
        shutil.make_archive(zip_path, "zip", dist_dir, f"windows-v{VERSION}")
        print(f"  Created {zip_path}.zip")

    if os.path.isdir(mac_dir):
        zip_path = os.path.join(dist_dir, f"kirkouski-typographic-v{VERSION}-macos")
        shutil.make_archive(zip_path, "zip", dist_dir, f"macos-v{VERSION}")
        print(f"  Created {zip_path}.zip")


def main():
    platforms = []
    layouts = []

    for arg in sys.argv[1:]:
        if arg in ("windows", "win"):
            platforms.append("windows")
        elif arg in ("macos", "mac"):
            platforms.append("macos")
        elif arg == "klc":
            platforms.append("klc")
        elif arg == "assets":
            platforms.append("assets")
        elif arg in ("polish", "russian", "us"):
            layouts.append(arg)
        else:
            print(f"Unknown argument: {arg}")
            print("Usage: python build.py [windows|macos|klc|assets] [polish|russian|us]")
            print("")
            print("Builds DLLs, keylayouts + .bundle, Inno Setup installer, .pkg (macOS only), and zip archives.")
            print("`assets` (re)generates icons, favicons, and OG image via the scripts/assets pipeline.")
            print("Prerequisites: Python 3.10+, MSVC Build Tools (windows), Inno Setup 6 (windows installer), pnpm (assets)")
            sys.exit(1)

    if not platforms:
        platforms = ["windows", "macos", "klc"]

    for platform in platforms:
        if platform == "windows":
            build_windows(layouts)
        elif platform == "macos":
            build_macos(layouts)
        elif platform == "klc":
            build_klc(layouts)
        elif platform == "assets":
            build_assets()

    # Organize dist with nice filenames
    dist_dir = os.path.join(SCRIPT_DIR, "dist")
    organize_dist(dist_dir, platforms)

    # Build installers and zips
    if "windows" in platforms:
        build_inno()
    if "macos" in platforms:
        build_pkg()
    build_zips()

    # Summary
    print(f"\n{'='*60}")
    print(f"  BUILD COMPLETE — v{VERSION}")
    print(f"{'='*60}")
    print(f"\nOutputs in dist/:")
    if os.path.isdir(dist_dir):
        for walk_entry in os.walk(dist_dir):
            root = walk_entry[0]
            files = walk_entry[2]
            level = root.replace(dist_dir, "").count(os.sep)
            indent = "  " + "  " * level
            if root != dist_dir:
                print(f"{indent}{os.path.basename(root)}/")
            for f in sorted(files):
                size = os.path.getsize(os.path.join(root, f))
                print(f"{indent}  {f:<40} {size:>8,} bytes")


def organize_dist(dist_dir, platforms):
    """Organize build outputs into versioned subdirectories, remove loose files."""
    dll_map = {"polish": "pltypo", "russian": "rutypo", "us": "ustypo"}
    ps1_src = os.path.join(SCRIPT_DIR, "install.ps1")

    if "windows" in platforms:
        win_dir = os.path.join(dist_dir, f"windows-v{VERSION}")
        os.makedirs(win_dir, exist_ok=True)
        for layout, short in dll_map.items():
            nice = NICE_NAMES.get(layout, short)
            dll_src = os.path.join(dist_dir, f"{short}.dll")
            klc_src = os.path.join(dist_dir, f"{short}.klc")
            if os.path.isfile(dll_src):
                shutil.move(dll_src, os.path.join(win_dir, f"{short}.dll"))
            if os.path.isfile(klc_src):
                shutil.move(klc_src, os.path.join(win_dir, f"{nice}-v{VERSION}.klc"))
        if os.path.isfile(ps1_src):
            shutil.copy2(ps1_src, os.path.join(win_dir, "install.ps1"))

    if "macos" in platforms:
        mac_dir = os.path.join(dist_dir, f"macos-v{VERSION}")
        os.makedirs(mac_dir, exist_ok=True)
        # Loose .keylayout files (legacy fallback for users who want to install
        # without the bundle, e.g. into a non-standard location).
        for layout in NICE_NAMES:
            nice = NICE_NAMES[layout]
            src = os.path.join(dist_dir, f"{layout}_typographic.keylayout")
            if os.path.isfile(src):
                shutil.move(src, os.path.join(mac_dir, f"{nice}-v{VERSION}.keylayout"))
        # The .bundle is the primary install artifact — copy (not move) so
        # build/ keeps a clean source for the .pkg builder.
        bundle_src = os.path.join(SCRIPT_DIR, "build", "macos", "Kirkouski Typographic.bundle")
        if os.path.isdir(bundle_src):
            bundle_dst = os.path.join(mac_dir, "Kirkouski Typographic.bundle")
            if os.path.isdir(bundle_dst):
                shutil.rmtree(bundle_dst)
            shutil.copytree(bundle_src, bundle_dst)

    # Clean any remaining loose files in dist/ root
    for f in os.listdir(dist_dir):
        path = os.path.join(dist_dir, f)
        if os.path.isfile(path):
            os.remove(path)


if __name__ == "__main__":
    main()
