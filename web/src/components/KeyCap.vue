<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
// floating-vue's `VTooltip` symbol is the directive object — the component
// equivalent is exported as `Tooltip` (we alias to keep the local name).
import { Tooltip as VTooltip } from 'floating-vue'
import type { KeyDef } from '../composables/keyboardData'
import type { LayoutData } from '../composables/useLayout'
import { parseEntry } from '../composables/useLayout'
import type { Layer } from '../composables/useModifierState'

const { t } = useI18n()

const props = defineProps<{
  keyDef: KeyDef
  layout: LayoutData | null
  activeLayer?: Layer
  isPressed?: boolean
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

const layerClass = computed(() => {
  if (!props.activeLayer || props.activeLayer === 'base') return ''
  return `key--layer-${props.activeLayer}`
})
</script>

<template>
  <VTooltip
    theme="key-tooltip"
    :disabled="keyDef.isModifier"
    :auto-hide="true"
  >
    <div
      class="key"
      :class="[
        layerClass,
        {
          'key--modifier': keyDef.isModifier,
          'key--altgr': isAltGrKey,
          'key--pressed': isPressed,
        },
      ]"
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
  transition: background 0.12s, border-color 0.12s, transform 80ms ease-out, box-shadow 80ms ease-out;
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

/* ── Layer highlighting ──────────────────────────────────────────────
   When a modifier layer is active, the "active" corner characters
   scale up slightly and stay at full opacity. The other corners fade
   to 0.3 so the active layer pops visually. GPU-composited properties
   only (opacity + transform) for smooth 150ms transitions. */

.key__base,
.key__shift,
.key__altgr,
.key__sh-altgr {
  transition: opacity 150ms ease-out, transform 150ms ease-out;
  will-change: opacity, transform;
}

/* Highlighted character in any active layer: scale up, sit above the
   faded siblings, and draw a white text-shadow "stroke" so the glyph
   stays legible when it overlaps its neighbours at the larger size. */
.key--layer-altgr .key__altgr,
.key--layer-shift .key__shift,
.key--layer-shift_altgr .key__sh-altgr {
  transform: scale(1.5);
  z-index: 2;
  text-shadow:
    -2px -2px 0 var(--key-bg), 2px -2px 0 var(--key-bg),
    -2px  2px 0 var(--key-bg), 2px  2px 0 var(--key-bg),
    -2px  0   0 var(--key-bg), 2px  0   0 var(--key-bg),
     0   -2px 0 var(--key-bg), 0    2px 0 var(--key-bg),
    -1px -1px 0 var(--key-bg), 1px -1px 0 var(--key-bg),
    -1px  1px 0 var(--key-bg), 1px  1px 0 var(--key-bg);
}

/* AltGr layer active → fade the inactive corners */
.key--layer-altgr .key__base,
.key--layer-altgr .key__shift,
.key--layer-altgr .key__sh-altgr {
  opacity: 0.25;
}

/* Shift layer active → fade the inactive corners */
.key--layer-shift .key__base,
.key--layer-shift .key__altgr,
.key--layer-shift .key__sh-altgr {
  opacity: 0.25;
}

/* Shift+AltGr layer active → fade the inactive corners */
.key--layer-shift_altgr .key__base,
.key--layer-shift_altgr .key__shift,
.key--layer-shift_altgr .key__altgr {
  opacity: 0.25;
}

/* ── Pressed key animation ───────────────────────────────────────────
   Subtle scale-down + highlight ring. The ring colour is a solid
   blend of the accent with the surrounding surface (page bg for the
   outer ring, elevated bg for the inset ring) via color-mix, rather
   than the accent at reduced opacity. Solid colour renders cleanly
   over anything underneath and avoids the compositing layer a
   transparent ::after would create. */
.key::after {
  content: '';
  position: absolute;
  inset: 2px;
  border-radius: calc(var(--key-radius) - 2px);
  box-shadow: 0 0 0 4px transparent;
  pointer-events: none;
  transition: box-shadow 120ms ease-out;
}

.key--pressed {
  transform: scale(0.95);
  transition: transform 80ms ease-out, background 0.12s, border-color 0.12s;
}

.key--pressed::after {
  box-shadow: 0 0 0 4px color-mix(in srgb, var(--color-altgr) 40%, var(--bg));
}

/* Tooltip body skin lives in style.css under .v-popper--theme-key-tooltip
   and .key-tooltip-body — the popper is teleported to <body> by floating-vue,
   so scoped styles here would not reach it. */
</style>
