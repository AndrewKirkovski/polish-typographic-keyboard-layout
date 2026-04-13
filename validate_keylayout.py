#!/usr/bin/env python
"""Validate .keylayout XML or _full.json files for common issues.

Checks:
  - Orphan dead key states (reachable but no terminator / no exit)
  - Actions referenced by keys but not defined
  - Keys referencing undefined actions
  - Multi-character output values (potential str.upper() leak)
  - Unused actions (defined but never referenced)

Usage:
    python validate_keylayout.py <file> [<file2> ...]
    python validate_keylayout.py dist/*.keylayout
    python validate_keylayout.py *_full.json
"""

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

_reconfigure = getattr(sys.stdout, "reconfigure", None)
if _reconfigure is not None:
    _reconfigure(encoding="utf-8", errors="replace")

MAC_CODE_TO_KEY: dict[str, str] = {
    "0": "A", "1": "S", "2": "D", "3": "F", "4": "H", "5": "G",
    "6": "Z", "7": "X", "8": "C", "9": "V",
    "10": "§",
    "11": "B", "12": "Q", "13": "W", "14": "E", "15": "R",
    "16": "Y", "17": "T", "18": "1", "19": "2", "20": "3",
    "21": "4", "22": "6", "23": "5", "24": "=", "25": "9",
    "26": "7", "27": "-", "28": "8", "29": "0", "30": "]",
    "31": "O", "32": "U", "33": "[", "34": "I", "35": "P",
    "36": "Return", "37": "L", "38": "J", "39": "'", "40": "K",
    "41": ";", "42": "\\", "43": ",", "44": "/", "45": "N",
    "46": "M", "47": ".", "48": "Tab", "49": "Space", "50": "`",
    "51": "Delete", "53": "Escape",
}

LAYER_NAMES: dict[str, str] = {
    "0": "base", "1": "shift", "2": "caps", "3": "altgr",
    "4": "shift+altgr", "5": "caps+altgr", "6": "opt+cmd",
    "7": "ctrl", "8": "shift+opt+cmd",
}


def key_label(code: str) -> str:
    return MAC_CODE_TO_KEY.get(code, f"?{code}")


def layer_name(index: str) -> str:
    return LAYER_NAMES.get(index, f"layer-{index}")


# ---------------------------------------------------------------------------
# Issue types
# ---------------------------------------------------------------------------

@dataclass
class Issue:
    severity: str  # ERROR, WARN
    code: str
    message: str
    location: str = ""

    def __str__(self) -> str:
        loc = f" [{self.location}]" if self.location else ""
        return f"  {self.severity}: {self.code}{loc} — {self.message}"


# ---------------------------------------------------------------------------
# Parsers (same as diff_keylayouts.py, kept self-contained)
# ---------------------------------------------------------------------------

def _preprocess_xml(raw: str) -> str:
    raw = re.sub(r'<\?xml\s+version="1\.1"', '<?xml version="1.0"', raw)
    def _escape_ctrl(m: re.Match[str]) -> str:
        cp = int(m.group(1), 16)
        if cp < 0x20 and cp not in (0x09, 0x0A, 0x0D):
            return f"__CTRL_{cp:04X}__"
        return m.group(0)
    return re.sub(r"&#x([0-9A-Fa-f]+);", _escape_ctrl, raw)


def _decode_refs(text: str) -> str:
    def _repl(m: re.Match[str]) -> str:
        return chr(int(m.group(1), 16))
    text = re.sub(r"&#x([0-9A-Fa-f]+);", _repl, text)
    return re.sub(r"__CTRL_([0-9A-Fa-f]{4})__", _repl, text)


@dataclass
class LayoutData:
    name: str = ""
    key_map_sets: dict[str, dict[str, dict[str, dict]]] = field(default_factory=dict)
    actions: dict[str, list[dict[str, str]]] = field(default_factory=dict)
    terminators: dict[str, str] = field(default_factory=dict)


def parse_xml(path: Path) -> LayoutData:
    raw = path.read_text(encoding="utf-8")
    root = ET.fromstring(_preprocess_xml(raw))
    data = LayoutData(name=root.get("name", path.name))

    for kms_el in root.iter("keyMapSet"):
        ks_id = kms_el.get("id", "")
        kms: dict[str, dict[str, dict]] = {}
        for km_el in kms_el.iter("keyMap"):
            idx = km_el.get("index", "")
            keys: dict[str, dict] = {}
            for key_el in km_el:
                if key_el.tag != "key":
                    continue
                code = key_el.get("code", "")
                entry: dict[str, str | None] = {}
                out = key_el.get("output")
                act = key_el.get("action")
                if out is not None:
                    entry["output"] = _decode_refs(out)
                if act is not None:
                    entry["action"] = act
                keys[code] = entry
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
                    w[attr] = _decode_refs(val) if attr == "output" else val
            whens.append(w)
        data.actions[act_id] = whens

    for term_el in root.iter("terminators"):
        for when_el in term_el:
            if when_el.tag != "when":
                continue
            data.terminators[when_el.get("state", "")] = _decode_refs(when_el.get("output", ""))

    return data


def parse_json(path: Path) -> LayoutData:
    raw = json.loads(path.read_text(encoding="utf-8"))
    data = LayoutData(name=raw.get("keyboard_name", path.name))
    for ks_id, ks_data in raw.get("key_map_sets", {}).items():
        kms: dict[str, dict[str, dict]] = {}
        for idx, km_data in ks_data.items():
            kms[idx] = km_data.get("keys", {})
        data.key_map_sets[ks_id] = kms
    data.actions = raw.get("actions", {})
    for term in raw.get("terminators", []):
        data.terminators[term.get("state", "")] = term.get("output", "")
    return data


def load(path: Path) -> LayoutData:
    if path.suffix == ".json":
        return parse_json(path)
    return parse_xml(path)


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------

def validate(data: LayoutData) -> list[Issue]:
    issues: list[Issue] = []

    # Collect all states that can be entered (via action "next" fields)
    reachable_states: set[str] = set()
    # Collect all states that are handled (via action "when state=X" clauses)
    handled_states: set[str] = set()
    # Collect all action IDs referenced by keys
    referenced_actions: set[str] = set()
    # Collect all defined action IDs
    defined_actions: set[str] = set(data.actions.keys())

    for act_id, whens in data.actions.items():
        for w in whens:
            state = w.get("state", "")
            if state and state != "none":
                handled_states.add(state)
            nxt = w.get("next")
            if nxt:
                reachable_states.add(nxt)

    terminated_states = set(data.terminators.keys())

    # 1. Orphan dead key states: reachable but never handled and no terminator
    for state in reachable_states:
        has_handler = state in handled_states
        has_terminator = state in terminated_states
        if not has_handler and not has_terminator:
            sources = [
                act_id for act_id, whens in data.actions.items()
                for w in whens if w.get("next") == state
            ]
            issues.append(Issue(
                severity="ERROR",
                code="ORPHAN_DEAD_KEY",
                message=(
                    f"State '{state}' is reachable (via actions: {sources}) "
                    f"but has no terminator and no handler. "
                    f"Apple's TIS parser will reject the entire file."
                ),
            ))
        elif not has_terminator and has_handler:
            issues.append(Issue(
                severity="WARN",
                code="NO_TERMINATOR",
                message=(
                    f"State '{state}' has action handlers but no terminator. "
                    f"Pressing the dead key followed by an unmatched key will produce nothing."
                ),
            ))

    # 2. Terminated states that are never reachable
    for state in terminated_states:
        if state not in reachable_states:
            issues.append(Issue(
                severity="WARN",
                code="UNREACHABLE_TERMINATOR",
                message=f"Terminator for state '{state}' exists but no action transitions into it.",
            ))

    # 3. Key entries referencing undefined actions + multi-char outputs
    for ks_id, kms in data.key_map_sets.items():
        for idx in sorted(kms, key=lambda x: int(x)):
            km = kms[idx]
            for code, entry in km.items():
                act = entry.get("action")
                if act is not None:
                    referenced_actions.add(act)
                    if act not in defined_actions:
                        issues.append(Issue(
                            severity="ERROR",
                            code="UNDEFINED_ACTION",
                            location=f"{ks_id}/{layer_name(idx)}/{key_label(code)}",
                            message=f"References action '{act}' which is not defined.",
                        ))

                out = entry.get("output")
                if out is not None and len(out) > 1:
                    cps = " ".join(f"U+{ord(c):04X}" for c in out)
                    issues.append(Issue(
                        severity="WARN",
                        code="MULTI_CHAR_OUTPUT",
                        location=f"{ks_id}/{layer_name(idx)}/{key_label(code)}",
                        message=f"Multi-character output: {out!r} [{cps}]",
                    ))

    # 4. Unused actions (defined but never referenced by any key)
    unused = defined_actions - referenced_actions
    if unused:
        for act_id in sorted(unused):
            whens = data.actions[act_id]
            is_dead_key_handler = any(
                w.get("state", "") != "none" for w in whens
            )
            if not is_dead_key_handler:
                issues.append(Issue(
                    severity="WARN",
                    code="UNUSED_ACTION",
                    message=f"Action '{act_id}' is defined but never referenced by any key.",
                ))

    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Validate keyboard layout files")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--errors-only", action="store_true",
                        help="Only show ERROR-level issues")
    args = parser.parse_args()

    total_errors = 0
    for path in args.files:
        if not path.exists():
            print(f"SKIP: {path} (not found)")
            continue
        data = load(path)
        issues = validate(data)
        if args.errors_only:
            issues = [i for i in issues if i.severity == "ERROR"]

        errors = sum(1 for i in issues if i.severity == "ERROR")
        warns = sum(1 for i in issues if i.severity == "WARN")
        total_errors += errors

        status = "FAIL" if errors > 0 else ("WARN" if warns > 0 else "OK")
        print(f"{status}: {data.name} ({path})")
        if issues:
            for issue in issues:
                print(issue)
            print()

    if total_errors > 0:
        print(f"\n{total_errors} error(s) found.")
        sys.exit(1)
    else:
        print("\nAll files passed validation.")


if __name__ == "__main__":
    main()
