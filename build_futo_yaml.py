#!/usr/bin/env python3
"""Generate FUTO Keyboard (Android) layout YAML from *_typographic_full.json.

FUTO Keyboard is an AOSP/LatinIME fork whose layouts are plain YAML, so the
Kirkouski layout ports without writing an app.

Design (see the plan for the full reasoning):

* **One file per layout.** The stock FUTO symbols pages already carry every
  non-letter character this layout uses, so we do NOT override them. No
  `layoutSetOverrides`, no forked `Special/symbols*.yaml`, nothing to re-diff
  when upstream edits them.
* **Dead keys port via combining marks.** `DeadKeyPreCombiner` promotes any key
  emitting U+0300-U+035B to a dead-key event, which `DeadKeyCombiner` then
  composes with `Normalizer.NFC`. So we emit `<spacing accent>|<combining mark>`
  and let NFC do what the desktop composition tables do.
* **Diacritics sit on their base letter, first, with an explicit `hint:`.**
  `KeyHintsSetting` defaults to false, so without an explicit hint the keycap
  shows nothing on a fresh install.

Usage:
    python build_futo_yaml.py [polish|russian|all] [--placement letter|position]
                              [--strict] [--out DIR]
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata as ud
from pathlib import Path
from typing import Any

from layout_adapter import MAC_CODE_TO_KEY, extract_layers_from_full_json

SCRIPT_DIR = Path(__file__).resolve().parent

# Physical key IDs per row, in visual order. Non-letter keys are filtered out
# per layout, so Latin gets 10/9/7 and Cyrillic gets 12/11/9.
PHYSICAL_ROWS: list[list[str]] = [
    ["Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]"],
    ["A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", "\\"],
    ["Z", "X", "C", "V", "B", "N", "M", ",", ".", "/"],
]

# Letters whose diacritic is a stroke/bar rather than a combining mark, so NFD
# does not decompose them. Needed to place them on the right base letter.
STROKE_BASE: dict[str, str] = {
    "ł": "l", "Ł": "L",   # l/L with stroke
    "đ": "d", "Đ": "D",   # d/D with stroke
    "ħ": "h", "Ħ": "H",   # h/H with stroke
    "ŧ": "t", "Ŧ": "T",   # t/T with stroke
    "ø": "o", "Ø": "O",   # o/O with stroke
    "ß": "s", "ẞ": "S",   # sharp s -> s
    "ı": "i", "İ": "I",   # dotless i / I with dot
}

# Cyrillic letters that are not canonically decomposable, mapped to the base
# letter a ru/be/uk typist would long-press to reach them. This is what lets
# one Cyrillic layout serve Russian, Belarusian and Ukrainian: the extra
# letters sit on the key you would expect, not on whatever key the desktop
# layout happened to park them on.
CYRILLIC_BASE: dict[str, str] = {
    "\u0491": "\u0433", "\u0490": "\u0413",   # ghe with upturn -> ghe   (uk)
    "\u0454": "\u0435", "\u0404": "\u0415",   # ye              -> ie    (uk)
    "\u0456": "\u0438", "\u0406": "\u0418",   # byelorussian i  -> i     (uk, be)
    "\u0457": "\u0438", "\u0407": "\u0418",   # yi              -> i     (uk)
    "\u045E": "\u0443", "\u040E": "\u0423",   # short u         -> u     (be)
    "\u0451": "\u0435", "\u0401": "\u0415",   # yo              -> ie    (ru, be)
}

# Typographic characters with no home anywhere: absent from the desktop layout
# AND from the stock FUTO symbols pages. The invisible ones are the real win --
# otherwise unreachable on a phone, and NBSP already anchors the family.
EXTRA_TYPOGRAPHY: list[str] = [
    "\u202F",   # NARROW NO-BREAK SPACE - ru/fr typography
    "\u2009",   # THIN SPACE
    "\u00AD",   # SOFT HYPHEN - optional line-break point
    "\u2011",   # NON-BREAKING HYPHEN
]

# Characters stock FUTO already provides on a `pl` subtype, verified against
# futo-keyboard-layouts/Special/symbols{,_shift}.yaml, the per-locale tables in
# android-keyboard/tools/make-keyboard-text-py/locales/, and KeySpecShortcuts.kt.
# Anything in the layout but NOT here is an "orphan" and gets a home on altPage 0.
STOCK_COVERED: set[str] = set(
    # symbols page taps
    "@#$_%&-+()*\"':;!?,/.0123456789"
    # symbols page filler row (number row on) + symbols-shift taps
    "\\|=[]<>{}~`"
    "•√π÷×¶∆"     # bullet sqrt pi div mult pilcrow increment
    "£¢¥€₱"                 # pound cent yen euro peso
    "^°©®™℅"           # caret degree copy reg tm care-of
    # popups
    "“„”«»"                 # " family
    "‘‚’‹›"                 # ' family
    "–—⁻₋·"                 # - family
    "±⁺₊"                             # + family
    "≠≈∞"                             # = family
    "↑↓←→"                       # ^ family
    "′″"                                   # degree family
    "§"                                         # pilcrow family
    "‰¡‽¿"                       # % ! ? families
    "†‡★"                             # * family
    "№"                                         # # family
    "♪♥♠♦♣"                 # bullet family
    "ΠμΩ"                             # pi family
    "≤≥"                                   # < > families
    "…"                                         # symbols-page period
    # digit popups: super/subscripts and vulgar fractions
    "¹²³⁰⁴⁵⁶⁷⁸⁹ⁿ"
    "₀₁₂₃₄₅₆₇₈₉"
    "½⅓¼⅛⅔¾⅜⅝⅞∅"
)

# Orphans that are invisible and need a visible popup label.
# Short text labels beat lookalike box glyphs: four kinds of invisible space
# all render as the same box, and autoXScale shrinks text to fit.
LABELLED: dict[str, str] = {
    "\u00A0": "NBSP",
    "\u202F": "NNBSP",
    "\u2009": "THIN",
    "\u00AD": "SHY",
    "\u2011": "NB-",
    "\u2060": "WJ",
}

# Multi-codepoint sequences the layout builds by hand, and the precomposed
# character stock FUTO already offers instead. Stock's version is better: one
# codepoint, and grouped by numerator on the digit long-press.
COMPOSITE_STOCK: dict[str, str] = {
    "¹⁄₂": "½",   # 1/2 -> VULGAR FRACTION ONE HALF
    "¹⁄₃": "⅓",   # 1/3 -> VULGAR FRACTION ONE THIRD
    "¹⁄₄": "¼",   # 1/4 -> VULGAR FRACTION ONE QUARTER
}

# Fallback for dead keys whose composition table is too small to infer the mark
# from (Russian caron/circumflex/ring/tilde each have a single entry).
SPACING_TO_COMBINING: dict[str, str] = {
    "`": "̀",  # grave
    "´": "́",  # acute
    "ˆ": "̂",  # circumflex
    "^": "̂",  # circumflex, Windows-fixup spelling
    "˜": "̃",  # tilde
    "~": "̃",  # tilde, ASCII spelling
    "¯": "̄",  # macron
    "˘": "̆",  # breve
    "˙": "̇",  # dot above
    "¨": "̈",  # diaeresis
    "˚": "̊",  # ring above
    "˝": "̋",  # double acute
    "ˇ": "̌",  # caron
    "¸": "̧",  # cedilla
    "˛": "̨",  # ogonek
}

LAYOUTS: dict[str, dict[str, str]] = {
    # One layout per script, not per language. The Latin file types English and
    # Polish; the Cyrillic file types Russian, Belarusian and Ukrainian. Both
    # carry the typographic layer. `languages` is metadata only (the engine keys
    # off the subtype locale) -- mapping.yaml is what actually offers a layout
    # to a language.
    "polish": {
        "full": "polish_typographic_full.json",
        "out": "polish_english_typographic.yaml",
        "name": "Polski / English (typograficzna)",
        "languages": "pl en_US",
        "blurb": "Polish and English on one layout, with dead-key accents and "
                 "the typographic characters the stock symbols pages lack.",
    },
    "russian": {
        "full": "russian_typographic_full.json",
        "out": "cyrillic_typographic.yaml",
        "name": "Кириллица (типографская)",
        "languages": "ru be uk",
        "blurb": "Russian, Belarusian and Ukrainian on one layout -- the extra "
                 "letters sit on the base letter you would expect -- with "
                 "dead-key accents and typographic characters.",
    },
}

# CLI aliases, so the script can be driven by script name as well as by the
# source layout it is generated from.
ALIASES: dict[str, str] = {"latin": "polish", "cyrillic": "russian"}


# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #

def base_letter(ch: str) -> str | None:
    """Return the undecorated base letter of `ch`, or None if it has none."""
    if ch in STROKE_BASE:
        return STROKE_BASE[ch]
    if ch in CYRILLIC_BASE:
        return CYRILLIC_BASE[ch]
    d = ud.normalize("NFD", ch)
    if len(d) > 1 and ud.combining(d[1]):
        return d[0]
    return None


def combining_mark_for(compositions: list[tuple[int, int]]) -> str | None:
    """Infer the combining mark a dead key applies, from its composition table."""
    votes: dict[str, int] = {}
    for base_cp, result_cp in compositions:
        d = ud.normalize("NFD", chr(result_cp))
        if len(d) >= 2 and d[0] == chr(base_cp) and ud.combining(d[1]):
            votes[d[1]] = votes.get(d[1], 0) + 1
    if not votes:
        return None
    return max(votes, key=lambda k: votes[k])


def yaml_scalar(s: str) -> str:
    """Quote a string for YAML, escaping what kaml and AOSP keyspecs both need."""
    out = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{out}"'


def keyspec(label: str, output: str | None = None) -> str:
    r"""Build an AOSP keyspec, escaping the spec-level metacharacters , \ | ."""
    def esc(t: str) -> str:
        return t.replace("\\", "\\\\").replace(",", "\\,").replace("|", "\\|")
    return esc(label) if output is None else f"{esc(label)}|{esc(output)}"


def escape_unicode(s: str) -> str:
    r"""Render non-printable / whitespace chars as \uXXXX so the YAML stays readable."""
    out = []
    for ch in s:
        cp = ord(ch)
        if ch in ("\\", '"'):
            out.append("\\" + ch)
        elif cp < 0x20 or ud.category(ch) in ("Zs", "Cf", "Mn") or cp == 0x7F:
            out.append(f"\\u{cp:04X}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


# --------------------------------------------------------------------------- #
# model
# --------------------------------------------------------------------------- #

def collect_diacritics(
    layers: dict[str, Any], placement: str
) -> dict[str, list[str]]:
    """Map each base letter key ID -> the accented letters that belong on it.

    placement="letter"   : ź goes on the `z` key (its base letter). Matches
                           stock pl.json and what a phone user expects.
    placement="position" : ź goes on the `x` key (its desktop AltGr position).
                           Faithful to the physical layout, surprising on a phone.
    """
    by_key: dict[str, list[tuple[str, bool]]] = {}
    base = layers["base"]

    # base letter -> key ID that produces it unshifted
    letter_to_key = {v: k for k, v in base.items() if len(v) == 1 and v.isalpha()}

    # Keys that actually make it onto the Android letter rows. A phone has no
    # backtick or backslash key, so a diacritic parked there in the desktop
    # layout (Russian yo on AltGr backslash) has to move or it is lost.
    in_rows = {k for row in PHYSICAL_ROWS for k in row}
    emittable = {k for k in in_rows if len(base.get(k, "")) == 1 and base[k].isalpha()}

    for layer in ("altgr", "shift_altgr"):
        for key_id, entry in layers[layer].items():
            if not entry:
                continue
            ch = entry["char"]
            if len(ch) != 1 or not ch.isalpha():
                continue

            b = base_letter(ch)
            by_letter = (letter_to_key.get(b.lower()) or letter_to_key.get(b)) if b else None

            if placement == "position":
                # Desktop-faithful, but only where that key exists on a phone.
                target = key_id if key_id in emittable else (by_letter or key_id)
            else:
                # Its own base letter, else the desktop position as a fallback
                # (Ukrainian ye/i are not decorated letters, so they have none).
                target = by_letter or key_id

            # Only the lowercase form goes in moreKeys; FUTO uppercases it
            # automatically when shifted (`shiftable` defaults true).
            low = ch.lower()
            if len(low) != 1:
                continue  # e.g. ss.upper() == "SS"; skip multi-char case folds
            # Canonical == this letter really is base+mark under NFD. Those lead,
            # so the hint shows the diacritic most typists of the primary locale
            # expect (yo before Ukrainian ye on the ie key).
            d = ud.normalize("NFD", low)
            canonical = (
                len(d) > 1
                and ud.combining(d[1]) != 0
                and d[0] == base.get(target, "")
            )
            bucket = by_key.setdefault(target, [])
            if low not in [c for c, _ in bucket]:
                bucket.append((low, canonical))

    # stable sort: canonical first, original layer order preserved within groups
    return {k: [c for c, _ in sorted(v, key=lambda t: not t[1])]
            for k, v in by_key.items()}


def collect_dead_keys(layers: dict[str, Any]) -> list[tuple[str, str, str]]:
    """Return [(state, spacing_accent, combining_mark)] deduped by combining mark."""
    out: list[tuple[str, str, str]] = []
    seen: set[str] = set()
    for state, cp in sorted(layers["dead_key_chars"].items()):
        comps = layers["dead_key_compositions"].get(cp, [])
        mark = combining_mark_for(comps) or SPACING_TO_COMBINING.get(chr(cp))
        if mark is None:
            raise ValueError(
                f"dead key {state!r} (U+{cp:04X}) has no inferable combining mark "
                f"and no SPACING_TO_COMBINING entry - it would be dropped silently"
            )
        if mark in seen:
            continue
        seen.add(mark)
        out.append((state, chr(cp), mark))
    # Order by the combining mark's codepoint for a stable, sensible arrangement
    out.sort(key=lambda t: ord(t[2]))
    return out


def collect_off_grid_outputs(data: dict[str, Any]) -> list[str]:
    """Real characters on keys layout_adapter does not expose.

    MAC_CODE_TO_KEY covers only the alphanumeric block, so anything the layout
    puts elsewhere is invisible to the flat layers. In practice that is NBSP on
    AltGr+Space; the rest of the off-grid keycodes are numpad and function keys
    carrying PUA placeholders. Scanning generically means a future addition is
    picked up instead of silently dropped.
    """
    found: list[str] = []
    ks_id = next(iter(data.get("key_map_sets", {})), None)
    if ks_id is None:
        return found
    kms = data["key_map_sets"][ks_id]
    for km in ("3", "4"):
        for code, entry in kms.get(km, {}).get("keys", {}).items():
            if code in MAC_CODE_TO_KEY:
                continue
            out = entry.get("output")
            if not out or len(out) != 1:
                continue
            cp = ord(out)
            if 0xE000 <= cp <= 0xF8FF:      # PUA: numpad / function placeholders
                continue
            if ud.category(out) in ("Cc", "Cf"):   # CR, TAB and friends
                continue
            if out not in found:
                found.append(out)
    return found


def collect_orphans(layers: dict[str, Any], data: dict[str, Any] | None = None) -> list[str]:
    """Layout characters with no home on the stock FUTO symbols pages."""
    orphans: list[str] = []
    for ch in collect_off_grid_outputs(data or {}):
        if ch not in STOCK_COVERED and ch not in orphans and not ch.isalpha():
            orphans.append(ch)
    for layer in ("altgr", "shift_altgr"):
        for entry in layers[layer].values():
            if not entry:
                continue
            ch = entry["char"]
            if ch.startswith("dk:"):
                continue
            if ch in COMPOSITE_STOCK:
                continue  # stock ships a better precomposed equivalent
            for c in ch:
                if c in STOCK_COVERED or c in orphans:
                    continue
                if c.isalpha():
                    continue  # letters live on the letter rows
                orphans.append(c)
    return orphans


# --------------------------------------------------------------------------- #
# emit
# --------------------------------------------------------------------------- #

def emit_letter_key(
    key_id: str, ch: str, more: list[str], strict: bool
) -> str:
    """One letter key. Diacritic first in moreKeys, and repeated as an explicit
    hint because KeyHintsSetting defaults to false."""
    low = ch.lower()
    restore = ""
    if strict and "a" <= low <= "z":
        # OnlyExplicit also drops the coordinate-derived symbol and quick-action,
        # so put them back. Both resolve to "" for letters that have none, which
        # MoreKeysBuilder discards cleanly.
        restore = f', "!text/qwertysyms_{low}", "!text/actions_{low}"'

    if not more:
        if strict:
            mk = restore.lstrip(", ")
            body = f", moreKeys: [{mk}]" if mk else ""
            return (
                f'      - {{type: base, spec: {escape_unicode(ch)}{body}, '
                f'attributes: {{moreKeyMode: OnlyExplicit}}}}'
            )
        return f"      - {escape_unicode(ch)}"

    mk = ", ".join(escape_unicode(m) for m in more)
    attrs = ""
    if strict:
        # countsToKeyCoordinate=false follows from OnlyExplicit, which is why
        # --strict has to be all-or-nothing across every letter row: applying it
        # to one key shifts every later key in that row by one column.
        mk += restore
        attrs = ", attributes: {moreKeyMode: OnlyExplicit}"
    return (
        f"      - {{type: base, spec: {escape_unicode(ch)}, "
        f"moreKeys: [{mk}], hint: {escape_unicode(more[0])}{attrs}}}"
    )


def emit(layout_key: str, layers: dict[str, Any], placement: str, strict: bool,
         version: str, data: dict[str, Any] | None = None) -> str:
    cfg = LAYOUTS[layout_key]
    base = layers["base"]
    diacritics = collect_diacritics(layers, placement)
    dead_keys = collect_dead_keys(layers)
    orphans = collect_orphans(layers, data) + [
        c for c in EXTRA_TYPOGRAPHY if c not in STOCK_COVERED
    ]

    L: list[str] = []
    L.append(f"# {cfg['name']} — Kirkouski Typographic v{version}")
    L.append("#")
    L.append("# GENERATED by build_futo_yaml.py — do not edit by hand.")
    L.append("# Source of truth: " + cfg["full"])
    L.append("# https://polish-typographic.com")
    L.append("#")
    L.append("# The stock FUTO symbols pages already carry every non-letter character")
    L.append("# this layout uses, so they are deliberately NOT overridden. Only the")
    L.append("# dead keys and the few characters stock lacks live on the alt page.")
    L.append("")
    L.append(f"name: {yaml_scalar(cfg['name'])}")
    L.append("description: " + yaml_scalar(cfg["blurb"]))
    L.append(f"languages: {cfg['languages']}")
    # These are CombinerKind enum *names*, not class names -- `DeadKey`'s factory
    # constructs DeadKeyCombiner(). Matches LatinScript/Americas/lakota.yaml.
    L.append("combiners: [DeadKeyPreCombiner, DeadKey]")
    L.append("mirrorInOneHanded: true")
    L.append("rows:")

    for row_idx, physical in enumerate(PHYSICAL_ROWS):
        keys = [k for k in physical if len(base.get(k, "")) == 1 and base[k].isalpha()]
        if not keys:
            continue
        L.append("  - letters:")
        if row_idx == len(PHYSICAL_ROWS) - 1:
            L.append("      - $shift")
        for k in keys:
            L.append(emit_letter_key(k, base[k], diacritics.get(k, []), strict))
        if row_idx == len(PHYSICAL_ROWS) - 1:
            L.append("      - $delete")

    # Bottom row. It does NOT inherit keyboard-level attributes, so anything set
    # above is ignored here. "…" leads; the stock punctuation morekeys follow.
    L.append("  - bottom:")
    L.append("      - $symbols")
    L.append('      - ","')
    L.append("      - $alt0")
    L.append("      - $space")
    L.append('      - {type: base, spec: ".", moreKeys: ["\u2026"]}')
    L.append("      - $enter")

    # --- alt page 0: dead keys + orphans ---
    L.append("altPages:")
    L.append("  - - letters:")
    for state, spacing, mark in dead_keys:
        spec = keyspec(spacing, mark)
        L.append(f"      - {escape_unicode(spec)}   # dead {state}")
    if orphans:
        L.append("    - letters:")
        for ch in orphans:
            spec = keyspec(LABELLED[ch], ch) if ch in LABELLED else keyspec(ch)
            try:
                nm = ud.name(ch)
            except ValueError:
                nm = f"U+{ord(ch):04X}"
            L.append(f"      - {escape_unicode(spec)}   # {nm}")
    # An altPage replaces every row, bottom included, so it needs its own way back.
    L.append("    - bottom:")
    L.append("      - $alt0")
    L.append('      - ","')
    L.append("      - $space")
    L.append('      - "."')
    L.append("      - $enter")
    L.append("")
    return "\n".join(L)


# --------------------------------------------------------------------------- #
# validation
# --------------------------------------------------------------------------- #

def validate(layout_key: str, text: str, layers: dict[str, Any],
             placement: str = "letter", data: dict[str, Any] | None = None) -> list[str]:
    """Cheap structural checks. The real gate is a device, but these catch the
    mistakes that make FUTO reject a layout silently."""
    errs: list[str] = []
    cfg = LAYOUTS[layout_key]

    if cfg["out"].startswith("custom"):
        errs.append(
            "filename starts with 'custom' — LayoutManager.getLayout hijacks that "
            "prefix and would try int() on the rest"
        )

    lines = [ln for ln in text.splitlines() if ln.strip()]
    letter_rows = sum(1 for ln in lines if ln.strip() == "- letters:" or ln.strip() == "- - letters:")
    if not 1 <= letter_rows <= 8:
        errs.append(f"{letter_rows} letter rows; Keyboard.ensureRowsValid allows 1-8")
    if text.count("- bottom:") != 2:
        errs.append("expected exactly one bottom row on the main layout and one on altPage 0")

    # Every diacritic-bearing key must carry an explicit hint (KeyHintsSetting
    # defaults to false, so an implicit hint would be invisible).
    for ln in text.splitlines():
        if "moreKeys:" in ln and "type: base" in ln and "spec: " in ln:
            if "hint:" in ln:
                continue
            first = ln.split("moreKeys: [")[1].split("]")[0].split(",")[0].strip()
            # Only a literal character needs advertising. Keys whose moreKeys are
            # purely "!text/..." restorations, and the bottom-row period, do not.
            if first.startswith('"!text/') or '"."' in ln:
                continue
            errs.append(f"key with a literal moreKey but no explicit hint: {ln.strip()}")

    # Popup width: default max is 5 columns and nothing clamps panel height.
    for ln in text.splitlines():
        if "moreKeys: [" in ln:
            n = ln.split("moreKeys: [")[1].split("]")[0].count(",") + 1
            if n > 8:
                errs.append(f"{n} moreKeys on one key (>8 renders a very tall panel): {ln.strip()}")

    # Every accented letter the desktop layout carries must survive, and must
    # lead its key's moreKeys so the hint shows it. Letters are skipped by the
    # generic coverage sweep below, so they need their own check.
    for key_id, more in collect_diacritics(layers, placement).items():
        for ch in more:
            if ch not in text:
                errs.append(f"diacritic {ch!r} (key {key_id}) is missing from the output")
        if more:
            want = f'moreKeys: [{escape_unicode(more[0])}'
            if want not in text:
                errs.append(
                    f"{more[0]!r} should lead moreKeys on key {key_id} so it becomes the hint"
                )

    # A phone has no backtick/bracket letter keys, so some base-layer letters
    # fall off the letter rows (Russian keeps yo there). That is fine only if
    # they come back as a long-press somewhere.
    in_rows = {k for row in PHYSICAL_ROWS for k in row}
    for layer in ("base", "shift"):
        for k, v in layers[layer].items():
            if len(v) != 1 or not v.isalpha():
                continue
            if k in in_rows and layers["base"].get(k, "").isalpha():
                continue
            if v not in text and v.lower() not in text:
                errs.append(
                    f"letter {v!r} (key {k}) has no key and no long-press home - it is "
                    f"unreachable on Android"
                )

    # Off-grid characters (NBSP on AltGr+Space) are invisible to the flat
    # layers, so check them explicitly or they vanish without a word.
    for ch in collect_off_grid_outputs(data or {}):
        if ch in STOCK_COVERED or ch.isalpha():
            continue
        if ch not in text and f"{chr(92)}u{ord(ch):04X}" not in text:
            errs.append(
                f"off-grid character U+{ord(ch):04X} ({ud.name(ch, '?')}) is neither "
                f"in stock nor emitted"
            )

    # The curated extras have to be there too.
    for ch in EXTRA_TYPOGRAPHY:
        if ch in STOCK_COVERED:
            continue
        if ch not in text and f"{chr(92)}u{ord(ch):04X}" not in text:
            errs.append(
                f"extra typography U+{ord(ch):04X} ({ud.name(ch, '?')}) is missing"
            )

    # No layout character may be silently dropped.
    covered = set(text)
    for layer in ("altgr", "shift_altgr"):
        for entry in layers[layer].values():
            if not entry:
                continue
            ch = entry["char"]
            if ch.startswith("dk:"):
                continue
            if ch in COMPOSITE_STOCK:
                continue
            for c in ch:
                if c.isalpha() or c in STOCK_COVERED or c in covered:
                    continue
                if f"\\u{ord(c):04X}" in text:
                    continue
                errs.append(f"character {c!r} (U+{ord(c):04X}) is neither in stock nor emitted")

    return errs


def nfc_report(layers: dict[str, Any]) -> tuple[int, int, list[str]]:
    """How much of the desktop composition table NFC reproduces."""
    total = ok = 0
    diverging: list[str] = []
    for cp, comps in layers["dead_key_compositions"].items():
        mark = combining_mark_for(comps) or SPACING_TO_COMBINING.get(chr(cp))
        if mark is None:
            continue
        for base_cp, result_cp in comps:
            if chr(base_cp).isspace():
                continue  # terminator: FUTO emits the combining mark, by design
            total += 1
            if ud.normalize("NFC", chr(base_cp) + mark) == chr(result_cp):
                ok += 1
            elif len(diverging) < 20:
                diverging.append(
                    f"{chr(base_cp)!r}+U+{ord(mark):04X} -> desktop {chr(result_cp)!r}, "
                    f"NFC {ud.normalize('NFC', chr(base_cp) + mark)!r}"
                )
    return ok, total, diverging


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #

def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("layouts", nargs="*", default=["all"],
                    help="polish (or latin), russian (or cyrillic), or all "
                         "(default: all). There is no separate `us` layout: on "
                         "Android the Latin file is listed under both pl and en_US.")
    ap.add_argument("--placement", choices=["letter", "position"], default="letter",
                    help="where an accented letter goes: on its base letter "
                         "(default, matches stock pl.json) or on its desktop AltGr key")
    ap.add_argument("--strict", action="store_true",
                    help="moreKeyMode: OnlyExplicit on every letter key, so only "
                         "our diacritics appear (no misc accents). Verbose but exact.")
    ap.add_argument("--out", default=None, help="output directory")
    ap.add_argument("--report", action="store_true",
                    help="print the NFC coverage report for the dead-key tables")
    args = ap.parse_args()

    version = (SCRIPT_DIR / "VERSION").read_text(encoding="utf-8").strip()

    requested: list[str] = list(args.layouts)
    wanted: list[str] = (list(LAYOUTS) if "all" in requested
                         else [ALIASES.get(x, x) for x in requested])
    unknown = [w for w in wanted if w not in LAYOUTS]
    if unknown:
        print(f"error: unknown layout(s): {', '.join(unknown)}", file=sys.stderr)
        print(f"       known: {', '.join(LAYOUTS)}, "
              f"{', '.join(ALIASES)}, all", file=sys.stderr)
        return 1

    out_dir = Path(args.out) if args.out else SCRIPT_DIR / "dist" / f"android-v{version}"
    out_dir.mkdir(parents=True, exist_ok=True)

    failed = False
    for key in wanted:
        cfg = LAYOUTS[key]
        full_path = SCRIPT_DIR / cfg["full"]
        if not full_path.exists():
            print(f"error: {cfg['full']} not found — run extract_base.py first",
                  file=sys.stderr)
            return 1

        data = json.loads(full_path.read_text(encoding="utf-8"))
        # windows_fixups=False keeps macOS' U+02C6 circumflex terminator; the
        # U+005E rewrite exists only for Windows keyboard drivers.
        layers = extract_layers_from_full_json(data, windows_fixups=False)

        text = emit(key, layers, args.placement, args.strict, version, data)
        dest = out_dir / cfg["out"]
        dest.write_text(text, encoding="utf-8", newline="\n")

        errs = validate(key, text, layers, args.placement, data)
        dks = collect_dead_keys(layers)
        orph = collect_orphans(layers, data) + [
            c for c in EXTRA_TYPOGRAPHY if c not in STOCK_COVERED
        ]
        diac = collect_diacritics(layers, args.placement)
        n_diac = sum(len(v) for v in diac.values())

        status = "FAIL" if errs else "ok"
        try:
            shown = dest.relative_to(SCRIPT_DIR)
        except ValueError:
            shown = dest
        print(f"[{status}] {shown}")
        print(f"       {len(dks)} dead keys, {n_diac} diacritics on "
              f"{len(diac)} keys, {len(orph)} orphan symbols")
        if orph:
            print("       orphans: " + " ".join(
                f"U+{ord(c):04X}" if ud.category(c) in ("Zs", "Cf") else c for c in orph))
        for e in errs:
            print(f"       ! {e}", file=sys.stderr)
            failed = True

        if args.report:
            ok, total, div = nfc_report(layers)
            pct = 100 * ok / total if total else 0.0
            print(f"       NFC reproduces {ok}/{total} desktop compositions ({pct:.1f}%)")
            for d in div:
                print(f"         ~ {d}")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
