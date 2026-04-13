"""Extract full keylayout structure from original Birman files and apply overlays.

Reads the original Birman .keylayout files, parses the complete structure
(all keyMaps, actions, dead keys, terminators, secondary keyMapSets), then
applies the Kirkouski overlay JSONs to produce the merged *_full.json files.

Usage:
    python extract_base.py
"""
import re
import json
import sys
import os
import xml.etree.ElementTree as ET
import copy
from typing import Any

# Pyright doesn't know `reconfigure` exists on the TextIO base class, but it
# does on the concrete TextIOWrapper used at runtime. Call via getattr so the
# type checker is satisfied without losing the safety the call provides.
_reconfigure = getattr(sys.stdout, "reconfigure", None)
if _reconfigure is not None:
    _reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _read_version():
    """Read project version from the repo-root VERSION file."""
    with open(os.path.join(SCRIPT_DIR, "VERSION"), encoding="utf-8") as f:
        return f.read().strip()


VERSION = _read_version()


def parse_xml11(filepath):
    """Parse XML 1.1 file (allows control char refs)."""
    with open(filepath, "r", encoding="utf-8") as f:
        xml_text = f.read()
    # Downgrade to XML 1.0 for Python parser, preserving control char refs as placeholders
    xml_text = xml_text.replace('version="1.1"', 'version="1.0"')

    def replace_control_ref(m):
        cp = int(m.group(1), 16)
        if cp in (0x09, 0x0A, 0x0D):
            return m.group(0)  # valid in XML 1.0
        if cp < 0x20 or cp == 0x7F:
            # Control chars invalid in XML 1.0 — use PUA placeholder
            return chr(0xE000 + cp)
        # Printable chars — let the XML parser handle them normally
        return m.group(0)
    xml_text = re.sub(r'&#x([0-9A-Fa-f]+);', replace_control_ref, xml_text)
    return ET.fromstring(xml_text)


def extract_keylayout(filepath):
    """Extract complete keylayout structure into a dict."""
    root = parse_xml11(filepath)

    result = {
        "keyboard_name": root.get("name", ""),
        "keyboard_group": root.get("group", ""),
        "keyboard_id": root.get("id", ""),
        "keyboard_maxout": root.get("maxout", ""),
        "layouts": [],
        "modifier_map": {},
        "key_map_sets": {},
        "actions": {},
        "terminators": [],
    }

    # Layouts
    for layout_el in root.iter("layout"):
        result["layouts"].append({
            "first": layout_el.get("first"),
            "last": layout_el.get("last"),
            "mapSet": layout_el.get("mapSet"),
            "modifiers": layout_el.get("modifiers"),
        })

    # Modifier map
    for mm in root.iter("modifierMap"):
        mm_id = mm.get("id")
        mm_data = {"defaultIndex": mm.get("defaultIndex"), "selects": []}
        for kms in mm.findall("keyMapSelect"):
            idx = kms.get("mapIndex")
            modifiers = []
            for mod in kms.findall("modifier"):
                modifiers.append(mod.get("keys", ""))
            mm_data["selects"].append({"mapIndex": idx, "modifiers": modifiers})
        result["modifier_map"][mm_id] = mm_data

    # Key map sets
    for kms in root.iter("keyMapSet"):
        kms_id = kms.get("id")
        key_maps = {}
        for km in kms.findall("keyMap"):
            index = km.get("index")
            base_map_set = km.get("baseMapSet")
            base_index = km.get("baseIndex")

            # `km_data` is heterogeneous (mixes str values and a nested dict),
            # so type-annotate as dict[str, Any] to silence Pyright's narrowing
            # of the empty literal to dict[str, dict[Unknown, Unknown]].
            km_data: dict[str, Any] = {"keys": {}}
            if base_map_set:
                km_data["baseMapSet"] = base_map_set
                km_data["baseIndex"] = base_index

            for key_el in km.findall("key"):
                code = key_el.get("code")
                entry = {}
                if key_el.get("output") is not None:
                    entry["output"] = key_el.get("output")
                if key_el.get("action") is not None:
                    entry["action"] = key_el.get("action")
                km_data["keys"][code] = entry

            key_maps[index] = km_data
        result["key_map_sets"][kms_id] = key_maps

    # Actions
    for action_el in root.iter("action"):
        action_id = action_el.get("id")
        whens = []
        for when_el in action_el.findall("when"):
            when_data = {}
            for attr in ("state", "next", "output", "through", "multiplier"):
                val = when_el.get(attr)
                if val is not None:
                    when_data[attr] = val
            whens.append(when_data)
        result["actions"][action_id] = whens

    # Terminators
    for term_el in root.iter("terminators"):
        for when_el in term_el.findall("when"):
            result["terminators"].append({
                "state": when_el.get("state"),
                "output": when_el.get("output"),
            })

    return result


# Mac keycode -> key ID mapping
MAC_CODE_TO_KEY = {
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
KEY_TO_MAC_CODE = {v: k for k, v in MAC_CODE_TO_KEY.items()}


def apply_overlay(full_data, overlay_json_path, layout_name):
    """Apply our merged layout overlay onto the full keylayout data."""
    with open(overlay_json_path, encoding="utf-8") as f:
        overlay = json.load(f)

    data = copy.deepcopy(full_data)
    data["keyboard_name"] = layout_name

    altgr = overlay["layers"].get("altgr", {})
    sh_altgr = overlay["layers"].get("shift_altgr", {})
    base = overlay["layers"].get("base", {})
    shift = overlay["layers"].get("shift", {})

    # Get the primary keyMapSet ID
    primary_set_id = None
    for kms_id, key_maps in data["key_map_sets"].items():
        if "0" in key_maps and "3" in key_maps:
            primary_set_id = kms_id
            break
    if not primary_set_id:
        print("ERROR: Could not find primary keyMapSet!", file=sys.stderr)
        return data

    key_maps = data["key_map_sets"][primary_set_id]

    # Layer index mapping (from Birman modifier map):
    # 0 = base, 1 = shift, 2 = caps, 3 = option, 4 = shift+option, 5 = caps+option

    # Apply base layer changes (index 0)
    if base:
        for key_id, char in base.items():
            mac_code = KEY_TO_MAC_CODE.get(key_id)
            if mac_code and char:
                km = key_maps.get("0", {}).get("keys", {})
                # Find the original entry for this keycode
                orig = km.get(mac_code, {})
                if orig.get("action"):
                    # Key uses an action — we need to update the action's base output
                    action_id = orig["action"]
                    if action_id in data["actions"]:
                        for when in data["actions"][action_id]:
                            if when.get("state") == "none" and "output" in when:
                                when["output"] = char
                                break
                else:
                    km[mac_code] = {"output": char}

    # Apply shift layer changes (index 1)
    if shift:
        for key_id, char in shift.items():
            mac_code = KEY_TO_MAC_CODE.get(key_id)
            if mac_code and char:
                km = key_maps.get("1", {}).get("keys", {})
                orig = km.get(mac_code, {})
                if orig.get("action"):
                    action_id = orig["action"]
                    if action_id in data["actions"]:
                        for when in data["actions"][action_id]:
                            if when.get("state") == "none" and "output" in when:
                                when["output"] = char
                                break
                else:
                    km[mac_code] = {"output": char}

    # Apply caps layer (index 2) — should match shift for letters
    if shift:
        for key_id, char in shift.items():
            mac_code = KEY_TO_MAC_CODE.get(key_id)
            if mac_code and char and key_id.isalpha():
                km = key_maps.get("2", {}).get("keys", {})
                orig = km.get(mac_code, {})
                if orig.get("action"):
                    action_id = orig["action"]
                    if action_id in data["actions"]:
                        for when in data["actions"][action_id]:
                            if when.get("state") == "none" and "output" in when:
                                when["output"] = char
                                break
                else:
                    km[mac_code] = {"output": char}

    # Apply AltGr layer changes (index 3 = option)
    for key_id, entry in altgr.items():
        mac_code = KEY_TO_MAC_CODE.get(key_id)
        if not mac_code:
            continue
        km = key_maps.get("3", {}).get("keys", {})
        if entry is None:
            km.pop(mac_code, None)
            continue
        else:
            char = entry.get("char", "")
            if char.startswith("dk:"):
                dk_name = char.replace("dk:", "")
                # Find or create action for this dead key
                action_id = _ensure_dead_key_action(data, dk_name)
                km[mac_code] = {"action": action_id}
            elif char.startswith("act:"):
                dk_name = char.replace("act:", "").strip()
                action_id = _ensure_dead_key_action(data, dk_name)
                km[mac_code] = {"action": action_id}
            elif char:
                km[mac_code] = {"output": char}

    # Apply Shift+AltGr layer changes (index 4 = shift+option)
    for key_id, entry in sh_altgr.items():
        mac_code = KEY_TO_MAC_CODE.get(key_id)
        if not mac_code:
            continue
        km = key_maps.get("4", {}).get("keys", {})
        if entry is None:
            km.pop(mac_code, None)
            continue
        else:
            char = entry.get("char", "")
            if char.startswith("dk:"):
                dk_name = char.replace("dk:", "")
                action_id = _ensure_dead_key_action(data, dk_name)
                km[mac_code] = {"action": action_id}
            elif char.startswith("act:"):
                dk_name = char.replace("act:", "").strip()
                action_id = _ensure_dead_key_action(data, dk_name)
                km[mac_code] = {"action": action_id}
            elif char:
                km[mac_code] = {"output": char}

    # Apply caps+option (index 5) — only for Kirkouski-specific overrides.
    # Birman's km=5 is an independent Latin-typographic layer (Å Î Ï Ó etc.),
    # NOT a mirror of shift+option. Preserve it for "BI"-sourced entries.
    # Null entries → remove from km=5 (intentionally unassigned).
    if "5" in key_maps:
        km5 = key_maps["5"].get("keys", {})
        for key_id, entry in sh_altgr.items():
            mac_code = KEY_TO_MAC_CODE.get(key_id)
            if not mac_code:
                continue
            if entry is None:
                km5.pop(mac_code, None)
                continue
            if entry.get("source") == "BI":
                continue
            char = entry.get("char", "")
            if char.startswith("dk:") or char.startswith("act:"):
                dk_name = char.replace("dk:", "").replace("act:", "").strip()
                action_id = _ensure_dead_key_action(data, dk_name)
                km5[mac_code] = {"action": action_id}
            elif char:
                km5[mac_code] = {"output": char}

    return data


def _ensure_dead_key_action(data, dk_name):
    """Ensure a dead key action exists, return its action ID."""
    # Look for existing action that enters this dead key state
    state_name = dk_name  # Birman uses the dk name directly as state
    for action_id, whens in data["actions"].items():
        for when in whens:
            if when.get("state") == "none" and when.get("next") == state_name:
                return action_id

    # Also check with state_ prefix
    state_name2 = f"state_{dk_name}"
    for action_id, whens in data["actions"].items():
        for when in whens:
            if when.get("state") == "none" and when.get("next") == state_name2:
                return action_id

    # Not found — create a new action
    action_id = f"dk_{dk_name}"
    data["actions"][action_id] = [{"state": "none", "next": state_name}]
    return action_id



def main():
    import glob

    # Find Birman source files by glob (filename encoding varies by OS)
    en_matches = glob.glob(os.path.join(SCRIPT_DIR, "English*Birman*.keylayout"))
    ru_matches = glob.glob(os.path.join(SCRIPT_DIR, "Russian*Birman*.keylayout"))
    if not en_matches or not ru_matches:
        print("ERROR: Original Birman .keylayout files not found in project root.", file=sys.stderr)
        print("  Download from https://ilyabirman.ru/typography-layout/", file=sys.stderr)
        sys.exit(1)
    en_keylayout = en_matches[0]
    ru_keylayout = ru_matches[0]

    # Canonical overlay sources live at repo root and are tracked in git.
    # We used to read from stale v0.1 copies in .local/ which meant every
    # v0.2/v0.3 release shipped v0.1-era overlay content (including the
    # `dk:acute-2` orphan in Russian that silently broke registration on
    # macOS, and never picked up the complete base/shift Cyrillic layers
    # added to the canonical files later).
    pl_overlay = os.path.join(SCRIPT_DIR, "polish_typographic.json")
    ru_overlay = os.path.join(SCRIPT_DIR, "russian_typographic.json")

    for path in [pl_overlay, ru_overlay]:
        if not os.path.exists(path):
            print(f"ERROR: Missing overlay file: {path}", file=sys.stderr)
            sys.exit(1)

    # Extract full structure from originals
    print("Extracting English Birman keylayout...", file=sys.stderr)
    en_full = extract_keylayout(en_keylayout)
    print(f"  {len(en_full['actions'])} actions, "
          f"{sum(len(km['keys']) for km in en_full['key_map_sets'].get('16c', {}).values())} key entries",
          file=sys.stderr)

    print("Extracting Russian Birman keylayout...", file=sys.stderr)
    ru_full = extract_keylayout(ru_keylayout)

    # Apply overlays
    print("Applying Polish overlay...", file=sys.stderr)
    pl_data = apply_overlay(en_full, pl_overlay, f"Polish Typographic by Kirkouski v{VERSION}")

    print("Applying Russian overlay...", file=sys.stderr)
    ru_data = apply_overlay(ru_full, ru_overlay, f"Russian Typographic by Kirkouski v{VERSION}")

    # Save complete JSONs (these become the tracked source of truth)
    pl_json_path = os.path.join(SCRIPT_DIR, "polish_typographic_full.json")
    ru_json_path = os.path.join(SCRIPT_DIR, "russian_typographic_full.json")

    with open(pl_json_path, "w", encoding="utf-8") as f:
        json.dump(pl_data, f, ensure_ascii=False, indent=2)
    print(f"Saved: {pl_json_path}", file=sys.stderr)

    with open(ru_json_path, "w", encoding="utf-8") as f:
        json.dump(ru_data, f, ensure_ascii=False, indent=2)
    print(f"Saved: {ru_json_path}", file=sys.stderr)

    print("Done.", file=sys.stderr)


if __name__ == "__main__":
    main()
