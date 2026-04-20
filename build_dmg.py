"""Build a single unsigned macOS DMG for Kirkouski Typographic.

One DMG ships all three locales' install instructions. The bundle inside
already localizes the layout display-name via en/pl/ru.lproj (picked by
macOS based on the user's system language). For the install-time UX inside
the DMG itself we pack:

  * Three ReadMe PDFs inside a `Read Me.localized/` folder. Finder auto-
    localizes the folder's display name via `.localized/<lang>.strings`.
    Users on a Polish system see the folder named "Czytaj"; Russian users
    see "Прочтите". Inside the folder all three PDFs are always present —
    any user can open any language's copy.
  * The three per-locale background PNGs under `.background/`. `.DS_Store`
    displays the English one by default (Finder does NOT auto-select DMG
    backgrounds by locale — that's a volume-window property, not a bundle
    resource). Shipping all three keeps the localized variants together
    and lets a curious user browse `.background/` directly.

Target install location is user scope (~/Library/Keyboard Layouts/), no
admin required — that's why this flow replaces the old .pkg (system scope,
admin prompt).

On macOS: invokes dmgbuild + hdiutil verify, produces .dmg + .sha256.
On Windows/Linux: validates inputs and writes the dmgbuild settings file,
skips actual assembly. Lets the user iterate on design + content before
pushing a tag; CI runs the real build on macos-latest.

Usage:
    python build_dmg.py
"""
import hashlib
import os
import shutil
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LANGUAGES = ["en", "pl", "ru"]
DMG_VOLUME_NAME = "Kirkouski Typographic"
BUNDLE_NAME = "Kirkouski Typographic.bundle"

# Finder displays the `Read Me.localized/` folder under these names when the
# user's system language matches. The raw folder name on disk is always
# "Read Me.localized" — the `.strings` files inside `.localized/` remap it.
READMELOCALIZED_DIRNAME = "Read Me.localized"
READMELOCALIZED_DISPLAY = {
    "en": "Read Me",
    "pl": "Czytaj",
    "ru": "Прочтите",
}

# Each language gets its own PDF filename inside the localized folder so a
# user who opens e.g. a Russian system's localized folder still sees three
# files and can pick any.
READMELOCALIZED_PDF = {
    "en": "Read Me.pdf",
    "pl": "Przeczytaj.pdf",
    "ru": "Прочтите.pdf",
}


def _read_version():
    """Read project version from the repo-root VERSION file (single source of truth)."""
    with open(os.path.join(SCRIPT_DIR, "VERSION"), encoding="utf-8") as f:
        return f.read().strip()


VERSION = _read_version()


def _validate_inputs():
    """Fail loudly if any committed input is missing before we start.

    We check the bundle (built by build_macos_bundle.py) and the per-locale
    background + ReadMe assets under assets/dmg/. Background ships as two
    reps (1x and @2x) per locale so macOS CI can build a Retina-aware TIFF
    via `tiffutil -cathidpicheck`.
    """
    required = [
        os.path.join(SCRIPT_DIR, "build", "macos", BUNDLE_NAME),
        os.path.join(SCRIPT_DIR, "assets", "icons", "Kirkouski.icns"),
    ]
    for lang in LANGUAGES:
        required.append(os.path.join(SCRIPT_DIR, "assets", "dmg", f"background-{lang}.png"))
        required.append(os.path.join(SCRIPT_DIR, "assets", "dmg", f"background-{lang}@2x.png"))
        required.append(os.path.join(SCRIPT_DIR, "assets", "dmg", f"readme-{lang}.pdf"))
    missing = [p for p in required if not os.path.exists(p)]
    if missing:
        print("ERROR: missing inputs for DMG build:", file=sys.stderr)
        for p in missing:
            print(f"  {p}", file=sys.stderr)
        print(
            "Hint: run `python build.py macos` first to produce the bundle,\n"
            "and ensure assets/dmg/ contains background-<lang>.png + @2x.png\n"
            "+ readme-<lang>.pdf for each of en/pl/ru.",
            file=sys.stderr,
        )
        sys.exit(1)


def _combine_retina_tiff(lang, out_dir):
    """Combine 1x + 2x PNGs into a single multi-rep TIFF via macOS tiffutil.

    Finder reads the @1x rep for the window geometry (so the window opens
    at 600×400 points, not 600×400 pixels at 2x scale) and the @2x rep for
    sharp rendering on Retina displays. The magic flag is
    `-cathidpicheck`, which concatenates the inputs and verifies the 2x
    has exactly twice the pixel dimensions of the 1x.

    Returns the absolute path to the written TIFF.
    """
    png1x = os.path.join(SCRIPT_DIR, "assets", "dmg", f"background-{lang}.png")
    png2x = os.path.join(SCRIPT_DIR, "assets", "dmg", f"background-{lang}@2x.png")
    tiff = os.path.join(out_dir, f"background-{lang}.tiff")
    result = subprocess.run(
        ["tiffutil", "-cathidpicheck", png1x, png2x, "-out", tiff],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"\nFAILED: tiffutil -cathidpicheck ({lang})", file=sys.stderr)
        if result.stdout:
            print(result.stdout[-500:], file=sys.stderr)
        if result.stderr:
            print(result.stderr[-500:], file=sys.stderr)
        sys.exit(result.returncode)
    return tiff


def _stage_payload():
    """Build build/dmg/payload/ with everything the single DMG ships.

    Layout:
        payload/
          Kirkouski Typographic.bundle/   (verbatim copy of the built bundle)
          Read Me.localized/
            .localized/
              en.strings                  "Read Me.localized" = "Read Me";
              pl.strings                  ... = "Czytaj";
              ru.strings                  ... = "Прочтите";
            Read Me.pdf                   (EN content)
            Przeczytaj.pdf                (PL content)
            Прочтите.pdf                  (RU content)

    The `.background/` directory lives elsewhere — dmgbuild writes it from
    the `background=` attribute in settings.py, and we copy the other two
    background PNGs into it via a post-processing step inside settings.py.

    Returns the absolute payload directory path.
    """
    payload_root = os.path.join(SCRIPT_DIR, "build", "dmg", "payload")
    if os.path.isdir(payload_root):
        shutil.rmtree(payload_root)
    os.makedirs(payload_root)

    # Bundle — copied whole.
    bundle_src = os.path.join(SCRIPT_DIR, "build", "macos", BUNDLE_NAME)
    bundle_dst = os.path.join(payload_root, BUNDLE_NAME)
    shutil.copytree(bundle_src, bundle_dst)

    # Read Me.localized/ — folder with auto-localized display name + 3 PDFs.
    readme_dir = os.path.join(payload_root, READMELOCALIZED_DIRNAME)
    os.makedirs(readme_dir)
    localized_meta = os.path.join(readme_dir, ".localized")
    os.makedirs(localized_meta)
    for lang, display in READMELOCALIZED_DISPLAY.items():
        # .strings files use UTF-16 LE with BOM, same rule as InfoPlist.strings.
        content = f'"{READMELOCALIZED_DIRNAME}" = "{display}";\n'
        with open(os.path.join(localized_meta, f"{lang}.strings"), "wb") as f:
            f.write(b"\xff\xfe" + content.encode("utf-16-le"))
    for lang, pdf_name in READMELOCALIZED_PDF.items():
        src = os.path.join(SCRIPT_DIR, "assets", "dmg", f"readme-{lang}.pdf")
        shutil.copy2(src, os.path.join(readme_dir, pdf_name))

    return payload_root


def _write_settings(payload_root, bg_paths):
    """Generate build/dmg/settings.py consumed by dmgbuild on macOS.

    `bg_paths` is a dict with keys 'default', 'pl', 'ru' pointing at the
    images to reference from the settings file. On macOS these are Retina
    TIFFs produced by _combine_retina_tiff; on Windows (validation-only)
    they fall back to the 1x PNGs so the settings file is still writeable.

    Paths are emitted with forward slashes so the file runs under macOS even
    when generated on Windows. `symlinks = {}` is deliberate — Gatekeeper
    blocks drops onto alias folders in quarantined DMGs, so the background
    graphic instructs the user to drop the bundle on ~/Library/Keyboard
    Layouts/ instead.
    """
    settings_dir = os.path.join(SCRIPT_DIR, "build", "dmg")
    os.makedirs(settings_dir, exist_ok=True)
    settings_path = os.path.join(settings_dir, "settings.py")

    bundle_path = os.path.join(payload_root, BUNDLE_NAME).replace("\\", "/")
    readme_localized_path = os.path.join(payload_root, READMELOCALIZED_DIRNAME).replace("\\", "/")
    bg_default = bg_paths["default"].replace("\\", "/")
    bg_pl = bg_paths["pl"].replace("\\", "/")
    bg_ru = bg_paths["ru"].replace("\\", "/")
    bg_ext = os.path.splitext(bg_default)[1].lstrip(".")
    bg_pl_name = f"background-pl.{bg_ext}"
    bg_ru_name = f"background-ru.{bg_ext}"
    volume_icon = os.path.join(SCRIPT_DIR, "assets", "icons", "Kirkouski.icns").replace("\\", "/")

    content = f'''# Generated by build_dmg.py — do not edit by hand.
import os, shutil

format = "UDZO"
# HFS+ is dmgbuild's documented default and works on every macOS version.
# APFS would require macOS 10.13+ on the reader side with no meaningful size
# gain for a small keyboard-layout bundle. Keep HFS+ for widest reach.
filesystem = "HFS+"

files = [
    {bundle_path!r},
    {readme_localized_path!r},
]

# Deliberately empty — Gatekeeper blocks drops onto alias folders in
# quarantined DMGs, so the background graphic directs the user to drop the
# bundle on ~/Library/Keyboard Layouts/ instead of an in-DMG symlink.
symlinks = {{}}

# English background is the default Finder renders. On macOS this is a
# multi-rep TIFF (1x + @2x) so Finder reads the @1x rep for the window
# geometry (600×400 points) and the @2x rep for crisp Retina rendering.
# On Windows the settings file points at a plain PNG — that branch exists
# only for validation; CI regenerates the file with the TIFF paths.
# dmgbuild writes this as `.background/<basename>` inside the mounted
# volume; a post_mount_hook below copies the Polish and Russian variants
# into the same folder for completeness.
background = {bg_default!r}

# Volume icon — shown in Finder sidebar when the DMG is mounted, on the
# desktop if the user has "Show mounted volumes" enabled, and by macOS's
# disk image file icon in Finder. Same brand-K icon as the bundle itself
# so the whole install story is visually consistent.
icon = {volume_icon!r}

def post_mount_hook(volume_path):
    bg_dir = os.path.join(volume_path, ".background")
    os.makedirs(bg_dir, exist_ok=True)
    shutil.copy2({bg_pl!r}, os.path.join(bg_dir, {bg_pl_name!r}))
    shutil.copy2({bg_ru!r}, os.path.join(bg_dir, {bg_ru_name!r}))

window_rect = ((200, 120), (600, 400))
icon_size = 96
text_size = 12

icon_locations = {{
    {BUNDLE_NAME!r}:             (150, 200),
    {READMELOCALIZED_DIRNAME!r}: (450, 200),
}}

default_view = "icon-view"
show_icon_preview = False
include_icon_view_settings = "auto"
include_list_view_settings = "auto"
show_status_bar = False
show_tab_view = False
show_toolbar = False
show_pathbar = False
show_sidebar = False
'''
    with open(settings_path, "w", encoding="utf-8") as f:
        f.write(content)
    return settings_path


def _build_darwin(settings_path):
    """macOS-only half of the build: dmgbuild + hdiutil + sha256."""
    dist_dir = os.path.join(SCRIPT_DIR, "dist")
    os.makedirs(dist_dir, exist_ok=True)
    dmg_path = os.path.join(dist_dir, f"kirkouski-typographic-v{VERSION}-macos.dmg")
    if os.path.exists(dmg_path):
        os.remove(dmg_path)

    result = subprocess.run(
        ["dmgbuild", "-s", settings_path, DMG_VOLUME_NAME, dmg_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print("\nFAILED: dmgbuild", file=sys.stderr)
        if result.stdout:
            print(result.stdout[-500:], file=sys.stderr)
        if result.stderr:
            print(result.stderr[-500:], file=sys.stderr)
        sys.exit(result.returncode)
    if result.stdout:
        print(result.stdout, end="")

    verify = subprocess.run(
        ["hdiutil", "verify", dmg_path],
        capture_output=True,
        text=True,
    )
    if verify.returncode != 0:
        print("\nFAILED: hdiutil verify", file=sys.stderr)
        if verify.stdout:
            print(verify.stdout[-500:], file=sys.stderr)
        if verify.stderr:
            print(verify.stderr[-500:], file=sys.stderr)
        sys.exit(verify.returncode)
    if verify.stdout:
        print(verify.stdout, end="")

    # SHA256 sidecar for release integrity checks.
    sha = hashlib.sha256()
    with open(dmg_path, "rb") as f:
        while True:
            chunk = f.read(1 << 16)
            if not chunk:
                break
            sha.update(chunk)
    sha_path = dmg_path + ".sha256"
    with open(sha_path, "w", encoding="utf-8") as f:
        f.write(f"{sha.hexdigest()}  {os.path.basename(dmg_path)}\n")

    size_kb = os.path.getsize(dmg_path) // 1024
    print(f"  -> {dmg_path} ({size_kb} KB)")
    print(f"  -> {sha_path}")
    return dmg_path


def build():
    """Stage the single DMG's payload + settings, then (on macOS) assemble it."""
    _validate_inputs()
    print(f"\n{'=' * 60}\n  DMG: kirkouski-typographic-v{VERSION}-macos.dmg\n{'=' * 60}")
    payload_root = _stage_payload()

    # Strip xattrs on macOS before dmgbuild reads the tree (no-op on Windows).
    # Extended attributes from Finder / drag-and-drop otherwise end up baked
    # into the image and trigger Gatekeeper quarantine warnings on download.
    current_platform: str = str(sys.platform)
    settings_dir = os.path.join(SCRIPT_DIR, "build", "dmg")
    os.makedirs(settings_dir, exist_ok=True)
    if current_platform == "darwin":
        subprocess.run(["xattr", "-cr", payload_root], check=False)
        # Build the multi-rep TIFFs (1x + @2x per locale) so Finder opens
        # the window at 600×400 points while rendering sharply on Retina.
        bg_paths = {
            "default": _combine_retina_tiff("en", settings_dir),
            "pl":      _combine_retina_tiff("pl", settings_dir),
            "ru":      _combine_retina_tiff("ru", settings_dir),
        }
    else:
        # Windows validation-only build: reference the 1x PNGs so the
        # settings file is still well-formed. CI rewrites this file with
        # the TIFF paths when the real build runs on macos-latest.
        assets = os.path.join(SCRIPT_DIR, "assets", "dmg")
        bg_paths = {
            "default": os.path.join(assets, "background-en.png"),
            "pl":      os.path.join(assets, "background-pl.png"),
            "ru":      os.path.join(assets, "background-ru.png"),
        }

    settings_path = _write_settings(payload_root, bg_paths)
    print(f"  payload:  {payload_root}")
    print(f"  settings: {settings_path}")

    if current_platform != "darwin":
        print(f"  SKIP: DMG assembly requires macOS (detected {current_platform}); inputs staged OK.")
        return None

    return _build_darwin(settings_path)


def main():
    build()


if __name__ == "__main__":
    main()
