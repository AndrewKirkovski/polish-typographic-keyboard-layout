"""Build a proper macOS keyboard layout .bundle.

A loose .keylayout file in ~/Library/Keyboard Layouts/ is unreliable on
modern macOS (Sonoma/Sequoia) and lands in the "Others" category with no
icon or localized name. A .bundle is the canonical packaging:

    Kirkouski Typographic.bundle/
    └── Contents/
        ├── Info.plist                       (CFBundleIdentifier .keyboardlayout., KLInfo_*)
        ├── version.plist
        └── Resources/
            ├── en.lproj/
            │   └── InfoPlist.strings        (UTF-16 LE, BOM)
            ├── Polish – Kirkouski Typographic.keylayout
            ├── Polish – Kirkouski Typographic.icns
            ├── Russian – Kirkouski Typographic.keylayout
            └── Russian – Kirkouski Typographic.icns

Critical rules learned the hard way:
  * The KLInfo_<filename> dict key in Info.plist must match the .keylayout
    filename (without extension) exactly — em-dash, spaces, casing.
  * InfoPlist.strings must be UTF-16 LE with BOM.
  * CFBundleIdentifier must contain ".keyboardlayout." or macOS won't even
    look at the bundle.

Usage:
    python build_macos_bundle.py
"""
import importlib.util
import os
import shutil
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _load_keyboard_names() -> dict[str, str]:
    """Pull the canonical display names from build_keylayout.py.

    Loaded dynamically (rather than `from build_keylayout import ...`) so that
    Pyright doesn't choke on the sibling-module path resolution at import time
    while still binding the two files at runtime — if someone adds or renames
    a layout in one place, the other side picks it up immediately, and the
    `_validate_layouts` check below catches typos before they reach disk.
    """
    spec = importlib.util.spec_from_file_location(
        "build_keylayout",
        os.path.join(SCRIPT_DIR, "build_keylayout.py"),
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load build_keylayout.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return dict(module.KEYBOARD_NAMES)


_KEYBOARD_NAMES = _load_keyboard_names()

# What goes into the bundle. Source paths are written by build_keylayout.py
# (the .keylayout under dist/, the .icns under assets/icons/). The display
# name is the canonical filename inside the bundle's Resources/ — it must
# match KEYBOARD_NAMES in build_keylayout.py byte for byte.
LAYOUTS = [
    {
        "key": "polish",
        "display_name": _KEYBOARD_NAMES["polish"],
        "src_keylayout": "dist/polish_typographic.keylayout",
        "src_icns": f"assets/icons/{_KEYBOARD_NAMES['polish']}.icns",
        "tis_input_source_id": "com.kirkouski.keyboardlayout.typographic.polish",
        "tis_intended_language": "pl-PL",
    },
    {
        "key": "russian",
        "display_name": _KEYBOARD_NAMES["russian"],
        "src_keylayout": "dist/russian_typographic.keylayout",
        "src_icns": f"assets/icons/{_KEYBOARD_NAMES['russian']}.icns",
        "tis_input_source_id": "com.kirkouski.keyboardlayout.typographic.russian",
        "tis_intended_language": "ru-RU",
    },
]

BUNDLE_NAME = "Kirkouski Typographic"
BUNDLE_IDENTIFIER = "com.kirkouski.keyboardlayout.typographic"

# Localized display names for the bundle's Resources/<lang>.lproj/InfoPlist.strings.
# macOS uses these to show the layout name in the user's system language when
# browsing input sources. Keys are the raw filenames from KEYBOARD_NAMES
# (English baseline); values are the translated display strings.
LPROJ_TRANSLATIONS = {
    "en": {
        "Polish – Kirkouski Typographic": "Polish – Kirkouski Typographic",
        "Russian – Kirkouski Typographic": "Russian – Kirkouski Typographic",
    },
    "pl": {
        "Polish – Kirkouski Typographic": "Polski – Kirkouski Typograficzny",
        "Russian – Kirkouski Typographic": "Rosyjski – Kirkouski Typograficzny",
    },
    "ru": {
        "Polish – Kirkouski Typographic": "Польский – Kirkouski Typographic",
        "Russian – Kirkouski Typographic": "Русский – Kirkouski Typographic",
    },
}


def _read_version():
    """Read project version from the repo-root VERSION file (matches the
    `_read_version()` helper convention used in build.py / build_kbd_c.py /
    extract_base.py)."""
    with open(os.path.join(SCRIPT_DIR, "VERSION"), encoding="utf-8") as f:
        return f.read().strip()


def xml_escape(text):
    """Minimal XML escape for plist string values."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def build_info_plist(version):
    """Build Contents/Info.plist as a UTF-8 string."""
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">',
        '<plist version="1.0">',
        "<dict>",
        "\t<key>CFBundleIdentifier</key>",
        f"\t<string>{xml_escape(BUNDLE_IDENTIFIER)}</string>",
        "\t<key>CFBundleName</key>",
        f"\t<string>{xml_escape(BUNDLE_NAME)}</string>",
        "\t<key>CFBundleVersion</key>",
        f"\t<string>{xml_escape(version)}</string>",
    ]
    for layout in LAYOUTS:
        lines += [
            f"\t<key>KLInfo_{xml_escape(layout['display_name'])}</key>",
            "\t<dict>",
            "\t\t<key>TICapsLockLanguageSwitchCapable</key>",
            "\t\t<true/>",
            "\t\t<key>TISIconIsTemplate</key>",
            "\t\t<false/>",
            "\t\t<key>TISInputSourceID</key>",
            f"\t\t<string>{xml_escape(layout['tis_input_source_id'])}</string>",
            "\t\t<key>TISIntendedLanguage</key>",
            f"\t\t<string>{xml_escape(layout['tis_intended_language'])}</string>",
            "\t</dict>",
        ]
    lines += ["</dict>", "</plist>", ""]
    return "\n".join(lines)


def build_version_plist(version):
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        '<plist version="1.0">\n'
        "<dict>\n"
        "\t<key>BuildVersion</key>\n"
        f"\t<string>{xml_escape(version)}</string>\n"
        "\t<key>ProjectName</key>\n"
        f"\t<string>{xml_escape(BUNDLE_NAME)}</string>\n"
        "\t<key>SourceVersion</key>\n"
        "\t<string>1</string>\n"
        "</dict>\n"
        "</plist>\n"
    )


def build_infoplist_strings(lang: str):
    """Localized display names for Resources/<lang>.lproj/InfoPlist.strings.

    UTF-16 LE with BOM (mandatory — macOS's plist/.strings loader rejects
    UTF-8 here, and the BOM tells it which endianness to use).

    The KEY in each line is the raw English filename (what macOS sees on
    disk); the VALUE is the translated display string for that locale.
    """
    translations = LPROJ_TRANSLATIONS[lang]
    lines = []
    for layout in LAYOUTS:
        src_name = layout["display_name"]
        dst_name = translations.get(src_name, src_name)
        # Escape backslashes and quotes for the .strings format.
        src_esc = src_name.replace("\\", "\\\\").replace('"', '\\"')
        dst_esc = dst_name.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'"{src_esc}" = "{dst_esc}";')
    text = "\n".join(lines) + "\n"
    # Explicit LE + manual BOM: byte-identical on all hosts (the generic
    # "utf-16" codec picks host-native endianness, which is LE on every real
    # current host but not strictly guaranteed).
    return b"\xff\xfe" + text.encode("utf-16-le")


def _validate_layouts() -> None:
    """Cross-check the LAYOUTS list against build_keylayout.KEYBOARD_NAMES.

    A drift here would mean a layout is in one file but not the other, and
    macOS would silently drop the bundle. Fail loudly at build time instead.
    """
    bundle_keys = {layout["key"] for layout in LAYOUTS}
    writer_keys = set(_KEYBOARD_NAMES.keys())
    if bundle_keys != writer_keys:
        only_bundle = bundle_keys - writer_keys
        only_writer = writer_keys - bundle_keys
        msg = ["LAYOUTS / KEYBOARD_NAMES mismatch:"]
        if only_bundle:
            msg.append(f"  in bundle only: {sorted(only_bundle)}")
        if only_writer:
            msg.append(f"  in keylayout writer only: {sorted(only_writer)}")
        raise RuntimeError("\n".join(msg))
    for layout in LAYOUTS:
        expected = _KEYBOARD_NAMES[layout["key"]]
        if layout["display_name"] != expected:
            raise RuntimeError(
                f"display_name mismatch for {layout['key']}: "
                f"bundle={layout['display_name']!r}, writer={expected!r}"
            )


def build_bundle():
    _validate_layouts()
    version = _read_version()
    bundle_root = os.path.join(SCRIPT_DIR, "build", "macos", f"{BUNDLE_NAME}.bundle")
    contents = os.path.join(bundle_root, "Contents")
    resources = os.path.join(contents, "Resources")

    # Clean any prior build to avoid stale files lingering.
    if os.path.isdir(bundle_root):
        shutil.rmtree(bundle_root)
    os.makedirs(resources, exist_ok=True)

    # Plists.
    with open(os.path.join(contents, "Info.plist"), "w", encoding="utf-8") as f:
        f.write(build_info_plist(version))
    with open(os.path.join(contents, "version.plist"), "w", encoding="utf-8") as f:
        f.write(build_version_plist(version))

    # Localized strings — one .lproj per supported UI language. Each
    # InfoPlist.strings is UTF-16 LE with BOM (mandatory for macOS).
    for lang in LPROJ_TRANSLATIONS:
        lproj_dir = os.path.join(resources, f"{lang}.lproj")
        os.makedirs(lproj_dir, exist_ok=True)
        with open(os.path.join(lproj_dir, "InfoPlist.strings"), "wb") as f:
            f.write(build_infoplist_strings(lang))

    # Per-layout files. Filenames in Resources/ MUST match the KLInfo_<...>
    # keys in Info.plist exactly, otherwise macOS won't pair them.
    for layout in LAYOUTS:
        src_kl = os.path.join(SCRIPT_DIR, layout["src_keylayout"])
        src_icns = os.path.join(SCRIPT_DIR, layout["src_icns"])
        if not os.path.isfile(src_kl):
            print(f"ERROR: missing {src_kl} — run build_keylayout.py first", file=sys.stderr)
            sys.exit(1)
        if not os.path.isfile(src_icns):
            print(f"ERROR: missing {src_icns} — run scripts/assets pipeline first", file=sys.stderr)
            sys.exit(1)
        shutil.copy2(src_kl, os.path.join(resources, f"{layout['display_name']}.keylayout"))
        shutil.copy2(src_icns, os.path.join(resources, f"{layout['display_name']}.icns"))

    print(f"Built {bundle_root}")
    for entry in os.walk(bundle_root):
        root, files = entry[0], entry[2]
        rel = os.path.relpath(root, bundle_root)
        prefix = "  " + ("" if rel == "." else rel.replace(os.sep, "/") + "/")
        for name in sorted(files):
            size = os.path.getsize(os.path.join(root, name))
            print(f"{prefix}{name}  ({size:,} bytes)")
    return bundle_root


if __name__ == "__main__":
    build_bundle()
