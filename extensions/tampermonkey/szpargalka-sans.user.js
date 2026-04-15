// ==UserScript==
// @name         Szpargalka Sans — Polish pronunciation font injector
// @namespace    https://polish-typographic.com/
// @version      0.2.0
// @description  Forces Szpargalka Sans on web pages so Polish digraphs (sz, cz, rz, szcz, ch, …) render as Cyrillic pronunciation hints via OpenType ligatures. Ships disabled — toggle on/off via the Tampermonkey menu.
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

  // Binary toggle — the script ships disabled and only lights up when the
  // user explicitly flips it on via the Tampermonkey menu.
  const enabled = GM_getValue('enabled', false)

  // ── Menu (Tampermonkey popup) ─────────────────────────────────────
  // Single entry that shows the current state and flips it on click.
  // Changes take effect after reload, which Tampermonkey does for us.
  GM_registerMenuCommand(
    (enabled ? '✓ ' : '  ') + 'Szpargalka Sans: ' + (enabled ? 'On' : 'Off'),
    () => {
      GM_setValue('enabled', !enabled)
      location.reload()
    },
  )

  if (!enabled) return

  // ── Style injection ───────────────────────────────────────────────

  const fontUri = GM_getResourceText('SZPARGALKA_FONT')

  const css = `
    @font-face {
      font-family: 'Szpargalka Sans';
      src: url('${fontUri}') format('truetype');
      font-display: swap;
    }

    * {
      font-family: 'Szpargalka Sans', sans-serif !important;
      /* letter-spacing disables OpenType ligatures — force it to 0
         so GSUB substitutions (sz→ш, cz→ч, szcz→щ, …) fire correctly */
      letter-spacing: 0 !important;
      font-feature-settings: 'liga' 1, 'dlig' 1 !important;
    }

    :is(
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

  GM_addStyle(css)
})()
