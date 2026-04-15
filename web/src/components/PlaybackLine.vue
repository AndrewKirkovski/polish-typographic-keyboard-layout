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
