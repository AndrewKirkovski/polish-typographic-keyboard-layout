<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
const { t, tm } = useI18n()

const SITE_URL = 'https://polish-typographic.com/'
const SHARE_TEXT = 'Kirkouski Typographic — Polish & Russian keyboard layout with 80+ typographic symbols via AltGr'

// Static feature detection — never changes after the first paint, so a
// plain `const` is enough (was a `ref()` for no reason).
const canNativeShare = typeof navigator !== 'undefined' && 'share' in navigator

const basedParts = computed(() => {
  const raw = (tm('about.based') as string) || 'Based on {link} by Ilya Birman.'
  const idx = raw.indexOf('{link}')
  if (idx === -1) return { before: raw, after: '' }
  return { before: raw.slice(0, idx), after: raw.slice(idx + 6) }
})

const shareLinks = computed(() => [
  {
    id: 'twitter',
    label: t('share.twitter'),
    url: `https://x.com/intent/tweet?url=${encodeURIComponent(SITE_URL)}&text=${encodeURIComponent(SHARE_TEXT)}`,
    icon: 'ri:twitter-x-fill',
  },
  {
    id: 'facebook',
    label: t('share.facebook'),
    url: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(SITE_URL)}`,
    icon: 'ri:facebook-fill',
  },
  {
    id: 'linkedin',
    label: t('share.linkedin'),
    url: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(SITE_URL)}`,
    icon: 'ri:linkedin-fill',
  },
  {
    id: 'reddit',
    label: t('share.reddit'),
    url: `https://reddit.com/submit?url=${encodeURIComponent(SITE_URL)}&title=${encodeURIComponent(SHARE_TEXT)}`,
    icon: 'ri:reddit-fill',
  },
])

async function nativeShare() {
  try {
    await navigator.share({ title: SHARE_TEXT, url: SITE_URL })
  } catch {
    // User cancelled or error — ignore
  }
}

const copied = ref(false)
async function copyLink() {
  try {
    await navigator.clipboard.writeText(SITE_URL)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // Clipboard API unavailable — ignore
  }
}
</script>

<template>
  <section id="about" class="section">
    <div class="container">
      <h2 class="section-title">{{ t('about.title') }}</h2>
      <div class="about-content">
        <p>
          {{ basedParts.before }}
          <a href="https://ilyabirman.ru/typography-layout/" target="_blank" rel="noopener">
            {{ t('about.birmanLink') }}
          </a>
          {{ basedParts.after }}
        </p>
        <p>{{ t('about.baseline') }}</p>
        <p>{{ t('about.license') }}</p>

        <div class="about-actions">
          <a
            href="https://github.com/AndrewKirkovski/polish-typographic-keyboard-layout"
            target="_blank"
            rel="noopener"
            class="action-btn action-btn--github"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 0C5.374 0 0 5.373 0 12c0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23A11.509 11.509 0 0112 5.803c1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576C20.566 21.797 24 17.3 24 12c0-6.627-5.373-12-12-12z"/>
            </svg>
            {{ t('about.github') }}
          </a>
          <a
            href="https://ko-fi.com/ryotsuke"
            target="_blank"
            rel="noopener"
            class="action-btn action-btn--kofi"
          >
            <iconify-icon icon="simple-icons:kofi" width="20" aria-hidden="true"></iconify-icon>
            {{ t('about.support') }}
          </a>
        </div>

        <p class="star-hint">
          <iconify-icon icon="mdi:star-outline" width="14" aria-hidden="true"></iconify-icon>
          {{ t('about.starHint') }}
        </p>

        <div class="share-section">
          <span class="share-label">{{ t('share.title') }}</span>
          <div class="share-buttons">
            <button
              v-if="canNativeShare"
              class="share-btn share-btn--native"
              :title="t('share.title')"
              :aria-label="t('share.title')"
              @click="nativeShare"
            >
              <iconify-icon icon="mdi:share-variant" width="18" aria-hidden="true"></iconify-icon>
            </button>
            <a
              v-for="link in shareLinks"
              :key="link.id"
              :href="link.url"
              :title="link.label"
              :aria-label="link.label"
              target="_blank"
              rel="noopener noreferrer"
              class="share-btn"
            >
              <iconify-icon :icon="link.icon" width="18" aria-hidden="true"></iconify-icon>
            </a>
            <button
              class="share-btn"
              :title="copied ? t('share.copied') : t('share.copyLink')"
              :aria-label="copied ? t('share.copied') : t('share.copyLink')"
              @click="copyLink"
            >
              <iconify-icon :icon="copied ? 'mdi:check' : 'mdi:link-variant'" width="18" aria-hidden="true"></iconify-icon>
            </button>
          </div>
        </div>

      </div>
    </div>
  </section>
</template>

<style scoped>
.about-content {
  max-width: 600px;
}

.about-content p {
  color: var(--text-secondary);
  line-height: 1.7;
  margin-bottom: 1rem;
}

.about-actions {
  display: flex;
  gap: 0.75rem;
  margin-top: 1.5rem;
  flex-wrap: wrap;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.9rem;
  transition: opacity 0.15s;
  text-decoration: none;
}

.action-btn:hover {
  opacity: 0.85;
}

.action-btn--github {
  background: var(--text);
  color: var(--bg);
}

.action-btn--kofi {
  background: #ff5e5b;
  color: #fff;
}

.star-hint {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-top: 1rem;
  font-size: 0.8rem;
  color: var(--text-muted);
}

.share-section {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border);
}

.share-label {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.share-buttons {
  display: flex;
  gap: 0.25rem;
}

.share-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: var(--bg-subtle);
  color: var(--text-secondary);
  border: none;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  text-decoration: none;
}

.share-btn:hover {
  background: var(--bg-elevated);
  color: var(--text);
}

.share-btn--native {
  background: var(--color-altgr);
  color: #fff;
}

.share-btn--native:hover {
  background: var(--color-altgr);
  opacity: 0.85;
}

</style>
