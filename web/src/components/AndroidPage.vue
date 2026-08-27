<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { trackDownload } from '../composables/useAnalytics'

const { t } = useI18n()

const VERSION = __APP_VERSION__
const RELEASE_TAG = `v${VERSION}`
const RELEASE_DL = `https://github.com/AndrewKirkovski/polish-typographic-keyboard-layout/releases/download/${RELEASE_TAG}`
const ANDROID_ZIP = `kirkouski-typographic-v${VERSION}-android.zip`

interface Layout {
  id: 'latin' | 'cyrillic'
  file: string
  nameKey: string
  descKey: string
  // Filename stem for /screenshots/<shots>-<theme>-<page>.webp
  shots: string
}

// FUTO files an imported dictionary under the locale in its header and offers no
// picker at import time, so there is one build per subtype you might be using
// rather than one file for everyone. Same 344,389 words in each.
interface Dict {
  locale: string
  label: string
  file: string
}

const DICTS: Dict[] = [
  { locale: 'en_US', label: 'English (US)', file: 'kirkouski-en-pl-en_US.dict' },
  { locale: 'en_GB', label: 'English (UK)', file: 'kirkouski-en-pl-en_GB.dict' },
  { locale: 'pl', label: 'Polski', file: 'kirkouski-en-pl-pl.dict' },
]

// Upstream review. Once these land, the layouts ship with FUTO Keyboard and the
// custom-layout steps above stop being necessary.
const PULL_REQUESTS = [
  { id: 309, labelKey: 'android.latinName' },
  { id: 310, labelKey: 'android.cyrillicName' },
]

const LAYOUTS: Layout[] = [
  {
    id: 'latin',
    file: 'polish_english_typographic.yaml',
    nameKey: 'android.latinName',
    descKey: 'android.latinDesc',
    shots: 'pl',
  },
  {
    id: 'cyrillic',
    file: 'cyrillic_typographic.yaml',
    nameKey: 'android.cyrillicName',
    descKey: 'android.cyrillicDesc',
    shots: 'cy',
  },
]

// The YAML is copied into public/layouts/ at build time by the parentLayouts()
// Vite plugin, the same way the keyboard diagram's JSON is. Fetching at runtime
// keeps the prerendered HTML small and means the page can never show a stale
// copy of a layout that has since been regenerated.
const source = ref<Record<string, string>>({})
const copied = ref<string | null>(null)

onMounted(async () => {
  await Promise.all(
    LAYOUTS.map(async (l) => {
      try {
        const res = await fetch(`/layouts/${l.file}`)
        if (res.ok) source.value[l.id] = await res.text()
      } catch {
        // Leave it unset; the template falls back to the download link.
      }
    }),
  )
})

async function copyLayout(l: Layout) {
  const text = source.value[l.id]
  if (!text) return
  try {
    await navigator.clipboard.writeText(text)
    copied.value = l.id
    window.setTimeout(() => {
      if (copied.value === l.id) copied.value = null
    }, 2000)
  } catch {
    // Clipboard can be blocked (insecure context, permissions). The <pre> below
    // is selectable, so the user can still copy by hand.
  }
}
</script>

<template>
  <div class="android-page">
    <div class="container">
      <a href="../" class="back-link">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" aria-hidden="true">
          <path d="M10 12L6 8l4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        {{ t('android.backToMain') }}
      </a>

      <header class="android-header">
        <h1 class="section-title">{{ t('android.title') }}</h1>
        <p class="section-subtitle">{{ t('android.subtitle') }}</p>
      </header>

      <section class="demo-section">
        <h2 class="demo-heading">{{ t('android.whyTitle') }}</h2>
        <p>{{ t('android.whyText') }}</p>
        <p>
          <a href="https://keyboard.futo.org/" target="_blank" rel="noopener noreferrer">
            keyboard.futo.org
          </a>
        </p>
      </section>

      <section class="demo-section">
        <h2 class="demo-heading">{{ t('android.installTitle') }}</h2>
        <ol class="android-steps">
          <li>{{ t('android.step1') }}</li>
          <li>{{ t('android.step2') }}</li>
          <li>{{ t('android.step3') }}</li>
          <li>{{ t('android.step4') }}</li>
        </ol>
        <p class="android-note">{{ t('android.upstreamNote') }}</p>
        <ul class="android-prs">
          <li v-for="pr in PULL_REQUESTS" :key="pr.id">
            <a
              :href="`https://github.com/futo-org/futo-keyboard-layouts/pull/${pr.id}`"
              target="_blank"
              rel="noopener noreferrer"
            >{{ t(pr.labelKey) }} — PR #{{ pr.id }}</a>
          </li>
        </ul>
      </section>

      <section class="demo-section">
        <h2 class="demo-heading">{{ t('android.layoutsTitle') }}</h2>

        <article v-for="l in LAYOUTS" :key="l.id" class="layout-card">
          <h3 class="layout-card__name">{{ t(l.nameKey) }}</h3>
          <p>{{ t(l.descKey) }}</p>

          <!-- Paired light/dark captures, selected by the browser's colour scheme
               rather than by script, so the prerendered HTML is already correct. -->
          <div class="layout-card__shots">
            <figure v-for="page in (['letters', 'alt'] as const)" :key="page" class="layout-shot">
              <picture>
                <source
                  :srcset="`/screenshots/${l.shots}-dark-${page}.webp`"
                  media="(prefers-color-scheme: dark)"
                />
                <img
                  :src="`/screenshots/${l.shots}-light-${page}.webp`"
                  :alt="`${t(l.nameKey)} — ${t(page === 'letters' ? 'android.shotLetters' : 'android.shotAltPage')}`"
                  width="1080"
                  height="737"
                  loading="lazy"
                  decoding="async"
                />
              </picture>
              <figcaption>
                {{ t(page === 'letters' ? 'android.shotLetters' : 'android.shotAltPage') }}
              </figcaption>
            </figure>
          </div>

          <div class="layout-card__actions">
            <button
              type="button"
              class="btn btn-secondary"
              :disabled="!source[l.id]"
              @click="copyLayout(l)"
            >
              {{ copied === l.id ? t('android.copied') : t('android.copy') }}
            </button>
            <a
              class="btn btn-secondary"
              :href="`${RELEASE_DL}/${ANDROID_ZIP}`"
              @click="trackDownload('android', ANDROID_ZIP, { layout: l.id })"
            >{{ t('download.layouts') }}</a>
          </div>

          <pre v-if="source[l.id]" class="layout-card__source"><code>{{ source[l.id] }}</code></pre>
        </article>
      </section>

      <section class="demo-section">
        <h2 class="demo-heading">{{ t('android.accentsTitle') }}</h2>
        <p>{{ t('android.accentsText') }}</p>
      </section>

      <section class="demo-section">
        <h2 class="demo-heading">{{ t('android.symbolsTitle') }}</h2>
        <p>{{ t('android.symbolsText') }}</p>
      </section>

      <section class="demo-section">
        <h2 class="demo-heading">{{ t('android.localeTitle') }}</h2>
        <p>{{ t('android.localeText') }}</p>
      </section>

      <section class="demo-section">
        <h2 class="demo-heading">{{ t('android.dictTitle') }}</h2>
        <p>{{ t('android.dictText') }}</p>
        <p>{{ t('android.dictSwipe') }}</p>
        <p class="android-note">{{ t('android.dictPick') }}</p>
        <div class="layout-card__actions">
          <a
            v-for="d in DICTS"
            :key="d.locale"
            class="btn btn-secondary"
            :href="`/dict/${d.file}`"
            :download="d.file"
            @click="trackDownload('android', d.file, { locale: d.locale })"
          >{{ d.label }}</a>
        </div>
        <p class="android-note">{{ t('android.dictImport') }}</p>
      </section>

      <section class="demo-section">
        <h2 class="demo-heading">{{ t('android.diffTitle') }}</h2>
        <ul class="android-diffs">
          <li>{{ t('android.diffDeadKey') }}</li>
          <li>{{ t('android.diffPositions') }}</li>
          <li>{{ t('android.diffMissing') }}</li>
        </ul>
      </section>

      <section class="demo-section">
        <h2 class="demo-heading">{{ t('android.sourceTitle') }}</h2>
        <p>{{ t('android.sourceText') }}</p>
        <p>
          <a
            href="https://github.com/AndrewKirkovski/polish-typographic-keyboard-layout"
            target="_blank"
            rel="noopener noreferrer"
          >github.com/AndrewKirkovski/polish-typographic-keyboard-layout</a>
        </p>
      </section>
    </div>
  </div>
</template>

<style scoped>
.android-page {
  padding: 2rem 0 4rem;
}

.android-header {
  margin-bottom: 2.5rem;
}

.android-steps,
.android-diffs {
  margin: 0.75rem 0 0;
  padding-left: 1.25rem;
  line-height: 1.7;
}

.android-steps li,
.android-diffs li,
.android-prs li {
  margin-bottom: 0.5rem;
}

.android-prs {
  margin-top: 0.5rem;
  font-size: 0.9375rem;
}

.layout-card__shots {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
  margin: 1.25rem 0;
}

.layout-shot {
  margin: 0;
}

.layout-shot img {
  display: block;
  width: 100%;
  height: auto;
  border-radius: 8px;
  /* The captures are edge-to-edge keyboards, so they need an outline to read as
     screenshots rather than as part of the page. */
  border: 1px solid rgba(128, 128, 128, 0.25);
}

.layout-shot figcaption {
  margin-top: 0.375rem;
  font-size: 0.8125rem;
  opacity: 0.7;
}

.android-note {
  margin-top: 1rem;
  font-size: 0.9375rem;
  opacity: 0.75;
}

.layout-card {
  margin-top: 1.5rem;
  padding: 1.25rem;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--surface);
}

.layout-card__name {
  margin: 0 0 0.5rem;
  font-size: 1.0625rem;
}

.layout-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 1rem;
}

.layout-card__source {
  margin-top: 1rem;
  padding: 0.875rem 1rem;
  max-height: 22rem;
  /* Wide YAML scrolls inside the card rather than widening the page. */
  overflow: auto;
  border-radius: 8px;
  background: var(--code-bg, rgba(127, 127, 127, 0.12));
  font-size: 0.8125rem;
  line-height: 1.55;
  white-space: pre;
  -webkit-user-select: all;
  user-select: all;
}
</style>
