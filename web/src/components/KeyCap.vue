<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
// floating-vue's `VTooltip` symbol is the directive object — the component
// equivalent is exported as `Tooltip` (we alias to keep the local name).
import { Tooltip as VTooltip } from 'floating-vue'
import type { KeyDef } from '../composables/keyboardData'
import type { LayoutData } from '../composables/useLayout'
import { parseEntry } from '../composables/useLayout'

const { t } = useI18n()

const props = defineProps<{
  keyDef: KeyDef
  layout: LayoutData | null
}>()

const baseChar = computed(() => {
  if (!props.layout || props.keyDef.isModifier) return props.keyDef.base
  return props.layout.layers.base[props.keyDef.id] || props.keyDef.base
})

const shiftChar = computed(() => {
  if (!props.layout || props.keyDef.isModifier) return props.keyDef.shift
  return props.layout.layers.shift[props.keyDef.id] || props.keyDef.shift
})

const altgrInfo = computed(() => {
  if (!props.layout || props.keyDef.isModifier) return null
  const entry = props.layout.layers.altgr[props.keyDef.id]
  const parsed = parseEntry(entry)
  if (parsed && parsed.display === baseChar.value) return null
  return parsed
})

const shAltgrInfo = computed(() => {
  if (!props.layout || props.keyDef.isModifier) return null
  const entry = props.layout.layers.shift_altgr[props.keyDef.id]
  const parsed = parseEntry(entry)
  if (parsed && parsed.display === shiftChar.value) return null
  return parsed
})

function colorClass(info: ReturnType<typeof parseEntry>) {
  if (!info) return ''
  if (info.isDead) return 'color-dead'
  if (info.source === 'PL') return 'color-polish'
  if (info.source === 'RU') return 'color-russian'
  return 'color-altgr'
}

const keyWidth = computed(() => {
  const w = props.keyDef.width || 1
  const gap = 3 // --key-gap
  return `${w * 52 + (w - 1) * gap}px`
})

const isAltGrKey = computed(() => props.keyDef.id === '_ra')
</script>

<template>
  <VTooltip
    theme="key-tooltip"
    :disabled="keyDef.isModifier"
    :auto-hide="true"
  >
    <div
      class="key"
      :class="{
        'key--modifier': keyDef.isModifier,
        'key--altgr': isAltGrKey,
      }"
      :style="{ width: keyWidth }"
      :tabindex="keyDef.isModifier ? -1 : 0"
      :role="keyDef.isModifier ? undefined : 'button'"
      :aria-label="keyDef.isModifier ? undefined : (shiftChar || baseChar)"
    >
      <!-- Base char (bottom-left) -->
      <span class="key__base">{{ baseChar }}</span>

      <!-- Shift char (top-left) -->
      <span v-if="shiftChar && !keyDef.isModifier" class="key__shift">
        {{ shiftChar }}
      </span>

      <!-- Platform-alternate label for modifiers (Mac symbols) -->
      <span v-if="keyDef.isModifier && keyDef.altLabel" class="key__alt-label">
        {{ keyDef.altLabel }}
      </span>

      <!-- AltGr char (bottom-right) -->
      <span v-if="altgrInfo" class="key__altgr" :class="colorClass(altgrInfo)">
        {{ altgrInfo.display }}
      </span>

      <!-- Shift+AltGr char (top-right) -->
      <span v-if="shAltgrInfo" class="key__sh-altgr" :class="colorClass(shAltgrInfo)">
        {{ shAltgrInfo.display }}
      </span>
    </div>

    <template #popper>
      <div class="key-tooltip-body">
        <div class="tooltip-row">
          <span class="tooltip-label">{{ shiftChar || baseChar }}</span>
        </div>
        <div v-if="altgrInfo" class="tooltip-row">
          <span class="tooltip-key"><span class="os-win">AltGr</span><span class="os-mac">⌥</span></span>
          <span>{{ altgrInfo.display }} &mdash; {{ altgrInfo.name }}</span>
        </div>
        <div v-if="shAltgrInfo" class="tooltip-row">
          <span class="tooltip-key"><span class="os-win">Sh+AltGr</span><span class="os-mac">⇧⌥</span></span>
          <span>{{ shAltgrInfo.display }} &mdash; {{ shAltgrInfo.name }}</span>
        </div>
        <div v-if="!altgrInfo && !shAltgrInfo" class="tooltip-row tooltip-empty">
          {{ t('keyboard.tooltip.none') }}
        </div>
      </div>
    </template>
  </VTooltip>
</template>

<style scoped>
.key {
  height: 52px;
  background: var(--key-bg);
  border: 1px solid var(--key-border);
  border-radius: var(--key-radius);
  position: relative;
  cursor: default;
  transition: background 0.12s, border-color 0.12s;
  box-shadow: var(--key-shadow);
  flex-shrink: 0;
}

.key:hover {
  background: var(--key-hover);
  border-color: var(--border-strong);
}

.key--modifier {
  background: var(--bg-subtle);
  border-color: var(--border);
  box-shadow: none;
}

.key--altgr {
  background: var(--altgr-key-bg);
  border-color: var(--altgr-key-border);
}

/* Character positions */
.key__base {
  position: absolute;
  left: 5px;
  bottom: 4px;
  font-size: 12px;
  color: var(--color-base);
  line-height: 1;
  font-family: var(--font-mono);
}

.key--modifier .key__base {
  font-family: var(--font-body);
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  opacity: 0.6;
}

.key__shift {
  position: absolute;
  left: 5px;
  top: 4px;
  font-size: 10px;
  color: var(--color-shift);
  line-height: 1;
  font-family: var(--font-mono);
}

.key__alt-label {
  position: absolute;
  right: 5px;
  bottom: 4px;
  font-size: 14px;
  opacity: 0.3;
  color: var(--text-muted);
  line-height: 1;
}

.key__altgr {
  position: absolute;
  right: 5px;
  bottom: 4px;
  font-size: 12px;
  line-height: 1;
  font-family: var(--font-mono);
}

.key__sh-altgr {
  position: absolute;
  right: 5px;
  top: 4px;
  font-size: 10px;
  line-height: 1;
  font-family: var(--font-mono);
}


/* Color classes */
.color-altgr { color: var(--color-altgr); }
.color-polish { color: var(--color-polish); }
.color-russian { color: var(--color-russian); }
.color-dead { color: var(--color-dead); }

/* Tooltip body skin lives in style.css under .v-popper--theme-key-tooltip
   and .key-tooltip-body — the popper is teleported to <body> by floating-vue,
   so scoped styles here would not reach it. */
</style>
