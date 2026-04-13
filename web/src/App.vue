<script setup lang="ts">
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useLayout } from './composables/useLayout'
import { detectOS } from './composables/useOS'
import SiteHeader from './components/SiteHeader.vue'
import HeroSection from './components/HeroSection.vue'
import KeyboardSection from './components/KeyboardSection.vue'
import WhySection from './components/WhySection.vue'
import DownloadSection from './components/DownloadSection.vue'
import InstallSection from './components/InstallSection.vue'
import AboutSection from './components/AboutSection.vue'

const { init } = useLayout()
const { t, locale } = useI18n()

// Move focus into <main> from the skip link.
//
// Browsers handle skip links inconsistently:
//   - Mouse click on the <a> → fires `click`, hash changes, browser scrolls,
//     but focus stays on the <a> in most browsers.
//   - Enter on a focused <a> → fires `click`, same as above.
//   - Space on a focused <a> → DOES NOT fire click. Browsers default Space
//     to "scroll page down". So a Space-pressing user gets no skip behavior
//     at all from a vanilla `<a href="#main">`.
//   - Programmatic hash change / browser back → fires `hashchange` but
//     again, focus stays put.
//
// We bind one handler to both `click` and `keydown.space` (with prevent on
// Space to suppress the page-scroll default), AND a `hashchange` listener
// to catch any other entry point. All three call into the same focus-shift.
function skipToMain(e?: Event) {
  e?.preventDefault()
  const main = document.getElementById('main')
  if (!main) return
  main.focus({ preventScroll: false })
  main.scrollIntoView({ block: 'start', behavior: 'auto' })
}

onMounted(async () => {
  await init()
  // Set `data-os="mac"` on <html> so CSS rules in style.css (the macOS
  // modifier key swap: AltGr → ⌥, Win → ⌘, and .os-win/.os-mac toggles) can
  // style themselves. Components that need OS for initial state import
  // detectOS() directly instead of waiting on this attribute.
  if (detectOS() === 'macos') {
    document.documentElement.setAttribute('data-os', 'mac')
  }
  window.addEventListener('hashchange', () => {
    if (window.location.hash === '#main') skipToMain()
  })
})
</script>

<template>
  <div class="app" :lang="locale">
    <a
      href="#main"
      class="skip-link"
      @click="skipToMain"
      @keydown.space.prevent="skipToMain"
      @keydown.enter="skipToMain"
    >{{ t('a11y.skipToMain') }}</a>
    <SiteHeader />
    <!--
      `tabindex="-1"` makes the <main> programmatically focusable so the
      browser actually moves focus there when the skip-link's hash target
      is followed. Without it, `<a href="#main">` only scrolls; focus
      stays on the skip link, the next Tab returns to the header nav,
      and the skip link is useless.
    -->
    <main id="main" tabindex="-1">
      <div class="dev-banner" role="note">
        <p>
          {{ t('banner.development') }}
          <a href="https://github.com/AndrewKirkovski/polish-typographic-keyboard-layout/issues" target="_blank" rel="noopener">{{ t('banner.issues') }}</a>
        </p>
      </div>
      <HeroSection />
      <KeyboardSection />
      <WhySection />
      <DownloadSection />
      <InstallSection />
      <AboutSection />
    </main>
    <footer class="site-footer">
      <p>MIT License &middot; 2026 Andrew Kirkouski</p>
    </footer>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

main {
  flex: 1;
}

.site-footer {
  text-align: center;
  padding: 3rem 2rem;
  font-family: var(--font-mono);
  font-size: 0.75rem;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: var(--text-muted);
  border-top: 1px solid var(--border);
}

.dev-banner {
  background: #8b1a2b;
  color: #fff;
  text-align: center;
  padding: 0.5rem 1rem;
  font-size: 0.85rem;
}

.dev-banner a {
  color: #fff;
  text-decoration: underline;
  margin-left: 0.5em;
}
</style>
