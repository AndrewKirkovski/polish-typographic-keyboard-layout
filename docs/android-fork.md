# The Android app fork

The layouts are plain YAML and work on stock FUTO Keyboard — most people need
nothing here. This document is for the patched build: our own APK carrying fixes
FUTO has not merged, installable alongside the official app.

**Upstream acceptance is a bonus, never a blocker.** Each patch sits on its own
branch so it stays PR-ready, but the fork is the thing we actually use.

## Where it lives

| Path | Repo | Remotes |
|---|---|---|
| `C:\Projects\futo\android-keyboard` | app fork | `origin` → `AndrewKirkovski/android-keyboard`, `upstream` → `futo-org/…` |
| `C:\Projects\futo\futo-keyboard-layouts` | layouts fork | same pattern |

## Licence — read this before sharing an APK

`LICENSE.md` is the **FUTO Source First License 1.1-kb** (note the suffix; the
README drops it). It permits modification and redistribution **only free of
charge and non-commercially**, and requires shipping the licence terms plus a
**prominent notice of modifications**.

Building your own APK and handing it to whoever wants it is squarely inside that
grant. Selling it, bundling it commercially, or stripping the payment prompts is
not. If you publish the APK, the release notes must carry the modification notice.

## First build

All seven submodules are publicly fetchable without credentials. The layouts one
points at **our** fork; the rest are upstream.

```bash
git submodule update --init --recursive
```

| Submodule | Host | Size |
|---|---|---|
| `libs` | gitlab.futo.org/keyboard/android-libs | 46 MB |
| `java/res-large` | gitlab.futo.org/keyboard/keyboard-large-resources | 82 MB |
| `java/assets/themes` | gitlab.futo.org/keyboard/seasonal-themes | 75 KB |
| `translations` | gitlab.futo.org/keyboard/keyboard-translations-public | 22 MB |
| `java/assets/futo-swipe` | huggingface.co/futo-org/futo-swipe | 28 MB |
| `voiceinput-shared/src/main/ml` | gitlab.futo.org/keyboard/voice-input-models | 79 MB |
| `java/assets/layouts` | **our layouts fork** | 1.2 MB |

Then:

```bash
export JAVA_HOME="/c/Program Files/Android/Android Studio/jbr"   # JDK 17+
export ANDROID_HOME="$HOME/AppData/Local/Android/Sdk"
echo "sdk.dir=$ANDROID_HOME" > local.properties

./gradlew assembleKirkouskiDebug
```

The first build takes roughly 8 minutes: it compiles llama.cpp, whisper.cpp,
ggml and sentencepiece from source for every ABI. Later builds are ~30 seconds
unless native sources change.

Do **not** pipe Gradle through `tail` — the pipeline then reports `tail`'s exit
code and a failed build looks like a success.

## Adding a product flavour needs four things, not one

This cost several failed builds. `kirkouski` exists so the APK installs
alongside both the Play Store app *and* FUTO's own `.unstable` nightly — using
`unstable` directly would let their nightly replace our build.

1. **`productFlavors` entry** — `applicationIdSuffix ".kirkouski"`,
   `versionNameSuffix`, and `UPDATE_CHECKING false` so the build never prompts to
   "update" to an upstream release that would drop our patches.
2. **`sourceSets` entry.** Without it the Kotlin compile fails on
   `CrashLoggingApplication`, which lives only in `java/stable/java`. Mirrors
   `unstable`.
3. **Per-flavour dependencies.** ACRA is declared as `stableImplementation` /
   `unstableImplementation`, so a new flavour needs its own
   `kirkouskiImplementation` lines or every ACRA import is unresolved.
4. **An idempotent `translationsWithoutEngValues()`.** It calls
   `tasks.register()` unconditionally, so a second flavour referencing the same
   translations directory (`translations/devbuild`) fails configuration with
   "task already exists".

## Patches carried

| | What | Upstream-worthy |
|---|---|---|
| **P1** | One-handed exit button: settings toggle + long-press-to-exit | yes |
| **P2** | `ModelList.kt:73` renders `Locale("en pl").displayLanguage` as a garbage heading for multi-language models | yes |
| **P3** | `actionForCoord` uses `regularColumn` raw while `symsForCoord` applies a centering offset, so Quick Actions land on the wrong letters on non-10/10/7 rows | yes |
| **P4** | The autocorrect encoder derives `inputSize` from `partialWordString.size()` (**bytes**) while `inComposeX` counts **taps**, then indexes the byte string by tap index — characters and coordinates desynchronise for any word with a multi-byte character. Latent for every non-Latin-1 script | yes, most substantive |
| **P5** | `:updateLocales` runs `python` with no encoding set; on Windows that inherits cp1252 and dies with UnicodeEncodeError before `preBuild`, breaking the build for every Windows contributor | yes |
| **P6** | `translationsWithoutEngValues()` made idempotent (see above) | marginal — only bites when adding a flavour |

P5 and P6 were found by building, not by reading.

## Branch layout

```
upstream/master
├─ fix/one-handed-exit-toggle       P1  ─┐
├─ fix/multilang-model-heading      P2  ─┤
├─ fix/action-coord-offset          P3  ─┤ PR-ready: clean, no local config
├─ fix/autocorrect-byte-tap-desync  P4  ─┤
├─ fix/windows-build-utf8           P5  ─┤
├─ fix/translations-task-idempotent P6  ─┘
└─ main  ◄── P1–P6 + the kirkouski flavour + .gitmodules → our layouts fork
```

**`.gitmodules` discipline:** the commit repointing `java/assets/layouts` at our
fork lives **only** on `main`. Every `fix/*` branch keeps `futo-org`, so a PR
never carries it. Check with:

```bash
git diff upstream/master -- .gitmodules   # must be empty on any fix/* branch
```

## Signing

`signingConfigs.debug` uses a **committed** `java/shared.keystore`, and release
signing silently falls back to it unless a gitignored `keystore.properties`
exists.

Generate your own keystore and point `keystore.properties` at it. Two reasons:
anything signed with the shared debug key can replace your install, and Android
refuses in-place upgrades when the signature changes — getting this wrong later
means uninstall-and-lose-your-settings. Keep the keystore out of git and back it
up somewhere durable.

To prove it works: bump the version, rebuild, and install over the top. If the
upgrade is refused, the signing is wrong.

## Staying current

Upstream ships roughly monthly (0.1.28 May, 0.1.29 Jun, 0.1.30 Aug 2026).

1. `git fetch upstream --tags`
2. Rebase each `fix/*` branch onto the new tag. A conflict is a useful signal —
   check whether the bug was fixed upstream before re-applying.
3. Rebuild `main` from the tag plus the rebased patches.
4. Tag `v<upstream>-kirkouski.N` and build the APK.

Rebase rather than merge, so `main` stays a readable "upstream plus N patches"
and dropping a patch upstream accepts is a deletion rather than a revert.
