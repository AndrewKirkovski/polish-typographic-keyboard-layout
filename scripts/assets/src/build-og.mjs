// Render scripts/assets/templates/og-template.html to a 1200×630 PNG via
// Playwright (headless Chromium).
//
// Hermetic font handling: the template declares @font-face rules with
// `__PLACEHOLDER__` URLs. We read the matching .ttf files from disk, base64
// them, and substring-replace before handing the HTML to Playwright. No
// network call, no system-font fallback drift, identical pixels in CI and
// on a dev box. The version label comes from the repo-root VERSION file
// so the OG image stays in lockstep with releases.
//
// Output is rendered at exactly 1200×630 pixels (no deviceScaleFactor) to
// match the og:image:width / og:image:height meta tags in web/index.html.
import { chromium } from 'playwright';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dir = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dir, '../../..');
const TEMPLATE = resolve(__dir, '../templates/og-template.html');
const FONTS_DIR = resolve(__dir, '../fonts');
const VERSION_FILE = resolve(REPO_ROOT, 'VERSION');
const OUT_DIR = resolve(REPO_ROOT, 'web/public');

const OG_LOCALES = {
  en: {
    subtitle: 'Typography symbols at your fingertips &mdash; for Polish and Russian keyboards',
    cta: 'Download Free &mdash; Windows &amp; macOS',
    platforms: 'Windows &bull; macOS &bull; Open Source',
  },
  pl: {
    subtitle: 'Symbole typograficzne pod palcami &mdash; dla polskiej i rosyjskiej klawiatury',
    cta: 'Pobierz za darmo &mdash; Windows i macOS',
    platforms: 'Windows &bull; macOS &bull; Open Source',
  },
  ru: {
    subtitle: 'Типографские символы под рукой &mdash; для польской и русской раскладки',
    cta: 'Скачать бесплатно &mdash; Windows и macOS',
    platforms: 'Windows &bull; macOS &bull; Open Source',
  },
};

const FONT_PLACEHOLDERS = {
  __DM_SERIF_DISPLAY_REGULAR__: 'DMSerifDisplay-Regular.ttf',
  __DM_SERIF_DISPLAY_ITALIC__: 'DMSerifDisplay-Italic.ttf',
  __DM_SANS_REGULAR__: 'DMSans-Regular.ttf',
  __JETBRAINS_MONO_REGULAR__: 'JetBrainsMono-Regular.ttf',
};

const FONTS_OG_TEMPLATE = resolve(__dir, '../templates/og-fonts-template.html');
const FONTS_DIST = resolve(REPO_ROOT, 'dist');

const FONTS_OG_PLACEHOLDERS = {
  __DM_SERIF_DISPLAY_ITALIC__: resolve(FONTS_DIR, 'DMSerifDisplay-Italic.ttf'),
  __NOTO_SANS_REGULAR__: resolve(FONTS_DIR, 'NotoSans-Regular.ttf'),
  __SZPARGALKA_SANS__: resolve(FONTS_DIST, 'SzpargalkaSans-Regular.ttf'),
  __POLISH_PHONETICS_SANS__: resolve(FONTS_DIST, 'PolishPhoneticsSans-Regular.ttf'),
};

function inlineFonts(html) {
  let out = html;
  for (const [placeholder, filename] of Object.entries(FONT_PLACEHOLDERS)) {
    const buf = readFileSync(resolve(FONTS_DIR, filename));
    const dataUri = `data:font/ttf;base64,${buf.toString('base64')}`;
    out = out.split(placeholder).join(dataUri);
  }
  return out;
}

export async function buildOgImage() {
  const version = readFileSync(VERSION_FILE, 'utf-8').trim();
  const versionLabel = `v${version.split('.').slice(0, 2).join('.')}`;

  const baseHtml = inlineFonts(readFileSync(TEMPLATE, 'utf-8'));

  const browser = await chromium.launch();
  try {
    for (const [locale, strings] of Object.entries(OG_LOCALES)) {
      // Replace the hardcoded English text with the locale-specific strings.
      const html = baseHtml
        .replace('Typography symbols at your fingertips &mdash; for Polish and Russian keyboards', strings.subtitle)
        .replace('Download Free &mdash; Windows &amp; macOS', strings.cta)
        .replace('Windows &bull; macOS &bull; Open Source', strings.platforms);

      const page = await browser.newPage({
        viewport: { width: 1200, height: 630 },
      });
      await page.setContent(html, { waitUntil: 'load' });
      await page.evaluate(() => document.fonts.ready);
      await page.evaluate((label) => {
        const el = document.getElementById('version');
        if (el) el.textContent = label;
      }, versionLabel);
      const png = await page.screenshot({
        type: 'png',
        omitBackground: false,
        clip: { x: 0, y: 0, width: 1200, height: 630 },
      });
      const outPath = resolve(OUT_DIR, `og-image-${locale}.png`);
      writeFileSync(outPath, png);
      console.log(`  og-image-${locale}.png  ${png.length.toLocaleString()} bytes  (${versionLabel})`);
      await page.close();
    }
  } finally {
    await browser.close();
  }
}

const FONTS_OG_LOCALES = {
  en: {
    subtitle: 'Polish pronunciation fonts &mdash; Cyrillic &amp; IPA hints',
    footer: 'polish-typographic.com/fonts',
  },
  pl: {
    subtitle: 'Czcionki wymowy polskiej &mdash; podpowiedzi cyrylicą i IPA',
    footer: 'polish-typographic.com/pl/fonts',
  },
  ru: {
    subtitle: 'Шрифты произношения польского &mdash; кириллица и IPA',
    footer: 'polish-typographic.com/ru/fonts',
  },
};

export async function buildFontsOgImage() {
  let baseHtml = readFileSync(FONTS_OG_TEMPLATE, 'utf-8');
  for (const [placeholder, filepath] of Object.entries(FONTS_OG_PLACEHOLDERS)) {
    try {
      const buf = readFileSync(filepath);
      baseHtml = baseHtml.split(placeholder).join(`data:font/ttf;base64,${buf.toString('base64')}`);
    } catch {
      console.log(`  SKIP og-fonts: ${filepath} not found (build fonts first)`);
      return null;
    }
  }

  const browser = await chromium.launch();
  try {
    for (const [locale, strings] of Object.entries(FONTS_OG_LOCALES)) {
      const html = baseHtml
        // Template uses literal em dash (U+2014), not &mdash; entity
        .replace('Polish pronunciation fonts \u2014 Cyrillic &amp; IPA hints', strings.subtitle)
        .replace('polish-typographic.com/fonts', strings.footer);

      const page = await browser.newPage({ viewport: { width: 1200, height: 630 } });
      await page.setContent(html, { waitUntil: 'load' });
      await page.evaluate(() => document.fonts.ready);
      const png = await page.screenshot({
        type: 'png',
        omitBackground: false,
        clip: { x: 0, y: 0, width: 1200, height: 630 },
      });
      const outPath = resolve(OUT_DIR, `og-fonts-${locale}.png`);
      writeFileSync(outPath, png);
      console.log(`  og-fonts-${locale}.png  ${png.length.toLocaleString()} bytes`);
      await page.close();
    }
  } finally {
    await browser.close();
  }
}
