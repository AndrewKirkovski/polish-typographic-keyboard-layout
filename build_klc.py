"""Generate Windows .klc keyboard layout files from *_full.json definitions.

Reads the merged full JSON layouts (produced by extract_base.py) and generates
.klc files compatible with MSKLC / kbdutool.exe.

Usage:
    python build_klc.py                    # builds all layouts
    python build_klc.py polish             # builds Polish only
    python build_klc.py russian            # builds Russian only
    python build_klc.py us                 # builds US+POL only

Output goes to dist/<name>.klc (UTF-16 LE with BOM).

Next steps (manual):
    1. Install MSKLC 1.4 from Microsoft
    2. Open the .klc in MSKLC
    3. Project > Build DLL and Setup Package
    4. This produces setup.exe + .msi installer
"""
import json
import sys
import os

from layout_adapter import KEY_MAP, extract_layers_from_full_json

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Scan code order for LAYOUT section
SC_ORDER = [
    "29", "02", "03", "04", "05", "06", "07", "08", "09", "0a", "0b", "0c", "0d",
    "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "1a", "1b",
    "1e", "1f", "20", "21", "22", "23", "24", "25", "26", "27", "28",
    "2b",
    "2c", "2d", "2e", "2f", "30", "31", "32", "33", "34", "35",
    "39",  # Space
    "56",  # ISO key (OEM_102)
    "53",  # Numpad decimal
]

# Layout configs
LAYOUTS = {
    "polish": {
        "json": "polish_typographic_full.json",
        "kbd_name": "pltypo",
        "description": "Polish Typographic by Kirkouski",
        "locale_name": "pl-PL",
        "locale_id": "00000415",
        "lang_id": "0415",
        "lang_name": "Polish",
    },
    "russian": {
        "json": "russian_typographic_full.json",
        "kbd_name": "rutypo",
        "description": "Russian Typographic by Kirkouski",
        "locale_name": "ru-RU",
        "locale_id": "00000419",
        "lang_id": "0419",
        "lang_name": "Russian",
    },
    "us": {
        "json": "polish_typographic_full.json",
        "kbd_name": "ustypo",
        "description": "US+POL Typographic by Kirkouski",
        "locale_name": "en-US",
        "locale_id": "00000409",
        "lang_id": "0409",
        "lang_name": "English",
    },
}


def char_to_hex(ch):
    """Convert a character to 4-digit hex."""
    if not ch:
        return "-1"
    return f"{ord(ch):04x}"


def format_char(ch, dead_keys_used, dead_key_chars):
    """Format a character for the LAYOUT section.
    Returns (hex_or_literal, is_dead_key).
    Multi-char strings (ligatures) are not supported in LAYOUT — use first char."""
    if not ch:
        return "-1", False
    if ch.startswith("dk:") or ch.startswith("act:"):
        dk_name = ch.replace("dk:", "").replace("act:", "").strip()
        dk_cp = dead_key_chars.get(dk_name)
        if dk_cp:
            dk_hex = f"{dk_cp:04x}"
            dead_keys_used.add(dk_hex)
            return f"{dk_hex}@", True
        return "-1", False
    if len(ch) > 1:
        # Ligature — MSKLC can't handle inline, skip for now
        # TODO: add LIGATURE section support
        return "-1", False
    cp = ord(ch)
    return f"{cp:04x}", False


def build_klc(config):
    """Build a .klc file content from layout config."""
    json_path = os.path.join(SCRIPT_DIR, config["json"])
    with open(json_path, encoding="utf-8") as f:
        full_data = json.load(f)

    layers = extract_layers_from_full_json(full_data)
    base = layers["base"]
    shift = layers["shift"]
    altgr = layers["altgr"]
    sh_altgr = layers["shift_altgr"]
    dead_key_chars = layers["dead_key_chars"]
    dead_key_compositions = layers["dead_key_compositions"]

    dead_keys_used = set()
    lines = []

    def w(line=""):
        lines.append(line)

    # Header
    w(f'KBD\t{config["kbd_name"]}\t"{config["description"]}"')
    w()
    w(f'COPYRIGHT\t"(c) 2026 Andrew Kirkouski"')
    w()
    w(f'COMPANY\t"Kirkouski"')
    w()
    w(f'LOCALENAME\t"{config["locale_name"]}"')
    w()
    w(f'LOCALEID\t"{config["locale_id"]}"')
    w()
    w('VERSION\t1.0')
    w()

    # Shift states
    w('SHIFTSTATE')
    w()
    w('0\t//Column 4')
    w('1\t//Column 5 : Shft')
    w('2\t//Column 6 :       Ctrl')
    w('6\t//Column 7 :       Ctrl+Alt')
    w('7\t//Column 8 : Shft  Ctrl+Alt')
    w()

    # Layout section
    w('LAYOUT\t\t;an extra \'@\' at the end is a dead key')
    w()
    w('//SC\tVK_\t\tCap\t0\t1\t2\t6\t7')
    w('//--\t----\t\t----\t----\t----\t----\t----\t----')
    w()

    # Build reverse lookup: scancode -> key_id
    sc_to_key = {}
    for key_id, (sc, vk, is_letter) in KEY_MAP.items():
        sc_to_key[sc] = (key_id, vk, is_letter)

    for sc in SC_ORDER:
        if sc == "39":
            # Space
            w(f'39\tSPACE\t\t0\t0020\t0020\t0020\t-1\t-1')
            continue
        if sc == "56":
            # ISO key (OEM_102)
            w(f'56\tOEM_102\t\t0\t005c\t007c\t001c\t-1\t-1')
            continue
        if sc == "53":
            # Numpad decimal
            w(f'53\tDECIMAL\t\t0\t002e\t002e\t-1\t-1\t-1')
            continue

        if sc not in sc_to_key:
            continue

        key_id, vk, is_letter = sc_to_key[sc]

        # Base char
        base_ch = base.get(key_id, "")
        base_hex = char_to_hex(base_ch) if base_ch else "-1"

        # Shift char
        shift_ch = shift.get(key_id, "")
        shift_hex = char_to_hex(shift_ch) if shift_ch else "-1"

        # Ctrl column: -1 for all keys. Windows handles Ctrl+letter shortcuts
        # automatically via VK codes — explicit control chars here are redundant
        # and trigger MSKLC warnings.
        ctrl_hex = "-1"

        # AltGr char
        ag_entry = altgr.get(key_id)
        if ag_entry and ag_entry.get("char"):
            ag_hex, _ = format_char(ag_entry["char"], dead_keys_used, dead_key_chars)
        else:
            ag_hex = "-1"

        # Shift+AltGr char
        sag_entry = sh_altgr.get(key_id)
        if sag_entry and sag_entry.get("char"):
            sag_hex, _ = format_char(sag_entry["char"], dead_keys_used, dead_key_chars)
        else:
            sag_hex = "-1"

        # Cap flag: 1 for letters (CapsLock = Shift), 0 otherwise
        # If AltGr layer has Polish diacritics that should also respond to CapsLock: use 5
        cap = "1" if is_letter else "0"

        # VK name formatting (pad for alignment)
        vk_padded = vk
        if len(vk) < 8:
            vk_padded = vk + "\t"

        w(f'{sc}\t{vk_padded}\t{cap}\t{base_hex}\t{shift_hex}\t{ctrl_hex}\t{ag_hex}\t{sag_hex}')

    w()

    # Dead key sections
    for dk_hex in sorted(dead_keys_used):
        dk_cp = int(dk_hex, 16)
        compositions = dead_key_compositions.get(dk_cp, [])
        if compositions:
            w(f'DEADKEY\t{dk_hex}')
            w()
            for base_cp, result_cp in compositions:
                w(f'{base_cp:04x}\t{result_cp:04x}\t// {chr(base_cp)} -> {chr(result_cp)}')
            w()

    # Ligature section (none for our layouts, but include the header)
    # (omitted — not needed)

    # Key names
    w('KEYNAME')
    w()
    for sc, name in [
        ("01", "Esc"), ("0e", "Backspace"), ("0f", "Tab"), ("1c", "Enter"),
        ("1d", "Ctrl"), ("2a", "Shift"), ("36", '"Right Shift"'), ("37", '"Num *"'),
        ("38", "Alt"), ("39", "Space"), ("3a", '"Caps Lock"'),
        ("3b", "F1"), ("3c", "F2"), ("3d", "F3"), ("3e", "F4"),
        ("3f", "F5"), ("40", "F6"), ("41", "F7"), ("42", "F8"),
        ("43", "F9"), ("44", "F10"), ("45", "Pause"),
        ("46", '"Scroll Lock"'), ("47", '"Num 7"'), ("48", '"Num 8"'),
        ("49", '"Num 9"'), ("4a", '"Num -"'), ("4b", '"Num 4"'),
        ("4c", '"Num 5"'), ("4d", '"Num 6"'), ("4e", '"Num +"'),
        ("4f", '"Num 1"'), ("50", '"Num 2"'), ("51", '"Num 3"'),
        ("52", '"Num 0"'), ("53", '"Num ."'), ("54", '"Sys Req"'),
        ("57", "F11"), ("58", "F12"),
    ]:
        w(f'{sc}\t{name}')
    w()

    w('KEYNAME_EXT')
    w()
    for sc, name in [
        ("1c", '"Num Enter"'), ("1d", '"Right Ctrl"'), ("35", '"Num /"'),
        ("37", '"Prnt Scrn"'), ("38", '"Right Alt"'), ("45", '"Num Lock"'),
        ("46", "Break"), ("47", "Home"), ("48", "Up"), ("49", '"Page Up"'),
        ("4b", "Left"), ("4d", "Right"), ("4f", "End"), ("50", "Down"),
        ("51", '"Page Down"'), ("52", "Insert"), ("53", "Delete"),
        ("5b", '"Left Windows"'), ("5c", '"Right Windows"'), ("5d", "Application"),
    ]:
        w(f'{sc}\t{name}')
    w()

    # Dead key names
    if dead_keys_used:
        w('KEYNAME_DEAD')
        w()
        dk_names = {
            "0060": '"GRAVE ACCENT"',
            "00b4": '"ACUTE ACCENT"',
            "005e": '"CIRCUMFLEX ACCENT"',
            "02dc": '"TILDE"',
            "00a8": '"DIAERESIS"',
            "02da": '"RING ABOVE"',
            "00b8": '"CEDILLA"',
            "02c7": '"CARON"',
            "02d8": '"BREVE"',
            "02dd": '"DOUBLE ACUTE ACCENT"',
        }
        for dk_hex in sorted(dead_keys_used):
            name = dk_names.get(dk_hex, f'"DEAD KEY {dk_hex}"')
            w(f'{dk_hex}\t{name}')
        w()

    # Descriptions and language names
    w('DESCRIPTIONS')
    w()
    w(f'{config["lang_id"]}\t{config["description"]}')
    w()

    w('LANGUAGENAMES')
    w()
    w(f'{config["lang_id"]}\t{config["lang_name"]}')
    w()

    w('ENDKBD')

    return "\r\n".join(lines)


def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(LAYOUTS.keys())
    os.makedirs(os.path.join(SCRIPT_DIR, "dist"), exist_ok=True)

    for target in targets:
        if target not in LAYOUTS:
            print(f"Unknown target: {target}. Use: {', '.join(LAYOUTS.keys())}")
            sys.exit(1)

        config = LAYOUTS[target]
        print(f"Building {target} .klc...")
        klc_content = build_klc(config)

        out_path = os.path.join(SCRIPT_DIR, "dist", f"{config['kbd_name']}.klc")
        # KLC files MUST be UTF-16 LE with BOM
        with open(out_path, "w", encoding="utf-16-le", newline="") as f:
            f.write("\ufeff")  # BOM
            f.write(klc_content)

        line_count = klc_content.count("\r\n") + 1
        print(f"  -> {out_path} ({line_count} lines)")

    print("Done.")
    print()
    print("Next steps:")
    print("  1. Install MSKLC 1.4: https://www.microsoft.com/en-us/download/details.aspx?id=102134")
    print("  2. Open the .klc file in MSKLC")
    print("  3. Project > Build DLL and Setup Package")
    print("  4. Run the generated setup.exe to install")


if __name__ == "__main__":
    main()
