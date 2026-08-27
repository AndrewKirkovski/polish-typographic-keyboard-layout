#!/usr/bin/env python3
"""Merge AOSP `.combined` wordlists into one multilingual dictionary source.

Why this exists
---------------
FUTO Keyboard loads exactly one main dictionary per locale
(`DictionaryFactory.java`: an imported custom dictionary REPLACES the bundled
one, it does not layer on top). To type two languages under a single subtype --
one entry in the language switcher, no switching -- the two wordlists have to
be merged before compilation.

The engine itself is locale-blind about dictionary contents: no per-word locale
tags, no script validation, no rejection at load or query time. So a merged
wordlist simply works, and swipe picks it up too, because swipe candidates come
from the loaded dictionaries rather than a per-locale list.

Frequencies
-----------
Every AOSP wordlist is already normalised to the same 0-255 scale, so no
cross-corpus rescaling is needed -- only a rule for words that appear in both.
`max` is the default and is the safe choice: it never demotes a word below what
either language thought it was worth. The clearest case is `i`, which is f=0 in
en_US (English "I" is always capitalised) and f=209 in Polish (it means "and").
`max` keeps Polish correct without hurting English.

Input
-----
The wordlists ship in the FUTO app repo under `dictionaries/`. Point --inputs at
them; `.gz` and plain text both work.

Output
------
A single `.combined` file. Compile it to the binary `.dict` FUTO imports with
AOSP dicttool:

    java -jar dicttool_aosp.jar makedict -s merged.combined -d main_pl.dict

dicttool emits format VERSION202, which FUTO accepts (it takes magic 0x9BC13AFE
and header versions 201, 202, 402 and 403). Note FUTO explicitly REJECTS a
`.combined` / `.combined.gz` upload -- only the compiled `.dict` imports.
"""

from __future__ import annotations

import argparse
import gzip
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ` word=foo,f=123,flags=,originalFreq=123` / `  shortcut=bar,f=whitelist`
# Deliberately backslash-free so the pattern survives any quoting layer.
LINE_RE = re.compile(r"^([ ]*)(word|shortcut)=(.*?),(.*)$")
HEADER_RE = re.compile(r"^dictionary=")

# Attributes that assert a word is NOT real. These must be INTERSECTED, not
# unioned: if any language treats the word as real, it is real.
#
# This matters more than it looks. English marks `i` and `im` not_a_word because
# there they are only shortcuts for "I" and "I'm" -- but in Polish `i` means
# "and" and is among the most frequent words in the language. Unioning the flag
# would suppress it from Polish suggestions entirely.
NEGATIVE_ATTRS = frozenset({"not_a_word"})


@dataclass
class Entry:
    word: str
    attrs: dict[str, str]
    children: list[tuple[str, dict[str, str]]] = field(default_factory=list)


def _open(path: Path):
    if path.suffix == ".gz":
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("r", encoding="utf-8")


def parse(path: Path) -> tuple[dict[str, str], list[Entry]]:
    """Return (header attrs, entries). Child lines attach to the preceding word."""
    header: dict[str, str] = {}
    entries: list[Entry] = []
    with _open(path) as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.rstrip("\n").rstrip("\r")
            if not line.strip():
                continue
            if HEADER_RE.match(line):
                header = dict(
                    kv.split("=", 1) for kv in line.split(",") if "=" in kv
                )
                continue
            m = LINE_RE.match(line)
            if not m:
                print(f"{path.name}:{lineno}: unparsed, skipped: {line[:70]!r}",
                      file=sys.stderr)
                continue
            indent, kind, value, rest = m.groups()
            attrs = dict(kv.split("=", 1) for kv in rest.split(",") if "=" in kv)
            if kind == "shortcut":
                if not entries:
                    print(f"{path.name}:{lineno}: orphan shortcut, skipped",
                          file=sys.stderr)
                    continue
                entries[-1].children.append((value, attrs))
            else:
                entries.append(Entry(word=value, attrs=attrs))
    return header, entries


def freq(attrs: dict[str, str]) -> int | None:
    """Numeric frequency, or None for non-numeric markers like f=whitelist."""
    v = attrs.get("f", "")
    return int(v) if v.isdigit() else None


def merge_attrs(a: dict[str, str], b: dict[str, str], rule: str) -> dict[str, str]:
    """Union the flags, resolve `f` by `rule`, keep originalFreq consistent."""
    out = dict(a)
    for k, v in b.items():
        if k == "f" or k in NEGATIVE_ATTRS:
            continue
        # Positive markers (possibly_offensive, whitelist, flags) union: if
        # either language says a word is offensive, it stays offensive.
        if k not in out or not out[k]:
            out[k] = v

    # Negative markers intersect: only keep one if BOTH sides assert it.
    # Merging is incremental, so pairwise intersection is intersection across
    # every input that contains the word.
    for k in NEGATIVE_ATTRS:
        if k in out and k not in b:
            del out[k]

    fa, fb = freq(a), freq(b)
    if fa is None and fb is None:
        out["f"] = a.get("f", b.get("f", ""))
    elif fa is None:
        out["f"] = str(fb)
    elif fb is None:
        out["f"] = str(fa)
    elif rule == "max":
        out["f"] = str(max(fa, fb))
    elif rule == "sum":
        out["f"] = str(min(255, fa + fb))
    elif rule == "mean":
        out["f"] = str((fa + fb) // 2)
    else:
        raise ValueError(f"unknown merge rule: {rule}")

    if "originalFreq" in out and out["f"].isdigit():
        out["originalFreq"] = out["f"]
    return out


def merge(sources: list[tuple[Path, list[Entry]]], rule: str) -> tuple[list[Entry], dict[str, int]]:
    by_word: dict[str, Entry] = {}
    stats = {"total": 0, "collisions": 0}
    for _, entries in sources:
        for e in entries:
            stats["total"] += 1
            existing = by_word.get(e.word)
            if existing is None:
                by_word[e.word] = Entry(e.word, dict(e.attrs), list(e.children))
                continue
            stats["collisions"] += 1
            existing.attrs = merge_attrs(existing.attrs, e.attrs, rule)
            seen = {c for c, _ in existing.children}
            existing.children.extend((c, a) for c, a in e.children if c not in seen)

    # Source lists are ordered by descending frequency; preserve that so the
    # merged file reads the same way and diffs sensibly.
    merged = sorted(
        by_word.values(),
        key=lambda e: (-(freq(e.attrs) or 0), e.word),
    )
    return merged, stats


def emit(path: Path, header: dict[str, str], entries: list[Entry]) -> None:
    key_order = ["word", "f", "flags", "originalFreq"]

    def render(kind: str, value: str, attrs: dict[str, str], indent: int) -> str:
        parts = [f"{kind}={value}"]
        for k in key_order[1:]:
            if k in attrs:
                parts.append(f"{k}={attrs[k]}")
        for k, v in attrs.items():
            if k not in key_order:
                parts.append(f"{k}={v}")
        return " " * indent + ",".join(parts)

    # The header is a flat comma-separated key=value line with no escaping, so a
    # separator inside a value (most plausibly in --description) would silently
    # split into a bogus extra field instead of failing.
    for k, v in header.items():
        for bad in (",", "=", "\n", "\r"):
            if bad in str(v):
                raise SystemExit(
                    f"header field {k}={v!r} contains {bad!r}, which would corrupt "
                    f"the .combined header rather than fail")

    hdr = ",".join(f"{k}={v}" for k, v in header.items())
    with path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(hdr + "\n")
        for e in entries:
            fh.write(render("word", e.word, e.attrs, 1) + "\n")
            for c, a in e.children:
                fh.write(render("shortcut", c, a, 2) + "\n")


def self_test() -> int:
    """Exercise the merge rules on synthetic entries.

    The repo has no test suite -- validation lives in standalone scripts
    (validate_keylayout.py) -- so the rules that are easy to get wrong guard
    themselves here.
    """
    cases: list[tuple[str, dict[str, str], dict[str, str], str, dict[str, str]]] = [
        # name, a, b, rule, expected subset of the merged attrs
        ("max keeps the higher frequency",
         {"f": "0"}, {"f": "209"}, "max", {"f": "209"}),
        ("max is order-independent",
         {"f": "209"}, {"f": "0"}, "max", {"f": "209"}),
        ("sum saturates at the 0-255 AOSP scale",
         {"f": "200"}, {"f": "100"}, "sum", {"f": "255"}),
        ("originalFreq follows the merged f",
         {"f": "10", "originalFreq": "10"}, {"f": "90", "originalFreq": "90"},
         "max", {"f": "90", "originalFreq": "90"}),
        ("non-numeric f on one side does not win",
         {"f": "whitelist"}, {"f": "42"}, "max", {"f": "42"}),
        ("offensive unions - either side is enough",
         {"f": "5"}, {"f": "5", "possibly_offensive": "true"}, "max",
         {"possibly_offensive": "true"}),
        ("flags union",
         {"f": "5"}, {"f": "5", "flags": "abbreviation"}, "max",
         {"flags": "abbreviation"}),
    ]

    failures = 0
    for name, a, b, rule, expected in cases:
        got = merge_attrs(a, b, rule)
        bad = {k: (v, got.get(k)) for k, v in expected.items() if got.get(k) != v}
        print(("  ok   " if not bad else "  FAIL ") + name)
        if bad:
            failures += 1
            print(f"         expected {bad}")

    # The one that actually bit: not_a_word must INTERSECT. English marks `i`
    # not_a_word; Polish does not, and Polish `i` means "and".
    neg_cases = [
        ("not_a_word dropped when only one side asserts it",
         {"f": "0", "not_a_word": "true"}, {"f": "209"}, False),
        ("not_a_word dropped when only the other side asserts it",
         {"f": "209"}, {"f": "0", "not_a_word": "true"}, False),
        ("not_a_word kept when both sides assert it",
         {"f": "0", "not_a_word": "true"}, {"f": "1", "not_a_word": "true"}, True),
    ]
    for name, a, b, want in neg_cases:
        got = "not_a_word" in merge_attrs(a, b, "max")
        ok = got == want
        print(("  ok   " if ok else "  FAIL ") + name)
        if not ok:
            failures += 1
            print(f"         expected not_a_word present={want}, got {got}")

    print()
    print("  " + ("all rules pass" if not failures else f"{failures} FAILURE(S)"))
    return 1 if failures else 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--self-test", action="store_true",
                    help="check the merge rules and exit")
    ap.add_argument("--inputs", nargs="+", type=Path,
                    help="AOSP .combined or .combined.gz wordlists to merge")
    ap.add_argument("--output", type=Path,
                    help="destination .combined file")
    ap.add_argument("--locale", default="pl",
                    help="locale for the merged header. Only soft-filters FUTO's "
                         "import picker and enables English vowel fuzzing in the "
                         "native proximity model; it is not validated against the "
                         "subtype you import into. (default: pl)")
    ap.add_argument("--description", default=None,
                    help="header description (default: derived from the inputs)")
    ap.add_argument("--rule", choices=["max", "sum", "mean"], default="max",
                    help="frequency rule for words present in more than one input "
                         "(default: max)")
    ap.add_argument("--report", action="store_true",
                    help="print the largest frequency disagreements, which are the "
                         "words most likely to autocorrect wrongly")
    args = ap.parse_args()

    if args.self_test:
        return self_test()
    if not args.inputs or not args.output:
        ap.error("--inputs and --output are required (or use --self-test)")

    missing = [p for p in args.inputs if not p.is_file()]
    if missing:
        for p in missing:
            print(f"error: not found: {p}", file=sys.stderr)
        print("\nThe AOSP wordlists ship in the FUTO app repo under dictionaries/.",
              file=sys.stderr)
        return 1
    if len(args.inputs) < 2:
        print("error: --inputs needs at least two wordlists to merge", file=sys.stderr)
        return 1

    sources: list[tuple[Path, list[Entry]]] = []
    headers: list[dict[str, str]] = []
    for p in args.inputs:
        header, entries = parse(p)
        headers.append(header)
        sources.append((p, entries))
        print(f"  {p.name}: {len(entries):,} entries "
              f"(locale={header.get('locale', '?')})")

    merged, stats = merge(sources, args.rule)

    locales = [h.get("locale", "?") for h in headers]
    description = args.description or " + ".join(
        h.get("description", h.get("locale", "?")) for h in headers
    )
    out_header = {
        "dictionary": f"main:{args.locale}",
        "locale": args.locale,
        "description": description,
        # A fixed date keeps the output reproducible; dicttool does not care.
        "date": headers[0].get("date", "0"),
        "version": headers[0].get("version", "54"),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    emit(args.output, out_header, merged)

    print(f"\n  merged {' + '.join(locales)} -> {args.output}")
    print(f"  {stats['total']:,} entries in, {len(merged):,} out, "
          f"{stats['collisions']:,} collisions "
          f"({100 * stats['collisions'] / max(stats['total'], 1):.1f}%)")
    print(f"  frequency rule: {args.rule}")

    if args.report and len(sources) == 2:
        (_, a), (_, b) = sources
        fa = {e.word: freq(e.attrs) for e in a}
        fb = {e.word: freq(e.attrs) for e in b}
        both = [w for w in fa if w in fb
                and fa[w] is not None and fb[w] is not None]
        both.sort(key=lambda w: -abs((fa[w] or 0) - (fb[w] or 0)))
        print(f"\n  largest disagreements ({locales[0]} / {locales[1]}) -- these are "
              f"where a merged dictionary is most likely to correct wrongly:")
        for w in both[:15]:
            print(f"    {w:<16} {fa[w]:>3} / {fb[w]:>3}  -> {max(fa[w] or 0, fb[w] or 0)}")

    print("\n  Next: compile to the binary .dict FUTO imports:")
    print(f"    java -jar dicttool_aosp.jar makedict -s {args.output} "
          f"-d main_{args.locale}.dict")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
