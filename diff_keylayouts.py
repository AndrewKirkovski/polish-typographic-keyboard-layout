#!/usr/bin/env python
"""Compare two keyboard layouts and list all differences.

Accepts .keylayout (XML) or _full.json files. Decodes Mac keycodes
to physical key labels and names each modifier layer.

Usage:
    python diff_keylayouts.py <file_a> <file_b> [--layer N] [--keys-only] [--json]
"""

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

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
    "36": "Return", "48": "Tab", "49": "Space", "51": "Delete",
    "53": "Escape", "65": "KP.", "67": "KP*", "69": "KP+",
    "71": "KPClear", "75": "KP/", "76": "KPEnter", "78": "KP-",
    "81": "KP=", "82": "KP0", "83": "KP1", "84": "KP2",
    "85": "KP3", "86": "KP4", "87": "KP5", "88": "KP6",
    "89": "KP7", "91": "KP8", "92": "KP9",
    "10": "§",
}

LAYER_NAMES: dict[str, str] = {
    "0": "base",
    "1": "shift",
    "2": "caps",
    "3": "altgr",
    "4": "shift+altgr",
    "5": "caps+altgr",
    "6": "opt+cmd",
    "7": "ctrl",
    "8": "shift+opt+cmd",
}


def key_label(code: str) -> str:
    label = MAC_CODE_TO_KEY.get(code, f"?{code}")
    return f"{label} ({code})"


def layer_name(index: str) -> str:
    return LAYER_NAMES.get(index, f"layer-{index}")


# ---------------------------------------------------------------------------
# Parsers
# ---------------------------------------------------------------------------

def _decode_xml_char_refs(text: str) -> str:
    """Decode &#xHHHH; references to actual characters."""
    def _repl(m: re.Match[str]) -> str:
        return chr(int(m.group(1), 16))
    return re.sub(r"&#x([0-9A-Fa-f]+);", _repl, text)


def _preprocess_xml(raw: str) -> str:
    """Handle XML 1.1 control-char placeholders that stdlib can't parse."""
    raw = re.sub(r'<\?xml\s+version="1\.1"', '<?xml version="1.0"', raw)
    def _escape_ctrl(m: re.Match[str]) -> str:
        cp = int(m.group(1), 16)
        if cp < 0x20 and cp not in (0x09, 0x0A, 0x0D):
            return f"__CTRL_{cp:04X}__"
        return m.group(0)
    return re.sub(r"&#x([0-9A-Fa-f]+);", _escape_ctrl, raw)


def _restore_ctrl(text: str) -> str:
    def _repl(m: re.Match[str]) -> str:
        return chr(int(m.group(1), 16))
    return re.sub(r"__CTRL_([0-9A-Fa-f]{4})__", _repl, text)


@dataclass
class KeyEntry:
    output: str | None = None
    action: str | None = None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, KeyEntry):
            return NotImplemented
        return self.output == other.output and self.action == other.action

    def __repr__(self) -> str:
        if self.action is not None:
            return f"act:{self.action}"
        if self.output is not None:
            if len(self.output) == 1:
                cp = ord(self.output)
                if cp < 0x20 or (0x7F <= cp < 0xA0):
                    return f"U+{cp:04X}"
                return f"{self.output} (U+{cp:04X})"
            if self.output == "":
                return '""'
            return repr(self.output)
        return "(none)"


@dataclass
class LayoutData:
    name: str = ""
    key_map_sets: dict[str, dict[str, dict[str, KeyEntry]]] = field(default_factory=dict)
    actions: dict[str, list[dict[str, str]]] = field(default_factory=dict)
    terminators: dict[str, str] = field(default_factory=dict)


def parse_keylayout_xml(path: Path) -> LayoutData:
    raw = path.read_text(encoding="utf-8")
    processed = _preprocess_xml(raw)
    root = ET.fromstring(processed)
    data = LayoutData(name=root.get("name", path.name))

    for kms_el in root.iter("keyMapSet"):
        ks_id = kms_el.get("id", "")
        kms: dict[str, dict[str, KeyEntry]] = {}
        for km_el in kms_el.iter("keyMap"):
            idx = km_el.get("index", "")
            keys: dict[str, KeyEntry] = {}
            for key_el in km_el:
                if key_el.tag != "key":
                    continue
                code = key_el.get("code", "")
                out = key_el.get("output")
                act = key_el.get("action")
                if out is not None:
                    out = _restore_ctrl(_decode_xml_char_refs(out))
                keys[code] = KeyEntry(output=out, action=act)
            kms[idx] = keys
        data.key_map_sets[ks_id] = kms

    for act_el in root.iter("action"):
        act_id = act_el.get("id", "")
        whens: list[dict[str, str]] = []
        for when_el in act_el:
            if when_el.tag != "when":
                continue
            w: dict[str, str] = {}
            for attr in ("state", "output", "next", "through", "multiplier"):
                val = when_el.get(attr)
                if val is not None:
                    if attr == "output":
                        val = _restore_ctrl(_decode_xml_char_refs(val))
                    w[attr] = val
            whens.append(w)
        data.actions[act_id] = whens

    for term_el in root.iter("terminators"):
        for when_el in term_el:
            if when_el.tag != "when":
                continue
            state = when_el.get("state", "")
            out = when_el.get("output", "")
            out = _restore_ctrl(_decode_xml_char_refs(out))
            data.terminators[state] = out

    return data


def parse_full_json(path: Path) -> LayoutData:
    raw = json.loads(path.read_text(encoding="utf-8"))
    data = LayoutData(name=raw.get("keyboard_name", path.name))

    for ks_id, ks_data in raw.get("key_map_sets", {}).items():
        kms: dict[str, dict[str, KeyEntry]] = {}
        for idx, km_data in ks_data.items():
            keys: dict[str, KeyEntry] = {}
            for code, entry in km_data.get("keys", {}).items():
                keys[code] = KeyEntry(
                    output=entry.get("output"),
                    action=entry.get("action"),
                )
            kms[idx] = keys
        data.key_map_sets[ks_id] = kms

    for act_id, whens_raw in raw.get("actions", {}).items():
        data.actions[act_id] = whens_raw

    for term in raw.get("terminators", []):
        data.terminators[term["state"]] = term.get("output", "")

    return data


def load(path: Path) -> LayoutData:
    if path.suffix == ".json":
        return parse_full_json(path)
    return parse_keylayout_xml(path)


# ---------------------------------------------------------------------------
# Diff engine
# ---------------------------------------------------------------------------

@dataclass
class KeyDiff:
    ks_id: str
    layer: str
    code: str
    a: KeyEntry | None
    b: KeyEntry | None


@dataclass
class ActionDiff:
    action_id: str
    a_whens: list[dict[str, str]] | None
    b_whens: list[dict[str, str]] | None


@dataclass
class TermDiff:
    state: str
    a_output: str | None
    b_output: str | None


@dataclass
class DiffResult:
    keys: list[KeyDiff] = field(default_factory=list)
    actions: list[ActionDiff] = field(default_factory=list)
    terminators: list[TermDiff] = field(default_factory=list)


def diff_layouts(a: LayoutData, b: LayoutData, *, layer_filter: str | None = None) -> DiffResult:
    result = DiffResult()

    all_ks = sorted(set(a.key_map_sets) | set(b.key_map_sets))
    for ks_id in all_ks:
        a_ks = a.key_map_sets.get(ks_id, {})
        b_ks = b.key_map_sets.get(ks_id, {})
        all_layers = sorted(set(a_ks) | set(b_ks), key=lambda x: int(x))
        for idx in all_layers:
            if layer_filter is not None and idx != layer_filter:
                continue
            a_km = a_ks.get(idx, {})
            b_km = b_ks.get(idx, {})
            all_codes = sorted(set(a_km) | set(b_km), key=lambda x: int(x))
            for code in all_codes:
                a_entry = a_km.get(code)
                b_entry = b_km.get(code)
                if a_entry == b_entry:
                    continue
                result.keys.append(KeyDiff(
                    ks_id=ks_id, layer=idx, code=code,
                    a=a_entry, b=b_entry,
                ))

    all_act = sorted(set(a.actions) | set(b.actions))
    for act_id in all_act:
        a_whens = a.actions.get(act_id)
        b_whens = b.actions.get(act_id)
        if a_whens == b_whens:
            continue
        result.actions.append(ActionDiff(act_id, a_whens, b_whens))

    all_states = sorted(set(a.terminators) | set(b.terminators))
    for state in all_states:
        a_out = a.terminators.get(state)
        b_out = b.terminators.get(state)
        if a_out == b_out:
            continue
        result.terminators.append(TermDiff(state, a_out, b_out))

    return result


# ---------------------------------------------------------------------------
# Resolve actions to effective output for display
# ---------------------------------------------------------------------------

def resolve_effective(entry: KeyEntry | None, actions: dict[str, list[dict[str, str]]]) -> str:
    """Resolve a key entry to its effective base-state output or dead-key target."""
    if entry is None:
        return "(absent)"
    if entry.output is not None:
        return repr_char(entry.output)
    if entry.action is not None:
        whens = actions.get(entry.action, [])
        for w in whens:
            if w.get("state") == "none":
                if "next" in w:
                    return f"dk:{w['next']}"
                if "output" in w:
                    return repr_char(w["output"])
        return f"act:{entry.action}"
    return "(empty)"


def repr_char(s: str) -> str:
    if not s:
        return '""'
    if len(s) == 1:
        cp = ord(s)
        if cp < 0x20 or (0x7F <= cp < 0xA0):
            return f"U+{cp:04X}"
        return f"{s}  U+{cp:04X}"
    cps = " ".join(f"U+{ord(c):04X}" for c in s)
    return f"{s}  [{cps}]"


# ---------------------------------------------------------------------------
# Output formatters
# ---------------------------------------------------------------------------

def format_text(a: LayoutData, b: LayoutData, result: DiffResult,
                *, keys_only: bool = False, primary_ks: str = "16c") -> str:
    lines: list[str] = []
    lines.append(f"  A: {a.name}")
    lines.append(f"  B: {b.name}")
    lines.append("")

    if result.keys:
        current_layer = ""
        for kd in result.keys:
            if kd.ks_id != primary_ks:
                continue
            ln = layer_name(kd.layer)
            if ln != current_layer:
                current_layer = ln
                lines.append(f"── {ln} ──")
            kl = key_label(kd.code)
            ea = resolve_effective(kd.a, a.actions)
            eb = resolve_effective(kd.b, b.actions)
            lines.append(f"  {kl:<14}  {ea:<24} → {eb}")

        secondary_diffs = [kd for kd in result.keys if kd.ks_id != primary_ks]
        if secondary_diffs:
            lines.append("")
            lines.append(f"── secondary keyMapSets ──")
            current_layer = ""
            for kd in secondary_diffs:
                ln = f"{kd.ks_id}/{layer_name(kd.layer)}"
                if ln != current_layer:
                    current_layer = ln
                    lines.append(f"  [{ln}]")
                kl = key_label(kd.code)
                ea = resolve_effective(kd.a, a.actions)
                eb = resolve_effective(kd.b, b.actions)
                lines.append(f"    {kl:<14}  {ea:<24} → {eb}")

    if keys_only:
        lines.append("")
        lines.append(f"Total key diffs: {len(result.keys)}")
        return "\n".join(lines)

    if result.actions:
        lines.append("")
        lines.append(f"── actions ({len(result.actions)} differ) ──")
        for ad in result.actions:
            label = ad.action_id if ad.action_id else '""'
            if ad.a_whens is None:
                lines.append(f"  + {label}  (added in B, {len(ad.b_whens or [])} whens)")
            elif ad.b_whens is None:
                lines.append(f"  - {label}  (removed in B, was {len(ad.a_whens)} whens)")
            else:
                lines.append(f"  ~ {label}")
                a_map = {w.get("state", ""): w for w in ad.a_whens}
                b_map = {w.get("state", ""): w for w in (ad.b_whens or [])}
                for state in sorted(set(a_map) | set(b_map)):
                    aw = a_map.get(state)
                    bw = b_map.get(state)
                    if aw == bw:
                        continue
                    aw_s = _when_short(aw) if aw else "(absent)"
                    bw_s = _when_short(bw) if bw else "(absent)"
                    lines.append(f"      state={state!r}: {aw_s} → {bw_s}")

    if result.terminators:
        lines.append("")
        lines.append(f"── terminators ({len(result.terminators)} differ) ──")
        for td in result.terminators:
            ao = repr_char(td.a_output) if td.a_output is not None else "(absent)"
            bo = repr_char(td.b_output) if td.b_output is not None else "(absent)"
            lines.append(f"  state={td.state!r}: {ao} → {bo}")

    lines.append("")
    lines.append(
        f"Summary: {len(result.keys)} key diffs, "
        f"{len(result.actions)} action diffs, "
        f"{len(result.terminators)} terminator diffs"
    )
    return "\n".join(lines)


def _when_short(w: dict[str, str]) -> str:
    parts: list[str] = []
    if "output" in w:
        parts.append(f"out={repr_char(w['output'])}")
    if "next" in w:
        parts.append(f"next={w['next']}")
    if "through" in w:
        parts.append(f"through={w['through']}")
    return ", ".join(parts) if parts else str(w)


def format_json_output(a: LayoutData, b: LayoutData, result: DiffResult) -> str:
    out: dict[str, Any] = {
        "a_name": a.name,
        "b_name": b.name,
        "key_diffs": [],
        "action_diffs": [],
        "terminator_diffs": [],
    }
    for kd in result.keys:
        out["key_diffs"].append({
            "keyMapSet": kd.ks_id,
            "layer": layer_name(kd.layer),
            "layer_index": kd.layer,
            "key": key_label(kd.code),
            "code": kd.code,
            "a": resolve_effective(kd.a, a.actions),
            "b": resolve_effective(kd.b, b.actions),
        })
    for ad in result.actions:
        out["action_diffs"].append({
            "action_id": ad.action_id,
            "a_whens": ad.a_whens,
            "b_whens": ad.b_whens,
        })
    for td in result.terminators:
        out["terminator_diffs"].append({
            "state": td.state,
            "a": td.a_output,
            "b": td.b_output,
        })
    return json.dumps(out, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    _reconfigure = getattr(sys.stdout, "reconfigure", None)
    if _reconfigure is not None:
        _reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Diff two keyboard layouts")
    parser.add_argument("file_a", type=Path)
    parser.add_argument("file_b", type=Path)
    parser.add_argument("--layer", type=str, default=None,
                        help="Only show diffs for this layer index (0-8)")
    parser.add_argument("--keys-only", action="store_true",
                        help="Only show key diffs, skip actions/terminators")
    parser.add_argument("--json", action="store_true", dest="json_out",
                        help="Output as JSON")
    args = parser.parse_args()

    a = load(args.file_a)
    b = load(args.file_b)
    result = diff_layouts(a, b, layer_filter=args.layer)

    if args.json_out:
        print(format_json_output(a, b, result))
    else:
        print(format_text(a, b, result, keys_only=args.keys_only))


if __name__ == "__main__":
    main()
