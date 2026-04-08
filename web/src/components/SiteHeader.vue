<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()

const langs = [
  { code: 'en', label: 'EN' },
  { code: 'pl', label: 'PL' },
  { code: 'ru', label: 'RU' },
]
</script>

<template>
  <header class="site-header">
    <div class="header-inner container">
      <a href="#" class="logo">
        <span class="logo-mark">&mdash;</span>
        <span class="logo-text">Kirkouski</span>
      </a>
      <nav class="nav">
        <a href="#keyboard">{{ t('nav.keyboard') }}</a>
        <a href="#download">{{ t('nav.download') }}</a>
        <a href="#about">{{ t('nav.about') }}</a>
      </nav>
      <div class="lang-switcher">
        <button
          v-for="lang in langs"
          :key="lang.code"
          :class="{ active: locale === lang.code }"
          @click="locale = lang.code"
        >
          {{ lang.label }}
        </button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.site-header {
  position: sticky;
  top: 0;
  z-index: 50;
  background: color-mix(in srgb, var(--bg) 85%, transparent);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
}

.header-inner {
  display: flex;
  align-items: center;
  height: 56px;
  gap: 2rem;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-family: var(--font-display);
  font-size: 1.1rem;
  color: var(--text);
  text-decoration: none;
}

.logo-mark {
  color: var(--color-altgr);
  font-weight: 700;
  font-size: 1.4rem;
}

.nav {
  display: flex;
  gap: 1.5rem;
  margin-left: auto;
}

.nav a {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  transition: color 0.15s;
}

.nav a:hover {
  color: var(--text);
  opacity: 1;
}

.lang-switcher {
  display: flex;
  gap: 2px;
  background: var(--bg-subtle);
  border-radius: 6px;
  padding: 2px;
}

.lang-switcher button {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  font-weight: 500;
  padding: 4px 8px;
  border: none;
  border-radius: 4px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.15s;
}

.lang-switcher button.active {
  background: var(--bg-elevated);
  color: var(--text);
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
}

.lang-switcher button:hover:not(.active) {
  color: var(--text-secondary);
}
</style>
