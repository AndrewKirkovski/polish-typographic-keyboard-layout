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
const BASE_URL = 'https://polish-typographic.com'
const APP_VERSION = readFileSync(resolve(ROOT, '..', 'VERSION'), 'utf-8').trim()

const LOCALES = [
  { code: 'en', path: '/', lang: 'en', ogLocale: 'en_US' },
  { code: 'pl', path: '/pl/', lang: 'pl', ogLocale: 'pl_PL' },
  { code: 'ru', path: '/ru/', lang: 'ru', ogLocale: 'ru_RU' },
]

const FONT_PAGES = [
  { code: 'en', path: '/fonts/', lang: 'en', ogLocale: 'en_US' },
  { code: 'pl', path: '/pl/fonts/', lang: 'pl', ogLocale: 'pl_PL' },
  { code: 'ru', path: '/ru/fonts/', lang: 'ru', ogLocale: 'ru_RU' },
]

const FONT_META = {
  en: {
    title: 'Szpargalka Sans — Polish pronunciation fonts with Cyrillic and IPA hints',
    description: 'Free fonts that show how to pronounce Polish digraphs — Cyrillic hints for Russian speakers, IPA for everyone. Type Polish text and see pronunciation above each letter combination.',
  },
  pl: {
    title: 'Szpargałka Sans — czcionki wymowy polskiej z podpowiedziami cyrylicą i IPA',
    description: 'Darmowe czcionki pokazujące wymowę polskich dwuznaków — podpowiedzi cyrylicą dla rosyjskojęzycznych, IPA dla wszystkich. Pisz po polsku i zobacz wymowę nad każdym połączeniem liter.',
  },
  ru: {
    title: 'Шпаргалка Sans — шрифты произношения польского с кириллицей и IPA',
    description: 'Бесплатные шрифты, показывающие произношение польских буквосочетаний — кириллицей для русскоязычных, IPA для всех. Пишите по-польски и видите произношение над каждой комбинацией букв.',
  },
}

// Translated meta content per locale.
const META = {
  en: {
    title: 'Kirkouski Typographic — Polish characters on AltGr without an extra input language',
    description: 'Type Polish characters via AltGr without adding Polish as a separate input language on Windows. Plus em dashes, curly quotes, currency, arrows, math, and 80+ typographic symbols. Polish, Russian, and US+POL variants for Windows and macOS.',
    keywords: 'keyboard layout, typographic, Polish keyboard, AltGr, em dash, curly quotes, Windows keyboard layout, macOS keylayout, Birman, Kirkouski, Polish characters, US keyboard, typographic symbols',
    ogTitle: 'Kirkouski Typographic — Polish characters without an extra input language',
    ogDescription: 'Type Polish characters on Windows without adding Polish to your input languages — US+POL Typographic registers under English (US). Plus em dashes, curly quotes, math, and 80+ symbols on AltGr.',
    twitterDescription: 'Type Polish characters on Windows without adding Polish to your input languages — US+POL Typographic registers under English (US). Plus em dashes, curly quotes, math, and 80+ symbols on AltGr.',
  },
  pl: {
    title: 'Kirkouski Typographic — polskie znaki na AltGr bez dodatkowego języka wprowadzania',
    description: 'Pisz polskie znaki przez AltGr bez dodawania polskiego jako osobnego języka wprowadzania w Windows. Dodatkowo pauzy, cudzysłowy, waluty, strzałki, znaki matematyczne i 80+ symboli typograficznych. Warianty polski, rosyjski i US+POL dla Windows i macOS.',
    keywords: 'układ klawiatury, typograficzny, polskie znaki, ogonki, AltGr, półpauza, cudzysłów drukarski, klawiatura Windows, macOS, Birman, Kirkouski, Polish Programmers, QWERTY',
    ogTitle: 'Kirkouski Typographic — polskie znaki bez dodatkowego języka wprowadzania',
    ogDescription: 'Pisz polskie znaki w Windows bez dodawania polskiego do języków wprowadzania — układ US+POL Typographic rejestruje się pod angielskim (US). Plus pauzy, cudzysłowy, matematyka i 80+ symboli na AltGr.',
    twitterDescription: 'Pisz polskie znaki w Windows bez dodawania polskiego do języków wprowadzania — układ US+POL Typographic rejestruje się pod angielskim (US). Plus pauzy, cudzysłowy, matematyka i 80+ symboli na AltGr.',
  },
  ru: {
    title: 'Kirkouski Typographic — польские символы на AltGr без отдельного языка ввода',
    description: 'Печатай польские символы через AltGr без добавления польского как отдельного языка ввода в Windows. Плюс тире, кавычки, валюты, стрелки, математика и 80+ типографских символов. Польский, русский и US+POL для Windows и macOS.',
    keywords: 'раскладка клавиатуры, типографская, польские символы, AltGr, тире, кавычки, Windows раскладка, macOS, Birman, Kirkouski, ЙЦУКЕН, типографические символы',
    ogTitle: 'Kirkouski Typographic — польские символы без отдельного языка ввода',
    ogDescription: 'Печатай польские символы в Windows без добавления польского в языки ввода — раскладка US+POL Typographic регистрируется под английским (US). Плюс тире, кавычки, математика и 80+ символов на AltGr.',
    twitterDescription: 'Печатай польские символы в Windows без добавления польского в языки ввода — раскладка US+POL Typographic регистрируется под английским (US). Плюс тире, кавычки, математика и 80+ символов на AltGr.',
  },
}

// Per-locale JSON-LD structured data: SoftwareApplication + FAQPage.
// Generated per locale and injected into <head> at build time so each
// locale page has matching structured data in its own language.
const FAQ = {
  en: [
    { q: 'How do I type an em dash on a Polish keyboard in Windows?', a: 'Press AltGr + - (minus key). The Kirkouski Typographic layout puts em dash, en dash, and other typographic symbols directly on AltGr — no Alt codes needed.' },
    { q: 'How do I type Polish characters on a US keyboard without switching layouts?', a: 'Install the US+POL Typographic variant. It registers under English (US) so Win+Space stays clean — Polish ogonki (ą ć ę ł ń ó ś ź ż) are on AltGr.' },
    { q: 'Does this work with Polish Programmers QWERTY?', a: 'Yes. The Polish variant is built on the standard Polish Programmers QWERTY layout. Typographic symbols are added on AltGr and Shift+AltGr layers only.' },
    { q: 'Will this add a new input language to Win+Space?', a: 'The US+POL variant does not — it registers under English (US). The standard Polish and Russian variants do add their respective input language.' },
    { q: 'Does this work on macOS?', a: 'Yes. Download the .bundle, place it in ~/Library/Keyboard Layouts/, clear the quarantine xattr, and log out/in. macOS keyboard layouts are not tied to system language.' },
  ],
  pl: [
    { q: 'Jak wpisać pauzę na polskiej klawiaturze w Windows?', a: 'Naciśnij AltGr + - (klawisz minus). Układ Kirkouski Typographic umieszcza pauzę, półpauzę i inne symbole typograficzne bezpośrednio na AltGr — bez kodów Alt.' },
    { q: 'Jak pisać polskie znaki na klawiaturze US bez przełączania układów?', a: 'Zainstaluj wariant US+POL Typographic. Rejestruje się pod angielskim (US), więc Win+Space pozostaje krótkie — ogonki (ą ć ę ł ń ó ś ź ż) są na AltGr.' },
    { q: 'Czy działa z układem Polish Programmers QWERTY?', a: 'Tak. Wariant polski bazuje na standardowym układzie Polish Programmers QWERTY. Symbole typograficzne dodane są wyłącznie na warstwy AltGr i Shift+AltGr.' },
    { q: 'Czy doda nowy język wprowadzania do Win+Space?', a: 'Wariant US+POL nie — rejestruje się pod angielskim (US). Standardowe warianty polski i rosyjski dodają odpowiedni język wprowadzania.' },
    { q: 'Czy działa na macOS?', a: 'Tak. Pobierz .bundle, umieść go w ~/Library/Keyboard Layouts/, usuń kwarantannę xattr i wyloguj/zaloguj się. Układy klawiatury macOS nie są powiązane z językiem systemu.' },
  ],
  ru: [
    { q: 'Как набрать длинное тире на польской клавиатуре в Windows?', a: 'Нажмите AltGr + - (клавиша минус). Раскладка Kirkouski Typographic размещает тире, короткое тире и другие типографские символы прямо на AltGr — без Alt-кодов.' },
    { q: 'Как печатать польские символы на клавиатуре US без переключения раскладок?', a: 'Установите вариант US+POL Typographic. Он регистрируется под английским (US), поэтому Win+Space остаётся коротким — огонки (ą ć ę ł ń ó ś ź ż) на AltGr.' },
    { q: 'Работает ли с раскладкой Polish Programmers QWERTY?', a: 'Да. Польский вариант построен на стандартной Polish Programmers QWERTY. Типографские символы добавлены только на слои AltGr и Shift+AltGr.' },
    { q: 'Добавит ли новый язык ввода в Win+Space?', a: 'Вариант US+POL не добавит — регистрируется под английским (US). Стандартные польский и русский варианты добавляют свой язык ввода.' },
    { q: 'Работает ли на macOS?', a: 'Да. Скачайте .bundle, поместите в ~/Library/Keyboard Layouts/, снимите карантин xattr и перезайдите. Раскладки macOS не привязаны к языку системы.' },
  ],
}

const APP_SCHEMA = {
  en: { name: 'Kirkouski Typographic Keyboard Layout', description: 'Keyboard layout that registers under English (US) so you can type Polish characters via AltGr without adding Polish as a separate input language on Windows. Includes em dashes, curly quotes, currency symbols, arrows, math, and 80+ typographic characters. Polish, Russian, and US+POL variants for Windows and macOS.' },
  pl: { name: 'Kirkouski Typographic — układ klawiatury', description: 'Układ klawiatury rejestrujący się pod angielskim (US), dzięki czemu polskie znaki są dostępne przez AltGr bez dodawania polskiego jako osobnego języka wprowadzania. Pauzy, cudzysłowy, waluty, strzałki, matematyka i 80+ symboli typograficznych. Warianty polski, rosyjski i US+POL dla Windows i macOS.' },
  ru: { name: 'Kirkouski Typographic — раскладка клавиатуры', description: 'Раскладка, регистрирующаяся под английским (US), позволяющая набирать польские символы через AltGr без добавления польского как отдельного языка ввода. Тире, кавычки, валюты, стрелки, математика и 80+ типографских символов. Польский, русский и US+POL для Windows и macOS.' },
}

function buildJsonLd(locale, path) {
  const app = APP_SCHEMA[locale]
  const faq = FAQ[locale]
  const softwareApp = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: app.name,
    description: app.description,
    inLanguage: locale,
    applicationCategory: 'UtilitiesApplication',
    operatingSystem: 'Windows, macOS',
    offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' },
    author: { '@type': 'Person', name: 'Andrew Kirkouski' },
    license: 'https://opensource.org/licenses/MIT',
    url: `${BASE_URL}${path}`,
    downloadUrl: 'https://github.com/AndrewKirkovski/polish-typographic-keyboard-layout/releases/latest',
    softwareVersion: APP_VERSION,
    isBasedOn: { '@type': 'SoftwareApplication', name: 'Ilya Birman Typography Layout', url: 'https://ilyabirman.ru/typography-layout/' },
  }
  const faqPage = {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    mainEntity: faq.map(f => ({
      '@type': 'Question',
      name: f.q,
      acceptedAnswer: { '@type': 'Answer', text: f.a },
    })),
  }
  return `<script type="application/ld+json">\n    ${JSON.stringify(softwareApp)}\n    </script>\n    <script type="application/ld+json">\n    ${JSON.stringify(faqPage)}\n    </script>`
}

function buildFontJsonLd(locale, path) {
  const fm = FONT_META[locale]
  const app = {
    '@context': 'https://schema.org',
    '@type': 'SoftwareApplication',
    name: 'Szpargalka Sans',
    description: fm.description,
    inLanguage: locale,
    applicationCategory: 'DesignApplication',
    operatingSystem: 'Windows, macOS, Linux',
    offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' },
    author: { '@type': 'Person', name: 'Andrew Kirkouski' },
    license: 'https://opensource.org/licenses/MIT',
    url: `${BASE_URL}${path}`,
  }
  const breadcrumbs = {
    '@context': 'https://schema.org',
    '@type': 'BreadcrumbList',
    itemListElement: [
      { '@type': 'ListItem', position: 1, name: 'Home', item: `${BASE_URL}${locale === 'en' ? '/' : `/${locale}/`}` },
      { '@type': 'ListItem', position: 2, name: fm.title.split('—')[0].trim(), item: `${BASE_URL}${path}` },
    ],
  }
  return `<script type="application/ld+json">\n    ${JSON.stringify(app)}\n    </script>\n    <script type="application/ld+json">\n    ${JSON.stringify(breadcrumbs)}\n    </script>`
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
      // Per-locale OG image
      .replace(/og-image-en\.png/g, `og-image-${locale.code}.png`)
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
      // Per-locale keywords
      .replace(
        /<meta name="keywords" content="[^"]*"/,
        `<meta name="keywords" content="${meta.keywords}"`
      )
      // Per-locale JSON-LD (replaces the placeholder comment in index.html)
      .replace(
        '<!-- JSON-LD structured data injected per-locale by prerender.mjs -->',
        buildJsonLd(locale.code, locale.path)
      )
      // Add hreflang links before </head>
      .replace('</head>', `    ${HREFLANG}\n  </head>`)

    const outDir = locale.code === 'en' ? DIST : resolve(DIST, locale.code)
    mkdirSync(outDir, { recursive: true })
    writeFileSync(resolve(outDir, 'index.html'), html)
    console.log(`  ${locale.code} -> ${locale.path} (${appHtml.length} chars SSR)`)
  }

  // Generate /fonts/ pages — same SSR app, the component detects /fonts in pathname
  const FONT_HREFLANG = FONT_PAGES.map(l =>
    `<link rel="alternate" hreflang="${l.lang}" href="${BASE_URL}${l.path}" />`
  ).concat(`<link rel="alternate" hreflang="x-default" href="${BASE_URL}/fonts/" />`).join('\n    ')

  for (const fp of FONT_PAGES) {
    const fm = FONT_META[fp.code]
    const appHtml = await render(fp.code, 'fonts')

    let html = template
      .replace('<div id="app"></div>', `<div id="app">${appHtml}</div>`)
      .replace('<html lang="en">', `<html lang="${fp.lang}">`)
      .replace(/<title>[^<]*<\/title>/, `<title>${fm.title}</title>`)
      .replace(/<meta name="description" content="[^"]*"/, `<meta name="description" content="${fm.description}"`)
      .replace(/<meta property="og:title" content="[^"]*"/, `<meta property="og:title" content="${fm.title}"`)
      .replace(/<meta property="og:description" content="[^"]*"/, `<meta property="og:description" content="${fm.description}"`)
      .replace(/<meta property="og:url" content="[^"]*"/, `<meta property="og:url" content="${BASE_URL}${fp.path}"`)
      .replace(/<meta property="og:locale" content="[^"]*"/, `<meta property="og:locale" content="${fp.ogLocale}"`)
      .replace(/og-image-en\.png/g, `og-fonts-${fp.code}.png`)
      .replace(/<meta name="twitter:title" content="[^"]*"/, `<meta name="twitter:title" content="${fm.title}"`)
      .replace(/<meta name="twitter:description" content="[^"]*"/, `<meta name="twitter:description" content="${fm.description}"`)
      .replace(/<link rel="canonical" href="[^"]*"/, `<link rel="canonical" href="${BASE_URL}${fp.path}"`)
      // Per-locale keywords (reuse main locale keywords for fonts pages)
      .replace(
        /<meta name="keywords" content="[^"]*"/,
        `<meta name="keywords" content="${META[fp.code].keywords}, pronunciation font, Szpargalka Sans"`
      )
      // Per-locale JSON-LD (font-specific SoftwareApplication + BreadcrumbList)
      .replace(
        '<!-- JSON-LD structured data injected per-locale by prerender.mjs -->',
        buildFontJsonLd(fp.code, fp.path)
      )
      .replace('</head>', `    ${FONT_HREFLANG}\n  </head>`)

    const outDir = fp.code === 'en' ? resolve(DIST, 'fonts') : resolve(DIST, fp.code, 'fonts')
    mkdirSync(outDir, { recursive: true })
    writeFileSync(resolve(outDir, 'index.html'), html)
    console.log(`  ${fp.code} -> ${fp.path} (${appHtml.length} chars SSR) [fonts]`)
  }

  await vite.close()
  console.log('Done.')
}

main().catch(e => {
  console.error('Prerender failed:', e)
  process.exit(1)
})
