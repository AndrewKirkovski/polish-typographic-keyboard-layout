"""Generate Windows keyboard layout C source files from layout JSON definitions.

Produces .c, .rc, and .def files that can be compiled with MSVC into a keyboard
layout DLL — no MSKLC dependency needed.

Usage:
    python build_kbd_c.py                # generates both Polish and Russian
    python build_kbd_c.py polish         # Polish only
    python build_kbd_c.py russian        # Russian only

Output goes to build/<kbd_name>.c, build/<kbd_name>.rc, build/<kbd_name>.def
"""
import json
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Key mapping: key_id → (scancode_hex, VK_name, is_letter) ──────────────
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

# Dead key char hex values (used for WCH_DEAD continuation rows and DEADTRANS)
DEAD_KEY_CHARS = {
    "grave":        0x0060,
    "acute":        0x00B4,
    "acute-2":      0x00B4,
    "circumflex":   0x005E,
    "tilde":        0x02DC,
    "diaeresis":    0x00A8,
    "ring":         0x02DA,
    "cedilla":      0x00B8,
    "caron":        0x02C7,
    "breve":        0x02D8,
    "double-acute": 0x02DD,
}

# Dead key compositions: dk_char_code → [(base_char, result_char), ...]
DEAD_KEY_COMPOSITIONS = {
    0x0060: [  # grave
        (0x0061, 0x00E0), (0x0065, 0x00E8), (0x0069, 0x00EC), (0x006F, 0x00F2), (0x0075, 0x00F9),
        (0x0041, 0x00C0), (0x0045, 0x00C8), (0x0049, 0x00CC), (0x004F, 0x00D2), (0x0055, 0x00D9),
        (0x0020, 0x0060),
    ],
    0x00B4: [  # acute
        (0x0061, 0x00E1), (0x0065, 0x00E9), (0x0069, 0x00ED), (0x006F, 0x00F3), (0x0075, 0x00FA),
        (0x0063, 0x0107), (0x006C, 0x013A), (0x006E, 0x0144), (0x0072, 0x0155), (0x0073, 0x015B),
        (0x007A, 0x017A), (0x0079, 0x00FD),
        (0x0041, 0x00C1), (0x0045, 0x00C9), (0x0049, 0x00CD), (0x004F, 0x00D3), (0x0055, 0x00DA),
        (0x0043, 0x0106), (0x004C, 0x0139), (0x004E, 0x0143), (0x0052, 0x0154), (0x0053, 0x015A),
        (0x005A, 0x0179), (0x0059, 0x00DD),
        (0x0020, 0x00B4),
    ],
    0x005E: [  # circumflex
        (0x0061, 0x00E2), (0x0065, 0x00EA), (0x0069, 0x00EE), (0x006F, 0x00F4), (0x0075, 0x00FB),
        (0x0041, 0x00C2), (0x0045, 0x00CA), (0x0049, 0x00CE), (0x004F, 0x00D4), (0x0055, 0x00DB),
        (0x0020, 0x005E),
    ],
    0x02DC: [  # tilde
        (0x0061, 0x00E3), (0x006E, 0x00F1), (0x006F, 0x00F5),
        (0x0041, 0x00C3), (0x004E, 0x00D1), (0x004F, 0x00D5),
        (0x0020, 0x02DC),
    ],
    0x00A8: [  # diaeresis
        (0x0061, 0x00E4), (0x0065, 0x00EB), (0x0069, 0x00EF), (0x006F, 0x00F6), (0x0075, 0x00FC),
        (0x0041, 0x00C4), (0x0045, 0x00CB), (0x0049, 0x00CF), (0x004F, 0x00D6), (0x0055, 0x00DC),
        (0x0079, 0x00FF), (0x0059, 0x0178),
        (0x0020, 0x00A8),
    ],
    0x02DA: [  # ring
        (0x0061, 0x00E5), (0x0075, 0x016F),
        (0x0041, 0x00C5), (0x0055, 0x016E),
        (0x0020, 0x02DA),
    ],
    0x00B8: [  # cedilla
        (0x0063, 0x00E7), (0x0073, 0x015F),
        (0x0043, 0x00C7), (0x0053, 0x015E),
        (0x0020, 0x00B8),
    ],
    0x02C7: [  # caron
        (0x0063, 0x010D), (0x0073, 0x0161), (0x007A, 0x017E), (0x0072, 0x0159), (0x006E, 0x0148),
        (0x0043, 0x010C), (0x0053, 0x0160), (0x005A, 0x017D), (0x0052, 0x0158), (0x004E, 0x0147),
        (0x0064, 0x010F), (0x0065, 0x011B), (0x0074, 0x0165),
        (0x0044, 0x010E), (0x0045, 0x011A), (0x0054, 0x0164),
        (0x0020, 0x02C7),
    ],
    0x02D8: [  # breve
        (0x0061, 0x0103), (0x0067, 0x011F),
        (0x0041, 0x0102), (0x0047, 0x011E),
        (0x0020, 0x02D8),
    ],
    0x02DD: [  # double-acute
        (0x006F, 0x0151), (0x0075, 0x0171),
        (0x004F, 0x0150), (0x0055, 0x0170),
        (0x0020, 0x02DD),
    ],
}

# Layout configs
LAYOUTS = {
    "polish": {
        "json": "polish_typographic.json",
        "kbd_name": "pltypo",
        "description": "Polish Typographic by Kirkouski",
        "locale_id": "0415",
        "res_id_text": 100,
        "res_id_lang": 101,
    },
    "russian": {
        "json": "russian_typographic.json",
        "kbd_name": "rutypo",
        "description": "Russian Typographic by Kirkouski",
        "locale_id": "0419",
        "res_id_text": 100,
        "res_id_lang": 101,
    },
}

# ── Scancode-to-VK mapping (matches Birman reference DLLs exactly) ────────
# 127 entries (0x00..0x7E). Flags: KBDEXT, KBDMULTIVK, KBDSPECIAL, KBDNUMPAD.
SCANCODE_TO_VK = [
    # 0x00-0x07
    "VK__none_", "VK_ESCAPE", "'1'", "'2'", "'3'", "'4'", "'5'", "'6'",
    # 0x08-0x0F
    "'7'", "'8'", "'9'", "'0'", "VK_OEM_MINUS", "VK_OEM_PLUS", "VK_BACK", "VK_TAB",
    # 0x10-0x17
    "'Q'", "'W'", "'E'", "'R'", "'T'", "'Y'", "'U'", "'I'",
    # 0x18-0x1F
    "'O'", "'P'", "VK_OEM_4", "VK_OEM_6", "VK_RETURN", "VK_LCONTROL", "'A'", "'S'",
    # 0x20-0x27
    "'D'", "'F'", "'G'", "'H'", "'J'", "'K'", "'L'", "VK_OEM_1",
    # 0x28-0x2F
    "VK_OEM_7", "VK_OEM_3", "VK_LSHIFT", "VK_OEM_5", "'Z'", "'X'", "'C'", "'V'",
    # 0x30-0x37
    "'B'", "'N'", "'M'", "VK_OEM_COMMA", "VK_OEM_PERIOD", "VK_OEM_2",
    "VK_RSHIFT | KBDEXT", "VK_MULTIPLY | KBDMULTIVK",
    # 0x38-0x3F
    "VK_LMENU", "VK_SPACE", "VK_CAPITAL", "VK_F1", "VK_F2", "VK_F3", "VK_F4", "VK_F5",
    # 0x40-0x47
    "VK_F6", "VK_F7", "VK_F8", "VK_F9", "VK_F10",
    "VK_NUMLOCK | KBDEXT | KBDMULTIVK", "VK_SCROLL | KBDMULTIVK",
    "VK_HOME | KBDSPECIAL | KBDNUMPAD",
    # 0x48-0x4F
    "VK_UP | KBDSPECIAL | KBDNUMPAD", "VK_PRIOR | KBDSPECIAL | KBDNUMPAD",
    "VK_SUBTRACT",
    "VK_LEFT | KBDSPECIAL | KBDNUMPAD", "VK_CLEAR | KBDSPECIAL | KBDNUMPAD",
    "VK_RIGHT | KBDSPECIAL | KBDNUMPAD",
    "VK_ADD",
    "VK_END | KBDSPECIAL | KBDNUMPAD",
    # 0x50-0x57
    "VK_DOWN | KBDSPECIAL | KBDNUMPAD", "VK_NEXT | KBDSPECIAL | KBDNUMPAD",
    "VK_INSERT | KBDSPECIAL | KBDNUMPAD", "VK_DELETE | KBDSPECIAL | KBDNUMPAD",
    "VK_SNAPSHOT", "VK__none_", "VK_OEM_102", "VK_F11",
    # 0x58-0x5F
    "VK_F12", "VK_CLEAR", "0xEE", "0xF1", "0xEA", "0xF9", "0xF5", "0xF3",
    # 0x60-0x67
    "VK__none_", "VK__none_", "0xFB", "0x2F", "0x7C", "0x7D", "0x7E", "0x7F",
    # 0x68-0x6F
    "0x80", "0x81", "0x82", "0x83", "0x84", "0x85", "0x86", "0xED",
    # 0x70-0x77
    "VK__none_", "0xE9", "VK__none_", "0xC1", "VK__none_", "VK__none_", "0x87", "VK__none_",
    # 0x78-0x7E (7 entries — total table is 127)
    "VK__none_", "VK__none_", "VK__none_", "0xEB", "VK_TAB", "VK__none_", "0xC2",
]


def wch(ch):
    """Format a character as a C wide char literal."""
    if ch is None:
        return "WCH_NONE"
    if isinstance(ch, int):
        return f"0x{ch:04X}"
    if len(ch) == 1:
        cp = ord(ch)
        if 0x20 <= cp <= 0x7E and ch not in ("'", "\\"):
            return f"L'{ch}'"
        return f"0x{cp:04X}"
    return "WCH_NONE"


def parse_char(entry, dead_keys_used):
    """Parse a JSON char entry. Returns (wch_value, is_dead, dead_char_code)."""
    if entry is None:
        return "WCH_NONE", False, 0
    ch = entry.get("char", "")
    if not ch:
        return "WCH_NONE", False, 0
    if ch.startswith("dk:") or ch.startswith("act:"):
        dk_name = ch.removeprefix("dk:").removeprefix("act:").strip()
        dk_code = DEAD_KEY_CHARS.get(dk_name)
        if dk_code:
            dead_keys_used.add(dk_code)
            return "WCH_DEAD", True, dk_code
        return "WCH_NONE", False, 0
    if len(ch) > 1:
        # Ligature — handled separately
        return "WCH_LGTR", False, 0
    return wch(ch), False, 0


def build_c_source(config):
    """Generate the C source for a keyboard layout DLL."""
    json_path = os.path.join(SCRIPT_DIR, config["json"])
    with open(json_path, encoding="utf-8") as f:
        layout = json.load(f)

    base = layout["layers"].get("base", {})
    shift = layout["layers"].get("shift", {})
    altgr = layout["layers"].get("altgr", {})
    sh_altgr = layout["layers"].get("shift_altgr", {})

    dead_keys_used = set()
    ligatures = []  # (vk_name, mod_index, [chars])

    # Classify keys into VK_TO_WCHARS groups (5 modifier columns: base, shift, ctrl, altgr, sh_altgr)
    wchar5_keys = []  # base, shift, ctrl, altgr, sh_altgr
    wchar3_keys = []  # base, shift, ctrl only

    for key_id, (sc, vk, is_letter) in KEY_MAP.items():
        base_ch = base.get(key_id, "")
        shift_ch = shift.get(key_id, "")
        ag_entry = altgr.get(key_id)
        sag_entry = sh_altgr.get(key_id)

        # Parse AltGr and Shift+AltGr
        ag_val, ag_dead, ag_dk_code = parse_char(ag_entry, dead_keys_used)
        sag_val, sag_dead, sag_dk_code = parse_char(sag_entry, dead_keys_used)

        has_altgr = ag_val != "WCH_NONE" or sag_val != "WCH_NONE"

        # Check for ligatures (multi-char output, not dead keys)
        def _check_ligature(entry, mod_idx):
            if not entry:
                return
            ch = entry.get("char", "")
            if not ch or ch.startswith("dk:") or ch.startswith("act:"):
                return
            if len(ch) > 1:
                chars = [ord(c) for c in ch[:5]]  # max 5 chars per LIGATURE
                vk_str = f"'{vk}'" if len(vk) == 1 else f"VK_{vk}"
                ligatures.append((vk_str, mod_idx, chars))
        _check_ligature(ag_entry, 2)
        _check_ligature(sag_entry, 3)

        # CapsLock flags
        cap_flags = "0"
        if is_letter:
            cap_flags = "CAPLOK"
            # If AltGr produces a lowercase letter with an uppercase counterpart,
            # add CAPLOKALTGR so CapsLock affects the AltGr layer too
            if ag_entry and ag_entry.get("char", ""):
                ag_ch = ag_entry["char"]
                if len(ag_ch) == 1 and ag_ch.islower() and ag_ch.upper() != ag_ch:
                    cap_flags = "CAPLOK | CAPLOKALTGR"

        base_val = wch(base_ch) if base_ch else "WCH_NONE"
        shift_val = wch(shift_ch) if shift_ch else "WCH_NONE"

        entry_data = {
            "vk": f"'{vk}'" if len(vk) == 1 else f"VK_{vk}",
            "cap": cap_flags,
            "base": base_val,
            "shift": shift_val,
            "ctrl": "WCH_NONE",
            "altgr": ag_val,
            "sh_altgr": sag_val,
            "ag_dead": ag_dead,
            "sag_dead": sag_dead,
            "ag_dk_code": ag_dk_code,
            "sag_dk_code": sag_dk_code,
        }

        if has_altgr:
            wchar5_keys.append(entry_data)
        else:
            wchar3_keys.append(entry_data)

    # ── Generate C source ──────────────────────────────────────────────
    lines = []
    w = lines.append

    w("/*")
    w(f" * {config['description']}")
    w(f" * Generated by build_kbd_c.py — do not edit manually.")
    w(" */")
    w("")
    w("#define KBD_TYPE 4")
    w("")
    w("#include <windows.h>")
    w("#include <kbd.h>")
    w("#include <dontuse.h>")
    w("")

    # ── Key names ──────────────────────────────────────────────────────
    w("/* Key names */")
    w("static VSC_LPWSTR key_names[] = {")
    for sc, name in [
        ("0x01", "Esc"), ("0x0e", "Backspace"), ("0x0f", "Tab"), ("0x1c", "Enter"),
        ("0x1d", "Ctrl"), ("0x2a", "Shift"), ("0x36", "Right Shift"), ("0x37", "Num *"),
        ("0x38", "Alt"), ("0x39", "Space"), ("0x3a", "Caps Lock"),
        ("0x3b", "F1"), ("0x3c", "F2"), ("0x3d", "F3"), ("0x3e", "F4"),
        ("0x3f", "F5"), ("0x40", "F6"), ("0x41", "F7"), ("0x42", "F8"),
        ("0x43", "F9"), ("0x44", "F10"), ("0x45", "Pause"), ("0x46", "Scroll Lock"),
        ("0x47", "Num 7"), ("0x48", "Num 8"), ("0x49", "Num 9"), ("0x4a", "Num -"),
        ("0x4b", "Num 4"), ("0x4c", "Num 5"), ("0x4d", "Num 6"), ("0x4e", "Num +"),
        ("0x4f", "Num 1"), ("0x50", "Num 2"), ("0x51", "Num 3"), ("0x52", "Num 0"),
        ("0x53", "Num ."), ("0x54", "Sys Req"), ("0x56", "<>"), ("0x57", "F11"), ("0x58", "F12"),
    ]:
        w(f'    {{{sc}, L"{name}"}},')
    w("    {0, NULL}")
    w("};")
    w("")

    w("static VSC_LPWSTR key_names_ext[] = {")
    for sc, name in [
        ("0x1c", "Num Enter"), ("0x1d", "Right Ctrl"), ("0x35", "Num /"),
        ("0x37", "Prnt Scrn"), ("0x38", "Right Alt"), ("0x45", "Num Lock"),
        ("0x46", "Break"), ("0x47", "Home"), ("0x48", "Up"), ("0x49", "Page Up"),
        ("0x4b", "Left"), ("0x4d", "Right"), ("0x4f", "End"), ("0x50", "Down"),
        ("0x51", "Page Down"), ("0x52", "Insert"), ("0x53", "Delete"),
        ("0x5b", "Left Windows"), ("0x5c", "Right Windows"), ("0x5d", "Application"),
    ]:
        w(f'    {{{sc}, L"{name}"}},')
    w("    {0, NULL}")
    w("};")
    w("")

    # Dead key names
    if dead_keys_used:
        dk_name_map = {
            0x0060: "GRAVE ACCENT", 0x00B4: "ACUTE ACCENT", 0x005E: "CIRCUMFLEX ACCENT",
            0x02DC: "TILDE", 0x00A8: "DIAERESIS", 0x02DA: "RING ABOVE",
            0x00B8: "CEDILLA", 0x02C7: "CARON", 0x02D8: "BREVE",
            0x02DD: "DOUBLE ACUTE ACCENT",
        }
        w("static LPWSTR key_names_dead[] = {")
        for dk_code in sorted(dead_keys_used):
            name = dk_name_map.get(dk_code, "DEAD KEY")
            w(f'    L"\\x{dk_code:04x}" L"{name}",')
        w("    NULL")
        w("};")
    else:
        w("static LPWSTR *key_names_dead = NULL;")
    w("")

    # ── Scancode-to-VK table ───────────────────────────────────────────
    w("/* Scancode to Virtual Key mapping */")
    w("static USHORT scancode_to_vk[] = {")
    for i in range(0, len(SCANCODE_TO_VK), 8):
        chunk = SCANCODE_TO_VK[i:i+8]
        formatted = ", ".join(chunk)
        w(f"    {formatted},  /* {i:#04x} */")
    w("};")
    w("")

    # E0-prefixed scancodes (extended keys)
    w("static VSC_VK scancode_to_vk_e0[] = {")
    e0_keys = [
        ("0x1c", "VK_RETURN"), ("0x1d", "VK_RCONTROL"), ("0x35", "VK_DIVIDE"),
        ("0x37", "VK_SNAPSHOT"), ("0x38", "VK_RMENU"), ("0x46", "VK_CANCEL"),
        ("0x47", "VK_HOME"), ("0x48", "VK_UP"), ("0x49", "VK_PRIOR"),
        ("0x4b", "VK_LEFT"), ("0x4d", "VK_RIGHT"), ("0x4f", "VK_END"),
        ("0x50", "VK_DOWN"), ("0x51", "VK_NEXT"), ("0x52", "VK_INSERT"),
        ("0x53", "VK_DELETE"), ("0x5b", "VK_LWIN"), ("0x5c", "VK_RWIN"),
        ("0x5d", "VK_APPS"),
    ]
    for sc, vk in e0_keys:
        w(f"    {{{sc}, {vk}}},")
    w("    {0, 0}")
    w("};")
    w("")

    w("static VSC_VK scancode_to_vk_e1[] = {")
    w("    {0x1d, VK_PAUSE},")
    w("    {0, 0}")
    w("};")
    w("")

    # ── Modifier definitions ───────────────────────────────────────────
    w("/* Modifier key definitions */")
    w("static VK_TO_BIT vk_to_bits[] = {")
    w("    {VK_SHIFT,   KBDSHIFT},")
    w("    {VK_CONTROL, KBDCTRL},")
    w("    {VK_MENU,    KBDALT},")
    w("    {0, 0}")
    w("};")
    w("")

    w("static MODIFIERS char_modifiers = {")
    w("    vk_to_bits,")
    w("    7,  /* max modifier bitmask */")
    w("    {")
    w("        0,              /* 000 = <none>          -> column 0 */")
    w("        1,              /* 001 = Shift            -> column 1 */")
    w("        2,              /* 010 = Ctrl             -> column 2 */")
    w("        SHFT_INVALID,   /* 011 = Shift+Ctrl       -> invalid  */")
    w("        SHFT_INVALID,   /* 100 = Alt              -> invalid  */")
    w("        SHFT_INVALID,   /* 101 = Shift+Alt        -> invalid  */")
    w("        3,              /* 110 = Ctrl+Alt (AltGr)  -> column 3 */")
    w("        4,              /* 111 = Shift+AltGr      -> column 4 */")
    w("    }")
    w("};")
    w("")

    # ── VK_TO_WCHARS tables ────────────────────────────────────────────
    # 5-column keys (base, shift, ctrl, altgr, shift+altgr)
    w("/* Character tables — 5 columns: Base, Shift, Ctrl, AltGr, Shift+AltGr */")
    w("static VK_TO_WCHARS5 vk_to_wchar5[] = {")
    for k in wchar5_keys:
        w(f"    {{{k['vk']}, {k['cap']}, {{{k['base']}, {k['shift']}, {k['ctrl']}, {k['altgr']}, {k['sh_altgr']}}}}},")
        # Dead key continuation row — must be a SINGLE row even if both columns are dead
        if k["ag_dead"] or k["sag_dead"]:
            ag_dk = f"0x{k['ag_dk_code']:04X}" if k["ag_dead"] else "WCH_NONE"
            sag_dk = f"0x{k['sag_dk_code']:04X}" if k["sag_dead"] else "WCH_NONE"
            w(f"    {{0xFF, 0, {{WCH_NONE, WCH_NONE, WCH_NONE, {ag_dk}, {sag_dk}}}}},")
    w("    {0, 0, {0, 0, 0, 0, 0}}")
    w("};")
    w("")

    # 3-column keys (base, shift, ctrl — no AltGr)
    w("/* Character tables — 3 columns: Base, Shift, Ctrl */")
    w("static VK_TO_WCHARS3 vk_to_wchar3[] = {")
    for k in wchar3_keys:
        w(f"    {{{k['vk']}, {k['cap']}, {{{k['base']}, {k['shift']}, {k['ctrl']}}}}},")
    w("    {0, 0, {0, 0, 0}}")
    w("};")
    w("")

    # Special and numpad keys — 3 columns (base, shift, ctrl)
    w("/* Special keys + numpad + extra keys */")
    w("static VK_TO_WCHARS3 vk_to_wchar_special[] = {")
    w("    {VK_SPACE,   0, {L' ',    L' ',    0x0020}},")
    w("    {VK_BACK,    0, {L'\\b',  L'\\b',  0x007F}},")
    w("    {VK_ESCAPE,  0, {0x001B,  0x001B,  0x001B}},")
    w("    {VK_RETURN,  0, {L'\\r',  L'\\r',  L'\\n'}},")
    w("    {VK_CANCEL,  0, {0x0003,  0x0003,  0x0003}},")
    w("    {VK_TAB,     0, {L'\\t',  L'\\t',  WCH_NONE}},")
    w("    {VK_DECIMAL, 0, {L'.',    L'.',    WCH_NONE}},")
    w("    {0, 0, {0, 0, 0}}")
    w("};")
    w("")

    # 1-column numpad keys (base only — no shift/ctrl behavior)
    w("/* Numpad character keys */")
    w("static VK_TO_WCHARS1 vk_to_wchar_numpad[] = {")
    for digit in range(10):
        w(f"    {{VK_NUMPAD{digit}, 0, {{L'{digit}'}}}},")
    w("    {0, 0, {0}}")
    w("};")
    w("")

    # VK_TO_WCHAR_TABLE array
    w("static VK_TO_WCHAR_TABLE vk_to_wchar[] = {")
    w("    {(PVK_TO_WCHARS1)vk_to_wchar5,       5, sizeof(VK_TO_WCHARS5)},")
    w("    {(PVK_TO_WCHARS1)vk_to_wchar3,        3, sizeof(VK_TO_WCHARS3)},")
    w("    {(PVK_TO_WCHARS1)vk_to_wchar_special, 3, sizeof(VK_TO_WCHARS3)},")
    w("    {(PVK_TO_WCHARS1)vk_to_wchar_numpad,  1, sizeof(VK_TO_WCHARS1)},")
    w("    {NULL, 0, 0}")
    w("};")
    w("")

    # ── Dead key composition table ─────────────────────────────────────
    if dead_keys_used:
        w("/* Dead key compositions */")
        w("static DEADKEY dead_keys[] = {")
        for dk_code in sorted(dead_keys_used):
            compositions = DEAD_KEY_COMPOSITIONS.get(dk_code, [])
            for base_ch, result_ch in compositions:
                w(f"    DEADTRANS(0x{base_ch:04X}, 0x{dk_code:04X}, 0x{result_ch:04X}, 0x0000),")
        w("    {0, 0, 0}")
        w("};")
    else:
        w("static DEADKEY *dead_keys = NULL;")
    w("")

    # ── Ligature table ─────────────────────────────────────────────────
    max_lig_len = 0
    if ligatures:
        max_lig_len = max(len(chars) for _, _, chars in ligatures)
        if max_lig_len < 2:
            max_lig_len = 2
        w(f"/* Ligature table — up to {max_lig_len} characters per key */")
        w(f"static LIGATURE{max_lig_len} ligature_table[] = {{")
        for vk, mod, chars in ligatures:
            padded = chars + [0] * (max_lig_len - len(chars))
            char_str = ", ".join(f"0x{c:04X}" for c in padded)
            w(f"    {{{vk}, {mod}, {{{char_str}}}}},")
        pad_zeros = ", ".join(["0"] * max_lig_len)
        w(f"    {{0, 0, {{{pad_zeros}}}}}")
        w("};")
        w("")

    # ── Master KBDTABLES struct ────────────────────────────────────────
    w("/* Master keyboard tables */")
    w("static KBDTABLES kbd_tables = {")
    w("    &char_modifiers,")
    w("    vk_to_wchar,")
    w(f"    {'dead_keys' if dead_keys_used else 'NULL'},")
    w("    key_names,")
    w("    key_names_ext,")
    w(f"    {'key_names_dead' if dead_keys_used else 'NULL'},")
    w("    scancode_to_vk,")
    w(f"    sizeof(scancode_to_vk) / sizeof(scancode_to_vk[0]),")
    w("    scancode_to_vk_e0,")
    w("    scancode_to_vk_e1,")
    w("    MAKELONG(KLLF_ALTGR, KBD_VERSION),")
    if ligatures:
        w(f"    {max_lig_len},")
        w(f"    sizeof(LIGATURE{max_lig_len}),")
        w(f"    (PLIGATURE1)ligature_table,")
    else:
        w("    0,")
        w("    0,")
        w("    NULL,")
    w("    4,  /* keyboard type */")
    w("    0,  /* keyboard subtype */")
    w("};")
    w("")

    # ── Export ─────────────────────────────────────────────────────────
    w("__declspec(dllexport)")
    w("PKBDTABLES KbdLayerDescriptor(void)")
    w("{")
    w("    return &kbd_tables;")
    w("}")
    w("")

    return "\n".join(lines)


def build_rc(config):
    """Generate the resource file with STRINGTABLE and VERSIONINFO."""
    return f"""#include <windows.h>

STRINGTABLE
BEGIN
    {config['res_id_text']}, "{config['description']}"
    {config['res_id_lang']}, "{config['locale_id']}"
END

1 VERSIONINFO
FILEVERSION     0,1,0,0
PRODUCTVERSION  0,1,0,0
FILEFLAGSMASK   VS_FFI_FILEFLAGSMASK
FILEFLAGS       0
FILEOS          VOS_NT_WINDOWS32
FILETYPE        VFT_DLL
FILESUBTYPE     0
BEGIN
    BLOCK "StringFileInfo"
    BEGIN
        BLOCK "000004B0"
        BEGIN
            VALUE "CompanyName",      "Andrew Kirkouski"
            VALUE "FileDescription",  "{config['description']} Keyboard Layout"
            VALUE "FileVersion",      "0.1"
            VALUE "InternalName",     "{config['kbd_name']} (0.1)"
            VALUE "ProductName",      "{config['description']}"
            VALUE "LegalCopyright",   "\\251 2025\\2014 2026 Andrew Kirkouski"
            VALUE "OriginalFilename", "{config['kbd_name']}"
            VALUE "ProductVersion",   "0.1"
        END
    END
    BLOCK "VarFileInfo"
    BEGIN
        VALUE "Translation", 0x0000, 0x04B0
    END
END
"""


def build_def(config):
    """Generate the module definition file."""
    return f"""LIBRARY {config['kbd_name']}
EXPORTS
    KbdLayerDescriptor @1
"""


def main():
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(LAYOUTS.keys())

    build_dir = os.path.join(SCRIPT_DIR, "build")
    os.makedirs(build_dir, exist_ok=True)

    for target in targets:
        if target not in LAYOUTS:
            print(f"Unknown target: {target}. Use: {', '.join(LAYOUTS.keys())}")
            sys.exit(1)

        config = LAYOUTS[target]
        name = config["kbd_name"]
        print(f"Generating C source for {target} ({name})...")

        c_source = build_c_source(config)
        rc_source = build_rc(config)
        def_source = build_def(config)

        c_path = os.path.join(build_dir, f"{name}.c")
        rc_path = os.path.join(build_dir, f"{name}.rc")
        def_path = os.path.join(build_dir, f"{name}.def")

        for path, content in [(c_path, c_source), (rc_path, rc_source), (def_path, def_source)]:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

        c_lines = c_source.count("\n") + 1
        print(f"  -> {c_path} ({c_lines} lines)")
        print(f"  -> {rc_path}")
        print(f"  -> {def_path}")

    print("Done. Next: python compile_kbd.py")


if __name__ == "__main__":
    main()
