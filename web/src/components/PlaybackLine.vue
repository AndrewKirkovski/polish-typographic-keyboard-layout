<script setup lang="ts">
/**
 * PlaybackLine — display-only widget for the keyboard playback animation.
 *
 * Renders a one-line "typewriter" field with a blinking caret that shows
 * what usePlayback is currently typing. Fixed minimum height so the
 * keyboard below doesn't jump when the field is empty between phrases.
 *
 * The toggle button is NOT here — it lives in KeyboardSection's
 * .keyboard-controls block alongside the variant switcher so it behaves
 * as another keyboard control rather than part of the demo output.
 *
 * Reduced-motion mode: shows a static hint line instead of an empty
 * field when the user has prefers-reduced-motion + playback disabled.
 */
import { useI18n } from 'vue-i18n'

defineProps<{
  text: string
  fading: boolean
  running: boolean
  pendingAccent: string
  reducedMotionHint: boolean
}>()

const { t } = useI18n()
</script>

<template>
  <div
    class="playback-line"
    :class="{ 'playback-line--fading': fading, 'playback-line--hint': reducedMotionHint }"
    aria-hidden="true"
  >
    <template v-if="reducedMotionHint">
      <span class="playback-line__hint">{{ t('keyboard.playback.reducedMotionHint') }}</span>
    </template>
    <template v-else>
      <span class="playback-line__text">{{ text }}</span>
      <span
        v-if="pendingAccent"
        class="playback-line__pending"
        :title="'Dead key held, waiting for a base letter'"
      >
        <span class="playback-line__pending-accent">{{ pendingAccent }}</span>
        <span class="playback-line__pending-slot" aria-hidden="true"></span>
      </span>
      <span
        class="playback-line__caret"
        :class="{ 'playback-line__caret--dim': !running }"
      ></span>
    </template>
  </div>
</template>

<style scoped>
.playback-line {
  /* Fixed minimum height so the keyboard doesn't jump when the line is
     empty between phrases or when the demo is off. The value matches
     ~1.6× body-line at the font-size below — tall enough for the caret
     without burning vertical space. */
  min-height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1px;
  margin: 0.25rem 0 0.5rem;
  padding: 0 0.75rem;
  font-family: var(--font-mono, ui-monospace, SFMono-Regular, Menlo, monospace);
  font-size: 1rem;
  line-height: 1.4;
  color: var(--text);
  opacity: 1;
  transition: opacity 250ms ease-out;
  /* Let the caret sit on the baseline cleanly without relying on text-bottom */
  white-space: pre;
}

.playback-line--fading {
  opacity: 0;
}

.playback-line--hint {
  font-family: var(--font-body);
  font-size: 0.85rem;
  color: var(--text-secondary);
}

.playback-line__text {
  /* Let the text shrink on very narrow screens instead of horizontally
     scrolling the whole keyboard section. Phrases are short, and clipping
     the tail with ellipsis on mobile is fine. */
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
}

.playback-line__pending {
  /* Two-part dead-state indicator:
       - the spacing accent glyph (caron, diaeresis, breve, …) at
         the top, marking which dead key is pending;
       - a dotted-outline circle slot below it, symbolising the
         empty "waiting for a base letter" placeholder the layout
         is about to fill.
     No background, no shadow, no box — just the glyph and the slot
     drawn in the current text color so it reads as part of the text
     rather than a separate UI chrome element. */
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
  margin: 0 3px;
  vertical-align: middle;
  line-height: 1;
}

.playback-line__pending-accent {
  display: block;
  font-size: 0.75em;
  font-weight: 700;
  line-height: 1;
  color: currentColor;
  /* Drop in with a subtle overshoot — no glow, no background, no
     flashing; the pulse lives on the slot circle below. */
  animation: playback-pending-accent-drop 160ms cubic-bezier(0.2, 1.6, 0.4, 1) both;
}

.playback-line__pending-slot {
  display: block;
  width: 0.85em;
  height: 0.85em;
  border-radius: 50%;
  border: 1.5px dashed currentColor;
  opacity: 0.55;
  animation: playback-pending-slot-pulse 900ms ease-in-out infinite;
}

@keyframes playback-pending-accent-drop {
  0% {
    opacity: 0;
    transform: translateY(-8px) scale(0.6);
  }
  70% {
    transform: translateY(1px) scale(1.15);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes playback-pending-slot-pulse {
  0%, 100% {
    opacity: 0.35;
    transform: scale(1);
  }
  50% {
    opacity: 0.75;
    transform: scale(1.12);
  }
}

@media (prefers-reduced-motion: reduce) {
  .playback-line__pending-accent,
  .playback-line__pending-slot {
    animation: none;
  }
  .playback-line__pending-slot {
    opacity: 0.6;
  }
}

.playback-line__caret {
  display: inline-block;
  width: 2px;
  height: 1.1em;
  background: currentColor;
  margin-left: 1px;
  animation: playback-caret-blink 1s steps(2, start) infinite;
  vertical-align: middle;
}

.playback-line__caret--dim {
  /* When the player is stopped, the caret stays visible but dimmed so
     the user can tell the widget is still "alive", just idle. */
  opacity: 0.35;
  animation: none;
}

@keyframes playback-caret-blink {
  to {
    visibility: hidden;
  }
}

@media (prefers-reduced-motion: reduce) {
  .playback-line {
    transition: none;
  }
  .playback-line__caret {
    animation: none;
  }
}
</style>
