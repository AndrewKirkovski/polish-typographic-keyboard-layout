<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const RELEASE_DL = 'https://github.com/AndrewKirkovski/polish-typographic-keyboard-layout/releases/download/v0.1'
const RELEASE_PAGE = 'https://github.com/AndrewKirkovski/polish-typographic-keyboard-layout/releases/latest'

const detectedOS = computed(() => {
  const ua = navigator.userAgent
  if (ua.includes('Mac')) return 'macos'
  return 'windows'
})

const platforms = computed(() => {
  const win = {
    id: 'windows',
    name: t('download.windows'),
    files: [
      { label: t('download.installer'), file: 'kirkouski-typographic-v0.1-windows-setup.exe', url: `${RELEASE_DL}/kirkouski-typographic-v0.1-windows-setup.exe` },
      { label: 'ZIP', file: 'kirkouski-typographic-v0.1-windows.zip', url: `${RELEASE_DL}/kirkouski-typographic-v0.1-windows.zip` },
    ],
    primary: detectedOS.value === 'windows',
  }
  const mac = {
    id: 'macos',
    name: t('download.macos'),
    files: [
      { label: t('download.installer'), file: 'kirkouski-typographic-v0.1-macos.pkg', url: `${RELEASE_DL}/kirkouski-typographic-v0.1-macos.pkg` },
      { label: 'ZIP', file: 'kirkouski-typographic-v0.1-macos.zip', url: `${RELEASE_DL}/kirkouski-typographic-v0.1-macos.zip` },
    ],
    primary: detectedOS.value === 'macos',
  }
  return detectedOS.value === 'windows' ? [win, mac] : [mac, win]
})
</script>

<template>
  <section id="download" class="section">
    <div class="container">
      <h2 class="section-title">{{ t('download.title') }}</h2>
      <p class="section-subtitle">{{ t('download.subtitle') }}</p>

      <div class="download-grid">
        <div
          v-for="platform in platforms"
          :key="platform.id"
          class="download-card"
          :class="{ 'download-card--primary': platform.primary }"
        >
          <div class="download-card__header">
            <span class="download-card__icon">
              {{ platform.id === 'windows' ? '&#xE764;' : '&#xF8FF;' }}
            </span>
            <h3>{{ platform.name }}</h3>
            <span v-if="platform.primary" class="badge">
              {{ t('download.recommended') }}
            </span>
          </div>
          <ul class="download-card__files">
            <li v-for="file in platform.files" :key="file.file">
              <a :href="file.url" target="_blank" rel="noopener">
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                  <path d="M7 1v8M3 6l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M1 11v1.5h12V11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span class="file-name">{{ file.file }}</span>
                <span class="file-label">{{ file.label }}</span>
              </a>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.download-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 1.5rem;
}

.download-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 2rem;
  transition: border-color 0.2s;
}

.download-card:hover {
  border-color: var(--border-strong);
}

.download-card--primary {
  border-color: var(--color-altgr);
  box-shadow: 0 0 0 1px var(--color-altgr);
}

.download-card__header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1.5rem;
}

.download-card__icon {
  font-size: 1.5rem;
  opacity: 0.6;
}

.download-card__header h3 {
  font-family: var(--font-body);
  font-size: 1.1rem;
  font-weight: 600;
}

.badge {
  font-family: var(--font-mono);
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-altgr);
  background: color-mix(in srgb, var(--color-altgr) 10%, transparent);
  padding: 3px 8px;
  border-radius: 4px;
  margin-left: auto;
}

.download-card__files {
  list-style: none;
}

.download-card__files li + li {
  margin-top: 0.75rem;
}

.download-card__files a {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: var(--bg-subtle);
  border-radius: 8px;
  color: var(--text);
  text-decoration: none;
  transition: background 0.15s;
}

.download-card__files a:hover {
  background: var(--bg);
  opacity: 1;
}

.download-card__files svg {
  color: var(--color-altgr);
  flex-shrink: 0;
}

.file-name {
  font-family: var(--font-mono);
  font-size: 0.85rem;
  font-weight: 500;
}

.file-label {
  margin-left: auto;
  font-size: 0.75rem;
  color: var(--text-muted);
}
</style>
