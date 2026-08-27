#!/usr/bin/env python3
"""Compile an AOSP `.combined` wordlist into the binary `.dict` FUTO imports.

Why this exists
---------------
`merge_wordlists.py` produces a `.combined` source; FUTO refuses to import that
file (`ImportResourceActivity.kt` maps the gzip and `dict` magics to
`InvalidFileHint.ImportedWordListInsteadOfDict`). Only the compiled binary is
accepted: magic `0x9BC13AFE`, header version 201, 202, 402 or 403.

The compiler is AOSP `dicttool`, which upstream builds with Soong
(`tools/dicttool/Android.bp` declares a `java_binary_host`). There is no Gradle
module for it and no AOSP host build on a normal dev machine, so this script
compiles the one code path we need -- `.combined` in, VERSION202 `.dict` out --
directly with `javac`, against the sources already checked out in the app repo.

That path is pure Java. The Ver4 encoder needs `libjni_latinime`; Ver2 does not,
so nothing here requires the NDK.

Three sources are stubbed for the host build, all of them Android-only leaves of
the dependency graph that the encoder never calls: `kotlin.Pair` (a field type in
`InputPointers`), `BuildConfig.DEBUG`, and
`DictionaryFacilitatorImpl.onAnyBinaryDictionaryClosed()` (on device this
invalidates the swipe tries; off device there are none).

Why swipe needs this
--------------------
Swipe candidates are drawn from tries built over the *loaded dictionaries*
(`DictionaryFacilitatorImpl.updateSwipeLayoutAndDictsIfNeeded`), and the decoder
bails out with "Applied tries are blank!" when there are none. FUTO ships no
Polish dictionary and its download site offers none, so a Polish subtype has no
main dictionary, no trie, and therefore no swipe -- regardless of layout. Import
the dictionary this script produces and swipe starts working.

The trie is built over the layout's letters, and `get_letter_index`
(`dictionary_itrie.cpp`) falls back to `CharUtils::toBaseLowerCase`, so all nine
Polish diacritics resolve to their base letter. Swiping l-o-d-z reaches `lodz`
with no need for the accented letters to have keys of their own.

Usage
-----
    python scripts/dict/compile_dict.py \\
        --input dist/dict/en_pl_wordlist.combined \\
        --output dist/dict/main_pl.dict

    # same words, retargeted at an en_US subtype
    python scripts/dict/compile_dict.py \\
        --input dist/dict/en_pl_wordlist.combined \\
        --output dist/dict/main_en_US.dict \\
        --locale en_US --dictionary-id main:en_US

`--locale` rewrites the `.combined` header before compiling. The value lands in
the `.dict` header, where it soft-filters the import picker and selects the
native proximity model's vowel fuzzing; it is never validated against the
subtype the dictionary is imported for.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Default location of the app fork; see docs/android-fork.md.
DEFAULT_FUTO_REPO = REPO_ROOT.parent / "futo" / "android-keyboard"

# Source roots inside the app repo. Order matters: the generated stubs shadow
# same-named classes further down the list.
SOURCE_ROOTS = ("tools/dicttool/compat", "java/src", "tests/src", "common/src")

# Listed explicitly because their directory layout does not match their package
# (`tools/dicttool/src/com/android/...` declaring `org.futo.inputmethod.latin.*`),
# so javac cannot find them through -sourcepath.
EXPLICIT_SOURCES = (
    "tools/dicttool/src/com/android/inputmethod/latin/dicttool/CombinedInputOutput.java",
    "tools/dicttool/compat/com/android/inputmethod/latin/utils/"
    "WordInputEventForPersonalization.java",
)

STUBS: dict[str, str] = {
    # jsr305 was removed from the JDK in 11 and is not otherwise on the host
    # classpath. Only these two are imported anywhere in the closure.
    "javax/annotation/Nonnull.java": """\
package javax.annotation;
import java.lang.annotation.*;
/** Host-build stub for jsr305. */
@Documented @Retention(RetentionPolicy.RUNTIME)
public @interface Nonnull { }
""",
    "javax/annotation/Nullable.java": """\
package javax.annotation;
import java.lang.annotation.*;
/** Host-build stub for jsr305. */
@Documented @Retention(RetentionPolicy.RUNTIME)
public @interface Nullable { }
""",
    "kotlin/Pair.java": """\
package kotlin;
/** Host-build stub: a field type in InputPointers, never read by the encoder. */
public class Pair<A, B> {
    private final A first;
    private final B second;
    public Pair(A a, B b) { first = a; second = b; }
    public A getFirst() { return first; }
    public B getSecond() { return second; }
    public A component1() { return first; }
    public B component2() { return second; }
}
""",
    "org/futo/inputmethod/latin/BuildConfig.java": """\
package org.futo.inputmethod.latin;
/** Host-build stub: only DEBUG is referenced, by DebugFlags. */
public final class BuildConfig { public static final boolean DEBUG = false; }
""",
    "org/futo/inputmethod/latin/DictionaryFacilitatorImpl.java": """\
package org.futo.inputmethod.latin;
/** Host-build stub: on device this invalidates swipe tries; off device there are none. */
public class DictionaryFacilitatorImpl {
    public static void onAnyBinaryDictionaryClosed() { }
}
""",
    "org/futo/inputmethod/latin/dicttool/MakeDictMain.java": """\
package org.futo.inputmethod.latin.dicttool;

import org.futo.inputmethod.latin.makedict.DictEncoder;
import org.futo.inputmethod.latin.makedict.FormatSpec;
import org.futo.inputmethod.latin.makedict.FusionDictionary;
import org.futo.inputmethod.latin.makedict.Ver2DictEncoder;

import java.io.BufferedReader;
import java.io.File;
import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;

/** The one dicttool code path we need: .combined in, VERSION202 .dict out. */
public final class MakeDictMain {
    public static void main(final String[] args) throws Exception {
        if (args.length < 2) {
            System.err.println("usage: MakeDictMain <in.combined> <out.dict>");
            System.exit(2);
        }
        final FusionDictionary dict;
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(
                new FileInputStream(args[0]), StandardCharsets.UTF_8))) {
            dict = CombinedInputOutput.readDictionaryCombined(reader);
        }
        final File outputFile = new File(args[1]);
        final FormatSpec.FormatOptions formatOptions =
                new FormatSpec.FormatOptions(FormatSpec.VERSION202);
        final DictEncoder encoder =
                new Ver2DictEncoder(outputFile, Ver2DictEncoder.CODE_POINT_TABLE_ON);
        encoder.writeDictionary(dict, formatOptions);
        System.out.println("wrote " + outputFile.getAbsolutePath()
                + " (" + outputFile.length() + " bytes)");
    }
}
""",
}

DICT_MAGIC = bytes((0x9B, 0xC1, 0x3A, 0xFE))
SUPPORTED_VERSIONS = (201, 202, 402, 403)


def find_jdk_tool(name: str, java_home: str | None) -> str:
    """Locate javac/java, preferring an explicit --java-home, then JAVA_HOME,
    then Android Studio's bundled JBR, then PATH."""
    exe = f"{name}.exe" if os.name == "nt" else name
    candidates = []
    if java_home:
        candidates.append(Path(java_home) / "bin" / exe)
    if os.environ.get("JAVA_HOME"):
        candidates.append(Path(os.environ["JAVA_HOME"]) / "bin" / exe)
    if os.name == "nt":
        candidates.append(
            Path(r"C:\Program Files\Android\Android Studio\jbr\bin") / exe)
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    found = shutil.which(name)
    if found:
        return found
    raise SystemExit(
        f"{name} not found. Pass --java-home, or set JAVA_HOME to a JDK 11+ install.")


def build_compiler(futo_repo: Path, work_dir: Path, java_home: str | None) -> Path:
    """Compile the host converter into work_dir/classes, and return that path."""
    for root in SOURCE_ROOTS:
        if not (futo_repo / root).is_dir():
            raise SystemExit(
                f"{futo_repo / root} not found -- is --futo-repo pointing at a full "
                "android-keyboard checkout? See docs/android-fork.md.")

    gen_dir = work_dir / "gen"
    for rel, body in STUBS.items():
        path = gen_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")

    classes_dir = work_dir / "classes"
    if classes_dir.exists():
        shutil.rmtree(classes_dir)
    classes_dir.mkdir(parents=True)

    sourcepath = os.pathsep.join(
        [str(gen_dir)] + [str(futo_repo / root) for root in SOURCE_ROOTS])

    cmd = [
        find_jdk_tool("javac", java_home),
        "-nowarn", "-proc:none", "--release", "11",
        "-d", str(classes_dir),
        "-sourcepath", sourcepath,
        str(gen_dir / "org/futo/inputmethod/latin/dicttool/MakeDictMain.java"),
    ]
    cmd += [str(futo_repo / rel) for rel in EXPLICIT_SOURCES]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        sys.stderr.write(result.stdout)
        sys.stderr.write(result.stderr)
        raise SystemExit("javac failed -- see output above.")
    return classes_dir


def check_header_value(name: str, value: str) -> str:
    """The .combined header is a flat comma-separated key=value line with no
    escaping, so a value containing a separator would silently split into a bogus
    extra field rather than fail. Reject it instead."""
    for bad in (",", "=", "\n", "\r"):
        if bad in value:
            raise SystemExit(
                f"--{name} may not contain {bad!r}: the .combined header is "
                f"comma-separated key=value with no escaping, so this would "
                f"corrupt the header rather than fail. Got: {value!r}")
    return value


def retarget_header(source: Path, dest: Path, locale: str | None,
                    dictionary_id: str | None, description: str | None) -> None:
    """Copy the .combined, rewriting the header's key=value pairs in place."""
    for name, value in (("locale", locale), ("dictionary-id", dictionary_id),
                        ("description", description)):
        if value is not None:
            check_header_value(name, value)
    with source.open(encoding="utf-8") as handle:
        header = handle.readline().rstrip("\n")
        if not header.startswith("dictionary="):
            raise SystemExit(f"{source} does not start with a dictionary= header.")
        fields = dict(
            part.split("=", 1) for part in header.split(",") if "=" in part)
        if dictionary_id:
            fields["dictionary"] = dictionary_id
        if locale:
            fields["locale"] = locale
        if description:
            fields["description"] = description
        # `dictionary` must stay first; the rest of the order is irrelevant.
        ordered = ["dictionary"] + [k for k in fields if k != "dictionary"]
        with dest.open("w", encoding="utf-8", newline="\n") as out:
            out.write(",".join(f"{k}={fields[k]}" for k in ordered) + "\n")
            shutil.copyfileobj(handle, out)


def verify(dict_path: Path) -> None:
    """Check the output against what ImportResourceActivity actually accepts."""
    with dict_path.open("rb") as handle:
        head = handle.read(4096)
    if head[:4] != DICT_MAGIC:
        raise SystemExit(
            f"{dict_path} has magic {head[:4].hex()}, expected {DICT_MAGIC.hex()}.")
    version = int.from_bytes(head[4:6], "big")
    if version not in SUPPORTED_VERSIONS:
        raise SystemExit(
            f"{dict_path} is version {version}; FUTO accepts {SUPPORTED_VERSIONS}.")

    # The header is a run of 0x1F-separated key/value pairs starting at `date`.
    text = head.decode("utf-8", errors="replace")
    parts = text.split("\x1f")
    header = {}
    for i in range(len(parts) - 1):
        key = parts[i].lstrip("\x00")
        if key in ("date", "dictionary", "description", "locale", "version"):
            header[key] = parts[i + 1]
    print("  magic     ok (0x9BC13AFE)")
    print(f"  version   {version}")
    for key in ("dictionary", "locale", "description"):
        if key in header:
            print(f"  {key:9s} {header[key]}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compile a .combined wordlist into a FUTO-importable .dict.")
    parser.add_argument("--input", required=True, type=Path,
                        help="Source .combined wordlist.")
    parser.add_argument("--output", required=True, type=Path,
                        help="Destination .dict file.")
    parser.add_argument("--locale",
                        help="Rewrite the header locale (e.g. pl, en_US).")
    parser.add_argument("--dictionary-id",
                        help="Rewrite the header dictionary id (e.g. main:en_US).")
    parser.add_argument("--description",
                        help="Rewrite the header description; this is the name "
                             "shown in FUTO's import picker.")
    parser.add_argument("--futo-repo", type=Path,
                        default=Path(os.environ.get("FUTO_KEYBOARD_REPO",
                                                    DEFAULT_FUTO_REPO)),
                        help=f"android-keyboard checkout (default: {DEFAULT_FUTO_REPO}).")
    parser.add_argument("--java-home", help="JDK 11+ to compile and run with.")
    parser.add_argument("--work-dir", type=Path,
                        default=REPO_ROOT / "build" / "dicttool",
                        help="Where the host converter is compiled.")
    parser.add_argument("--heap", default="4g",
                        help="JVM max heap for the conversion (default: 4g).")
    args = parser.parse_args()

    if not args.input.is_file():
        raise SystemExit(f"{args.input} not found.")

    futo_repo = args.futo_repo.resolve()
    args.work_dir.mkdir(parents=True, exist_ok=True)

    print(f"Compiling host converter against {futo_repo} ...")
    classes_dir = build_compiler(futo_repo, args.work_dir, args.java_home)

    source = args.input
    temp_source = None
    # The temp file is created inside the try so that a failure in
    # retarget_header -- a missing header, an undecodable input -- still reaches
    # the finally below instead of leaving the file behind.
    try:
        if args.locale or args.dictionary_id or args.description:
            # mkstemp hands back an open descriptor; on Windows the file stays
            # locked until it is closed, which would break the unlink below.
            handle, temp_name = tempfile.mkstemp(suffix=".combined")
            os.close(handle)
            temp_source = Path(temp_name)
            retarget_header(args.input, temp_source, args.locale,
                            args.dictionary_id, args.description)
            source = temp_source

        args.output.parent.mkdir(parents=True, exist_ok=True)
        print(f"Converting {args.input.name} -> {args.output.name} ...")
        result = subprocess.run(
            [find_jdk_tool("java", args.java_home), f"-Xmx{args.heap}",
             "-cp", str(classes_dir),
             "org.futo.inputmethod.latin.dicttool.MakeDictMain",
             str(source), str(args.output)],
            capture_output=True, text=True)
        if result.returncode != 0:
            sys.stderr.write(result.stdout)
            sys.stderr.write(result.stderr)
            raise SystemExit("Conversion failed -- see output above.")
    finally:
        if temp_source is not None:
            temp_source.unlink(missing_ok=True)

    print("Verifying header:")
    verify(args.output)
    print(f"OK -- {args.output} ({args.output.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
