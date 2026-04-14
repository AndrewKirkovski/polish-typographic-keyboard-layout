<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useLayout } from '../composables/useLayout'
import { KEYBOARD_ROWS, CODE_TO_KEY_ID } from '../composables/keyboardData'
import { useModifierState } from '../composables/useModifierState'
import type { Layer } from '../composables/useModifierState'
import KeyCap from './KeyCap.vue'

const { t } = useI18n()
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
            @click="setActive('polish')"
          >{{ t('keyboard.polish') }}</button>
          <button
            id="layout-russian"
            role="tab"
            :aria-selected="activeId === 'russian'"
            :tabindex="activeId === 'russian' ? 0 : -1"
            :class="{ active: activeId === 'russian' }"
            @click="setActive('russian')"
          >{{ t('keyboard.russian') }}</button>
        </div>
      </div>

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
          @click="setManualLayer(opt.value)"
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
