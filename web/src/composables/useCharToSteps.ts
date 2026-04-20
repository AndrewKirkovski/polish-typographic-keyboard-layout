/**
 * useCharToSteps — pure resolver from a character (or grapheme cluster)
 * to the sequence of physical key presses that types it on the currently-
 * loaded layout. Used by the playback animation to drive the keyboard viz.
 *
 * Design notes:
 *   - No Vite plugin, no extra data files. The resolver walks the same
 *     `LayoutData.layers` that useLayout already loads at runtime.
 *   - Direct single-press chars win on collision-prefer-simpler-layer
 *     (base < shift < altgr < shift_altgr), so the demo takes the
 *     easiest path by default.
 *   - Chars that aren't in any layer directly (e.g. č, ö, ő) are resolved
 *     via Unicode NFD decomposition: base letter + combining mark →
 *     dead-key trigger + base letter. The flat layer JSON already exposes
 *     dead-key triggers as `{ char: "dk:<state>" }` entries, so no
 *     additional data is required.
 *
 * Grapheme-cluster iteration:
 *   We iterate the phrase via `Intl.Segmenter({granularity:'grapheme'})`.
 *   A phrase author can force the dead-key path by writing the explicit
 *   NFD form even when a precomposed char exists:
 *
 *     'ё'        → 1-codepoint cluster, direct path (base-layer key)
 *     'е\u0308'  → 2-codepoint cluster, dead-key path (diaeresis + е)
 *     'у\u0306'  → 2-codepoint cluster, dead-key path (breve + у) = ў
 *     'ы\u0308'  → 2-codepoint cluster, dead-key path, no precomposed form —
 *                  the font renders it as ы with a combining diaeresis
 *                  (purely a demo of how the dead-key system works)
 *
 *   This is how the Russian demo pool can show off the dead-key system
 *   even though Russian's native chars are all direct.
 *
 * Space: hardcoded as a `{kind: 'space'}` step since the flat extractor
 * doesn't write the space key to any layer.
 */

import type { LayoutData, LayoutEntry } from './useLayout'

export type Layer = 'base' | 'shift' | 'altgr' | 'shift_altgr'

/**
 * One atomic action in a playback sequence.
 *
 *   kind: 'key'     — press a physical key in a given layer. The player
 *                     sets manualLayer and adds keyId to pressedKeyIds
 *                     for holdMs, then removes it. If `typed` is set,
 *                     append that string to the on-screen text line when
 *                     the key is released. Dead-key trigger steps leave
 *                     `typed` empty — nothing gets committed visually
 *                     until the follow-up letter fires.
 *
 *   kind: 'space'   — advance the caret by one space character. No key
 *                     highlight (space bar lighting up for every word is
 *                     visual noise). Uses its own shorter dwell.
 */
export type Step =
  | { kind: 'key'; keyId: string; layer: Layer; typed: string }
  | { kind: 'space' }

const LAYER_ORDER: Record<Layer, number> = {
  base: 0,
  shift: 1,
  altgr: 2,
  shift_altgr: 3,
}

const LAYER_NAMES: Layer[] = ['base', 'shift', 'altgr', 'shift_altgr']

// Unicode combining mark → dead-key state name as used in the flat
// layer JSON (`dk:<state>`). Covers every trigger the extractor emits;
// `acute-2` is also recognized below so both the macOS `acute` and
// `acute-2` variants resolve to the same state name internally.
const COMBINING_MARK_TO_STATE: Record<string, string> = {
  '\u0300': 'grave',
  '\u0301': 'acute',
  '\u0302': 'circumflex',
  '\u0303': 'tilde',
  '\u0304': 'macron',
  '\u0306': 'breve',
  '\u0307': 'dot-above',
  '\u0308': 'diaeresis',
  '\u030A': 'ring',
  '\u030B': 'double-acute',
  '\u030C': 'caron',
  '\u0326': 'cedilla', // combining comma below
  '\u0327': 'cedilla', // combining cedilla
}

/** Return the raw char field of a layer entry (string or LayoutEntry). */
function entryChar(entry: string | LayoutEntry | null | undefined): string {
  if (entry == null) return ''
  if (typeof entry === 'string') return entry
  return entry.char ?? ''
}

interface CharMap {
  direct: Map<string, { keyId: string; layer: Layer }>
  deadTriggers: Map<string, { keyId: string; layer: Layer }>
}

function buildCharMap(layout: LayoutData): CharMap {
  const direct = new Map<string, { keyId: string; layer: Layer }>()
  const deadTriggers = new Map<string, { keyId: string; layer: Layer }>()

  for (const layerName of LAYER_NAMES) {
    const layer = (layout.layers as Record<Layer, Record<string, unknown>>)[layerName]
    if (!layer) continue
    for (const [keyId, raw] of Object.entries(layer)) {
      const ch = entryChar(raw as string | LayoutEntry | null)
      if (!ch) continue

      if (ch.startsWith('dk:')) {
        // Dead-key trigger. Normalise acute-2 → acute so combining
        // U+0301 resolves consistently whichever physical key we pick.
        let state = ch.slice(3)
        if (state === 'acute-2') state = 'acute'
        const prev = deadTriggers.get(state)
        if (!prev || LAYER_ORDER[layerName] < LAYER_ORDER[prev.layer]) {
          deadTriggers.set(state, { keyId, layer: layerName })
        }
        continue
      }

      if (ch.startsWith('act:')) {
        // Single-press action key whose output isn't directly embedded
        // in the flat extractor — skip for now. None of our phrase
        // targets depend on `act:` entries (verified via .local/ script).
        continue
      }

      // Direct typeable char. Prefer the simplest layer on collision.
      const prev = direct.get(ch)
      if (!prev || LAYER_ORDER[layerName] < LAYER_ORDER[prev.layer]) {
        direct.set(ch, { keyId, layer: layerName })
      }
    }
  }

  return { direct, deadTriggers }
}

// Module-level cache keyed by the layout object identity. `useLayout`
// memoises loaded layouts, so re-renders reuse the same reference and
// the reverse map is built exactly once per variant.
const cache = new WeakMap<LayoutData, CharMap>()

function getCharMap(layout: LayoutData): CharMap {
  let map = cache.get(layout)
  if (!map) {
    map = buildCharMap(layout)
    cache.set(layout, map)
  }
  return map
}

/**
 * Resolve a grapheme cluster to the sequence of playback steps that
 * types it. Returns null if the cluster can't be reached on the given
 * layout — callers should warn once and skip it.
 *
 * Three code paths:
 *   1. Single-codepoint cluster that's a direct layer hit → 1-step.
 *   2. Single-codepoint cluster that NFD-decomposes to base + mark →
 *      2-step dead-key sequence (covers č, ö, ő, etc.).
 *   3. Multi-codepoint cluster (author wrote explicit NFD form) →
 *      2-step dead-key sequence, forced even if a precomposed form
 *      exists. Use for alternative-path demos and fun compositions.
 */
export function resolveCluster(layout: LayoutData, cluster: string): Step[] | null {
  if (!cluster) return null

  if (cluster === ' ' || cluster === '\u00A0') {
    return [{ kind: 'space' }]
  }

  const map = getCharMap(layout)
  const codepoints = Array.from(cluster)

  // Path 1: single codepoint, direct hit.
  if (codepoints.length === 1) {
    const directHit = map.direct.get(cluster)
    if (directHit) {
      return [
        { kind: 'key', keyId: directHit.keyId, layer: directHit.layer, typed: cluster },
      ]
    }

    // Path 2: single codepoint, NFD fallback.
    const nfd = cluster.normalize('NFD')
    if (nfd.length !== 2) return null
    return resolveDeadKeySequence(map, nfd[0], nfd[1], cluster)
  }

  // Path 3: explicit base+mark form. Exactly 2 codepoints: a base
  // letter followed by a combining mark we recognise. This lets the
  // phrase author force the dead-key path even when the precomposed
  // form is directly typeable, and also lets them demo "fun" nonsense
  // compositions that don't have a precomposed form at all (e.g. ӹ).
  if (codepoints.length === 2) {
    return resolveDeadKeySequence(map, codepoints[0], codepoints[1], cluster)
  }

  return null
}

function resolveDeadKeySequence(
  map: CharMap,
  base: string,
  mark: string,
  displayCluster: string,
): Step[] | null {
  const state = COMBINING_MARK_TO_STATE[mark]
  if (!state) return null

  const trigger = map.deadTriggers.get(state)
  if (!trigger) return null

  const baseHit = map.direct.get(base)
  if (!baseHit) return null

  return [
    // First press: dead-key trigger. Nothing committed visually —
    // the accent doesn't land until the base letter arrives.
    { kind: 'key', keyId: trigger.keyId, layer: trigger.layer, typed: '' },
    // Second press: base letter. The composed cluster gets appended
    // to the demo text line (keeps the visual in sync with the font's
    // rendering of the cluster).
    { kind: 'key', keyId: baseHit.keyId, layer: baseHit.layer, typed: displayCluster },
  ]
}

// Module-private segmenter cache. `Intl.Segmenter` is ~0.5ms to
// instantiate on first use; reuse one per resolver call is fine.
let segmenter: Intl.Segmenter | null = null
function getSegmenter(): Intl.Segmenter | null {
  if (typeof Intl === 'undefined' || typeof Intl.Segmenter !== 'function') {
    return null
  }
  if (!segmenter) segmenter = new Intl.Segmenter(undefined, { granularity: 'grapheme' })
  return segmenter
}

/**
 * Resolve a whole phrase into a flat step list. Iterates over grapheme
 * clusters (not codepoints) so phrase authors can embed explicit NFD
 * forms like `'у\u0306'` and get the dead-key path even when a
 * precomposed character exists.
 *
 * Unreachable clusters are silently dropped but logged in dev.
 */
export function resolvePhrase(layout: LayoutData, phrase: string): Step[] {
  const steps: Step[] = []
  const seg = getSegmenter()
  const clusters: string[] = []
  if (seg) {
    for (const s of seg.segment(phrase)) clusters.push(s.segment)
  } else {
    // Fallback for ancient environments without Intl.Segmenter. Iterates
    // codepoints and re-joins base+mark pairs manually. Acceptable loss
    // of correctness for legacy browsers — modern targets use the path
    // above.
    const cps = Array.from(phrase)
    let i = 0
    while (i < cps.length) {
      const cp = cps[i]
      const next = cps[i + 1]
      if (next && COMBINING_MARK_TO_STATE[next]) {
        clusters.push(cp + next)
        i += 2
      } else {
        clusters.push(cp)
        i += 1
      }
    }
  }

  for (const cluster of clusters) {
    const stepList = resolveCluster(layout, cluster)
    if (stepList) {
      steps.push(...stepList)
    } else if (import.meta.env?.DEV) {
      // Per-cluster warning with hex codepoints so the phrase author
      // can tell whether they typo'd a char vs. used an unsupported mark.
      const hex = Array.from(cluster)
        .map((c) => `U+${c.codePointAt(0)!.toString(16).toUpperCase().padStart(4, '0')}`)
        .join(' ')
        // eslint-disable-next-line no-console
      console.warn(
        `[playback] cannot type cluster ${JSON.stringify(cluster)} (${hex}) on layout ${layout.name}`,
      )
    }
  }
  return steps
}

