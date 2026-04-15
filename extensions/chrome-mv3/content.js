/* Szpargalka Sans content script.
 *
 * Injects a @font-face rule loading the font from the base64 data URI
 * prepared by font-data.js (which runs first per manifest.content_scripts.js
 * order), then toggles a `szpargalka-active` class on <html> to apply the
 * universal font override. The actual CSS override lives in the same style
 * block so we only inject once per page.
 *
 * Two settings layers:
 *   - `mode` (global default): 'on' | 'off', defaults to 'off'
 *   - `siteOverrides[hostname]`: 'on' | 'off' | undefined
 *
 * Site overrides always win over the global default. Both the global and
 * the per-site overrides are strict binary toggles — we no longer try to
 * auto-detect Polish pages because that was too intrusive in practice.
 */

const SZPARGALKA_STYLE_ID = 'szpargalka-sans-override'
const ACTIVE_CLASS = 'szpargalka-active'
const DEFAULT_MODE = 'off' // on | off
const DEFAULT_SITE_OVERRIDES = {}

// Coerce any stored value (including legacy 'polish' / 'always' from the
// pre-binary extension) to the current 'on' | 'off' scheme.
function normalizeMode(mode) {
  if (mode === 'on' || mode === 'always') return 'on'
  return 'off'
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
      i[class*="icon" i], i.bi, .glyphicon, .octicon
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
  if (normalizeMode(mode) === 'on') activate()
  else deactivate()
}

// ── Effective mode resolver ─────────────────────────────────────────
// A site override always wins over the global mode.

function resolveEffectiveMode(globalMode, siteOverrides) {
  const override = siteOverrides?.[location.hostname]
  if (override === 'on' || override === 'off') return override
  return normalizeMode(globalMode)
}

// ── Load state + listen for changes ─────────────────────────────────

function loadAndApply() {
  chrome.storage.sync.get(
    { mode: DEFAULT_MODE, siteOverrides: DEFAULT_SITE_OVERRIDES },
    ({ mode, siteOverrides }) => {
      applyMode(resolveEffectiveMode(mode, siteOverrides))
    },
  )
}

loadAndApply()

chrome.storage.onChanged.addListener((changes, area) => {
  if (area !== 'sync') return
  // Re-apply if either the global mode OR our site's override changed.
  const modeChanged = !!changes.mode
  const overrideChanged =
    !!changes.siteOverrides &&
    (changes.siteOverrides.oldValue?.[location.hostname] !==
      changes.siteOverrides.newValue?.[location.hostname])
  if (modeChanged || overrideChanged) {
    loadAndApply()
  }
})
