<script setup lang="ts">
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useLayout } from './composables/useLayout'
import SiteHeader from './components/SiteHeader.vue'
import HeroSection from './components/HeroSection.vue'
import KeyboardSection from './components/KeyboardSection.vue'
import WhySection from './components/WhySection.vue'
import DownloadSection from './components/DownloadSection.vue'
import InstallSection from './components/InstallSection.vue'
import AboutSection from './components/AboutSection.vue'

const { init } = useLayout()
const { t, locale } = useI18n()

onMounted(async () => {
  await init()
  // Detect macOS for platform-specific labels (AltGr → ⌥, Win → ⌘)
  if (typeof navigator !== 'undefined' && /Mac|iPhone|iPad|iPod/.test(navigator.userAgent)) {
    document.documentElement.setAttribute('data-os', 'mac')
  }
})
</script>

<template>
  <div class="app" :lang="locale">
    <a href="#main" class="skip-link">{{ t('a11y.skipToMain') }}</a>
    <SiteHeader />
    <main id="main">
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
</style>
