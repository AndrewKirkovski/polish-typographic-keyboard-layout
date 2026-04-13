"""Adapter: convert macOS-centric *_full.json to flat layers for Windows generators.

The full JSON (produced by extract_base.py) uses macOS keycodes and an action
state machine for dead keys. Windows generators need flat key-ID layers and
explicit dead key composition tables. This module bridges the gap.

Used by build_kbd_c.py and build_klc.py.
"""

from typing import Any

# Mac keycode (string) -> key ID (human label)
MAC_CODE_TO_KEY: dict[str, str] = {
    "0": "A", "1": "S", "2": "D", "3": "F", "4": "H", "5": "G",
    "6": "Z", "7": "X", "8": "C", "9": "V",
    "11": "B", "12": "Q", "13": "W", "14": "E", "15": "R",
    "16": "Y", "17": "T", "18": "1", "19": "2", "20": "3",
    "21": "4", "22": "6", "23": "5", "24": "=", "25": "9",
    "26": "7", "27": "-", "28": "8", "29": "0", "30": "]",
    "31": "O", "32": "U", "33": "[", "34": "I", "35": "P",
    "37": "L", "38": "J", "39": "'", "40": "K", "41": ";",
    "42": "\\", "43": ",", "44": "/", "45": "N", "46": "M",
    "47": ".", "50": "`",
}

# Key ID -> (scancode_hex, VK_name, is_letter) — Windows-specific
KEY_MAP: dict[str, tuple[str, str, bool]] = {
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


def _resolve_action_base_output(
    action_id: str,
    actions: dict[str, list[dict[str, str]]],
) -> tuple[str | None, str | None]:
    """Resolve an action to its base-state behavior.

    Returns (output_char, next_state):
    - Direct output: ("a", None)
    - Dead key:      (None, "acute")
    - Unresolvable:  (None, None)
    """
    whens = actions.get(action_id, [])
    for w in whens:
        if w.get("state") == "none":
            if "next" in w:
                return None, w["next"]
            if "output" in w:
                return w["output"], None
    return None, None


def _extract_key_entry(
    key_data: dict[str, Any] | None,
    actions: dict[str, list[dict[str, str]]],
) -> str | dict[str, str] | None:
    """Convert a full-JSON key entry to an overlay-style entry.

    Returns:
    - str: direct character output (for base/shift layers)
    - dict: {"char": "dk:name", ...} or {"char": "x", ...} (for altgr layers)
    - None: key is absent/unassigned
    """
    if key_data is None:
        return None

    out = key_data.get("output")
    if out is not None:
        return out

    act_id = key_data.get("action")
    if act_id is not None:
        char, next_state = _resolve_action_base_output(act_id, actions)
        if next_state is not None:
            return {"char": f"dk:{next_state}", "name": f"dead key: {next_state}"}
        if char is not None:
            return char

    return None


def _entry_to_overlay_dict(val: str | dict | None) -> dict[str, str] | None:
    """Normalize a resolved entry to overlay dict format for altgr layers."""
    if val is None:
        return None
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        return {"char": val, "name": ""}


def extract_layers_from_full_json(data: dict[str, Any]) -> dict[str, Any]:
    """Convert macOS-centric full JSON to flat layers + dead key tables.

    Returns dict with keys:
    - "base": {key_id: char_str, ...}
    - "shift": {key_id: char_str, ...}
    - "altgr": {key_id: {"char": ..., "name": ...} | None, ...}
    - "shift_altgr": {key_id: {"char": ..., "name": ...} | None, ...}
    - "dead_key_chars": {state_name: char_codepoint, ...}
    - "dead_key_compositions": {dk_char_code: [(base_cp, result_cp), ...], ...}
    """
    actions = data.get("actions", {})

    ks_id = next(iter(data.get("key_map_sets", {})), None)
    if ks_id is None:
        raise ValueError("No key_map_sets found in full JSON")

    kms = data["key_map_sets"][ks_id]
    km_base = kms.get("0", {}).get("keys", {})
    km_shift = kms.get("1", {}).get("keys", {})
    km_altgr = kms.get("3", {}).get("keys", {})
    km_sh_altgr = kms.get("4", {}).get("keys", {})

    base: dict[str, str] = {}
    shift: dict[str, str] = {}
    altgr: dict[str, dict[str, str] | None] = {}
    sh_altgr: dict[str, dict[str, str] | None] = {}

    for mac_code, key_id in MAC_CODE_TO_KEY.items():
        if key_id not in KEY_MAP:
            continue

        b = _extract_key_entry(km_base.get(mac_code), actions)
        if isinstance(b, str):
            base[key_id] = b

        s = _extract_key_entry(km_shift.get(mac_code), actions)
        if isinstance(s, str):
            shift[key_id] = s

        ag = _extract_key_entry(km_altgr.get(mac_code), actions)
        altgr[key_id] = _entry_to_overlay_dict(ag) if ag is not None else None

        sag = _extract_key_entry(km_sh_altgr.get(mac_code), actions)
        sh_altgr[key_id] = _entry_to_overlay_dict(sag) if sag is not None else None

    dk_chars, dk_comps = extract_dead_keys_from_actions(data)

    # macOS uses U+02C6 (MODIFIER LETTER CIRCUMFLEX) as the circumflex
    # terminator, but Windows keyboard drivers expect U+005E (ASCII CARET).
    if "circumflex" in dk_chars and dk_chars["circumflex"] == 0x02C6:
        old_cp = 0x02C6
        new_cp = 0x005E
        dk_chars["circumflex"] = new_cp
        if old_cp in dk_comps:
            dk_comps[new_cp] = dk_comps.pop(old_cp)

    return {
        "base": base,
        "shift": shift,
        "altgr": altgr,
        "shift_altgr": sh_altgr,
        "dead_key_chars": dk_chars,
        "dead_key_compositions": dk_comps,
    }


def extract_dead_keys_from_actions(
    data: dict[str, Any],
) -> tuple[dict[str, int], dict[int, list[tuple[int, int]]]]:
    """Build dead key composition tables from the full JSON action state machine.

    Returns:
    - dead_key_chars: {state_name: terminator_codepoint, ...}
    - dead_key_compositions: {dk_char_code: [(base_cp, result_cp), ...], ...}
    """
    actions = data.get("actions", {})
    terminators_list = data.get("terminators", [])

    dk_chars: dict[str, int] = {}
    for term in terminators_list:
        state = term.get("state", "")
        out = term.get("output", "")
        if state and out and len(out) == 1:
            dk_chars[state] = ord(out)

    dk_comps: dict[int, list[tuple[int, int]]] = {}

    for state_name, dk_cp in dk_chars.items():
        compositions: list[tuple[int, int]] = []

        for whens in actions.values():
            base_char: str | None = None
            result_char: str | None = None

            for w in whens:
                if w.get("state") == "none" and "output" in w:
                    base_char = w["output"]
                if w.get("state") == state_name and "output" in w:
                    result_char = w["output"]

            if base_char and result_char and len(base_char) == 1 and len(result_char) == 1:
                compositions.append((ord(base_char), ord(result_char)))

        compositions.sort()

        if compositions:
            existing = dk_comps.get(dk_cp, [])
            seen = set(existing)
            for pair in compositions:
                if pair not in seen:
                    existing.append(pair)
                    seen.add(pair)
            dk_comps[dk_cp] = existing

    return dk_chars, dk_comps
