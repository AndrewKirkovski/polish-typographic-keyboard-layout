/* Szpargalka Sans content script.
 *
 * Injects a @font-face rule loading the font from the base64 data URI
 * prepared by font-data.js (which runs first per manifest.content_scripts.js
 * order), then toggles a `szpargalka-active` class on <html> to apply the
 * universal font override. The actual CSS override lives in the same style
 * block so we only inject once per page.
 *
 * Mode is read from chrome.storage.sync and defaults to "polish" (only
 * activate on Polish pages). The popup writes to the same key and the
 * storage.onChanged listener below re-applies without needing a reload.
 */

const SZPARGALKA_STYLE_ID = 'szpargalka-sans-override'
const ACTIVE_CLASS = 'szpargalka-active'
const DEFAULT_MODE = 'polish' // polish | always | off

// ── Polish detection ───────────────────────────────────────────────

function langIsPolish() {
  const lang = (document.documentElement.lang || '').toLowerCase()
  if (lang.startsWith('pl')) return true
  const metaLang = document
    .querySelector('meta[http-equiv="content-language" i]')
    ?.getAttribute('content')
    ?.toLowerCase()
  return !!metaLang && metaLang.startsWith('pl')
}

function textLooksPolish() {
  const text = (document.body?.innerText || '').slice(0, 5000)
  if (text.length < 200) return false
  const polishChars = text.match(/[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]/g) || []
  return polishChars.length / text.length > 0.02
}

// ── Style injection ─────────────────────────────────────────────────

function injectStyle() {
  if (document.getElementById(SZPARGALKA_STYLE_ID)) return

  // font-data.js (loaded before this script by manifest.js order) sets
  // globalThis.SZPARGALKA_FONT_DATA_URI to a `data:font/ttf;base64,...`
  // URI. If the file wasn't generated, bail gracefully.
  const fontUri = globalThis.SZPARGALKA_FONT_DATA_URI
  if (!fontUri) {
    console.warn(
      '[Szpargalka Sans] font-data.js missing — run `node build-font.mjs`',
    )
    return
  }

  const style = document.createElement('style')
  style.id = SZPARGALKA_STYLE_ID
  style.textContent = `
    @font-face {
      font-family: 'Szpargalka Sans';
      src: url('${fontUri}') format('truetype');
      font-display: swap;
    }

    html.${ACTIVE_CLASS} * {
      font-family: 'Szpargalka Sans', sans-serif !important;
      /* letter-spacing disables OpenType ligatures — force it to 0 so
         the GSUB substitutions that render sz→ш, cz→ч, szcz→щ, etc.
         actually fire on the rendered text */
      letter-spacing: 0 !important;
      font-feature-settings: 'liga' 1, 'dlig' 1 !important;
    }

    html.${ACTIVE_CLASS} :is(
      code, pre, kbd, samp, tt, var,
      .material-icons, .material-symbols-outlined,
      [class*="fa-"], [class^="icon-"], [class*=" icon-"],
      i.bi, .glyphicon, .octicon
    ) {
      font-family: revert !important;
      letter-spacing: revert !important;
      font-feature-settings: revert !important;
    }
  `

  // Prefer <head> but fall back to documentElement since we run at
  // document_start and <head> may not exist on first invocation.
  ;(document.head || document.documentElement).appendChild(style)
}

function activate() {
  injectStyle()
  document.documentElement.classList.add(ACTIVE_CLASS)
}

function deactivate() {
  document.documentElement.classList.remove(ACTIVE_CLASS)
}

// ── Apply current mode ──────────────────────────────────────────────

function applyMode(mode) {
  if (mode === 'off') {
    deactivate()
    return
  }

  if (mode === 'always') {
    activate()
    return
  }

  // mode === 'polish' — try fast path (lang attribute) first, fall back
  // to a text density check once the body is ready.
  if (langIsPolish()) {
    activate()
    return
  }

  const recheck = () => {
    if (langIsPolish() || textLooksPolish()) activate()
    else deactivate()
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', recheck, { once: true })
  } else {
    recheck()
  }
}

// ── Load mode + listen for changes ──────────────────────────────────

chrome.storage.sync.get({ mode: DEFAULT_MODE }, ({ mode }) => applyMode(mode))

chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== 'sync' || !changes.mode) return
  applyMode(changes.mode.newValue || DEFAULT_MODE)
})
