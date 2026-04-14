// Popup script: wires the 3-way mode radio to chrome.storage.sync.
// Content scripts on every tab listen to storage.onChanged and re-apply
// without needing a page reload.

const DEFAULT_MODE = 'polish'
const radios = document.querySelectorAll('input[name="mode"]')

// Load current mode and tick the matching radio.
chrome.storage.sync.get({ mode: DEFAULT_MODE }, ({ mode }) => {
  for (const r of radios) r.checked = r.value === mode
})

// On change, persist. Content scripts pick it up via onChanged.
for (const r of radios) {
  r.addEventListener('change', () => {
    if (!r.checked) return
    chrome.storage.sync.set({ mode: r.value })
  })
}
