<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useLayout } from '../composables/useLayout'
import { KEYBOARD_ROWS, CODE_TO_KEY_ID } from '../composables/keyboardData'
import { useModifierState } from '../composables/useModifierState'
import type { Layer } from '../composables/useModifierState'
import { usePlayback } from '../composables/usePlayback'
import { trackLayerSwitch, trackVariantSwitch } from '../composables/useAnalytics'
import KeyCap from './KeyCap.vue'
import PlaybackLine from './PlaybackLine.vue'

const { t, tm, rt } = useI18n()
const { active, activeId, setActive } = useLayout()
const {
  activeLayer,
  pressedKeyIds,
  manualLayer,
  setManualLayer,
  setCodeToKeyId,
} = useModifierState()

// Wire up the code-to-key-id mapping so pressed keys light up.
setCodeToKeyId(CODE_TO_KEY_ID)

// Variant-specific phrase pool from i18n. `tm` returns the raw
// message (the array); `rt` turns each entry into its runtime string
// so NFD escape sequences like `у\u0306` resolve correctly.
const phrases = computed<readonly string[]>(() => {
  const key = `keyboard.playback.phrases.${activeId.value}`
  const raw = tm(key)
  if (!Array.isArray(raw)) return []
  return raw.map((item) => rt(item as Parameters<typeof rt>[0]))
})

const playback = usePlayback({
  pressedKeyIds,
  setManualLayer,
  layout: active,
  phrases,
})

function onVariantClick(variant: 'polish' | 'russian') {
  if (activeId.value === variant) return
  setActive(variant)
  trackVariantSwitch(variant)
}

function onLayerClick(layer: Layer | null) {
  setManualLayer(layer)
  trackLayerSwitch(layer ?? 'auto')
}

const LAYER_OPTIONS: { value: Layer | null; labelKey: string }[] = [
  { value: null, labelKey: 'keyboard.layers.auto' },
  { value: 'base', labelKey: 'keyboard.legend.base' },
  { value: 'altgr', labelKey: 'keyboard.legend.altgr' },
  { value: 'shift_altgr', labelKey: 'keyboard.legend.shAltgr' },
]
</script>

<template>
  <section id="keyboard" class="section">
    <div class="container">
      <div class="keyboard-controls">
        <div class="layout-switcher" role="tablist" :aria-label="t('keyboard.layoutSwitcher')">
          <button
            id="layout-polish"
            role="tab"
            :aria-selected="activeId === 'polish'"
            :tabindex="activeId === 'polish' ? 0 : -1"
            :class="{ active: activeId === 'polish' }"
            @click="onVariantClick('polish')"
          >{{ t('keyboard.polish') }}</button>
          <button
            id="layout-russian"
            role="tab"
            :aria-selected="activeId === 'russian'"
            :tabindex="activeId === 'russian' ? 0 : -1"
            :class="{ active: activeId === 'russian' }"
            @click="onVariantClick('russian')"
          >{{ t('keyboard.russian') }}</button>
        </div>

        <button
          type="button"
          class="playback-toggle"
          :class="{ 'playback-toggle--on': playback.enabled.value }"
          :aria-pressed="playback.enabled.value"
          :aria-label="t('keyboard.playback.aria')"
          @click="playback.toggle()"
        >
          <svg
            class="playback-toggle__icon"
            width="10"
            height="12"
            viewBox="0 0 10 12"
            aria-hidden="true"
          >
            <!-- Play glyph when off, pause glyph when on. Two sibling
                 paths so we can swap via CSS without re-rendering. -->
            <path
              v-if="playback.enabled.value"
              d="M2 1h2v10H2zm4 0h2v10H6z"
              fill="currentColor"
            />
            <path v-else d="M1 1l8 5-8 5z" fill="currentColor" />
          </svg>
          <span class="playback-toggle__label">{{
            playback.enabled.value
              ? t('keyboard.playback.toggleOn')
              : t('keyboard.playback.toggleOff')
          }}</span>
        </button>
      </div>

      <PlaybackLine
        :text="playback.currentText.value"
        :fading="playback.fading.value"
        :running="playback.running.value"
        :reducedMotionHint="
          playback.prefersReducedMotion.value && !playback.enabled.value
        "
      />

      <div class="keyboard-wrapper">
        <div class="keyboard">
          <div v-for="(row, ri) in KEYBOARD_ROWS" :key="ri" class="keyboard__row">
            <KeyCap
              v-for="keyDef in row"
              :key="keyDef.id"
              :keyDef="keyDef"
              :layout="active"
              :activeLayer="activeLayer"
              :isPressed="pressedKeyIds.has(keyDef.id)"
            />
          </div>
        </div>
      </div>

      <div class="layer-switcher" role="radiogroup" :aria-label="t('keyboard.layers.label')">
        <button
          v-for="opt in LAYER_OPTIONS"
          :key="opt.labelKey"
          role="radio"
          :aria-checked="manualLayer === opt.value"
          :class="{ active: manualLayer === opt.value }"
          @click="onLayerClick(opt.value)"
        >{{ t(opt.labelKey) }}</button>
      </div>

      <div class="legend">
        <div class="legend-item">
          <span class="legend-swatch" style="background: var(--color-base)" aria-hidden="true"></span>
          {{ t('keyboard.legend.base') }}
        </div>
        <div class="legend-item">
          <span class="legend-swatch" style="background: var(--color-altgr)" aria-hidden="true"></span>
          <span class="os-win">{{ t('keyboard.legend.altgr') }}</span>
          <span class="os-mac">⌥ Option</span>
        </div>
        <div class="legend-item">
          <span class="legend-swatch" style="background: var(--color-polish)" aria-hidden="true"></span>
          {{ t('keyboard.legend.polish') }}
        </div>
        <div class="legend-item">
          <span class="legend-swatch" style="background: var(--color-russian)" aria-hidden="true"></span>
          {{ t('keyboard.legend.russian') }}
        </div>
        <div class="legend-item legend-item--has-tip">
          <span class="legend-swatch" style="background: var(--color-dead)" aria-hidden="true"></span>
          {{ t('keyboard.legend.deadKey') }}
          <span class="legend-help" aria-hidden="true">?</span>
          <div class="legend-tooltip">{{ t('keyboard.legend.deadKeyTip') }}</div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.section {
  /* Bigger top padding so the keyboard section reads as separate from
     the hero above. The controls-to-keyboard gap below is intentionally
     small so the layout switcher feels anchored to the keyboard. */
  padding-top: 1.75rem;
}

.keyboard-controls {
  /* Controls belong to the keyboard, not the hero — make the gap to the
     keyboard much smaller than the gap to the hero subtitle above. */
  margin-bottom: 0.5rem;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem 0.75rem;
}

/* ── Playback toggle ────────────────────────────────────────────────
   Sits alongside the layout switcher inside .keyboard-controls. Hybrid
   icon+text on desktop, icon-only on narrow screens. */

.playback-toggle {
  font-family: var(--font-body);
  font-size: 0.8rem;
  font-weight: 500;
  padding: 6px 12px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: var(--bg-subtle);
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.15s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.playback-toggle:hover {
  color: var(--text);
  border-color: var(--border-strong);
}

.playback-toggle--on {
  color: var(--text);
  background: var(--bg-elevated);
  border-color: var(--border-strong);
}

.playback-toggle__icon {
  flex-shrink: 0;
}

@media (max-width: 560px) {
  /* Icon-only on narrow screens to keep the controls row single-line. */
  .playback-toggle__label {
    display: none;
  }
  .playback-toggle {
    padding: 6px 10px;
  }
}

.layout-switcher {
  display: inline-flex;
  gap: 2px;
  background: var(--bg-subtle);
  border-radius: 8px;
  padding: 3px;
}

.layout-switcher button {
  font-family: var(--font-body);
  font-size: 0.85rem;
  font-weight: 500;
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.15s;
}

.layout-switcher button.active {
  background: var(--bg-elevated);
  color: var(--text);
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.layout-switcher button:hover:not(.active) {
  color: var(--text-secondary);
}

.keyboard-wrapper {
  overflow-x: auto;
  padding: 1rem 0;
  margin: 0 -2rem;
  padding-left: 2rem;
  padding-right: 2rem;
}

.keyboard {
  display: inline-flex;
  flex-direction: column;
  gap: 3px;
}

.keyboard__row {
  display: flex;
  gap: 3px;
}

.legend {
  display: flex;
  gap: 1.5rem;
  margin-top: 1.5rem;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.legend-swatch {
  width: 10px;
  height: 10px;
  border-radius: 3px;
}

.legend-help {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  font-size: 9px;
  font-weight: 700;
  color: var(--text-muted);
  border: 1px solid var(--border-strong);
  border-radius: 50%;
  margin-left: 2px;
}

.legend-tooltip {
  display: none;
  position: absolute;
  bottom: calc(100% + 8px);
  left: 50%;
  transform: translateX(-50%);
  background: var(--bg-elevated);
  border: 1px solid var(--border-strong);
  border-radius: 8px;
  padding: 8px 12px;
  font-size: 11px;
  white-space: nowrap;
  z-index: 100;
  pointer-events: none;
  box-shadow: 0 4px 12px rgba(0,0,0,0.12);
  font-family: var(--font-body);
  color: var(--text-secondary);
}

.legend-item--has-tip:hover .legend-tooltip {
  display: block;
}

.legend-item--has-tip {
  cursor: help;
  position: relative;
}

/* ── Layer toggle (mobile / manual) ────────────────────────────────── */
.layer-switcher {
  display: inline-flex;
  gap: 2px;
  background: var(--bg-subtle);
  border-radius: 8px;
  padding: 3px;
  margin-top: 0.75rem;
}

.layer-switcher button {
  font-family: var(--font-body);
  font-size: 0.8rem;
  font-weight: 500;
  padding: 6px 14px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.15s;
}

.layer-switcher button.active {
  background: var(--bg-elevated);
  color: var(--text);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.layer-switcher button:hover:not(.active) {
  color: var(--text-secondary);
}
</style>
