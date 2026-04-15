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
      >{{ pendingAccent }}</span>
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
  /* Highlighted dead-state indicator — macOS paints a yellow accent
     overlay at the caret when a dead key is pending. We get ~1.5 s
     between the trigger release and the base letter commit, so the
     animation has to land fast and stay visible for the whole
     window. Two stages:
       1. Drop-in with overshoot bounce (140 ms): the glyph falls
          from above, slightly past its resting position, and lands.
          Enough motion to catch the eye.
       2. Continuous glow pulse (700 ms loop): a soft box-shadow
          halo pulses around the box so the user keeps noticing the
          accent while waiting for the base letter. Subtle scale
          breath so it feels alive without moving the text around. */
  display: inline-block;
  padding: 1px 5px;
  margin: 0 2px;
  background: rgba(255, 206, 84, 0.35);
  color: var(--text);
  border-radius: 4px;
  font-weight: 700;
  transform-origin: center bottom;
  animation:
    playback-pending-drop 140ms cubic-bezier(0.2, 1.6, 0.4, 1) both,
    playback-pending-glow 700ms ease-in-out 140ms infinite;
}

@media (prefers-color-scheme: dark) {
  .playback-line__pending {
    background: rgba(255, 206, 84, 0.22);
  }
}

@keyframes playback-pending-drop {
  0% {
    opacity: 0;
    transform: translateY(-14px) scale(0.4);
  }
  70% {
    transform: translateY(3px) scale(1.12);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes playback-pending-glow {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(255, 206, 84, 0);
    background: rgba(255, 206, 84, 0.30);
    transform: scale(1);
  }
  50% {
    box-shadow: 0 0 12px 2px rgba(255, 206, 84, 0.55);
    background: rgba(255, 206, 84, 0.55);
    transform: scale(1.06);
  }
}

@media (prefers-reduced-motion: reduce) {
  .playback-line__pending {
    animation: none;
    /* Still show the highlight, just no motion/pulse */
    background: rgba(255, 206, 84, 0.45);
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
