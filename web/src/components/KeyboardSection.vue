<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { useLayout } from '../composables/useLayout'
import { KEYBOARD_ROWS } from '../composables/keyboardData'
import KeyCap from './KeyCap.vue'

const { t } = useI18n()
const { active, activeId, setActive } = useLayout()
</script>

<template>
  <section id="keyboard" class="section">
    <div class="container">
      <h2 class="section-title">{{ t('keyboard.title') }}</h2>
      <div class="keyboard-controls">
        <div class="layout-switcher">
          <button
            :class="{ active: activeId === 'polish' }"
            @click="setActive('polish')"
          >{{ t('keyboard.polish') }}</button>
          <button
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
            />
          </div>
        </div>
      </div>

      <div class="legend">
        <div class="legend-item">
          <span class="legend-swatch" style="background: var(--color-base)"></span>
          {{ t('keyboard.legend.base') }}
        </div>
        <div class="legend-item">
          <span class="legend-swatch" style="background: var(--color-altgr)"></span>
          {{ t('keyboard.legend.altgr') }}
        </div>
        <div class="legend-item">
          <span class="legend-swatch" style="background: var(--color-polish)"></span>
          {{ t('keyboard.legend.polish') }}
        </div>
        <div class="legend-item">
          <span class="legend-swatch" style="background: var(--color-russian)"></span>
          {{ t('keyboard.legend.russian') }}
        </div>
        <div class="legend-item legend-item--has-tip" :title="t('keyboard.legend.deadKeyTip')">
          <span class="legend-swatch" style="background: var(--color-dead)"></span>
          {{ t('keyboard.legend.deadKey') }}
          <span class="legend-help">?</span>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.keyboard-controls {
  margin-bottom: 2rem;
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

.legend-item--has-tip {
  cursor: help;
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
</style>
