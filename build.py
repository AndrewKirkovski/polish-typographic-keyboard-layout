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
VERSION = "0.1"

# Nice filenames for distribution (DLL names stay short for Windows registry)
# Format: lang-variation-author-version
NICE_NAMES = {
    "polish": "polish-typographic-kirkouski",
    "russian": "russian-typographic-kirkouski",
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
    """Build macOS .keylayout files."""
    run(["build_keylayout.py"] + layouts, "Building macOS .keylayout files")


def build_klc(layouts):
    """Build Windows .klc files (MSKLC fallback)."""
    run(["build_klc.py"] + layouts, "Building .klc files for MSKLC")


def build_nsis():
    """Build NSIS Windows installer (.exe)."""
    nsi_file = os.path.join(SCRIPT_DIR, "installer.nsi")
    if not os.path.isfile(nsi_file):
        print("SKIP: installer.nsi not found")
        return

    # Find makensis
    makensis = None
    for path in [
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "NSIS", "makensis.exe"),
        os.path.join(os.environ.get("ProgramFiles", ""), "NSIS", "makensis.exe"),
    ]:
        if os.path.isfile(path):
            makensis = path
            break

    if not makensis:
        print("SKIP: NSIS not installed. Install with: winget install NSIS.NSIS")
        return

    print(f"\n{'='*60}")
    print("  Building NSIS installer")
    print(f"{'='*60}\n")

    result = subprocess.run(
        [makensis, nsi_file],
        cwd=SCRIPT_DIR,
    )
    if result.returncode != 0:
        print("\nFAILED: NSIS compilation")
        sys.exit(result.returncode)


def build_pkg():
    """Build macOS .pkg installer (macOS only)."""
    if sys.platform != "darwin":
        print("SKIP: .pkg can only be built on macOS")
        return

    dist_dir = os.path.join(SCRIPT_DIR, "dist")
    mac_dir = os.path.join(dist_dir, f"macos-v{VERSION}")
    pkg_out = os.path.join(dist_dir, f"kirkouski-typographic-v{VERSION}-macos.pkg")

    # Create payload directory
    payload = os.path.join(SCRIPT_DIR, "build", "pkg-payload", "Library", "Keyboard Layouts")
    os.makedirs(payload, exist_ok=True)

    for name in ["polish_typographic.keylayout", "russian_typographic.keylayout"]:
        src = os.path.join(dist_dir, name)
        if not os.path.isfile(src):
            # Try the versioned folder
            nice = NICE_NAMES.get(name.split("_")[0], name)
            src = os.path.join(mac_dir, f"{nice}-v{VERSION}.keylayout")
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(payload, name))

    print(f"\n{'='*60}")
    print("  Building macOS .pkg installer")
    print(f"{'='*60}\n")

    result = subprocess.run([
        "pkgbuild",
        "--root", os.path.join(SCRIPT_DIR, "build", "pkg-payload"),
        "--identifier", "com.kirkouski.typographic",
        "--version", VERSION,
        "--install-location", "/",
        pkg_out,
    ])
    if result.returncode != 0:
        print("\nFAILED: pkgbuild")
        sys.exit(result.returncode)
    print(f"  -> {pkg_out}")

    # Clean payload
    shutil.rmtree(os.path.join(SCRIPT_DIR, "build", "pkg-payload"), ignore_errors=True)


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
        elif arg in ("polish", "russian"):
            layouts.append(arg)
        else:
            print(f"Unknown argument: {arg}")
            print("Usage: python build.py [windows|macos|klc] [polish|russian]")
            print("")
            print("Builds DLLs, keylayouts, NSIS installer, .pkg (macOS only), and zip archives.")
            print("Prerequisites: Python 3.10+, MSVC Build Tools (windows), NSIS (windows installer)")
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

    # Organize dist with nice filenames
    dist_dir = os.path.join(SCRIPT_DIR, "dist")
    organize_dist(dist_dir, platforms)

    # Build installers and zips
    if "windows" in platforms:
        build_nsis()
    if "macos" in platforms:
        build_pkg()
    build_zips()

    # Summary
    print(f"\n{'='*60}")
    print(f"  BUILD COMPLETE — v{VERSION}")
    print(f"{'='*60}")
    print(f"\nOutputs in dist/:")
    if os.path.isdir(dist_dir):
        for root, dirs, files in os.walk(dist_dir):
            level = root.replace(dist_dir, "").count(os.sep)
            indent = "  " + "  " * level
            if root != dist_dir:
                print(f"{indent}{os.path.basename(root)}/")
            for f in sorted(files):
                size = os.path.getsize(os.path.join(root, f))
                print(f"{indent}  {f:<40} {size:>8,} bytes")


def organize_dist(dist_dir, platforms):
    """Organize build outputs into versioned subdirectories, remove loose files."""
    dll_map = {"polish": "pltypo", "russian": "rutypo"}
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
        for layout in NICE_NAMES:
            nice = NICE_NAMES[layout]
            src = os.path.join(dist_dir, f"{layout}_typographic.keylayout")
            if os.path.isfile(src):
                shutil.move(src, os.path.join(mac_dir, f"{nice}-v{VERSION}.keylayout"))

    # Clean any remaining loose files in dist/ root
    for f in os.listdir(dist_dir):
        path = os.path.join(dist_dir, f)
        if os.path.isfile(path):
            os.remove(path)


if __name__ == "__main__":
    main()
