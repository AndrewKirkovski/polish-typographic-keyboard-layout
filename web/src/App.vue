<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useLayout } from './composables/useLayout'
import { detectOS } from './composables/useOS'
import SiteHeader from './components/SiteHeader.vue'
import HeroSection from './components/HeroSection.vue'
import KeyboardSection from './components/KeyboardSection.vue'
import WhySection from './components/WhySection.vue'
import DownloadSection from './components/DownloadSection.vue'
import InstallSection from './components/InstallSection.vue'
import FaqSection from './components/FaqSection.vue'
import AboutSection from './components/AboutSection.vue'
import FontDemoPage from './components/FontDemoPage.vue'

const props = defineProps<{ ssrPage?: string }>()

const { init } = useLayout()
const { t, locale } = useI18n()

const isFontsPage = computed(() => {
  if (props.ssrPage) return props.ssrPage === 'fonts'
  if (typeof window === 'undefined') return false
  return window.location.pathname.includes('/fonts')
})

const fontsUrl = computed(() => {
  const base = locale.value === 'en' ? '' : `/${locale.value}`
  return `${base}/fonts/`
})

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
      <template v-if="isFontsPage">
        <FontDemoPage />
      </template>
      <template v-else>
        <HeroSection />
        <KeyboardSection />
        <WhySection />
        <FaqSection />
        <DownloadSection />
        <InstallSection />

        <section class="section font-teaser">
          <div class="container">
            <h2 class="section-title">{{ t('fonts.teaserTitle') }}</h2>
            <p class="font-teaser__text">{{ t('fonts.teaserText') }}</p>
            <div class="font-teaser__samples">
              <div class="font-teaser__sample">
                <span class="font-teaser__label">Cyrillic</span>
                <span class="font-teaser__preview" style="font-family: 'Szpargalka Sans', sans-serif;">szczególnie</span>
              </div>
              <div class="font-teaser__sample">
                <span class="font-teaser__label">IPA</span>
                <span class="font-teaser__preview" style="font-family: 'Polish Phonetics Sans', sans-serif;">szczególnie</span>
              </div>
            </div>
            <a :href="fontsUrl" class="font-teaser__link">{{ t('fonts.teaserLink') }} &rarr;</a>
          </div>
        </section>

        <AboutSection />
      </template>
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

.font-teaser__text {
  color: var(--text-secondary);
  margin-bottom: 1.5rem;
  max-width: 40rem;
}

.font-teaser__samples {
  display: flex;
  gap: 2rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.font-teaser__sample {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.font-teaser__label {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}

.font-teaser__preview {
  font-size: 2rem;
  line-height: 2;
  padding: 0.75rem 1.5rem;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 8px;
}

.font-teaser__link {
  font-family: var(--font-mono);
  font-size: 0.85rem;
  color: var(--color-altgr);
  text-decoration: none;
}

.font-teaser__link:hover {
  text-decoration: underline;
}
</style>
