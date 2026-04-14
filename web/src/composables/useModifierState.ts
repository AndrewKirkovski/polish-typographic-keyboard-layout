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

  const keyboardLayer = computed<Layer>(() => {
    if (altGrHeld.value && shiftHeld.value) return 'shift_altgr'
    if (altGrHeld.value) return 'altgr'
    if (shiftHeld.value) return 'shift'
    return 'base'
  })

  const activeLayer = computed<Layer>(() => manualLayer.value ?? keyboardLayer.value)

  function setManualLayer(layer: Layer | null) {
    manualLayer.value = layer
  }

  // ── AltGr timing heuristic (Windows) ────────────────────────────────
  // Windows sends ControlLeft keydown ~0-2 ms before AltRight keydown
  // when the physical AltGr key is pressed. We track the ControlLeft
  // timestamp and suppress it if AltRight follows within 10 ms.
  let ctrlLeftDownTime = 0
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
    // Primary detection: the browser knows.
    if (e.getModifierState('AltGraph')) return true

    // macOS: either Alt/Option key is "AltGr" for our purposes.
    if (isMac && (e.code === 'AltLeft' || e.code === 'AltRight')) return true

    // Windows fallback: AltRight within 10 ms of ControlLeft = AltGr.
    if (!isMac && e.code === 'AltRight') {
      const gap = e.timeStamp - ctrlLeftDownTime
      if (gap < 10) {
        suppressCtrlLeft = true
        return true
      }
    }

    return false
  }

  function resetAll() {
    shiftHeld.value = false
    altGrHeld.value = false
    pressedKeyIds.value = new Set()
    ctrlLeftDownTime = 0
    suppressCtrlLeft = false
  }

  // ── Event handlers ──────────────────────────────────────────────────
  function onKeyDown(e: KeyboardEvent) {
    // Clear manual override on any real key press so the keyboard
    // visualisation follows the physical state again.
    if (manualLayer.value !== null) {
      manualLayer.value = null
    }

    // Track ControlLeft timing for AltGr heuristic.
    if (e.code === 'ControlLeft') {
      ctrlLeftDownTime = e.timeStamp
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

    // AltGr / Alt release
    if (e.code === 'AltRight' || (isMac && (e.code === 'AltLeft' || e.code === 'AltRight'))) {
      altGrHeld.value = false
      suppressCtrlLeft = false
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
    if (typeof document !== 'undefined' && document.hidden) {
      resetAll()
    }
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
    setCodeToKeyId,
  }
}
