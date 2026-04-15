/* Popup script
 *
 * Two independent control groups:
 *   - Per-site override (top): "default / force on / force off" for the
 *     active tab's hostname. Stored as `siteOverrides[hostname]` in
 *     chrome.storage.sync, with "default" meaning the entry is removed.
 *   - Global default (bottom): "on / off" stored as `mode`, defaulting
 *     to "off" — the extension ships silent and only lights up when the
 *     user opts in, globally or per-site.
 *
 * Content scripts on every open tab subscribe to storage.onChanged and
 * re-apply the effective mode live — no reload needed.
 */

const DEFAULT_MODE = 'off'

// Coerce any stored value (including legacy 'polish' / 'always' from the
// pre-binary extension) to the current 'on' | 'off' scheme so the radio
// state stays correct after upgrading.
function normalizeMode(mode) {
  if (mode === 'on' || mode === 'always') return 'on'
  return 'off'
}
const hostnameEl = document.getElementById('hostname')
const siteHintEl = document.getElementById('site-hint')
const siteRadios = document.querySelectorAll('input[name="siteOverride"]')
const modeRadios = document.querySelectorAll('input[name="mode"]')

// Per-site segmented control disabled until we know the hostname.
function setSiteDisabled(disabled) {
  for (const r of siteRadios) r.disabled = disabled
}

setSiteDisabled(true)

// ── Resolve current tab's hostname ────────────────────────────────
// Chrome URLs (chrome://, chrome-extension://, devtools://, etc.) can't
// be overridden because content scripts don't run on them. We detect
// those and surface a friendly message instead of a broken control.

async function getActiveHostname() {
  try {
    const [tab] = await chrome.tabs.query({
      active: true,
      currentWindow: true,
    })
    if (!tab?.url) return null
    const url = new URL(tab.url)
    if (!['http:', 'https:'].includes(url.protocol)) return null
    return url.hostname
  } catch {
    return null
  }
}

// ── Initial state ─────────────────────────────────────────────────

Promise.all([
  getActiveHostname(),
  chrome.storage.sync.get({ mode: DEFAULT_MODE, siteOverrides: {} }),
]).then(([hostname, { mode, siteOverrides }]) => {
  const currentMode = normalizeMode(mode)
  // Global mode radios
  for (const r of modeRadios) r.checked = r.value === currentMode

  // Hostname + per-site section
  if (!hostname) {
    hostnameEl.textContent = '(not a web page)'
    hostnameEl.title = 'Extensions can only apply to http:// and https:// pages'
    siteHintEl.textContent = 'Open a regular web page to override it.'
    return
  }

  hostnameEl.textContent = hostname
  hostnameEl.title = hostname

  const override = siteOverrides[hostname] // 'on' | 'off' | undefined
  const activeValue = override ?? 'default'
  for (const r of siteRadios) r.checked = r.value === activeValue
  setSiteDisabled(false)
  updateSiteHint(activeValue, currentMode)
})

// ── Event handlers ────────────────────────────────────────────────

for (const r of modeRadios) {
  r.addEventListener('change', () => {
    if (!r.checked) return
    chrome.storage.sync.set({ mode: r.value })
    refreshSiteHint()
  })
}

for (const r of siteRadios) {
  r.addEventListener('change', async () => {
    if (!r.checked) return
    const hostname = await getActiveHostname()
    if (!hostname) return
    const { siteOverrides } = await chrome.storage.sync.get({
      siteOverrides: {},
    })
    if (r.value === 'default') {
      delete siteOverrides[hostname]
    } else {
      siteOverrides[hostname] = r.value // 'on' or 'off'
    }
    await chrome.storage.sync.set({ siteOverrides })
    refreshSiteHint()
  })
}

// ── Hint text ─────────────────────────────────────────────────────
// Explains what the current per-site choice actually does given the
// current global mode. Keeps the popup honest — "Default" alone isn't
// enough information if the global is "Off".

function globalModeLabel(mode) {
  return normalizeMode(mode) === 'on' ? 'On' : 'Off'
}

function updateSiteHint(siteValue, globalMode) {
  if (siteValue === 'on') {
    siteHintEl.textContent = 'Font always applied on this site, regardless of global default.'
  } else if (siteValue === 'off') {
    siteHintEl.textContent = 'Font never applied on this site, regardless of global default.'
  } else {
    siteHintEl.textContent = `Using global default: “${globalModeLabel(globalMode)}”.`
  }
}

async function refreshSiteHint() {
  const siteChecked = document.querySelector('input[name="siteOverride"]:checked')
  const modeChecked = document.querySelector('input[name="mode"]:checked')
  updateSiteHint(siteChecked?.value ?? 'default', modeChecked?.value ?? DEFAULT_MODE)
}
