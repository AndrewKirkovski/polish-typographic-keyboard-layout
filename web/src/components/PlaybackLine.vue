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
        <span class="playback-line__pending-inner">
          <span class="playback-line__pending-accent">{{ pendingAccent }}</span>
          <span class="playback-line__pending-slot" aria-hidden="true"></span>
        </span>
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
  /* Zero-width in-flow anchor. When the paired letter commits and
     this element is removed, the upcoming char slots into the caret
     position with ZERO horizontal shift — the pending indicator
     never took up any flow width to begin with. The visible parts
     (accent + slot) are absolutely positioned inside `pending-inner`
     and hover right next to the caret. */
  display: inline-block;
  position: relative;
  width: 0;
  height: 1em;
  vertical-align: baseline;
}

.playback-line__pending-inner {
  /* Absolute anchor to the 0-width parent. Vertically we center
     on the parent (no extra nudge) — the sized-down accent + slot
     stack is now short enough to fit inside the glyph box directly,
     aligning with the caron / body regions of the committed char
     it's replacing. */
  position: absolute;
  left: 5px;
  top: 50%;
  transform: translate(0, calc(-50% - 1.5px));
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
  pointer-events: none;
  line-height: 1;
}

.playback-line__pending-accent {
  /* Spacing accent glyph — at full 1em to match the visual size
     of the accent on the committed char. Weight inherited from
     the text so the strokes match too. */
  display: block;
  font-size: 1em;
  line-height: 1;
  color: currentColor;
  animation: playback-pending-accent-drop 160ms cubic-bezier(0.2, 1.6, 0.4, 1) both;
}

.playback-line__pending-slot {
  /* Dotted outline representing where the base letter will land.
     Negative margin-top pulls the slot up into the accent's lower
     region so the slot lands on the x-height band regardless of
     how tall the accent glyph is. The two shapes are visually
     distinct so the overlap reads fine. */
  display: block;
  width: 0.4em;
  height: 0.4em;
  border-radius: 50%;
  border: 1px dashed currentColor;
  opacity: 0.55;
  margin-top: -10px;
}

@keyframes playback-pending-accent-drop {
  /* Pop in with a scale overshoot — no vertical motion. An earlier
     version dropped from translateY(-8px) which looked like the glyph
     snapping down, since the pending-inner parent is already offset
     upward by 5px and the motion compounded into a visible jerk. */
  0% {
    opacity: 0;
    transform: scale(0.5);
  }
  60% {
    transform: scale(1.2);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

@media (prefers-reduced-motion: reduce) {
  .playback-line__pending-accent {
    animation: none;
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
