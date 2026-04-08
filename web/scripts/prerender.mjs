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

// Translated meta content per locale
const META = {
  en: {
    title: 'Kirkouski Typographic Keyboard Layout — Polish & Russian Typography Symbols via AltGr',
    description: 'Custom keyboard layouts for Windows and macOS. Type em dashes, curly quotes, copyright symbols, euro signs, and 80+ typographic characters via AltGr on Polish and Russian keyboards.',
    ogTitle: 'Kirkouski Typographic Keyboard Layout',
    ogDescription: 'Polish & Russian keyboard layouts with 80+ typographic symbols via AltGr. Em dashes, curly quotes, copyright, euro, arrows, math symbols — all at your fingertips.',
    twitterDescription: 'Polish & Russian keyboard layouts with typographic symbols via AltGr. For Windows and macOS.',
  },
  pl: {
    title: 'Kirkouski Typographic — Polska typograficzna klawiatura z symbolami przez AltGr',
    description: 'Układy klawiatury dla Windows i macOS. Pauzy, cudzysłowy, znaki copyright, symbole walut i 80+ znaków typograficznych przez AltGr na polskiej i rosyjskiej klawiaturze.',
    ogTitle: 'Kirkouski Typographic — Typograficzna klawiatura',
    ogDescription: 'Polska i rosyjska klawiatura z 80+ symbolami typograficznymi przez AltGr. Pauzy, cudzysłowy, copyright, euro, strzałki — wszystko pod ręką.',
    twitterDescription: 'Polska i rosyjska klawiatura z symbolami typograficznymi przez AltGr. Dla Windows i macOS.',
  },
  ru: {
    title: 'Kirkouski Typographic — Типографская раскладка для польской и русской клавиатуры',
    description: 'Раскладки клавиатуры для Windows и macOS. Тире, кавычки, знак копирайта, символы валют и 80+ типографских символов через AltGr на польской и русской клавиатуре.',
    ogTitle: 'Kirkouski Typographic — Типографская раскладка',
    ogDescription: 'Польская и русская раскладка с 80+ типографскими символами через AltGr. Тире, кавычки, copyright, евро, стрелки — всё под рукой.',
    twitterDescription: 'Польская и русская раскладка с типографскими символами через AltGr. Для Windows и macOS.',
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
