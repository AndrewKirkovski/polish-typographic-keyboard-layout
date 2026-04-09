<script setup lang="ts">
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
const version = `v${__APP_VERSION__}`
</script>

<template>
  <section class="hero">
    <div class="container">
      <div class="hero-content">
        <div class="hero-top">
          <div>
            <p class="hero-eyebrow">{{ version }}</p>
            <h1 class="hero-title">
              <span class="hero-title-line">Kirkouski</span>
              <span class="hero-title-line accent">Typographic</span>
            </h1>
          </div>
          <div class="hero-symbols" aria-hidden="true">
            <span>&mdash;</span>
            <span>&laquo;&raquo;</span>
            <span>&euro;</span>
            <span>&copy;</span>
            <span>&sect;</span>
            <span>&bdquo;&ldquo;</span>
            <span>&times;</span>
            <span>&hellip;</span>
            <span>&trade;</span>
            <span>&reg;</span>
          </div>
        </div>
        <p class="hero-subtitle">{{ t('hero.subtitle') }}</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.hero {
  /* User feedback: hero felt top-heavy. Reduced top padding (3 → 2) and
     bumped bottom (1 → 2) so the title and subtitle sit closer to the
     vertical centre of the visible-above-the-fold area. */
  padding: 2rem 0 2rem;
  position: relative;
  overflow: hidden;
}

.hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse 60% 50% at 20% 80%, color-mix(in srgb, var(--color-altgr) 6%, transparent), transparent),
    radial-gradient(ellipse 40% 40% at 80% 20%, color-mix(in srgb, var(--color-dead) 5%, transparent), transparent);
  pointer-events: none;
}

.hero-content {
  position: relative;
  z-index: 1;
}

.hero-top {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 2rem;
  margin-bottom: 0.75rem;
}

.hero-eyebrow {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--color-altgr);
  margin-bottom: 0.5rem;
}

.hero-title {
  font-family: var(--font-display);
  font-weight: 400;
  line-height: 1.05;
  letter-spacing: -0.03em;
}

.hero-title-line {
  display: block;
  font-size: clamp(2rem, 6vw, 3.5rem);
}

.hero-title-line.accent {
  font-style: italic;
  color: var(--color-altgr);
}

.hero-subtitle {
  font-size: 1rem;
  color: var(--text-secondary);
  max-width: 500px;
  line-height: 1.5;
}

.hero-symbols {
  display: flex;
  gap: 1rem;
  font-size: 1.2rem;
  color: var(--text-muted);
  font-family: var(--font-display);
  flex-wrap: wrap;
  justify-content: flex-end;
}

.hero-symbols span {
  opacity: 0.4;
  transition: opacity 0.3s, color 0.3s;
}

.hero-symbols span:hover {
  opacity: 1;
  color: var(--color-altgr);
}

@media (max-width: 768px) {
  .hero-top {
    flex-direction: column;
    align-items: flex-start;
  }
  .hero-symbols {
    justify-content: flex-start;
  }
}
</style>
