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
const OUT_PATH = resolve(REPO_ROOT, 'web/public/og-image.png');

const FONT_PLACEHOLDERS = {
  __DM_SERIF_DISPLAY_REGULAR__: 'DMSerifDisplay-Regular.ttf',
  __DM_SERIF_DISPLAY_ITALIC__: 'DMSerifDisplay-Italic.ttf',
  __DM_SANS_REGULAR__: 'DMSans-Regular.ttf',
  __JETBRAINS_MONO_REGULAR__: 'JetBrainsMono-Regular.ttf',
};

const FONTS_OG_TEMPLATE = resolve(__dir, '../templates/og-fonts-template.html');
const FONTS_OG_OUT = resolve(REPO_ROOT, 'web/public/og-fonts.png');
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
  // VERSION may be `0.3` or `0.3.1` — show major.minor for compactness.
  const versionLabel = `v${version.split('.').slice(0, 2).join('.')}`;

  const html = inlineFonts(readFileSync(TEMPLATE, 'utf-8'));

  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({
      viewport: { width: 1200, height: 630 },
      // No deviceScaleFactor — output must match the 1200×630 og:image meta.
    });
    // setContent loads the HTML inline; no file:// URL needed for hermetic
    // rendering, and base64 data URIs work without any web origin.
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
    writeFileSync(OUT_PATH, png);
    console.log(`  og-image.png  ${png.length.toLocaleString()} bytes  (${versionLabel})`);
    return OUT_PATH;
  } finally {
    await browser.close();
  }
}

export async function buildFontsOgImage() {
  let html = readFileSync(FONTS_OG_TEMPLATE, 'utf-8');
  for (const [placeholder, filepath] of Object.entries(FONTS_OG_PLACEHOLDERS)) {
    try {
      const buf = readFileSync(filepath);
      html = html.split(placeholder).join(`data:font/ttf;base64,${buf.toString('base64')}`);
    } catch {
      console.log(`  SKIP og-fonts.png: ${filepath} not found (build fonts first)`);
      return null;
    }
  }

  const browser = await chromium.launch();
  try {
    const page = await browser.newPage({ viewport: { width: 1200, height: 630 } });
    await page.setContent(html, { waitUntil: 'load' });
    await page.evaluate(() => document.fonts.ready);
    const png = await page.screenshot({
      type: 'png',
      omitBackground: false,
      clip: { x: 0, y: 0, width: 1200, height: 630 },
    });
    writeFileSync(FONTS_OG_OUT, png);
    console.log(`  og-fonts.png  ${png.length.toLocaleString()} bytes`);
    return FONTS_OG_OUT;
  } finally {
    await browser.close();
  }
}
