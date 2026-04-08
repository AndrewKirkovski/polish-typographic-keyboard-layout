<script setup lang="ts">
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { KeyDef } from '../composables/keyboardData'
import type { LayoutData } from '../composables/useLayout'
import { parseEntry } from '../composables/useLayout'

const { t } = useI18n()

const props = defineProps<{
  keyDef: KeyDef
  layout: LayoutData | null
}>()

const keyEl = ref<HTMLElement | null>(null)
const showTooltip = ref(false)
const tooltipStyle = ref<Record<string, string>>({})

function updateTooltip() {
  if (!keyEl.value) return
  const rect = keyEl.value.getBoundingClientRect()
  const tooltipHeight = 80
  const above = rect.top > tooltipHeight + 12

  if (above) {
    tooltipStyle.value = {
      left: `${rect.left + rect.width / 2}px`,
      top: `${rect.top - 8}px`,
      transform: 'translate(-50%, -100%)',
    }
  } else {
    tooltipStyle.value = {
      left: `${rect.left + rect.width / 2}px`,
      top: `${rect.bottom + 8}px`,
      transform: 'translate(-50%, 0)',
    }
  }
}

function onEnter() {
  if (props.keyDef.isModifier) return
  updateTooltip()
  showTooltip.value = true
}

function onLeave() {
  showTooltip.value = false
}

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
  <div
    ref="keyEl"
    class="key"
    :class="{
      'key--modifier': keyDef.isModifier,
      'key--altgr': isAltGrKey,
    }"
    :style="{ width: keyWidth }"
    @mouseenter="onEnter"
    @mouseleave="onLeave"
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

  <!-- Teleported tooltip — renders in document body, never clipped -->
  <Teleport to="body">
    <div v-if="showTooltip && !keyDef.isModifier" class="key-tooltip-portal" :style="tooltipStyle">
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
  </Teleport>
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

/* Old tooltip styles removed — tooltip now uses Teleport (see style.css) */
</style>
