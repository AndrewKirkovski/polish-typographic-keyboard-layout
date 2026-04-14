import * as Counterscale from '@counterscale/tracker'

/**
 * Analytics wrapper around @counterscale/tracker.
 *
 * Counterscale's tracker only exposes pageview tracking, so custom events
 * are synthesised as virtual pageviews under the `/__e/<event-name>` path.
 * Properties attach as query-string params, which Counterscale keeps in its
 * collect beacon. The dashboard surfaces them alongside real pageviews —
 * filter by path prefix to separate the two.
 *
 * Initialisation no-ops when `VITE_COUNTERSCALE_URL` is unset so the app
 * keeps running during local dev and before the CF Worker is deployed.
 *
 * SSR-safe: every call guards on `typeof window`.
 */

const SITE_ID =
  import.meta.env.VITE_COUNTERSCALE_SITE_ID || 'polish-typographic-keyboard-layout'
const REPORTER_URL = import.meta.env.VITE_COUNTERSCALE_URL || ''

let initialized = false

type EventProps = Record<string, string | number | boolean | undefined>

export function initAnalytics(): void {
  if (initialized) return
  if (typeof window === 'undefined') return
  if (!REPORTER_URL) return

  Counterscale.init({
    siteId: SITE_ID,
    reporterUrl: REPORTER_URL,
    autoTrackPageviews: true,
  })
  initialized = true
}

/**
 * Fire a custom event. Encoded as a virtual pageview to `/__e/<name>` with
 * the props serialised into the query string (primitives only — objects are
 * skipped).
 */
export function trackEvent(name: string, props?: EventProps): void {
  if (!initialized || typeof window === 'undefined') return

  const url = new URL(`/__e/${name}`, window.location.origin)
  if (props) {
    for (const [key, value] of Object.entries(props)) {
      if (value === undefined || value === null) continue
      url.searchParams.set(key, String(value))
    }
  }
  Counterscale.trackPageview({ url: url.toString() })
}

/** Fired when an SPA-style route change happens (locale switch, hash nav). */
export function trackPageview(path?: string): void {
  if (!initialized || typeof window === 'undefined') return
  if (path) {
    const url = new URL(path, window.location.origin)
    Counterscale.trackPageview({ url: url.toString() })
  } else {
    Counterscale.trackPageview()
  }
}

export function trackDownload(
  category: 'windows' | 'macos' | 'pdf' | 'font',
  file: string,
  extra?: EventProps,
): void {
  trackEvent('download', { category, file, ...extra })
}

export function trackLayerSwitch(layer: string): void {
  trackEvent('layer-switch', { layer })
}

export function trackVariantSwitch(variant: 'polish' | 'russian'): void {
  trackEvent('variant-switch', { variant })
}

export function trackLocaleSwitch(from: string, to: string): void {
  trackEvent('locale-switch', { from, to })
}

export function trackFontTab(tab: 'cyrillic' | 'ipa'): void {
  trackEvent('font-tab', { tab })
}

export function trackScrollDepth(percent: 25 | 50 | 75 | 100): void {
  trackEvent('scroll-depth', { percent })
}

export function useAnalytics() {
  return {
    trackEvent,
    trackPageview,
    trackDownload,
    trackLayerSwitch,
    trackVariantSwitch,
    trackLocaleSwitch,
    trackFontTab,
    trackScrollDepth,
  }
}
