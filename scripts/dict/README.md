# Combined en+pl dictionary

FUTO Keyboard loads exactly **one** main dictionary per locale — an imported
custom dictionary *replaces* the bundled one rather than layering on top
(`DictionaryFactory.java`). So typing two languages under a single subtype —
one entry in the language switcher, no switching — means merging the two
wordlists before compiling.

This is what makes the "one universal keyboard" goal work. The engine is
locale-blind about dictionary *contents*: no per-word locale tags, no script
validation, no rejection at load or query time. Swipe benefits automatically,
because swipe candidates come from the loaded dictionaries rather than a
separate per-locale list.

## Build

The source wordlists ship in the FUTO app repo under `dictionaries/`:

```bash
D=../futo/android-keyboard/dictionaries
python scripts/dict/merge_wordlists.py \
    --inputs "$D/en_US_wordlist.combined.gz" "$D/pl_wordlist.combined.gz" \
    --output dist/dict/en_pl_wordlist.combined \
    --locale pl --report
```

Then compile to the binary `.dict` FUTO imports, using AOSP dicttool:

```bash
java -jar dicttool_aosp.jar makedict \
    -s dist/dict/en_pl_wordlist.combined -d main_pl.dict
```

Import it in FUTO: share the `.dict` to the app, or Settings → Languages →
the language → dictionary.

## Facts worth knowing

- **No frequency rescaling is needed.** Every AOSP wordlist is already on the
  same 0–255 scale (en_US tops out at 222, pl at 218), so only a collision rule
  is required. `max` is the default.
- **The collision rate is low** — 11,425 words of 344,389, about 3%.
- **`not_a_word` is intersected, not unioned.** English marks `i` and `im`
  `not_a_word` because there they are only shortcuts for "I" and "I'm". Polish
  `i` means "and" and is one of its most frequent words. Unioning the flag would
  suppress it from Polish suggestions entirely. `possibly_offensive` and
  `flags` *are* unioned. `python scripts/dict/merge_wordlists.py --self-test`
  guards both rules.
- **`--report` prints the largest frequency disagreements.** Those are the words
  most likely to autocorrect wrongly — mostly short function words like
  `i co im ani do to a by we on`.
- **FUTO rejects `.combined` / `.combined.gz` uploads.** Only the compiled
  `.dict` imports (magic `0x9BC13AFE`, header versions 201/202/402/403; dicttool
  emits 202).
- **`dicttool` is not a Gradle module.** It is a Soong `java_binary_host`
  (`tools/dicttool/Android.bp`), so building it needs the AOSP host build or a
  prebuilt `dicttool_aosp.jar`.
- **The header `locale=`** only soft-filters FUTO's import picker and enables
  English vowel fuzzing in the native proximity model. It is not validated
  against the subtype you import into.

## Licensing

The wordlists come from the FUTO app repo, which carries the FUTO Source First
License 1.1-kb, though the wordlists themselves are AOSP/LatinIME heritage
(historically Apache-2.0). **Verify their provenance before redistributing a
compiled dictionary** — using them purely as a local input avoids the question.
