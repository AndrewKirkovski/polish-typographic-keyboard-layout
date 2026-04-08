"""Generate Windows .klc keyboard layout files from layout JSON definitions.

Reads the simple overlay JSONs (polish_typographic.json, russian_typographic.json)
and generates .klc files compatible with MSKLC / kbdutool.exe.

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

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Key ID -> (scancode_hex, VK_name, is_letter)
KEY_MAP = {
    "`":  ("29", "OEM_3",      False),
    "1":  ("02", "1",           False),
    "2":  ("03", "2",           False),
    "3":  ("04", "3",           False),
    "4":  ("05", "4",           False),
    "5":  ("06", "5",           False),
    "6":  ("07", "6",           False),
    "7":  ("08", "7",           False),
    "8":  ("09", "8",           False),
    "9":  ("0a", "9",           False),
    "0":  ("0b", "0",           False),
    "-":  ("0c", "OEM_MINUS",   False),
    "=":  ("0d", "OEM_PLUS",    False),
    "Q":  ("10", "Q",           True),
    "W":  ("11", "W",           True),
    "E":  ("12", "E",           True),
    "R":  ("13", "R",           True),
    "T":  ("14", "T",           True),
    "Y":  ("15", "Y",           True),
    "U":  ("16", "U",           True),
    "I":  ("17", "I",           True),
    "O":  ("18", "O",           True),
    "P":  ("19", "P",           True),
    "[":  ("1a", "OEM_4",       False),
    "]":  ("1b", "OEM_6",       False),
    "A":  ("1e", "A",           True),
    "S":  ("1f", "S",           True),
    "D":  ("20", "D",           True),
    "F":  ("21", "F",           True),
    "G":  ("22", "G",           True),
    "H":  ("23", "H",           True),
    "J":  ("24", "J",           True),
    "K":  ("25", "K",           True),
    "L":  ("26", "L",           True),
    ";":  ("27", "OEM_1",       False),
    "'":  ("28", "OEM_7",       False),
    "\\": ("2b", "OEM_5",       False),
    "Z":  ("2c", "Z",           True),
    "X":  ("2d", "X",           True),
    "C":  ("2e", "C",           True),
    "V":  ("2f", "V",           True),
    "B":  ("30", "B",           True),
    "N":  ("31", "N",           True),
    "M":  ("32", "M",           True),
    ",":  ("33", "OEM_COMMA",   False),
    ".":  ("34", "OEM_PERIOD",  False),
    "/":  ("35", "OEM_2",       False),
}

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

# Dead key name -> Unicode hex of the dead key character
DEAD_KEY_CHARS = {
    "grave":        "0060",
    "acute":        "00b4",
    "acute-2":      "00b4",
    "circumflex":   "005e",
    "tilde":        "02dc",
    "diaeresis":    "00a8",
    "ring":         "02da",
    "cedilla":      "00b8",
    "caron":        "02c7",
    "breve":        "02d8",
    "double-acute": "02dd",
}

# Dead key compositions: dk_char_hex -> [(base_hex, result_hex), ...]
DEAD_KEY_COMPOSITIONS = {
    "0060": [  # grave
        ("0061", "00e0"), ("0065", "00e8"), ("0069", "00ec"), ("006f", "00f2"), ("0075", "00f9"),
        ("0041", "00c0"), ("0045", "00c8"), ("0049", "00cc"), ("004f", "00d2"), ("0055", "00d9"),
        ("0020", "0060"),
    ],
    "00b4": [  # acute
        ("0061", "00e1"), ("0065", "00e9"), ("0069", "00ed"), ("006f", "00f3"), ("0075", "00fa"),
        ("0063", "0107"), ("006c", "013a"), ("006e", "0144"), ("0072", "0155"), ("0073", "015b"),
        ("007a", "017a"), ("0079", "00fd"),
        ("0041", "00c1"), ("0045", "00c9"), ("0049", "00cd"), ("004f", "00d3"), ("0055", "00da"),
        ("0043", "0106"), ("004c", "0139"), ("004e", "0143"), ("0052", "0154"), ("0053", "015a"),
        ("005a", "0179"), ("0059", "00dd"),
        ("0020", "00b4"),
    ],
    "005e": [  # circumflex
        ("0061", "00e2"), ("0065", "00ea"), ("0069", "00ee"), ("006f", "00f4"), ("0075", "00fb"),
        ("0041", "00c2"), ("0045", "00ca"), ("0049", "00ce"), ("004f", "00d4"), ("0055", "00db"),
        ("0020", "005e"),
    ],
    "02dc": [  # tilde
        ("0061", "00e3"), ("006e", "00f1"), ("006f", "00f5"),
        ("0041", "00c3"), ("004e", "00d1"), ("004f", "00d5"),
        ("0020", "02dc"),
    ],
    "00a8": [  # diaeresis
        ("0061", "00e4"), ("0065", "00eb"), ("0069", "00ef"), ("006f", "00f6"), ("0075", "00fc"),
        ("0041", "00c4"), ("0045", "00cb"), ("0049", "00cf"), ("004f", "00d6"), ("0055", "00dc"),
        ("0079", "00ff"), ("0059", "0178"),
        ("0020", "00a8"),
    ],
    "02da": [  # ring
        ("0061", "00e5"), ("0075", "016f"),
        ("0041", "00c5"), ("0055", "016e"),
        ("0020", "02da"),
    ],
    "00b8": [  # cedilla
        ("0063", "00e7"), ("0073", "015f"),
        ("0043", "00c7"), ("0053", "015e"),
        ("0020", "00b8"),
    ],
    "02c7": [  # caron
        ("0063", "010d"), ("0073", "0161"), ("007a", "017e"), ("0072", "0159"), ("006e", "0148"),
        ("0043", "010c"), ("0053", "0160"), ("005a", "017d"), ("0052", "0158"), ("004e", "0147"),
        ("0064", "010f"), ("0065", "011b"), ("0074", "0165"),
        ("0044", "010e"), ("0045", "011a"), ("0054", "0164"),
        ("0020", "02c7"),
    ],
    "02d8": [  # breve
        ("0061", "0103"), ("0067", "011f"),
        ("0041", "0102"), ("0047", "011e"),
        ("0020", "02d8"),
    ],
    "02dd": [  # double-acute
        ("006f", "0151"), ("0075", "0171"),
        ("004f", "0150"), ("0055", "0170"),
        ("0020", "02dd"),
    ],
}

# Layout configs
LAYOUTS = {
    "polish": {
        "json": "polish_typographic.json",
        "kbd_name": "pltypo",
        "description": "Polish Typographic by Kirkouski",
        "locale_name": "pl-PL",
        "locale_id": "00000415",
        "lang_id": "0415",
        "lang_name": "Polish",
    },
    "russian": {
        "json": "russian_typographic.json",
        "kbd_name": "rutypo",
        "description": "Russian Typographic by Kirkouski",
        "locale_name": "ru-RU",
        "locale_id": "00000419",
        "lang_id": "0419",
        "lang_name": "Russian",
    },
    "us": {
        "json": "polish_typographic.json",
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


def format_char(ch, dead_keys_used):
    """Format a character for the LAYOUT section.
    Returns (hex_or_literal, is_dead_key).
    Multi-char strings (ligatures) are not supported in LAYOUT — use first char."""
    if not ch:
        return "-1", False
    if ch.startswith("dk:") or ch.startswith("act:"):
        dk_name = ch.replace("dk:", "").replace("act:", "").strip()
        dk_hex = DEAD_KEY_CHARS.get(dk_name)
        if dk_hex:
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
        layout = json.load(f)

    base = layout["layers"].get("base", {})
    shift = layout["layers"].get("shift", {})
    altgr = layout["layers"].get("altgr", {})
    sh_altgr = layout["layers"].get("shift_altgr", {})

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
            ag_hex, ag_dead = format_char(ag_entry["char"], dead_keys_used)
        else:
            ag_hex, ag_dead = "-1", False

        # Shift+AltGr char
        sag_entry = sh_altgr.get(key_id)
        if sag_entry and sag_entry.get("char"):
            sag_hex, sag_dead = format_char(sag_entry["char"], dead_keys_used)
        else:
            sag_hex, sag_dead = "-1", False

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
        compositions = DEAD_KEY_COMPOSITIONS.get(dk_hex, [])
        if compositions:
            w(f'DEADKEY\t{dk_hex}')
            w()
            for base_hex, result_hex in compositions:
                w(f'{base_hex}\t{result_hex}\t// {chr(int(base_hex, 16))} -> {chr(int(result_hex, 16))}')
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
        with open(out_path, "w", encoding="utf-16-le") as f:
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
