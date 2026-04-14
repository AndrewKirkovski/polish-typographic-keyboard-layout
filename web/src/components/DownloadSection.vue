<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { detectOS } from '../composables/useOS'
import { trackDownload } from '../composables/useAnalytics'

const { t } = useI18n()

const VERSION = __APP_VERSION__
const RELEASE_TAG = `v${VERSION}`
const RELEASE_DL = `https://github.com/AndrewKirkovski/polish-typographic-keyboard-layout/releases/download/${RELEASE_TAG}`

const detectedOS = detectOS()

const isMobile = typeof navigator !== 'undefined'
  && /Android|iPhone|iPad|iPod|Mobile/i.test(navigator.userAgent)

const platforms = computed(() => {
  const winInstaller = `kirkouski-typographic-v${VERSION}-windows-setup.exe`
  const winZip = `kirkouski-typographic-v${VERSION}-windows.zip`
  const macPkg = `kirkouski-typographic-v${VERSION}-macos.pkg`
  const macZip = `kirkouski-typographic-v${VERSION}-macos.zip`
  const win = {
    id: 'windows',
    name: t('download.windows'),
    files: [
      { label: t('download.installer'), file: winInstaller, url: `${RELEASE_DL}/${winInstaller}` },
      { label: 'ZIP', file: winZip, url: `${RELEASE_DL}/${winZip}` },
    ],
    primary: !isMobile && detectedOS === 'windows',
  }
  const mac = {
    id: 'macos',
    name: t('download.macos'),
    files: [
      { label: t('download.installer'), file: macPkg, url: `${RELEASE_DL}/${macPkg}` },
      { label: 'ZIP', file: macZip, url: `${RELEASE_DL}/${macZip}` },
    ],
    primary: !isMobile && detectedOS === 'macos',
  }
  return detectedOS === 'windows' ? [win, mac] : [mac, win]
})

const pdfFiles = computed(() => [
  { file: `polish_typographic_color.pdf`, label: t('download.pdfPolishColor') },
  { file: `polish_typographic_bw.pdf`, label: t('download.pdfPolishBw') },
  { file: `russian_typographic_color.pdf`, label: t('download.pdfRussianColor') },
  { file: `russian_typographic_bw.pdf`, label: t('download.pdfRussianBw') },
].map(f => ({ ...f, url: `${RELEASE_DL}/${f.file}` })))
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
              <iconify-icon v-if="platform.id === 'windows'" icon="mdi:microsoft-windows" width="22" aria-hidden="true"></iconify-icon>
              <iconify-icon v-else icon="mdi:apple" width="22" aria-hidden="true"></iconify-icon>
            </span>
            <h3>{{ platform.name }}</h3>
          </div>
          <span v-if="platform.primary" class="badge">
            {{ t('download.recommended') }}
          </span>
          <ul class="download-card__files">
            <li v-for="file in platform.files" :key="file.file">
              <a
                :href="file.url"
                target="_blank"
                rel="noopener"
                @click="trackDownload(platform.id as 'windows' | 'macos', file.file)"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                  <path d="M7 1v8M3 6l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M1 11v1.5h12V11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span class="file-name">{{ file.file }}</span>
                <span class="file-label">{{ file.label }}</span>
              </a>
            </li>
          </ul>
        </div>

        <div class="download-card download-card--full">
          <div class="download-card__header">
            <span class="download-card__icon">
              <iconify-icon icon="mdi:file-pdf-box" width="22" aria-hidden="true"></iconify-icon>
            </span>
            <h3>{{ t('download.pdfTitle') }}</h3>
          </div>
          <ul class="download-card__files download-card__files--2col">
            <li v-for="pdf in pdfFiles" :key="pdf.file">
              <a
                :href="pdf.url"
                target="_blank"
                rel="noopener"
                @click="trackDownload('pdf', pdf.file)"
              >
                <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
                  <path d="M7 1v8M3 6l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M1 11v1.5h12V11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                <span class="file-name">{{ pdf.file }}</span>
                <span class="file-label">{{ pdf.label }}</span>
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
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

@media (max-width: 640px) {
  .download-grid {
    grid-template-columns: 1fr;
  }
}

.download-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 2rem;
  transition: border-color 0.2s;
  min-width: 0;
  overflow: hidden;
}

.download-card:hover {
  border-color: var(--border-strong);
}

.download-card--primary {
  border-color: var(--color-altgr);
  box-shadow: 0 0 0 1px var(--color-altgr);
}

.download-card--full {
  grid-column: 1 / -1;
}

.download-card__header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
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
  font-size: 0.6rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-altgr);
  background: color-mix(in srgb, var(--color-altgr) 10%, transparent);
  padding: 3px 8px;
  border-radius: 4px;
  display: inline-block;
  margin-bottom: 1rem;
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
  overflow: hidden;
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
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.file-label {
  margin-left: auto;
  font-size: 0.75rem;
  color: var(--text-muted);
  flex-shrink: 0;
  white-space: nowrap;
}

.download-card__files--2col {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

.download-card__files--2col li {
  min-width: 0;
}

.download-card__files--2col li + li {
  margin-top: 0;
}

@media (max-width: 640px) {
  .download-card__files--2col {
    grid-template-columns: 1fr;
  }
}
</style>
