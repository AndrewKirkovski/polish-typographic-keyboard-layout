<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()
const menuOpen = ref(false)

const langs = [
  { code: 'en', label: 'EN' },
  { code: 'pl', label: 'PL' },
  { code: 'ru', label: 'RU' },
]

function closeMenu() {
  menuOpen.value = false
}
</script>

<template>
  <header class="site-header">
    <div class="header-inner container">
      <a href="#" class="logo">
        <span class="logo-mark">&mdash;</span>
        <span class="logo-text">Kirkouski</span>
      </a>
      <nav class="nav" :class="{ open: menuOpen }">
        <a href="#keyboard" @click="closeMenu">{{ t('nav.keyboard') }}</a>
        <a href="#download" @click="closeMenu">{{ t('nav.download') }}</a>
        <a href="#about" @click="closeMenu">{{ t('nav.about') }}</a>
        <div class="lang-switcher lang-switcher--mobile">
          <button
            v-for="lang in langs"
            :key="lang.code"
            :class="{ active: locale === lang.code }"
            @click="locale = lang.code; closeMenu()"
          >
            {{ lang.label }}
          </button>
        </div>
      </nav>
      <div class="lang-switcher lang-switcher--desktop">
        <button
          v-for="lang in langs"
          :key="lang.code"
          :class="{ active: locale === lang.code }"
          @click="locale = lang.code"
        >
          {{ lang.label }}
        </button>
      </div>
      <button class="hamburger" :class="{ open: menuOpen }" @click="menuOpen = !menuOpen" aria-label="Menu">
        <span /><span /><span />
      </button>
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

/* Hamburger button — hidden on desktop */
.hamburger {
  display: none;
  flex-direction: column;
  gap: 5px;
  padding: 4px;
  margin-left: auto;
  background: none;
  border: none;
  cursor: pointer;
}

.hamburger span {
  display: block;
  width: 20px;
  height: 2px;
  background: var(--text);
  border-radius: 1px;
  transition: transform 0.2s, opacity 0.2s;
}

.hamburger.open span:nth-child(1) { transform: translateY(7px) rotate(45deg); }
.hamburger.open span:nth-child(2) { opacity: 0; }
.hamburger.open span:nth-child(3) { transform: translateY(-7px) rotate(-45deg); }

/* Mobile lang switcher hidden on desktop, shown in mobile nav */
.lang-switcher--mobile { display: none; }

/* ── Mobile ────────────────────────────────────────────────────── */
@media (max-width: 640px) {
  .lang-switcher--desktop { display: none; }
  .lang-switcher--mobile { display: flex; margin-top: 0.5rem; }

  .hamburger { display: flex; }

  .nav {
    display: none;
    position: absolute;
    top: 56px;
    left: 0;
    right: 0;
    flex-direction: column;
    gap: 0;
    padding: 0.5rem 1.5rem 1rem;
    background: color-mix(in srgb, var(--bg) 95%, transparent);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid var(--border);
    margin-left: 0;
  }

  .nav.open { display: flex; }

  .nav a {
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--border);
  }

  .nav a:last-of-type {
    border-bottom: none;
  }
}
</style>
