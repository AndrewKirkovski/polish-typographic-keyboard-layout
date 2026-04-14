<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { trackFontTab, trackDownload } from '../composables/useAnalytics'

const { t } = useI18n()

const VERSION = __APP_VERSION__
const RELEASE_TAG = `v${VERSION}`
const RELEASE_DL = `https://github.com/AndrewKirkovski/polish-typographic-keyboard-layout/releases/download/${RELEASE_TAG}`

// Active font tab
type FontTab = 'cyrillic' | 'ipa'
const activeTab = ref<FontTab>('cyrillic')

function selectTab(tab: FontTab) {
  if (activeTab.value === tab) return
  activeTab.value = tab
  trackFontTab(tab)
}

const activeFont = computed(() =>
  activeTab.value === 'cyrillic' ? 'Szpargalka Sans' : 'Polish Phonetics Sans',
)

function reshapeText(e: Event) {
  const el = e.target as HTMLElement
  if (!el) return
  const sel = window.getSelection()
  const offset = sel?.focusOffset ?? 0
  const text = el.textContent ?? ''
  el.textContent = ''
  el.textContent = text
  if (sel && el.firstChild) {
    const pos = Math.min(offset, text.length)
    sel.collapse(el.firstChild, pos)
  }
}

// Font file names
const FONT_FILES = {
  cyrillic: 'SzpargalkaSans-Regular.ttf',
  ipa: 'PolishPhoneticsSans-Regular.ttf',
} as const

// Ligature reference data — Cyrillic variant (Szpargalka Sans)
const ligaturesCyrillic = [
  { input: 'szcz', pronunciation: "\u0449 (shch, as in \"fresh cheese\")" },
  { input: 'sz',   pronunciation: "\u0448 (sh, as in \"shop\")" },
  { input: 'cz',   pronunciation: "\u0447 (ch, as in \"church\")" },
  { input: 'ch',   pronunciation: "\u0445 (kh, as in \"Bach\")" },
  { input: 'rz',   pronunciation: "\u0436 (zh, as in \"vision\")" },
  { input: 'dz',   pronunciation: "\u0434\u0437 (dz, as in \"adze\")" },
  { input: 'ci',   pronunciation: "\u0447\u044c (soft ch, as in \"cheer\")" },
  { input: 'si',   pronunciation: "\u0448\u044c (soft sh)" },
  { input: 'zi',   pronunciation: "\u0436\u044c (soft zh)" },
  { input: 'ia',   pronunciation: "\u044f (ya)" },
  { input: 'ie',   pronunciation: "\u0435 (ye)" },
  { input: 'io',   pronunciation: "\u0439\u043e (yo)" },
  { input: 'iu',   pronunciation: "\u044e (yu)" },
  { input: '\u00f3', pronunciation: "\u0443 (u)" },
  { input: '\u0142', pronunciation: "\u0432 (v/w)" },
]

// Ligature reference data — IPA variant (Polish Phonetics Sans)
const ligaturesIpa = [
  { input: 'szcz', pronunciation: '\u0282t\u0282 (retroflex shch)' },
  { input: 'sz',   pronunciation: '\u0282 (voiceless retroflex fricative)' },
  { input: 'cz',   pronunciation: 't\u0282 (voiceless retroflex affricate)' },
  { input: 'ch',   pronunciation: 'x (voiceless velar fricative)' },
  { input: 'rz',   pronunciation: '\u0290 (voiced retroflex fricative)' },
  { input: 'dz',   pronunciation: 'dz (voiced alveolar affricate)' },
  { input: 'ci',   pronunciation: 't\u0255 (voiceless alveolo-palatal affricate)' },
  { input: 'si',   pronunciation: '\u0255 (voiceless alveolo-palatal fricative)' },
  { input: 'zi',   pronunciation: '\u0291 (voiced alveolo-palatal fricative)' },
  { input: 'ia',   pronunciation: 'ja' },
  { input: 'ie',   pronunciation: 'j\u025b' },
  { input: 'io',   pronunciation: 'j\u0254' },
  { input: 'iu',   pronunciation: 'ju' },
  { input: '\u00f3', pronunciation: 'u (close back rounded vowel)' },
  { input: '\u0142', pronunciation: 'w (labial-velar approximant)' },
]

const activeLigatures = computed(() =>
  activeTab.value === 'cyrillic' ? ligaturesCyrillic : ligaturesIpa,
)
</script>

<template>
  <div class="font-demo-page">
    <div class="container">
      <!-- Back link -->
      <a href="../" class="back-link">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path d="M10 12L6 8l4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        {{ t('fonts.backToMain') }}
      </a>

      <!-- Header -->
      <header class="font-demo-header">
        <h1 class="section-title">{{ t('fonts.title') }}</h1>
        <p class="section-subtitle">{{ t('fonts.subtitle') }}</p>
      </header>

      <!-- Tab switcher -->
      <div class="tabs" role="tablist" :aria-label="t('fonts.title')">
        <button
          id="tab-cyrillic"
          role="tab"
          :aria-selected="activeTab === 'cyrillic'"
          :tabindex="activeTab === 'cyrillic' ? 0 : -1"
          aria-controls="panel-font"
          :class="{ active: activeTab === 'cyrillic' }"
          @click="selectTab('cyrillic')"
        >{{ t('fonts.tabCyrillic') }}</button>
        <button
          id="tab-ipa"
          role="tab"
          :aria-selected="activeTab === 'ipa'"
          :tabindex="activeTab === 'ipa' ? 0 : -1"
          aria-controls="panel-font"
          :class="{ active: activeTab === 'ipa' }"
          @click="selectTab('ipa')"
        >{{ t('fonts.tabIpa') }}</button>
      </div>

      <p v-if="activeTab === 'ipa'" class="ipa-note">{{ t('fonts.ipaNote') }}</p>

      <!-- Content-editable test area -->
      <section id="panel-font" role="tabpanel" :aria-labelledby="`tab-${activeTab}`" class="demo-section">
        <h2 class="demo-heading">{{ t('fonts.testTitle') }}</h2>
        <div
          class="editable-area"
          contenteditable="true"
          spellcheck="false"
          :style="{ fontFamily: `'${activeFont}', sans-serif` }"
          :data-placeholder="t('fonts.placeholder')"
          @input="reshapeText"
        ></div>
        <p class="editable-hint">{{ t('fonts.testHint') }}</p>
      </section>

      <!-- Sample text -->
      <section class="demo-section">
        <h2 class="demo-heading">{{ t('fonts.sampleTitle') }}</h2>
        <div
          class="sample-text"
          :style="{ fontFamily: `'${activeFont}', sans-serif` }"
        >{{ t('fonts.sampleText') }}</div>
      </section>

      <!-- Ligature reference table -->
      <section class="demo-section">
        <h2 class="demo-heading">{{ t('fonts.referenceTitle') }}</h2>
        <div class="table-wrapper">
          <table class="ligature-table">
            <thead>
              <tr>
                <th>{{ t('fonts.tableInput') }}</th>
                <th>{{ t('fonts.tableRendered') }}</th>
                <th>{{ t('fonts.tablePronunciation') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in activeLigatures" :key="row.input">
                <td class="col-input">{{ row.input }}</td>
                <td
                  class="col-rendered"
                  :style="{ fontFamily: `'${activeFont}', sans-serif` }"
                >{{ row.input }}</td>
                <td class="col-pronunciation">{{ row.pronunciation }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <!-- Download links -->
      <section class="demo-section">
        <h2 class="demo-heading">{{ t('fonts.download') }}</h2>
        <div class="download-cards">
          <a
            :href="`${RELEASE_DL}/${FONT_FILES.cyrillic}`"
            class="font-download-card"
            :class="{ 'font-download-card--active': activeTab === 'cyrillic' }"
            target="_blank"
            rel="noopener"
            @click="trackDownload('font', FONT_FILES.cyrillic, { variant: 'cyrillic' })"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
              <path d="M7 1v8M3 6l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M1 11v1.5h12V11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span class="font-download-card__name">{{ FONT_FILES.cyrillic }}</span>
            <span class="font-download-card__label">{{ t('fonts.tabCyrillic') }}</span>
          </a>
          <a
            :href="`${RELEASE_DL}/${FONT_FILES.ipa}`"
            class="font-download-card"
            :class="{ 'font-download-card--active': activeTab === 'ipa' }"
            target="_blank"
            rel="noopener"
            @click="trackDownload('font', FONT_FILES.ipa, { variant: 'ipa' })"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
              <path d="M7 1v8M3 6l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M1 11v1.5h12V11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span class="font-download-card__name">{{ FONT_FILES.ipa }}</span>
            <span class="font-download-card__label">{{ t('fonts.tabIpa') }}</span>
          </a>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
/*
 * @font-face declarations live in the unscoped block below so they are global.
 * The font URLs point to the release download for production and to local
 * dist/ copies for dev (Vite resolves relative paths from index.html).
 *
 * In production the fonts are fetched from the GitHub release on first use.
 * For dev, run `python polish_liga.py` to generate the .ttf files in dist/.
 */

.font-demo-page {
  padding: var(--section-gap) 0;
  min-height: 100vh;
}

/* ── Back link ─────────────────────────────────────────────────────── */
.back-link {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-family: var(--font-body);
  font-size: 0.85rem;
  color: var(--text-muted);
  text-decoration: none;
  margin-bottom: 2rem;
  transition: color 0.15s;
}

.back-link:hover {
  color: var(--color-altgr);
  opacity: 1;
}

/* ── Header ────────────────────────────────────────────────────────── */
.font-demo-header {
  margin-bottom: 2rem;
}

/* ── Tabs (matches InstallSection.vue) ─────────────────────────────── */
.tabs {
  display: inline-flex;
  gap: 2px;
  background: var(--bg-subtle);
  border-radius: 8px;
  padding: 3px;
  margin-bottom: 2.5rem;
  flex-wrap: wrap;
}

.tabs button {
  font-family: var(--font-body);
  font-size: 0.85rem;
  font-weight: 500;
  padding: 8px 20px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
}

.tabs button.active {
  background: var(--bg-elevated);
  color: var(--text);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

/* ── Demo sections ─────────────────────────────────────────────────── */
.ipa-note {
  font-size: 0.8rem;
  color: var(--text-muted);
  background: var(--bg-subtle);
  padding: 0.6rem 1rem;
  border-radius: 6px;
  margin-bottom: 1.5rem;
  border-left: 3px solid var(--color-altgr);
}

.demo-section {
  margin-bottom: 3rem;
}

.demo-heading {
  font-family: var(--font-display);
  font-size: 1.35rem;
  font-weight: 400;
  margin-bottom: 1rem;
  letter-spacing: -0.01em;
}

/* ── Content-editable area ─────────────────────────────────────────── */
.editable-area {
  font-size: 2.25rem;
  line-height: 2;
  padding: 1.5rem 2rem;
  background: var(--bg-elevated);
  border: 2px solid var(--border);
  border-radius: 12px;
  min-height: 160px;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
  color: var(--text);
}

.editable-area:focus {
  border-color: var(--color-altgr);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--color-altgr) 15%, transparent);
}

.editable-area:empty::before {
  content: attr(data-placeholder);
  color: var(--text-muted);
  pointer-events: none;
}

.editable-hint {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin-top: 0.5rem;
}

/* ── Sample text ───────────────────────────────────────────────────── */
.sample-text {
  font-size: 2rem;
  line-height: 2;
  padding: 1.5rem 2rem;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 12px;
  color: var(--text);
}

/* ── Ligature table ────────────────────────────────────────────────── */
.table-wrapper {
  overflow-x: auto;
}

.ligature-table {
  border-collapse: collapse;
  width: 100%;
}

.ligature-table th {
  text-align: left;
  padding: 0.6rem 1rem;
  font-family: var(--font-mono);
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  border-bottom: 2px solid var(--border);
}

.ligature-table td {
  padding: 0.6rem 1rem;
  border-bottom: 1px solid var(--border);
}

.col-input {
  font-family: var(--font-mono);
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text);
}

.col-rendered {
  font-size: 1.8rem;
  line-height: 1.8;
  color: var(--text);
}

.col-pronunciation {
  font-size: 0.85rem;
  color: var(--text-secondary);
}

/* ── Download cards ────────────────────────────────────────────────── */
.download-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

@media (max-width: 640px) {
  .download-cards {
    grid-template-columns: 1fr;
  }
}

.font-download-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  background: var(--bg-subtle);
  border: 1px solid var(--border);
  border-radius: 10px;
  color: var(--text);
  text-decoration: none;
  transition: background 0.15s, border-color 0.2s;
  overflow: hidden;
}

.font-download-card:hover {
  background: var(--bg-elevated);
  border-color: var(--border-strong);
  opacity: 1;
}

.font-download-card--active {
  border-color: var(--color-altgr);
  box-shadow: 0 0 0 1px var(--color-altgr);
}

.font-download-card svg {
  color: var(--color-altgr);
  flex-shrink: 0;
}

.font-download-card__name {
  font-family: var(--font-mono);
  font-size: 0.85rem;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.font-download-card__label {
  margin-left: auto;
  font-size: 0.75rem;
  color: var(--text-muted);
  flex-shrink: 0;
  white-space: nowrap;
}

/* ── Responsive ────────────────────────────────────────────────────── */
@media (max-width: 640px) {
  .editable-area {
    font-size: 1.5rem;
    padding: 1rem 1.25rem;
    min-height: 120px;
  }

  .sample-text {
    font-size: 1.35rem;
    padding: 1rem 1.25rem;
  }

  .col-rendered {
    font-size: 1.4rem;
  }
}
</style>

<style>
/* ── @font-face declarations (unscoped — must be global) ───────────── */

/* Production: load from GitHub release. Dev: Vite dev server proxies
   these to the dist/ folder at the repo root. The parentLayouts() plugin
   in vite.config.ts handles /layouts/ — for fonts we rely on Vite's
   standard public-dir serving from web/public/. Developers should
   symlink or copy the .ttf files there, or the fonts will 404 in dev
   and the editable area will fall back to sans-serif. */
@font-face {
  font-family: 'Szpargalka Sans';
  src: url('/fonts/SzpargalkaSans-Regular.ttf') format('truetype');
  font-weight: normal;
  font-style: normal;
  font-display: swap;
}

@font-face {
  font-family: 'Polish Phonetics Sans';
  src: url('/fonts/PolishPhoneticsSans-Regular.ttf') format('truetype');
  font-weight: normal;
  font-style: normal;
  font-display: swap;
}
</style>
