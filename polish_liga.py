"""Add Polish pronunciation ligatures to TTF fonts.

Creates composite glyphs that show the original Latin letter(s) with a
small Cyrillic pronunciation hint above, then wires them up via GSUB
ligature substitution so shaping engines render them automatically.

Usage:
    python polish_liga.py --input font.ttf --output font_liga.ttf
    python polish_liga.py --input font.ttf --dry-run

Requires fonttools (pip install fonttools).
"""
import argparse
import sys
import os
from typing import Any

_reconfigure = getattr(sys.stdout, "reconfigure", None)
if _reconfigure is not None:
    _reconfigure(encoding="utf-8", errors="replace")

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_vp = os.path.join(SCRIPT_DIR, "VERSION")
if os.path.exists(_vp):
    with open(_vp, encoding="utf-8") as _f:
        VERSION = _f.read().strip()
else:
    VERSION = "dev"

_reconfigure_err = getattr(sys.stderr, "reconfigure", None)
if _reconfigure_err is not None:
    _reconfigure_err(encoding="utf-8", errors="replace")

try:
    from fontTools.ttLib import TTFont
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib.tables import otTables
except ImportError:
    print("ERROR: fonttools is required. Install with: pip install fonttools", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Substitution tables
# ---------------------------------------------------------------------------
# Each entry: (input_letters, hint_string)
# Longest sequences first so GSUB picks the most specific match.

SUBSTITUTION_CYRILLIC: list[tuple[str, str]] = [
    ("chrz", "хш"),   ("szcz", "щ"),    ("strz", "стш"),  ("sprz", "спш"),
    ("prz", "пш"),    ("trz", "тш"),    ("krz", "кш"),
    ("dzią", "дзён"), ("dzię", "дзен"),
    ("dzia", "дзя"),  ("dzie", "дзе"),  ("dzio", "дзё"),  ("dziu", "дзю"),
    ("dzi", "дзи"),
    ("sz", "ш"),      ("cz", "ч"),      ("ch", "х"),      ("rz", "ж"),
    ("dż", "дж"),     ("dź", "дзь"),    ("dz", "дз"),
    ("cią", "чён"),   ("cię", "чен"),
    ("cia", "чя"),    ("cie", "че"),    ("cio", "чё"),    ("ciu", "чю"),
    ("sią", "шён"),   ("się", "шен"),
    ("sia", "шя"),    ("sie", "ше"),    ("sio", "шё"),    ("siu", "шю"),
    ("zią", "жён"),   ("zię", "жен"),
    ("zia", "жя"),    ("zie", "же"),    ("zio", "жё"),    ("ziu", "жю"),
    ("ci", "чи"),     ("si", "ши"),     ("zi", "жи"),
    ("ia", "я"),      ("ie", "е"),      ("io", "йо"),     ("iu", "ю"),
    ("ją", "ён"),     ("ią", "ён"),     ("ię", "ен"),
    ("jó", "ю"),      ("ió", "ю"),
    ("ó", "у"),       ("ł", "ў"),      ("ą", "он"),
]

SUBSTITUTION_IPA: list[tuple[str, str]] = [
    ("chrz", "xʂ"),   ("szcz", "ʂtʂ"),  ("strz", "stʂ"),  ("sprz", "spʂ"),
    ("prz", "pʂ"),    ("trz", "tʂ"),    ("krz", "kʂ"),
    ("dzią", "dʑɔ̃"),  ("dzię", "dʑɛ̃"),
    ("dzia", "dʑa"),  ("dzie", "dʑɛ"),  ("dzio", "dʑɔ"),  ("dziu", "dʑu"),
    ("dzi", "dʑi"),
    ("sz", "ʂ"),      ("cz", "tʂ"),     ("ch", "x"),      ("rz", "ʐ"),
    ("dż", "dʐ"),     ("dź", "dʑ"),     ("dz", "dz"),
    ("cią", "tɕɔ̃"),   ("cię", "tɕɛ̃"),
    ("cia", "tɕa"),   ("cie", "tɕɛ"),   ("cio", "tɕɔ"),   ("ciu", "tɕu"),
    ("sią", "ɕɔ̃"),    ("się", "ɕɛ̃"),
    ("sia", "ɕa"),    ("sie", "ɕɛ"),    ("sio", "ɕɔ"),    ("siu", "ɕu"),
    ("zią", "ʑɔ̃"),    ("zię", "ʑɛ̃"),
    ("zia", "ʑa"),    ("zie", "ʑɛ"),    ("zio", "ʑɔ"),    ("ziu", "ʑu"),
    ("ci", "tɕi"),    ("si", "ɕi"),     ("zi", "ʑi"),
    ("ia", "ja"),     ("ie", "jɛ"),     ("io", "jɔ"),     ("iu", "ju"),
    ("ją", "jɔ̃"),     ("ią", "jɔ̃"),     ("ię", "jɛ̃"),
    ("jó", "ju"),     ("ió", "ju"),
    ("ó", "u"),       ("ł", "w"),      ("ą", "ɔ̃"),
]

VARIANT_CONFIG = {
    "cyrillic": {
        "table": SUBSTITUTION_CYRILLIC,
        "font_family": "Szpargalka Sans",
        "default_output": "SzpargalkaSans-Regular.ttf",
    },
    "ipa": {
        "table": SUBSTITUTION_IPA,
        "font_family": "Polish Phonetics Sans",
        "default_output": "PolishPhoneticsSans-Regular.ttf",
    },
}

def _expand_with_caps(table: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Add first-letter-capitalized variants for each rule (Sz→ш, Cz→ч, etc.)."""
    expanded = list(table)
    for latin, hint in table:
        if len(latin) >= 2 and latin[0].islower():
            cap = latin[0].upper() + latin[1:]
            expanded.append((cap, hint))
    return expanded

SUBSTITUTION_TABLE = _expand_with_caps(SUBSTITUTION_CYRILLIC)

# Collect exactly which Cyrillic chars are used by the substitution table
def _required_hint_chars() -> set[str]:
    chars: set[str] = set()
    for _latin, cyrillic in SUBSTITUTION_TABLE:
        for ch in cyrillic:
            chars.add(ch)
    return chars


FONTS_WITH_CYRILLIC = [
    "Noto Sans", "Noto Serif", "Inter", "Roboto", "PT Sans", "PT Serif",
    "Source Sans 3", "IBM Plex Sans", "Fira Sans", "Ubuntu", "Open Sans",
    "Montserrat", "Raleway", "Merriweather",
]


def _validate_cyrillic(font: TTFont) -> list[str]:
    """Return list of missing Cyrillic characters needed for hints."""
    cmap = font.getBestCmap()
    needed = _required_hint_chars()
    missing: list[str] = []
    for ch in sorted(needed):
        cp = ord(ch)
        if cp not in cmap:
            missing.append(f"  U+{cp:04X} {ch}")
    return missing


def _get_font_metrics(font: TTFont) -> dict[str, int]:
    """Extract key vertical metrics from the font."""
    head = font["head"]
    os2 = font["OS/2"]
    units_per_em: int = head.unitsPerEm

    cap_height: int = getattr(os2, "sCapHeight", 0)
    if cap_height == 0:
        cap_height = int(units_per_em * 0.70)

    x_height: int = getattr(os2, "sxHeight", 0)
    if x_height == 0:
        x_height = int(units_per_em * 0.50)

    ascender: int = os2.sTypoAscender
    descender: int = os2.sTypoDescender

    return {
        "units_per_em": units_per_em,
        "cap_height": cap_height,
        "x_height": x_height,
        "ascender": ascender,
        "descender": descender,
    }


# ---------------------------------------------------------------------------
# Glyph creation
# ---------------------------------------------------------------------------

def _make_hint_glyph_name(cyrillic_str: str) -> str:
    """Generate a glyph name for a Cyrillic hint (possibly multi-char)."""
    parts = []
    for ch in cyrillic_str:
        cp = ord(ch)
        parts.append(f"uni{cp:04X}")
    return "hint." + ".".join(parts)


def _make_liga_glyph_name(latin_str: str) -> str:
    """Generate a glyph name for the composite ligature glyph."""
    parts = []
    for ch in latin_str:
        cp = ord(ch)
        parts.append(f"uni{cp:04X}")
    return "liga." + ".".join(parts)


def _create_hint_glyph(
    font: TTFont,
    cyrillic_str: str,
    hint_scale: float,
    metrics: dict[str, int],
) -> str:
    """Create a scaled hint glyph from one or more Cyrillic source glyphs.

    Returns the new glyph name. If the glyph already exists, returns its name
    without recreating it.
    """
    glyph_name = _make_hint_glyph_name(cyrillic_str)
    glyf_table = font["glyf"]
    if glyph_name in glyf_table:
        return glyph_name

    cmap = font.getBestCmap()
    hmtx = font["hmtx"]

    total_advance = 0
    components: list[tuple[str, int]] = []

    for ch in cyrillic_str:
        cp = ord(ch)
        src_name = cmap.get(cp)
        if src_name is None:
            raise ValueError(f"Missing Cyrillic glyph U+{cp:04X} ({ch})")
        src_advance = hmtx[src_name][0]
        scaled_advance = int(src_advance * hint_scale)
        components.append((src_name, total_advance))
        total_advance += scaled_advance

    pen = TTGlyphPen(font.getGlyphSet())
    cap_height = metrics["cap_height"]
    gap = int(metrics["units_per_em"] * 0.08)
    y_offset = cap_height + gap

    for src_name, x_offset in components:
        pen.addComponent(
            src_name,
            (hint_scale, 0, 0, hint_scale, x_offset, y_offset),
        )

    glyf_table[glyph_name] = pen.glyph()
    hmtx[glyph_name] = (total_advance, 0)
    return glyph_name


def _create_liga_glyph(
    font: TTFont,
    latin_str: str,
    hint_glyph_name: str,
    advance_factor: float,
    metrics: dict[str, int],
) -> str:
    """Create a composite ligature glyph: Latin base letters + Cyrillic hint above.

    The Latin letters are placed sequentially at advance_factor of their
    original width. The hint glyph is centered above the combined base.
    """
    glyph_name = _make_liga_glyph_name(latin_str)
    glyf_table = font["glyf"]
    if glyph_name in glyf_table:
        return glyph_name

    cmap = font.getBestCmap()
    hmtx = font["hmtx"]

    pen = TTGlyphPen(font.getGlyphSet())

    total_base_advance = 0
    first_lsb = 0
    for i, ch in enumerate(latin_str):
        cp = ord(ch)
        src_name = cmap.get(cp)
        if src_name is None:
            raise ValueError(f"Missing Latin glyph U+{cp:04X} ({ch})")
        src_advance, src_lsb = hmtx[src_name]
        if i == 0:
            first_lsb = src_lsb
        pen.addComponent(src_name, (1, 0, 0, 1, total_base_advance, 0))
        total_base_advance += int(src_advance * advance_factor)

    hint_advance = hmtx[hint_glyph_name][0]
    hint_x = (total_base_advance - hint_advance) // 2
    pen.addComponent(hint_glyph_name, (1, 0, 0, 1, hint_x, 0))

    glyf_table[glyph_name] = pen.glyph()
    hmtx[glyph_name] = (total_base_advance, first_lsb)
    return glyph_name


# ---------------------------------------------------------------------------
# GSUB construction
# ---------------------------------------------------------------------------

def _ensure_gsub(font: TTFont) -> otTables.GSUB:
    """Return the GSUB table object, creating one if absent."""
    if "GSUB" not in font:
        gsub = otTables.GSUB()
        gsub.Version = 0x00010000
        gsub_table = font.newTable("GSUB")
        gsub_table.table = gsub

        gsub.ScriptList = otTables.ScriptList()
        gsub.ScriptList.ScriptRecord = []

        dflt_script = otTables.ScriptRecord()
        dflt_script.ScriptTag = "DFLT"
        dflt_script.Script = otTables.Script()
        dflt_script.Script.DefaultLangSys = otTables.DefaultLangSys()
        dflt_script.Script.DefaultLangSys.ReqFeatureIndex = 0xFFFF
        dflt_script.Script.DefaultLangSys.FeatureIndex = []
        dflt_script.Script.LangSysRecord = []
        gsub.ScriptList.ScriptRecord.append(dflt_script)

        latn_script = otTables.ScriptRecord()
        latn_script.ScriptTag = "latn"
        latn_script.Script = otTables.Script()
        latn_script.Script.DefaultLangSys = otTables.DefaultLangSys()
        latn_script.Script.DefaultLangSys.ReqFeatureIndex = 0xFFFF
        latn_script.Script.DefaultLangSys.FeatureIndex = []
        latn_script.Script.LangSysRecord = []
        gsub.ScriptList.ScriptRecord.append(latn_script)

        gsub.FeatureList = otTables.FeatureList()
        gsub.FeatureList.FeatureRecord = []
        gsub.LookupList = otTables.LookupList()
        gsub.LookupList.Lookup = []
        font["GSUB"] = gsub_table
    else:
        gsub = font["GSUB"].table
    return gsub


def _add_feature_for_lookups(
    gsub: otTables.GSUB,
    tag: str,
    lookup_indices: list[int],
) -> None:
    """Register a feature record pointing at the given lookup indices."""
    feature_record = otTables.FeatureRecord()
    feature_record.FeatureTag = tag
    feature_record.Feature = otTables.Feature()
    feature_record.Feature.FeatureParams = None
    feature_record.Feature.LookupListIndex = lookup_indices
    feature_record.Feature.LookupCount = len(lookup_indices)

    feature_index = len(gsub.FeatureList.FeatureRecord)
    gsub.FeatureList.FeatureRecord.append(feature_record)

    for script_record in gsub.ScriptList.ScriptRecord:
        if script_record.Script.DefaultLangSys is not None:
            script_record.Script.DefaultLangSys.FeatureIndex.append(feature_index)
            script_record.Script.DefaultLangSys.FeatureCount = len(
                script_record.Script.DefaultLangSys.FeatureIndex
            )
        for lang_sys in script_record.Script.LangSysRecord:
            lang_sys.LangSys.FeatureIndex.append(feature_index)
            lang_sys.LangSys.FeatureCount = len(lang_sys.LangSys.FeatureIndex)


def _build_gsub_ligatures(
    font: TTFont,
    ligature_map: dict[tuple[str, ...], str],
) -> None:
    """Add SingleSubst + LigatureSubst lookups to the font's GSUB table.

    Single-char rules use GSUB Type 1 (SingleSubst).
    Multi-char rules use GSUB Type 4 (LigatureSubst).
    Both are registered under the 'liga' feature tag.
    """
    from fontTools.otlLib.builder import (
        buildLigatureSubstSubtable,
        buildSingleSubstSubtable,
    )

    singles: dict[str, str] = {}
    multi: dict[tuple[str, ...], str] = {}
    for key, val in ligature_map.items():
        if len(key) == 1:
            singles[key[0]] = val
        else:
            multi[key] = val

    gsub = _ensure_gsub(font)
    lookup_indices: list[int] = []

    if multi:
        liga_subtable = buildLigatureSubstSubtable(multi)
        liga_lookup = otTables.Lookup()
        liga_lookup.LookupType = 4
        liga_lookup.LookupFlag = 0
        liga_lookup.SubTableCount = 1
        liga_lookup.SubTable = [liga_subtable]
        lookup_indices.append(len(gsub.LookupList.Lookup))
        gsub.LookupList.Lookup.append(liga_lookup)

    if singles:
        single_subtable = buildSingleSubstSubtable(singles)
        single_lookup = otTables.Lookup()
        single_lookup.LookupType = 1
        single_lookup.LookupFlag = 0
        single_lookup.SubTableCount = 1
        single_lookup.SubTable = [single_subtable]
        lookup_indices.append(len(gsub.LookupList.Lookup))
        gsub.LookupList.Lookup.append(single_lookup)

    existing_liga = None
    for fr in gsub.FeatureList.FeatureRecord:
        if fr.FeatureTag == "liga":
            existing_liga = fr
            break

    if existing_liga:
        existing_liga.Feature.LookupListIndex.extend(lookup_indices)
        existing_liga.Feature.LookupCount = len(existing_liga.Feature.LookupListIndex)
    else:
        _add_feature_for_lookups(gsub, "liga", lookup_indices)


# ---------------------------------------------------------------------------
# Line height adjustment
# ---------------------------------------------------------------------------

def _adjust_line_height(font: TTFont, factor: float = 1.25) -> dict[str, Any]:
    """Increase vertical metrics by factor to accommodate hint glyphs above caps."""
    changes: dict[str, Any] = {}

    os2 = font["OS/2"]
    old_win_ascent = os2.usWinAscent
    old_typo_ascender = os2.sTypoAscender

    os2.usWinAscent = int(old_win_ascent * factor)
    os2.sTypoAscender = int(old_typo_ascender * factor)

    changes["OS/2.usWinAscent"] = f"{old_win_ascent} -> {os2.usWinAscent}"
    changes["OS/2.sTypoAscender"] = f"{old_typo_ascender} -> {os2.sTypoAscender}"

    if "hhea" in font:
        hhea = font["hhea"]
        old_ascent = hhea.ascent
        hhea.ascent = int(old_ascent * factor)
        changes["hhea.ascent"] = f"{old_ascent} -> {hhea.ascent}"

    return changes


def _rename_font(font: TTFont, family: str, style: str) -> None:
    name_table = font["name"]
    full_name = f"{family} {style}"
    ps_name = family.replace(" ", "") + "-" + style
    records = {
        0: f"Copyright 2022 The Noto Project Authors. Modified: Szpargalka Sans by Kirkouski.",
        1: family,
        2: style,
        3: f"{ps_name};{VERSION}",
        4: full_name,
        5: f"Version {VERSION}",
        6: ps_name,
        16: family,
        17: style,
    }
    for name_id, value in records.items():
        name_table.setName(value, name_id, 3, 1, 0x0409)
        name_table.setName(value, name_id, 1, 0, 0)


# ---------------------------------------------------------------------------
# Dry run
# ---------------------------------------------------------------------------

def _print_dry_run(font: TTFont, hint_scale: float, advance_factor: float) -> None:
    """Print what would be done without modifying anything."""
    cmap = font.getBestCmap()
    metrics = _get_font_metrics(font)

    print("=" * 60)
    print("DRY RUN — no changes will be made")
    print("=" * 60)
    print()

    print(f"Font metrics:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")
    print(f"  hint_scale: {hint_scale}")
    print(f"  advance_factor: {advance_factor}")
    print()

    print(f"Substitution rules ({len(SUBSTITUTION_TABLE)} total):")
    print(f"  {'Latin':<10} {'Cyrillic':<10} {'Liga glyph':<30} {'Hint glyph':<30}")
    print(f"  {'-'*10} {'-'*10} {'-'*30} {'-'*30}")
    for latin, cyrillic in SUBSTITUTION_TABLE:
        liga_name = _make_liga_glyph_name(latin)
        hint_name = _make_hint_glyph_name(cyrillic)
        print(f"  {latin:<10} {cyrillic:<10} {liga_name:<30} {hint_name:<30}")
    print()

    missing_latin: list[str] = []
    for latin, _cyrillic in SUBSTITUTION_TABLE:
        for ch in latin:
            if ord(ch) not in cmap:
                missing_latin.append(f"  U+{ord(ch):04X} {ch}")
    if missing_latin:
        print(f"Missing Latin glyphs ({len(missing_latin)}):")
        for m in missing_latin:
            print(m)
        print()

    missing_cyrillic = _validate_cyrillic(font)
    if missing_cyrillic:
        print(f"Missing Cyrillic glyphs ({len(missing_cyrillic)}):")
        for m in missing_cyrillic:
            print(m)
        print()
    else:
        print("All required Cyrillic glyphs present.")
        print()

    print("New glyphs that would be created:")
    hint_glyphs: set[str] = set()
    liga_glyphs: list[str] = []
    for latin, cyrillic in SUBSTITUTION_TABLE:
        hint_glyphs.add(_make_hint_glyph_name(cyrillic))
        liga_glyphs.append(_make_liga_glyph_name(latin))
    print(f"  Hint glyphs: {len(hint_glyphs)}")
    for g in sorted(hint_glyphs):
        print(f"    {g}")
    print(f"  Liga glyphs: {len(liga_glyphs)}")
    for g in liga_glyphs:
        print(f"    {g}")
    print()

    single_count = sum(1 for latin, _ in SUBSTITUTION_TABLE if len(latin) == 1)
    multi_count = len(SUBSTITUTION_TABLE) - single_count
    print("GSUB changes:")
    if single_count:
        print(f"  1 new SingleSubst lookup (Type 1) with {single_count} rules")
    if multi_count:
        print(f"  1 new LigatureSubst lookup (Type 4) with {multi_count} rules")
    print(f"  Feature tag: 'liga'")
    print()

    print("Line height changes (x1.25):")
    os2 = font["OS/2"]
    print(f"  OS/2.usWinAscent: {os2.usWinAscent} -> {int(os2.usWinAscent * 1.25)}")
    print(f"  OS/2.sTypoAscender: {os2.sTypoAscender} -> {int(os2.sTypoAscender * 1.25)}")
    if "hhea" in font:
        print(f"  hhea.ascent: {font['hhea'].ascent} -> {int(font['hhea'].ascent * 1.25)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add Polish pronunciation ligatures to TTF fonts.",
        epilog="Requires a font with both Latin and Cyrillic glyph coverage.",
    )
    parser.add_argument("--input", "-i", required=True, help="Input TTF font path")
    parser.add_argument("--output", "-o", help="Output TTF font path")
    parser.add_argument("--variant", choices=["cyrillic", "ipa"], default="cyrillic",
                        help="Hint style: cyrillic (Szpargalka Sans) or ipa (Polish Phonetics Sans)")
    parser.add_argument("--dry-run", action="store_true", help="Print planned changes without modifying")
    parser.add_argument(
        "--hint-scale", type=float, default=0.42,
        help="Scale factor for hint glyphs (default: 0.42)",
    )
    parser.add_argument(
        "--advance-factor", type=float, default=1.0,
        help="Advance width factor for base Latin letters in ligatures (default: 1.0)",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.input):
        print(f"ERROR: Input file not found: {args.input}", file=sys.stderr)
        sys.exit(1)

    global SUBSTITUTION_TABLE
    vcfg = VARIANT_CONFIG[args.variant]
    SUBSTITUTION_TABLE = _expand_with_caps(vcfg["table"])

    font = TTFont(args.input)

    if "glyf" not in font:
        print("ERROR: Only TrueType (.ttf) fonts with 'glyf' outlines are supported.", file=sys.stderr)
        print("  CFF/CFF2-based fonts (.otf) require a different glyph construction approach.", file=sys.stderr)
        font.close()
        sys.exit(1)

    if args.dry_run:
        _print_dry_run(font, args.hint_scale, args.advance_factor)
        font.close()
        return

    missing = _validate_cyrillic(font)
    if missing:
        print(f"ERROR: Font is missing required hint glyphs for '{args.variant}' variant:", file=sys.stderr)
        for m in missing:
            print(m, file=sys.stderr)
        print(file=sys.stderr)
        print("Suggested fonts with full coverage: Noto Sans, Source Sans 3", file=sys.stderr)
        font.close()
        sys.exit(1)

    cmap = font.getBestCmap()
    missing_latin: list[str] = []
    for latin, _cyrillic in SUBSTITUTION_TABLE:
        for ch in latin:
            if ord(ch) not in cmap:
                missing_latin.append(f"U+{ord(ch):04X} {ch}")
    if missing_latin:
        print("ERROR: Font is missing required Latin glyphs:", file=sys.stderr)
        for m in missing_latin:
            print(f"  {m}", file=sys.stderr)
        font.close()
        sys.exit(1)

    metrics = _get_font_metrics(font)
    print(f"Font: {args.input}")
    print(f"  unitsPerEm={metrics['units_per_em']}  capHeight={metrics['cap_height']}  xHeight={metrics['x_height']}")

    ligature_map: dict[tuple[str, ...], str] = {}
    created_hints: set[str] = set()
    created_ligas: list[str] = []

    for latin, cyrillic in SUBSTITUTION_TABLE:
        hint_name = _create_hint_glyph(font, cyrillic, args.hint_scale, metrics)
        if hint_name not in created_hints:
            created_hints.add(hint_name)

        liga_name = _create_liga_glyph(
            font, latin, hint_name,
            args.advance_factor, metrics,
        )
        created_ligas.append(liga_name)

        input_glyph_names = tuple(cmap[ord(ch)] for ch in latin)
        ligature_map[input_glyph_names] = liga_name

    print(f"  Created {len(created_hints)} hint glyphs, {len(created_ligas)} ligature glyphs")

    _build_gsub_ligatures(font, ligature_map)
    print("  Added GSUB LigatureSubst lookup (liga feature)")

    height_changes = _adjust_line_height(font)
    print("  Adjusted line height:")
    for k, v in height_changes.items():
        print(f"    {k}: {v}")

    output_path = args.output
    if not output_path:
        output_path = os.path.join("dist", vcfg["default_output"])

    font_family = vcfg["font_family"]
    _rename_font(font, font_family, "Regular")
    print(f"  Renamed to {font_family} Regular")

    font.save(output_path)
    font.close()
    print(f"  Saved: {output_path}")


if __name__ == "__main__":
    main()
