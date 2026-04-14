// ==UserScript==
// @name         Szpargalka Sans — Polish pronunciation font injector
// @namespace    https://polish-typographic.com/
// @version      0.1.0
// @description  Forces Szpargalka Sans on web pages so Polish digraphs (sz, cz, rz, szcz, ch, …) render as Cyrillic pronunciation hints via OpenType ligatures. Toggle between "Polish pages only / Everywhere / Off" via the Tampermonkey menu.
// @author       Andrei Kirkouski
// @homepageURL  https://polish-typographic.com/fonts
// @match        *://*/*
// @resource     SZPARGALKA_FONT https://polish-typographic.com/fonts/SzpargalkaSans-Regular.ttf
// @grant        GM_getResourceText
// @grant        GM_addStyle
// @grant        GM_getValue
// @grant        GM_setValue
// @grant        GM_registerMenuCommand
// @run-at       document-start
// @license      MIT
// ==/UserScript==

(function () {
  'use strict'

  const MODES = {
    POLISH: 'polish',
    ALWAYS: 'always',
    OFF: 'off',
  }

  const mode = GM_getValue('mode', MODES.POLISH)

  // ── Menu (Tampermonkey popup) ─────────────────────────────────────
  // Each entry shows a ✓ next to the currently-active mode. Clicking
  // switches to that mode and reloads the current tab.
  function registerMenu() {
    const tick = (m) => (mode === m ? '✓ ' : '  ')
    GM_registerMenuCommand(
      tick(MODES.POLISH) + 'Polish pages only',
      () => setMode(MODES.POLISH),
    )
    GM_registerMenuCommand(
      tick(MODES.ALWAYS) + 'Everywhere',
      () => setMode(MODES.ALWAYS),
    )
    GM_registerMenuCommand(
      tick(MODES.OFF) + 'Off',
      () => setMode(MODES.OFF),
    )
  }

  function setMode(next) {
    GM_setValue('mode', next)
    location.reload()
  }

  registerMenu()

  if (mode === MODES.OFF) return

  // ── Polish detection ──────────────────────────────────────────────
  // Primary: <html lang> attribute (fast, runs at document-start).
  // Secondary: letter-density sniff of body text (runs after DOM ready,
  // catches Reddit/X/etc. that don't set lang).

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

  // ── Style injection ───────────────────────────────────────────────

  const fontUri = GM_getResourceText('SZPARGALKA_FONT')

  const css = `
    @font-face {
      font-family: 'Szpargalka Sans';
      src: url('${fontUri}') format('truetype');
      font-display: swap;
    }

    html.szpargalka-active * {
      font-family: 'Szpargalka Sans', sans-serif !important;
      /* letter-spacing disables OpenType ligatures — force it to 0
         so GSUB substitutions (sz→ш, cz→ч, szcz→щ, …) fire correctly */
      letter-spacing: 0 !important;
      font-feature-settings: 'liga' 1, 'dlig' 1 !important;
    }

    html.szpargalka-active :is(
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

  GM_addStyle(css)

  // ── Activation ────────────────────────────────────────────────────
  // In always-mode we activate immediately. In polish-mode we do a fast
  // lang check at document-start, then a fallback text-density check once
  // the body exists — gives us a near-instant hit on well-tagged sites
  // (Wikipedia, government pages) and a second chance on sloppy ones.

  function activate() {
    document.documentElement.classList.add('szpargalka-active')
  }

  function deactivate() {
    document.documentElement.classList.remove('szpargalka-active')
  }

  if (mode === MODES.ALWAYS) {
    activate()
  } else if (mode === MODES.POLISH) {
    if (langIsPolish()) {
      activate()
    } else {
      // Wait for body, then re-check via text density
      const check = () => {
        if (langIsPolish() || textLooksPolish()) activate()
        else deactivate()
      }
      if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', check, { once: true })
      } else {
        check()
      }
    }
  }
})()
