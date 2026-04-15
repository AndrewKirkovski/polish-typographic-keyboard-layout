import { ref, computed, onMounted, onUnmounted } from 'vue'
import { detectOS } from './useOS'

export type Layer = 'base' | 'shift' | 'altgr' | 'shift_altgr'

/**
 * Tracks physical modifier state (Shift, AltGr) and pressed key IDs from
 * real keyboard events. Exports a reactive `activeLayer` and `pressedKeyIds`
 * set for the keyboard visualisation.
 *
 * AltGr detection:
 *  - Primary: `getModifierState('AltGraph')` (works in Chrome/Edge/Firefox)
 *  - Windows fallback: the OS sends a synthetic Ctrl before AltGr's Alt.
 *    If ControlLeft arrives <10 ms before AltRight, treat it as AltGr.
 *    If the gap is >50 ms, treat as real Ctrl+Alt (no AltGr).
 *  - macOS: either Option key acts as AltGr.
 *
 * SSR-safe: all DOM access is guarded behind onMounted.
 */
export function useModifierState() {
  const shiftHeld = ref(false)
  const altGrHeld = ref(false)
  const pressedKeyIds = ref<Set<string>>(new Set())

  /** Manual override from the layer toggle buttons (null = follow keyboard). */
  const manualLayer = ref<Layer | null>(null)

  /**
   * Layer forced by the playback animation while it drives the
   * keyboard. Kept separate from `manualLayer` so the user's
   * layer-switcher tabs don't flicker during playback — the player
   * only influences which keycap glyphs render, not the tab state.
   * Priority: manualLayer (user click) > hardware modifiers held
   * (real keypress) > playbackLayer (animation) > base.
   */
  const playbackLayer = ref<Layer | null>(null)

  const keyboardLayer = computed<Layer>(() => {
    if (altGrHeld.value && shiftHeld.value) return 'shift_altgr'
    if (altGrHeld.value) return 'altgr'
    if (shiftHeld.value) return 'shift'
    return 'base'
  })

  const activeLayer = computed<Layer>(() => {
    if (manualLayer.value !== null) return manualLayer.value
    // Hardware modifiers take precedence over the animation if the
    // user is actually holding something — bare Shift during playback
    // should surface the shift layer instead of whatever the demo
    // was about to show.
    if (keyboardLayer.value !== 'base') return keyboardLayer.value
    if (playbackLayer.value !== null) return playbackLayer.value
    return 'base'
  })

  function setManualLayer(layer: Layer | null) {
    manualLayer.value = layer
  }

  function setPlaybackLayer(layer: Layer | null) {
    playbackLayer.value = layer
  }

  let suppressCtrlLeft = false
  const isMac = detectOS() === 'macos'

  // CODE_TO_KEY_ID will be imported by the caller; we work with
  // KeyboardEvent.code values and translate to KeyDef.id externally.
  // But we also need a reverse lookup here so we can populate
  // pressedKeyIds with KeyDef ids. We accept an optional map.
  let codeToKeyId: Record<string, string> = {}

  function setCodeToKeyId(map: Record<string, string>) {
    codeToKeyId = map
  }

  // ── Helpers ─────────────────────────────────────────────────────────
  function isAltGrEvent(e: KeyboardEvent): boolean {
    if (e.getModifierState('AltGraph')) return true

    // AltRight is physically AltGr on every platform.
    if (e.code === 'AltRight') {
      if (!isMac) suppressCtrlLeft = true
      return true
    }

    // Windows: AltGr fires as synthetic Ctrl+Alt. Treat any Ctrl+Alt
    // combination as AltGr so users on keyboards without a physical AltGr
    // (or who prefer the Ctrl+Alt substitute Windows provides) still see
    // the AltGr / Shift+AltGr layers highlight correctly.
    if (!isMac && e.ctrlKey && e.altKey) return true

    // macOS: Left Option also acts as AltGr.
    if (isMac && e.code === 'AltLeft') return true

    return false
  }

  function resetAll() {
    shiftHeld.value = false
    altGrHeld.value = false
    pressedKeyIds.value = new Set()
    suppressCtrlLeft = false
  }

  // ── Event handlers ──────────────────────────────────────────────────
  function onKeyDown(e: KeyboardEvent) {
    // Clear manual override on any real key press so the keyboard
    // visualisation follows the physical state again.
    if (manualLayer.value !== null) {
      manualLayer.value = null
    }

    // Shift
    if (e.code === 'ShiftLeft' || e.code === 'ShiftRight') {
      shiftHeld.value = true
    }

    // AltGr
    if (isAltGrEvent(e)) {
      altGrHeld.value = true
    }

    // Track pressed key for visual feedback.
    const keyId = codeToKeyId[e.code]
    if (keyId) {
      const target = e.target as HTMLElement | null
      const isEditable = target?.tagName === 'INPUT' || target?.tagName === 'TEXTAREA'
        || target?.tagName === 'SELECT' || target?.isContentEditable
        || target?.getAttribute('role') === 'textbox'
      if (altGrHeld.value && !isEditable) e.preventDefault()
      const next = new Set(pressedKeyIds.value)
      next.add(keyId)
      pressedKeyIds.value = next
    }
  }

  function onKeyUp(e: KeyboardEvent) {
    // Shift
    if (e.code === 'ShiftLeft' || e.code === 'ShiftRight') {
      shiftHeld.value = false
    }

    // ControlLeft: if it was the suppressed half of AltGr, ignore its
    // release for modifier tracking. But still allow the visual
    // pressed-key tracking below.
    if (e.code === 'ControlLeft' && suppressCtrlLeft) {
      suppressCtrlLeft = false
      // Also clear AltGr if AltRight is no longer held.
      // (AltGr release sends both ControlLeft up and AltRight up.)
    }

    // AltGr / Alt release — also clears when either half of Ctrl+Alt is released
    if (e.code === 'AltRight' || e.code === 'AltLeft' || e.code === 'ControlLeft') {
      if (altGrHeld.value && (!e.ctrlKey || !e.altKey)) {
        altGrHeld.value = false
        suppressCtrlLeft = false
      }
    }

    // Un-track pressed key.
    const keyId = codeToKeyId[e.code]
    if (keyId) {
      const next = new Set(pressedKeyIds.value)
      next.delete(keyId)
      pressedKeyIds.value = next
    }
  }

  function onBlur() {
    resetAll()
  }

  function onVisibilityChange() {
    resetAll()
  }

  // ── Lifecycle ───────────────────────────────────────────────────────
  onMounted(() => {
    window.addEventListener('keydown', onKeyDown)
    window.addEventListener('keyup', onKeyUp)
    window.addEventListener('blur', onBlur)
    document.addEventListener('visibilitychange', onVisibilityChange)
  })

  onUnmounted(() => {
    window.removeEventListener('keydown', onKeyDown)
    window.removeEventListener('keyup', onKeyUp)
    window.removeEventListener('blur', onBlur)
    document.removeEventListener('visibilitychange', onVisibilityChange)
  })

  return {
    activeLayer,
    keyboardLayer,
    pressedKeyIds,
    manualLayer,
    setManualLayer,
    playbackLayer,
    setPlaybackLayer,
    setCodeToKeyId,
  }
}
