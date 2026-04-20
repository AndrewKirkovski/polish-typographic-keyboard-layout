<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { trackLocaleSwitch } from '../composables/useAnalytics'

const { t, locale } = useI18n()
const menuOpen = ref(false)

const langs = [
  { code: 'en', label: 'EN', href: '/' },
  { code: 'pl', label: 'PL', href: '/pl/' },
  { code: 'ru', label: 'RU', href: '/ru/' },
]

function langHref(lang: typeof langs[0]) {
  const hash = typeof window !== 'undefined' ? window.location.hash : ''
  return lang.href + hash
}

// Anchor nav (Keyboard / Download / About) only works when the homepage
// is currently rendered — the target sections live in App.vue's home
// route, not in the standalone /fonts page. When we're on a subpage,
// prefix the anchor with the locale-matching homepage so the browser
// navigates home and then scrolls to the section.
function navHref(hash: string): string {
  if (typeof window === 'undefined') return hash
  const path = window.location.pathname
  const onHome =
    path === '/' ||
    path === '/pl' || path === '/pl/' ||
    path === '/ru' || path === '/ru/'
  if (onHome) return hash
  const homeRoot = locale.value === 'en' ? '/' : `/${locale.value}/`
  return homeRoot + hash
}

function switchLang(e: Event, lang: typeof langs[0]) {
  e.preventDefault()
  if (locale.value === lang.code) return
  const from = locale.value
  locale.value = lang.code
  const url = langHref(lang)
  history.pushState(null, '', url)
  document.documentElement.lang = lang.code
  menuOpen.value = false
  trackLocaleSwitch(from, lang.code)
}

function closeMenu() {
  menuOpen.value = false
}
</script>

<template>
  <header class="site-header">
    <div class="header-inner container">
      <a href="#main" class="logo">
        <span class="logo-mark" aria-hidden="true">&mdash;</span>
        <span class="logo-text">Kirkouski</span>
      </a>
      <nav id="site-nav" class="nav" :class="{ open: menuOpen }">
        <a :href="navHref('#keyboard')" @click="closeMenu">{{ t('nav.keyboard') }}</a>
        <a :href="navHref('#download')" @click="closeMenu">{{ t('nav.download') }}</a>
        <a :href="navHref('#about')" @click="closeMenu">{{ t('nav.about') }}</a>
        <div class="lang-switcher lang-switcher--mobile">
          <a
            v-for="lang in langs"
            :key="lang.code"
            :href="langHref(lang)"
            :class="{ active: locale === lang.code }"
            :aria-current="locale === lang.code ? 'page' : undefined"
            @click="switchLang($event, lang)"
          >
            {{ lang.label }}
          </a>
        </div>
      </nav>
      <div class="lang-switcher lang-switcher--desktop">
        <a
          v-for="lang in langs"
          :key="lang.code"
          :href="langHref(lang)"
          :class="{ active: locale === lang.code }"
          :aria-current="locale === lang.code ? 'page' : undefined"
          @click="switchLang($event, lang)"
        >
          {{ lang.label }}
        </a>
      </div>
      <button
        class="hamburger"
        :class="{ open: menuOpen }"
        :aria-expanded="menuOpen"
        aria-controls="site-nav"
        :aria-label="t('nav.menu')"
        @click="menuOpen = !menuOpen"
      >
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

/* Scope to direct children only so the lang-switcher (which lives inside
   .nav on mobile) keeps its pill styling instead of inheriting nav-link
   padding + border-bottom. */
.nav > a {
  font-size: 0.85rem;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  transition: color 0.15s;
}

.nav > a:hover {
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

.lang-switcher a {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  font-weight: 500;
  padding: 4px 8px;
  border-radius: 4px;
  background: transparent;
  color: var(--text-muted);
  text-decoration: none;
  cursor: pointer;
  transition: all 0.15s;
}

.lang-switcher a.active {
  background: var(--bg-elevated);
  color: var(--text);
  box-shadow: 0 1px 2px rgba(0,0,0,0.08);
}

.lang-switcher a:hover:not(.active) {
  color: var(--text-secondary);
}

/* Hamburger button — hidden on desktop. WCAG 2.5.5 (AAA) requires
   touch targets ≥ 44×44 px on mobile; padding bumped from 4px so the
   total tap area clears 44×44. */
.hamburger {
  display: none;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  padding: 12px;
  min-width: 44px;
  min-height: 44px;
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

  /* Same direct-child scope on mobile so the lang-switcher pill isn't
     stretched to full width with a divider line below it. */
  .nav > a {
    padding: 0.75rem 0;
    border-bottom: 1px solid var(--border);
  }

  .nav > a:last-of-type {
    border-bottom: none;
  }

  /* Mobile lang-switcher: give it breathing room from the last nav link
     and align it to the start (left) of the mobile menu so it reads as
     a self-contained control rather than a stretched row. Pills get
     larger padding on mobile to clear the 44×44 touch target minimum. */
  .lang-switcher--mobile {
    align-self: flex-start;
    margin-top: 0.75rem;
  }
  .lang-switcher--mobile a {
    padding: 12px 16px;
    min-width: 44px;
    min-height: 44px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }
}
</style>
