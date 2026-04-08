<script setup lang="ts">
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
</script>

<template>
  <section class="hero">
    <div class="container">
      <div class="hero-content">
        <p class="hero-eyebrow">v0.1</p>
        <h1 class="hero-title">
          <span class="hero-title-line">Kirkouski</span>
          <span class="hero-title-line accent">Typographic</span>
        </h1>
        <p class="hero-subtitle">{{ t('hero.subtitle') }}</p>
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
      <a href="#keyboard" class="hero-scroll">
        <span>{{ t('hero.scroll') }}</span>
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <path d="M8 3v10M4 9l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </a>
    </div>
  </section>
</template>

<style scoped>
.hero {
  min-height: 80vh;
  display: flex;
  align-items: center;
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

.hero-eyebrow {
  font-family: var(--font-mono);
  font-size: 0.75rem;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--color-altgr);
  margin-bottom: 1.5rem;
}

.hero-title {
  font-family: var(--font-display);
  font-weight: 400;
  line-height: 1.05;
  letter-spacing: -0.03em;
  margin-bottom: 1.5rem;
}

.hero-title-line {
  display: block;
  font-size: clamp(3rem, 8vw, 5.5rem);
}

.hero-title-line.accent {
  font-style: italic;
  color: var(--color-altgr);
}

.hero-subtitle {
  font-size: 1.2rem;
  color: var(--text-secondary);
  max-width: 500px;
  line-height: 1.5;
  margin-bottom: 3rem;
}

.hero-symbols {
  display: flex;
  gap: 1.5rem;
  font-size: 1.5rem;
  color: var(--text-muted);
  font-family: var(--font-display);
  flex-wrap: wrap;
}

.hero-symbols span {
  opacity: 0.5;
  transition: opacity 0.3s, color 0.3s;
}

.hero-symbols span:hover {
  opacity: 1;
  color: var(--color-altgr);
}

.hero-scroll {
  position: absolute;
  bottom: 2rem;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  font-family: var(--font-mono);
  font-size: 0.7rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
  text-decoration: none;
  animation: float 2s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translateX(-50%) translateY(0); }
  50% { transform: translateX(-50%) translateY(4px); }
}
</style>
