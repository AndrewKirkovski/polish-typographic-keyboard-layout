/**
 * usePlayback — keyboard playback animation state machine.
 *
 * Drives the per-character typewriter animation that types one of the
 * variant-specific demo phrases while highlighting the corresponding
 * keys on the keyboard visualisation.
 *
 * Dependencies (injected by caller):
 *   - `pressedKeyIds: Ref<Set<string>>` — writes keyId in, removes after holdMs
 *   - `setManualLayer(layer|null)` — forces the visual layer to match
 *   - `layout: Ref<LayoutData|null>` — resolved against for step sequences
 *   - `phrases: Ref<readonly string[]>` — the pool to cycle
 *
 * External behaviour:
 *   - `enabled` is persisted in localStorage so the user's on/off choice
 *     survives reloads. Default = true, overridden to false when the user
 *     has `prefers-reduced-motion: reduce` set at first mount.
 *   - `sessionInterrupted` is a session-only flag that flips true on any
 *     real keyboard interaction while the player is running. The player
 *     stops and refuses auto-restart until the user either reloads or
 *     explicitly clicks the toggle.
 *   - Bare Shift presses do NOT interrupt (the user is probably inspecting
 *     the shift layer while the demo runs).
 *   - A single recursive setTimeout chain drives step progression;
 *     cancellation is a one-liner (clearTimeout on the tracked id).
 */

import { ref, watch, onMounted, onBeforeUnmount, type Ref } from 'vue'
import type { LayoutData } from './useLayout'
import { resolvePhrase, type Step, type Layer } from './useCharToSteps'

// Two-tier timing. "Fast" is the default for everything a user would
// actually type a lot (Cyrillic, Latin, digits, Polish direct diacritics,
// typographic marks on AltGr). "Slow" applies to dead-key compositions
// where the whole point is to *see* the trigger + letter sequence
// compose into an otherwise-unreachable character (č, ö, ő, ў, …).
// Every gap between visible actions gets its own delay so each press
// reads as a distinct event.
interface Tempo {
  modPressHold: number    // after a modifier goes down, pause before the next press
  letterHold: number      // how long the letter keycap stays lit
  letterReleaseGap: number // after letter released, before releasing mods
  modReleaseGap: number   // after each modifier released
  interChar: number       // gap between adjacent chars in the phrase
  spaceDwell: number      // space bar advance
}

const FAST_TEMPO: Tempo = {
  modPressHold: 120,
  letterHold: 120,
  letterReleaseGap: 90,
  modReleaseGap: 70,
  interChar: 140,
  spaceDwell: 180,
}

const SLOW_TEMPO: Tempo = {
  modPressHold: 280,
  letterHold: 280,
  letterReleaseGap: 220,
  modReleaseGap: 160,
  interChar: 380,
  spaceDwell: 320,
}

// Gap between a dead-key trigger and its paired letter — always slow
// since dead-key sequences ARE the slow tier.
const DEAD_GAP_MS = 320

const END_PHRASE_DWELL_MS = 2200
const FADE_OUT_MS = 300

// Physical modifier key IDs (see keyboardData.KEYBOARD_ROWS).
const KEY_LSHIFT = '_lsh'
const KEY_ALTGR = '_ra'

const STORAGE_KEY = 'kbd.playback.enabled'

export interface UsePlaybackOptions {
  pressedKeyIds: Ref<Set<string>>
  setManualLayer: (layer: Layer | null) => void
  layout: Ref<LayoutData | null>
  phrases: Ref<readonly string[]>
}

export function usePlayback(opts: UsePlaybackOptions) {
  // ── persisted + transient state ──────────────────────────────────

  const enabled = ref<boolean>(readStoredEnabled())
  const running = ref<boolean>(false)
  const sessionInterrupted = ref<boolean>(false)
  const prefersReducedMotion = ref<boolean>(false)

  // Visible demo text and fade state — what PlaybackLine.vue renders.
  const currentText = ref<string>('')
  const fading = ref<boolean>(false)

  const phraseIdx = ref<number>(0)

  // Active timer id (number in browser, NodeJS.Timeout in node types).
  // Tracked so stop() can cancel whatever's in flight.
  let timerId: ReturnType<typeof setTimeout> | null = null

  // Seen-unreachable set for dev warnings; reused per-layout.
  // (resolvePhrase already deduplicates at that level; kept here in case
  // we later log from multiple call sites.)

  // ── persistence ──────────────────────────────────────────────────

  function readStoredEnabled(): boolean {
    if (typeof localStorage === 'undefined') return true
    const v = localStorage.getItem(STORAGE_KEY)
    if (v === null) return true
    return v === '1'
  }

  function writeStoredEnabled(value: boolean): void {
    if (typeof localStorage === 'undefined') return
    localStorage.setItem(STORAGE_KEY, value ? '1' : '0')
  }

  // ── timer helpers ────────────────────────────────────────────────

  function schedule(fn: () => void, ms: number): void {
    timerId = setTimeout(() => {
      timerId = null
      fn()
    }, ms)
  }

  function cancelTimer(): void {
    if (timerId !== null) {
      clearTimeout(timerId)
      timerId = null
    }
  }

  // ── cleanup ──────────────────────────────────────────────────────
  //
  // Clear every reactive ref the player wrote to. Called on stop(),
  // reset(), and unmount. Never swallows manualLayer — the caller's
  // KeyboardSection may still want the default auto-layer afterwards.

  function clearKeyboardState(): void {
    opts.pressedKeyIds.value = new Set()
    opts.setManualLayer(null)
  }

  function clearDisplay(): void {
    currentText.value = ''
    fading.value = false
  }

  // ── micro-step expansion ────────────────────────────────────────
  //
  // Every resolver Step becomes a flat list of MicroStep entries. Each
  // MicroStep is one atomic write to the reactive state plus a fixed
  // delay afterwards. The player just walks this list with a single
  // recursive setTimeout, which makes cancellation trivial and keeps
  // the timing math visible in one place.

  // MicroStep kinds:
  //   modPress / modRelease   — push/pop a physical modifier key
  //                             (Shift, AltGr) into pressedKeyIds.
  //   keyPress / keyRelease   — light up a letter keycap. Only used
  //                             for dead-key compositions (slow tier)
  //                             where the specific keys are the demo.
  //   commit                  — silent text commit: append the typed
  //                             char to the display without lighting
  //                             up any letter keycap. Used for every
  //                             "normal" char (Cyrillic, Latin, digits,
  //                             Polish diacritics, typographic marks).
  //                             The whole point of the typographic
  //                             layout is that these are first-class
  //                             single-press chars — highlighting the
  //                             letter key would imply effort where
  //                             there is none.
  //   space                   — append a space, no highlight.
  type MicroStep =
    | { kind: 'modPress'; keyId: string; layer: Layer; delayAfter: number }
    | { kind: 'modRelease'; keyId: string; delayAfter: number }
    | { kind: 'keyPress'; keyId: string; layer: Layer; delayAfter: number }
    | { kind: 'keyRelease'; keyId: string; typed: string; delayAfter: number }
    | { kind: 'commit'; typed: string; delayAfter: number }
    | { kind: 'space'; delayAfter: number }

  function modsForLayer(layer: Layer): { needShift: boolean; needAltGr: boolean } {
    return {
      needShift: layer === 'shift' || layer === 'shift_altgr',
      needAltGr: layer === 'altgr' || layer === 'shift_altgr',
    }
  }

  /**
   * Expand a resolver Step[] into a flat MicroStep[] that the player
   * can walk. Per-step tempo selection:
   *
   *   - Fast by default (normal keys on the target layout).
   *   - Slow for BOTH halves of a dead-key pair: the trigger step
   *     (typed='') and the letter step immediately after it. Dead-key
   *     compositions are the whole point of the slow tier — they
   *     demonstrate a mechanic the user wouldn't otherwise see.
   *
   * Between a dead-key trigger and its paired letter we always use
   * DEAD_GAP_MS (slightly longer than the slow inter-char) so the
   * trigger + letter read as a deliberate pair.
   */
  function expandPhrase(steps: Step[]): MicroStep[] {
    // Pre-compute a tempo per step. A step is slow iff it's part of a
    // dead-key pair: either the trigger (typed==='' followed by a key
    // step) or the letter that follows a trigger.
    const tempos: Tempo[] = steps.map((step, i) => {
      if (step.kind !== 'key') return FAST_TEMPO
      const prev = steps[i - 1]
      const next = steps[i + 1]
      const isTrigger =
        step.typed === '' && next && next.kind === 'key'
      const isPairedLetter =
        prev && prev.kind === 'key' && prev.typed === ''
      return isTrigger || isPairedLetter ? SLOW_TEMPO : FAST_TEMPO
    })

    const micro: MicroStep[] = []

    for (let i = 0; i < steps.length; i++) {
      const step = steps[i]
      const tempo = tempos[i]
      const isLast = i === steps.length - 1
      const next = steps[i + 1]
      const isDeadToLetter =
        step.kind === 'key' &&
        step.typed === '' &&
        next &&
        next.kind === 'key'
      const afterStepGap = isLast
        ? 0
        : isDeadToLetter
          ? DEAD_GAP_MS
          : tempo.interChar

      if (step.kind === 'space') {
        micro.push({ kind: 'space', delayAfter: tempo.spaceDwell + afterStepGap })
        continue
      }

      const { needShift, needAltGr } = modsForLayer(step.layer)
      const highlightLetter = tempo === SLOW_TEMPO

      // Press modifiers in a fixed order (shift → altgr) so the visual
      // sequence reads the same regardless of which is needed.
      if (needShift) {
        micro.push({
          kind: 'modPress',
          keyId: KEY_LSHIFT,
          layer: step.layer,
          delayAfter: tempo.modPressHold,
        })
      }
      if (needAltGr) {
        micro.push({
          kind: 'modPress',
          keyId: KEY_ALTGR,
          layer: step.layer,
          delayAfter: tempo.modPressHold,
        })
      }

      // Letter: highlight the keycap only for dead-key sequences;
      // otherwise just commit the character silently. See MicroStep
      // comment for the rationale.
      if (highlightLetter) {
        micro.push({
          kind: 'keyPress',
          keyId: step.keyId,
          layer: step.layer,
          delayAfter: tempo.letterHold,
        })
        micro.push({
          kind: 'keyRelease',
          keyId: step.keyId,
          typed: step.typed,
          delayAfter:
            needShift || needAltGr ? tempo.letterReleaseGap : afterStepGap,
        })
      } else {
        micro.push({
          kind: 'commit',
          typed: step.typed,
          delayAfter:
            needShift || needAltGr ? tempo.letterReleaseGap : afterStepGap,
        })
      }

      // Release modifiers in reverse order.
      if (needAltGr) {
        micro.push({
          kind: 'modRelease',
          keyId: KEY_ALTGR,
          delayAfter: needShift ? tempo.modReleaseGap : afterStepGap,
        })
      }
      if (needShift) {
        micro.push({
          kind: 'modRelease',
          keyId: KEY_LSHIFT,
          delayAfter: afterStepGap,
        })
      }
    }

    return micro
  }

  /**
   * Recompute manualLayer from whichever physical modifier keys are
   * currently held. Called after every press/release so the keyboard
   * visualisation shows the right layer glyphs on the letter keys.
   */
  function syncLayer(): void {
    const held = opts.pressedKeyIds.value
    const shift = held.has(KEY_LSHIFT) || held.has('_rsh')
    const altgr = held.has(KEY_ALTGR)
    if (shift && altgr) opts.setManualLayer('shift_altgr')
    else if (altgr) opts.setManualLayer('altgr')
    else if (shift) opts.setManualLayer('shift')
    else opts.setManualLayer(null)
  }

  function pressKey(keyId: string): void {
    const next = new Set(opts.pressedKeyIds.value)
    next.add(keyId)
    opts.pressedKeyIds.value = next
  }

  function releaseKey(keyId: string): void {
    const next = new Set(opts.pressedKeyIds.value)
    next.delete(keyId)
    opts.pressedKeyIds.value = next
  }

  // ── core loop ────────────────────────────────────────────────────

  function startCurrentPhrase(): void {
    const layout = opts.layout.value
    if (!layout || !running.value) return
    if (opts.phrases.value.length === 0) {
      running.value = false
      return
    }

    const phrase = opts.phrases.value[phraseIdx.value % opts.phrases.value.length]
    const steps = resolvePhrase(layout, phrase)
    if (steps.length === 0) {
      // Empty or fully-unreachable phrase — skip forward to avoid stalling.
      advanceAndContinue()
      return
    }

    const micro = expandPhrase(steps)
    if (micro.length === 0) {
      advanceAndContinue()
      return
    }
    playMicro(micro, 0)
  }

  function playMicro(micro: MicroStep[], i: number): void {
    if (!running.value) return
    if (i >= micro.length) {
      finishPhrase()
      return
    }

    const step = micro[i]

    switch (step.kind) {
      case 'modPress':
        pressKey(step.keyId)
        syncLayer()
        break
      case 'modRelease':
        releaseKey(step.keyId)
        syncLayer()
        break
      case 'keyPress':
        pressKey(step.keyId)
        syncLayer()
        break
      case 'keyRelease':
        releaseKey(step.keyId)
        if (step.typed) currentText.value += step.typed
        syncLayer()
        break
      case 'commit':
        if (step.typed) currentText.value += step.typed
        break
      case 'space':
        currentText.value += ' '
        break
    }

    schedule(() => playMicro(micro, i + 1), step.delayAfter)
  }

  function finishPhrase(): void {
    // Release any stuck highlights before the end-of-phrase dwell —
    // otherwise the last key stays lit during the 1.8 s pause.
    clearKeyboardState()

    schedule(() => {
      if (!running.value) return
      fading.value = true
      schedule(() => {
        if (!running.value) return
        clearDisplay()
        advanceAndContinue()
      }, FADE_OUT_MS)
    }, END_PHRASE_DWELL_MS)
  }

  function advanceAndContinue(): void {
    phraseIdx.value = (phraseIdx.value + 1) % Math.max(1, opts.phrases.value.length)
    startCurrentPhrase()
  }

  // ── public API ───────────────────────────────────────────────────

  function start(): void {
    if (running.value) return
    if (!enabled.value) return
    if (sessionInterrupted.value) return
    if (!opts.layout.value) return
    if (opts.phrases.value.length === 0) return
    running.value = true
    startCurrentPhrase()
  }

  function stop(reason: 'toggle' | 'interrupt' | 'reset' = 'toggle'): void {
    running.value = false
    cancelTimer()
    clearKeyboardState()
    clearDisplay()
    if (reason === 'interrupt') {
      sessionInterrupted.value = true
    }
  }

  // Reset is for variant/locale switches: stop, clear, rewind to
  // phrase 0, then auto-start if still enabled. Does NOT clear the
  // sessionInterrupted flag — a variant change shouldn't resurrect
  // a demo the user already dismissed.
  function reset(): void {
    stop('reset')
    phraseIdx.value = 0
    if (enabled.value && !sessionInterrupted.value) {
      start()
    }
  }

  // Toggle is the user-visible on/off click. Persists to localStorage
  // and clears sessionInterrupted so the user can explicitly restart
  // after an auto-stop.
  function toggle(): void {
    enabled.value = !enabled.value
    writeStoredEnabled(enabled.value)
    if (enabled.value) {
      sessionInterrupted.value = false
      start()
    } else {
      stop('toggle')
    }
  }

  // ── interrupt detection ──────────────────────────────────────────
  //
  // Attached to window while mounted. Any non-Shift keydown stops
  // the player with reason='interrupt', flipping sessionInterrupted
  // so the player doesn't auto-restart until the user clicks toggle
  // or reloads the page.

  function isBareShift(e: KeyboardEvent): boolean {
    if (e.code !== 'ShiftLeft' && e.code !== 'ShiftRight') return false
    return !e.ctrlKey && !e.altKey && !e.metaKey
  }

  function onKeyDown(e: KeyboardEvent): void {
    if (!running.value) return
    if (isBareShift(e)) return
    stop('interrupt')
  }

  // ── visibility / blur pausing ────────────────────────────────────
  //
  // Pause (not interrupt) when the tab is hidden, resume when it
  // returns. This avoids burning cycles on a backgrounded tab and
  // keeps the animation aligned with the user's actual attention.

  function onVisibilityChange(): void {
    if (document.hidden) {
      if (running.value) {
        // Pause without flipping sessionInterrupted — tab switches
        // aren't user intent to dismiss the demo.
        running.value = false
        cancelTimer()
        clearKeyboardState()
        clearDisplay()
      }
    } else if (enabled.value && !sessionInterrupted.value) {
      start()
    }
  }

  // ── lifecycle ────────────────────────────────────────────────────

  onMounted(() => {
    // Reduced-motion check. If set, default to disabled — PlaybackLine
    // will show a static hint so the user can still opt in manually.
    if (typeof window !== 'undefined' && typeof window.matchMedia === 'function') {
      const mql = window.matchMedia('(prefers-reduced-motion: reduce)')
      prefersReducedMotion.value = mql.matches
      if (mql.matches && localStorage.getItem(STORAGE_KEY) === null) {
        enabled.value = false
      }
    }

    window.addEventListener('keydown', onKeyDown, { capture: true })
    document.addEventListener('visibilitychange', onVisibilityChange)
  })

  onBeforeUnmount(() => {
    stop('reset')
    window.removeEventListener('keydown', onKeyDown, { capture: true })
    document.removeEventListener('visibilitychange', onVisibilityChange)
  })

  // Auto-reset when the layout or phrase pool changes (variant / locale).
  // Debounces implicitly via the schedule chain since reset() → stop()
  // cancels any in-flight timer before rescheduling.
  watch(
    [() => opts.layout.value, () => opts.phrases.value],
    () => {
      reset()
    },
  )

  return {
    // State for PlaybackLine.vue to render
    enabled,
    running,
    sessionInterrupted,
    prefersReducedMotion,
    currentText,
    fading,
    // Commands
    start,
    stop,
    reset,
    toggle,
  }
}
