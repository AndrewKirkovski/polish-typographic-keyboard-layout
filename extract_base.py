"""Extract full keylayout structure from original Birman files into JSON.

One-time script. Reads the original .keylayout, dumps the COMPLETE structure
(all keyMaps, all actions, all dead keys, terminators, secondary keyMapSets)
into a JSON file. Then applies our overlay changes (relocated symbols, Polish
diacritics, etc.) to produce the final source JSONs.

Usage:
    python extract_base.py
"""
import re
import json
import sys
import os
import xml.etree.ElementTree as ET
import copy

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


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

            km_data = {"keys": {}}
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
            # Clear this key — output the base character
            base_char = base.get(key_id, "")
            if base_char:
                km[mac_code] = {"output": base_char}
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
            shift_char = shift.get(key_id, "")
            if shift_char:
                km[mac_code] = {"output": shift_char}
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

    # Apply caps+option (index 5) — only update keys we changed in option (index 3)
    # The original Birman caps+option layer already has correct uppercase handling
    # for unchanged keys. We only need to patch the keys we modified.
    if "5" in key_maps:
        km5 = key_maps["5"].get("keys", {})
        for key_id, entry in altgr.items():
            mac_code = KEY_TO_MAC_CODE.get(key_id)
            if not mac_code:
                continue
            if entry is None:
                # Cleared key — output uppercase base char
                shift_char = shift.get(key_id, "")
                if isinstance(shift_char, str) and shift_char:
                    km5[mac_code] = {"output": shift_char}
            else:
                char = entry.get("char", "")
                if char and char.upper() != char and len(char) == 1:
                    # Has uppercase variant — use it
                    km5[mac_code] = {"output": char.upper()}
                elif char.startswith("dk:") or char.startswith("act:"):
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


def serialize_keylayout(data):
    """Serialize the full keylayout data back to XML 1.1 string."""
    lines = []
    lines.append('<?xml version="1.1" encoding="UTF-8"?>')
    lines.append('<!DOCTYPE keyboard SYSTEM "file://localhost/System/Library/DTDs/KeyboardLayout.dtd">')

    attrs = f'group="{data["keyboard_group"]}" id="{data["keyboard_id"]}"'
    attrs += f' name="{esc_attr(data["keyboard_name"])}" maxout="{data["keyboard_maxout"]}"'
    lines.append(f'<keyboard {attrs}>')

    # Layouts
    lines.append('\t<layouts>')
    for layout in data["layouts"]:
        lines.append(f'\t\t<layout first="{layout["first"]}" last="{layout["last"]}"'
                     f' mapSet="{layout["mapSet"]}" modifiers="{layout["modifiers"]}"/>')
    lines.append('\t</layouts>')

    # Modifier maps
    for mm_id, mm_data in data["modifier_map"].items():
        lines.append(f'\t<modifierMap id="{mm_id}" defaultIndex="{mm_data["defaultIndex"]}">')
        for select in mm_data["selects"]:
            lines.append(f'\t\t<keyMapSelect mapIndex="{select["mapIndex"]}">')
            for mod_keys in select["modifiers"]:
                lines.append(f'\t\t\t<modifier keys="{mod_keys}"/>')
            lines.append(f'\t\t</keyMapSelect>')
        lines.append(f'\t</modifierMap>')

    # Key map sets
    for kms_id in sorted(data["key_map_sets"].keys()):
        key_maps = data["key_map_sets"][kms_id]
        lines.append(f'\t<keyMapSet id="{kms_id}">')
        for idx in sorted(key_maps.keys(), key=int):
            km_data = key_maps[idx]
            attrs = f'index="{idx}"'
            if "baseMapSet" in km_data:
                attrs += f' baseMapSet="{km_data["baseMapSet"]}" baseIndex="{km_data["baseIndex"]}"'
            lines.append(f'\t\t<keyMap {attrs}>')
            for code in sorted(km_data["keys"].keys(), key=int):
                entry = km_data["keys"][code]
                if "output" in entry:
                    out = esc_output(entry["output"])
                    lines.append(f'\t\t\t<key code="{code}" output="{out}"/>')
                elif "action" in entry:
                    lines.append(f'\t\t\t<key code="{code}" action="{esc_attr(entry["action"])}"/>')
            lines.append(f'\t\t</keyMap>')
        lines.append(f'\t</keyMapSet>')

    # Actions
    if data["actions"]:
        lines.append('\t<actions>')
        for action_id in sorted(data["actions"].keys()):
            whens = data["actions"][action_id]
            lines.append(f'\t\t<action id="{esc_attr(action_id)}">')
            for when in whens:
                attrs_parts = []
                if "state" in when:
                    attrs_parts.append(f'state="{esc_attr(when["state"])}"')
                if "next" in when:
                    attrs_parts.append(f'next="{esc_attr(when["next"])}"')
                if "output" in when:
                    attrs_parts.append(f'output="{esc_output(when["output"])}"')
                if "through" in when:
                    attrs_parts.append(f'through="{esc_attr(when["through"])}"')
                if "multiplier" in when:
                    attrs_parts.append(f'multiplier="{esc_attr(when["multiplier"])}"')
                lines.append(f'\t\t\t<when {" ".join(attrs_parts)}"/>')
            lines.append(f'\t\t</action>')
        lines.append('\t</actions>')

    # Terminators
    if data["terminators"]:
        lines.append('\t<terminators>')
        for term in data["terminators"]:
            out = esc_output(term["output"])
            lines.append(f'\t\t<when state="{esc_attr(term["state"])}" output="{out}"/>')
        lines.append('\t</terminators>')

    lines.append('</keyboard>')
    return "\n".join(lines)


def esc_attr(text):
    """Escape XML attribute value."""
    if not text:
        return ""
    return (text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;"))


def esc_output(text):
    """Escape output value, converting PUA placeholders and control chars back to &#x refs."""
    if not text:
        return ""
    result = []
    for ch in text:
        cp = ord(ch)
        # PUA placeholder for control chars (set during parsing)
        if 0xE000 <= cp <= 0xE07F:
            orig_cp = cp - 0xE000
            result.append(f"&#x{orig_cp:04X};")
        elif cp < 0x20 or cp == 0x7F:
            # Control chars (TAB, CR, LF, etc.) — encode as &#x refs
            result.append(f"&#x{cp:04X};")
        elif ch == "&":
            result.append("&amp;")
        elif ch == "<":
            result.append("&lt;")
        elif ch == ">":
            result.append("&gt;")
        elif ch == '"':
            result.append("&quot;")
        else:
            result.append(ch)
    return "".join(result)


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

    pl_overlay = os.path.join(SCRIPT_DIR, ".local", "merged_layout.json")
    ru_overlay = os.path.join(SCRIPT_DIR, ".local", "russian_merged_layout.json")

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
    pl_data = apply_overlay(en_full, pl_overlay, "Polish Typographic by Kirkouski v0.1")

    print("Applying Russian overlay...", file=sys.stderr)
    ru_data = apply_overlay(ru_full, ru_overlay, "Russian Typographic by Kirkouski v0.1")

    # Save complete JSONs (these become the tracked source of truth)
    pl_json_path = os.path.join(SCRIPT_DIR, "polish_typographic_full.json")
    ru_json_path = os.path.join(SCRIPT_DIR, "russian_typographic_full.json")

    with open(pl_json_path, "w", encoding="utf-8") as f:
        json.dump(pl_data, f, ensure_ascii=False, indent=2)
    print(f"Saved: {pl_json_path}", file=sys.stderr)

    with open(ru_json_path, "w", encoding="utf-8") as f:
        json.dump(ru_data, f, ensure_ascii=False, indent=2)
    print(f"Saved: {ru_json_path}", file=sys.stderr)

    # Also generate .keylayout files directly
    os.makedirs(os.path.join(SCRIPT_DIR, "dist"), exist_ok=True)

    pl_keylayout = serialize_keylayout(pl_data)
    pl_out = os.path.join(SCRIPT_DIR, "dist", "polish_typographic.keylayout")
    with open(pl_out, "w", encoding="utf-8") as f:
        f.write(pl_keylayout)
    print(f"Built: {pl_out} ({pl_keylayout.count(chr(10))+1} lines)", file=sys.stderr)

    ru_keylayout_out = serialize_keylayout(ru_data)
    ru_out = os.path.join(SCRIPT_DIR, "dist", "russian_typographic.keylayout")
    with open(ru_out, "w", encoding="utf-8") as f:
        f.write(ru_keylayout_out)
    print(f"Built: {ru_out} ({ru_keylayout_out.count(chr(10))+1} lines)", file=sys.stderr)

    print("Done.", file=sys.stderr)


if __name__ == "__main__":
    main()
