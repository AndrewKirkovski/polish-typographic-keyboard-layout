// Single source of truth for OS detection.
//
// Synchronous by design: the user agent never changes mid-session, so the
// callers can read this in <script setup> (which runs BEFORE onMounted) and
// get a correct answer on the very first render. Previously
// `DownloadSection.vue` computed this off `document.documentElement.dataset.os`,
// which was only set in App.vue's onMounted — a race that made mac visitors
// see the Windows card as "recommended". `InstallSection.vue` didn't detect
// at all and always defaulted to Windows.
//
// SSR-safe: returns 'windows' when navigator is undefined (we ship as a
// static SPA so this only matters for prerender/tooling, but keep it safe).
export function detectOS(): 'windows' | 'macos' {
  if (typeof navigator === 'undefined') return 'windows'
  return /Mac|iPhone|iPad|iPod/.test(navigator.userAgent) ? 'macos' : 'windows'
}
