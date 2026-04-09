/**
 * Post-build prerender script.
 * Uses Vite's SSR pipeline to render the Vue app for each locale,
 * then injects the HTML into the built index.html template.
 *
 * Run after `vite build`: node scripts/prerender.mjs
 */
import { createServer } from 'vite'
import { readFileSync, writeFileSync, mkdirSync } from 'fs'
import { resolve, dirname } from 'path'
import { fileURLToPath } from 'url'

const __dirname = dirname(fileURLToPath(import.meta.url))
const ROOT = resolve(__dirname, '..')
const DIST = resolve(ROOT, 'dist')
const BASE_URL = 'https://polish-typographic-keyboard-layout.pages.dev'

const LOCALES = [
  { code: 'en', path: '/', lang: 'en', ogLocale: 'en_US' },
  { code: 'pl', path: '/pl/', lang: 'pl', ogLocale: 'pl_PL' },
  { code: 'ru', path: '/ru/', lang: 'ru', ogLocale: 'ru_RU' },
]

// Translated meta content per locale. The descriptions lead with the
// real differentiator (US+POL = type Polish on Windows without adding
// Polish as a separate input language) instead of the generic "lots of
// typographic symbols" framing.
const META = {
  en: {
    title: 'Kirkouski Typographic — Polish characters on AltGr without an extra input language',
    description: 'Type Polish characters via AltGr without adding Polish as a separate input language on Windows. Plus em dashes, curly quotes, currency, arrows, math, and 80+ typographic symbols. Polish, Russian, and US+POL variants for Windows and macOS.',
    ogTitle: 'Kirkouski Typographic — Polish characters without an extra input language',
    ogDescription: 'Type Polish characters on Windows without adding Polish to your input languages — US+POL Typographic registers under English (US). Plus em dashes, curly quotes, math, and 80+ symbols on AltGr.',
    twitterDescription: 'Type Polish characters on Windows without adding Polish to your input languages — US+POL Typographic registers under English (US). Plus em dashes, curly quotes, math, and 80+ symbols on AltGr.',
  },
  pl: {
    title: 'Kirkouski Typographic — polskie znaki na AltGr bez dodatkowego języka wprowadzania',
    description: 'Pisz polskie znaki przez AltGr bez dodawania polskiego jako osobnego języka wprowadzania w Windows. Dodatkowo pauzy, cudzysłowy, waluty, strzałki, znaki matematyczne i 80+ symboli typograficznych. Warianty polski, rosyjski i US+POL dla Windows i macOS.',
    ogTitle: 'Kirkouski Typographic — polskie znaki bez dodatkowego języka wprowadzania',
    ogDescription: 'Pisz polskie znaki w Windows bez dodawania polskiego do języków wprowadzania — układ US+POL Typographic rejestruje się pod angielskim (US). Plus pauzy, cudzysłowy, matematyka i 80+ symboli na AltGr.',
    twitterDescription: 'Pisz polskie znaki w Windows bez dodawania polskiego do języków wprowadzania — układ US+POL Typographic rejestruje się pod angielskim (US). Plus pauzy, cudzysłowy, matematyka i 80+ symboli na AltGr.',
  },
  ru: {
    title: 'Kirkouski Typographic — польские символы на AltGr без отдельного языка ввода',
    description: 'Печатай польские символы через AltGr без добавления польского как отдельного языка ввода в Windows. Плюс тире, кавычки, валюты, стрелки, математика и 80+ типографских символов. Польский, русский и US+POL для Windows и macOS.',
    ogTitle: 'Kirkouski Typographic — польские символы без отдельного языка ввода',
    ogDescription: 'Печатай польские символы в Windows без добавления польского в языки ввода — раскладка US+POL Typographic регистрируется под английским (US). Плюс тире, кавычки, математика и 80+ символов на AltGr.',
    twitterDescription: 'Печатай польские символы в Windows без добавления польского в языки ввода — раскладка US+POL Typographic регистрируется под английским (US). Плюс тире, кавычки, математика и 80+ символов на AltGr.',
  },
}

// Hreflang links to inject into <head>
const HREFLANG = LOCALES.map(l =>
  `<link rel="alternate" hreflang="${l.lang}" href="${BASE_URL}${l.path}" />`
).concat(`<link rel="alternate" hreflang="x-default" href="${BASE_URL}/" />`).join('\n    ')

async function main() {
  console.log('Pre-rendering locale pages...')

  // Start Vite in SSR mode to load Vue SFCs in Node
  const vite = await createServer({
    root: ROOT,
    server: { middlewareMode: true },
    appType: 'custom',
    logLevel: 'warn',
  })

  const { render } = await vite.ssrLoadModule('/src/entry-server.ts')
  const template = readFileSync(resolve(DIST, 'index.html'), 'utf-8')

  for (const locale of LOCALES) {
    const meta = META[locale.code]
    const appHtml = await render(locale.code)

    let html = template
      // Inject SSR content
      .replace('<div id="app"></div>', `<div id="app">${appHtml}</div>`)
      // Set <html lang>
      .replace('<html lang="en">', `<html lang="${locale.lang}">`)
      // Title
      .replace(/<title>[^<]*<\/title>/, `<title>${meta.title}</title>`)
      // Meta description
      .replace(
        /<meta name="description" content="[^"]*"/,
        `<meta name="description" content="${meta.description}"`
      )
      // OG tags
      .replace(
        /<meta property="og:title" content="[^"]*"/,
        `<meta property="og:title" content="${meta.ogTitle}"`
      )
      .replace(
        /<meta property="og:description" content="[^"]*"/,
        `<meta property="og:description" content="${meta.ogDescription}"`
      )
      .replace(
        /<meta property="og:url" content="[^"]*"/,
        `<meta property="og:url" content="${BASE_URL}${locale.path}"`
      )
      .replace(
        /<meta property="og:locale" content="[^"]*"/,
        `<meta property="og:locale" content="${locale.ogLocale}"`
      )
      // Twitter
      .replace(
        /<meta name="twitter:title" content="[^"]*"/,
        `<meta name="twitter:title" content="${meta.ogTitle}"`
      )
      .replace(
        /<meta name="twitter:description" content="[^"]*"/,
        `<meta name="twitter:description" content="${meta.twitterDescription}"`
      )
      // Canonical
      .replace(
        /<link rel="canonical" href="[^"]*"/,
        `<link rel="canonical" href="${BASE_URL}${locale.path}"`
      )
      // Add hreflang links before </head>
      .replace('</head>', `    ${HREFLANG}\n  </head>`)

    const outDir = locale.code === 'en' ? DIST : resolve(DIST, locale.code)
    mkdirSync(outDir, { recursive: true })
    writeFileSync(resolve(outDir, 'index.html'), html)
    console.log(`  ${locale.code} -> ${locale.path} (${appHtml.length} chars SSR)`)
  }

  await vite.close()
  console.log('Done.')
}

main().catch(e => {
  console.error('Prerender failed:', e)
  process.exit(1)
})
