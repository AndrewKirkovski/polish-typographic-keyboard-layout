// Render DMG assets for the macOS DMG build.
//
// Outputs, per language {en,pl,ru}, committed under assets/dmg/:
//   background-<lang>.png       600×400 PNG (1x — matches the DMG window
//                               at logical size so Finder opens the window
//                               at 600×400 points instead of 600×400 pixels
//                               at 2x density, which would make the window
//                               oversized on Retina).
//   background-<lang>@2x.png    1200×800 PNG (2x — crisp rep for Retina
//                               displays). build_dmg.py combines the pair
//                               into a multi-rep TIFF via `tiffutil
//                               -cathidpicheck` on macOS CI, which is what
//                               Finder reads to pick the right rep for the
//                               current display scale factor.
//   readme-<lang>.pdf           A5 portrait PDF.
//
// Mirrors the hermetic-rendering idioms from build-og.mjs:
//   - chromium.launch() once, reuse across locales
//   - Font files read from disk, base64 inlined via placeholder swaps
//   - setContent + document.fonts.ready before screenshot / pdf
//   - explicit clip for PNG screenshots
//
// Placeholder names in the strings dict match the HTML literally
// (__STEP1__, __SECTION_INSTALL_TITLE__, etc.) so the substitution is
// a trivial split().join() — no camelCase conversion indirection.
import { chromium } from 'playwright';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const __dir = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dir, '../../..');
const FONTS_DIR = resolve(__dir, '../fonts');
const TEMPLATES_DIR = resolve(__dir, '../templates');
const OUT_DIR = resolve(ROOT, 'assets/dmg');

const FONT_PLACEHOLDERS = {
  __DM_SERIF_DISPLAY_REGULAR__: 'DMSerifDisplay-Regular.ttf',
  __DM_SANS_REGULAR__: 'DMSans-Regular.ttf',
  __JETBRAINS_MONO_REGULAR__: 'JetBrainsMono-Regular.ttf',
  __NOTO_SANS_REGULAR__: 'NotoSans-Regular.ttf',
};

function inlineFonts(html) {
  let out = html;
  for (const [placeholder, filename] of Object.entries(FONT_PLACEHOLDERS)) {
    // Not every template references every placeholder — skip silently
    // if it isn't present rather than bloating the HTML.
    if (!out.includes(placeholder)) continue;
    const buf = readFileSync(resolve(FONTS_DIR, filename));
    const dataUri = `data:font/ttf;base64,${buf.toString('base64')}`;
    out = out.split(placeholder).join(dataUri);
  }
  return out;
}

const VERSION = readFileSync(resolve(ROOT, 'VERSION'), 'utf8').trim();

// Step-1 caption for the background needs a red-highlighted path token.
// Rather than parsing the caption string, the template renders a wrapper
// <span class="path"> via a literal substring — we swap the whole step-1
// caption HTML for a pre-built chunk with the `~/Library/Keyboard
// Layouts/` inside a .path span.
function step1Html(prefix, suffix) {
  return `${prefix}<span class="path">~/Library/Keyboard Layouts/</span>${suffix}`;
}

// Placeholder keys match the HTML literally (__FOO__). Values are plain
// strings (or small HTML fragments for step 1). One dict per locale.
const LOCALES = {
  en: {
    // Keep step captions short — the background image is a map, not a
    // manual. Full instructions live in the ReadMe PDF. Any long string
    // wraps badly in the narrow middle column (80px per step).
    __STEP1__: step1Html('Open ', ''),
    __STEP2__: 'Drag the bundle in',
    __STEP3__: 'Log out, log back in',
    __WORDMARK__: 'Kirkouski Typographic',
    // Polish diacritics watermark — the Polish layout's headline glyphs.
    __WATERMARK__: '\u0105 \u0119 \u0142 \u0144 \u00F3 \u015B \u017C \u017A',
    __CAPTION_LEFT__: 'KIRKOUSKI TYPOGRAPHIC \u00B7 .BUNDLE',
    __README_LABEL__: 'READ ME FIRST',
    __TITLE__: 'Install Kirkouski Typographic',
    __SECTION_INSTALL_TITLE__: '1. Install',
    __SECTION_INSTALL_BODY__: 'Open Finder, press \u21E7\u2318G, paste ~/Library/Keyboard Layouts/, and drag Kirkouski Typographic.bundle into that folder.',
    __SECTION_ENABLE_TITLE__: '2. Enable',
    __SECTION_ENABLE_BODY__: 'Log out and log back in. Then System Settings \u2192 Keyboard \u2192 Input Sources \u2192 + \u2192 Polish \u2192 Kirkouski Typographic \u2192 Add.',
    __SECTION_UNINSTALL_TITLE__: '3. Uninstall',
    __SECTION_UNINSTALL_BODY__: 'Remove the bundle from ~/Library/Keyboard Layouts/. Log out and back in.',
  },
  pl: {
    __STEP1__: step1Html('Otw\u00F3rz ', ''),
    __STEP2__: 'Przeci\u0105gnij bundle',
    __STEP3__: 'Wyloguj i zaloguj',
    __WORDMARK__: 'Kirkouski Typographic',
    __WATERMARK__: '\u0105 \u0119 \u0142 \u0144 \u00F3 \u015B \u017C \u017A',
    __CAPTION_LEFT__: 'KIRKOUSKI TYPOGRAPHIC \u00B7 PAKIET',
    __README_LABEL__: 'PRZECZYTAJ NAJPIERW',
    __TITLE__: 'Instalacja Kirkouski Typographic',
    __SECTION_INSTALL_TITLE__: '1. Instalacja',
    __SECTION_INSTALL_BODY__: 'Otw\u00F3rz Finder, naci\u015Bnij \u21E7\u2318G, wklej ~/Library/Keyboard Layouts/ i przeci\u0105gnij Kirkouski Typographic.bundle do tego folderu.',
    __SECTION_ENABLE_TITLE__: '2. Aktywacja',
    __SECTION_ENABLE_BODY__: 'Wyloguj si\u0119 i zaloguj ponownie. Nast\u0119pnie Ustawienia \u2192 Klawiatura \u2192 \u0179r\u00F3d\u0142a wprowadzania \u2192 + \u2192 Polski \u2192 Kirkouski Typographic \u2192 Dodaj.',
    __SECTION_UNINSTALL_TITLE__: '3. Odinstalowanie',
    __SECTION_UNINSTALL_BODY__: 'Usu\u0144 bundle z ~/Library/Keyboard Layouts/. Wyloguj si\u0119 i zaloguj ponownie.',
  },
  ru: {
    __STEP1__: step1Html('\u041E\u0442\u043A\u0440\u043E\u0439\u0442\u0435 ', ''),
    __STEP2__: '\u041F\u0435\u0440\u0435\u0442\u0430\u0449\u0438\u0442\u0435 bundle',
    __STEP3__: '\u0412\u044B\u0439\u0434\u0438\u0442\u0435 \u0438 \u0432\u043E\u0439\u0434\u0438\u0442\u0435',
    __WORDMARK__: 'Kirkouski Typographic',
    // Cyrillic/typographic glyphs the Russian layout introduces:
    // short-u (Belarusian), dotted-i (Ukrainian/Belarusian), ye/yi,
    // yo, and typographic guillemets.
    __WATERMARK__: '\u0451 \u0454 \u0456 \u0457 \u045E \u00AB \u00BB',
    __CAPTION_LEFT__: 'KIRKOUSKI TYPOGRAPHIC \u00B7 \u041F\u0410\u041A\u0415\u0422',
    __README_LABEL__: '\u041F\u0420\u041E\u0427\u0418\u0422\u0410\u0419\u0422\u0415 \u0421\u041D\u0410\u0427\u0410\u041B\u0410',
    __TITLE__: '\u0423\u0441\u0442\u0430\u043D\u043E\u0432\u043A\u0430 Kirkouski Typographic',
    __SECTION_INSTALL_TITLE__: '1. \u0423\u0441\u0442\u0430\u043D\u043E\u0432\u043A\u0430',
    __SECTION_INSTALL_BODY__: '\u041E\u0442\u043A\u0440\u043E\u0439\u0442\u0435 Finder, \u043D\u0430\u0436\u043C\u0438\u0442\u0435 \u21E7\u2318G, \u0432\u0441\u0442\u0430\u0432\u044C\u0442\u0435 ~/Library/Keyboard Layouts/ \u0438 \u043F\u0435\u0440\u0435\u0442\u0430\u0449\u0438\u0442\u0435 Kirkouski Typographic.bundle \u0432 \u044D\u0442\u0443 \u043F\u0430\u043F\u043A\u0443.',
    __SECTION_ENABLE_TITLE__: '2. \u0410\u043A\u0442\u0438\u0432\u0430\u0446\u0438\u044F',
    __SECTION_ENABLE_BODY__: '\u0412\u044B\u0439\u0434\u0438\u0442\u0435 \u0438\u0437 \u0441\u0438\u0441\u0442\u0435\u043C\u044B \u0438 \u0432\u043E\u0439\u0434\u0438\u0442\u0435 \u0441\u043D\u043E\u0432\u0430. \u0417\u0430\u0442\u0435\u043C \u041D\u0430\u0441\u0442\u0440\u043E\u0439\u043A\u0438 \u2192 \u041A\u043B\u0430\u0432\u0438\u0430\u0442\u0443\u0440\u0430 \u2192 \u0418\u0441\u0442\u043E\u0447\u043D\u0438\u043A\u0438 \u0432\u0432\u043E\u0434\u0430 \u2192 + \u2192 \u0420\u0443\u0441\u0441\u043A\u0438\u0439 \u2192 Kirkouski Typographic \u2192 \u0414\u043E\u0431\u0430\u0432\u0438\u0442\u044C.',
    __SECTION_UNINSTALL_TITLE__: '3. \u0423\u0434\u0430\u043B\u0435\u043D\u0438\u0435',
    __SECTION_UNINSTALL_BODY__: '\u0423\u0434\u0430\u043B\u0438\u0442\u0435 bundle \u0438\u0437 ~/Library/Keyboard Layouts/. \u0412\u044B\u0439\u0434\u0438\u0442\u0435 \u0438 \u0432\u043E\u0439\u0434\u0438\u0442\u0435 \u0441\u043D\u043E\u0432\u0430.',
  },
};

function substitute(html, strings) {
  let out = html;
  for (const [key, value] of Object.entries(strings)) {
    out = out.split(key).join(value);
  }
  out = out.split('__VERSION__').join(VERSION);
  return out;
}

export async function buildDmgAssets() {
  mkdirSync(OUT_DIR, { recursive: true });
  const bgTemplate = readFileSync(resolve(TEMPLATES_DIR, 'dmg-bg-template.html'), 'utf8');
  const readmeTemplate = readFileSync(resolve(TEMPLATES_DIR, 'dmg-readme-template.html'), 'utf8');
  const bgInlined = inlineFonts(bgTemplate);
  const readmeInlined = inlineFonts(readmeTemplate);

  const browser = await chromium.launch();
  try {
    for (const [lang, strings] of Object.entries(LOCALES)) {
      // --- Background PNGs (both 1x and 2x reps).
      // Chromium's `deviceScaleFactor` doesn't reliably upscale the
      // screenshot raster in headless Playwright — it only affects
      // `window.devicePixelRatio`. CSS `zoom: N` on <body> is the
      // dependable way to control the raster: we match viewport to the
      // desired output size and override the body zoom per rep.
      // The template bakes `zoom: 2` in by default for the 2x case; a
      // `<style>` injection overrides it to `zoom: 1` for the 1x case.
      const bgHtml = substitute(bgInlined, strings);
      const zoomOverride = '<style>body { zoom: __ZOOM__ !important; }</style>';

      const bgReps = [
        { suffix: '',     width: 600,  height: 400, zoom: '1' },
        { suffix: '@2x',  width: 1200, height: 800, zoom: '2' },
      ];
      for (const rep of bgReps) {
        const html = bgHtml.replace(
          '</head>',
          `${zoomOverride.replace('__ZOOM__', rep.zoom)}</head>`,
        );
        const page = await browser.newPage({
          viewport: { width: rep.width, height: rep.height },
        });
        await page.setContent(html, { waitUntil: 'load' });
        // Resolve to `undefined` — FontFaceSet itself serializes unreliably
        // across Playwright versions on Windows.
        await page.evaluate(() => document.fonts.ready.then(() => undefined));
        const png = await page.screenshot({
          type: 'png',
          clip: { x: 0, y: 0, width: rep.width, height: rep.height },
        });
        const path = resolve(OUT_DIR, `background-${lang}${rep.suffix}.png`);
        writeFileSync(path, png);
        console.log(`  background-${lang}${rep.suffix}.png  ${png.length.toLocaleString()} bytes`);
        await page.close();
      }

      // --- ReadMe PDF (A5 portrait)
      const readmeHtml = substitute(readmeInlined, strings);
      const pdfPage = await browser.newPage();
      await pdfPage.setContent(readmeHtml, { waitUntil: 'load' });
      await pdfPage.evaluate(() => document.fonts.ready.then(() => undefined));
      const pdfBuf = await pdfPage.pdf({
        format: 'A5',
        printBackground: true,
        margin: { top: '0mm', right: '0mm', bottom: '0mm', left: '0mm' },
      });
      const pdfPath = resolve(OUT_DIR, `readme-${lang}.pdf`);
      writeFileSync(pdfPath, pdfBuf);
      console.log(`  readme-${lang}.pdf  ${pdfBuf.length.toLocaleString()} bytes`);
      await pdfPage.close();
    }
  } finally {
    await browser.close();
  }
}

// Allow direct execution: `node src/build-dmg-assets.mjs`.
// Use pathToFileURL() for the Windows-correct file:// form — manual
// string-building produces `file://...` (2 slashes) while Node's
// `import.meta.url` on Windows is `file:///...` (3 slashes), so the
// naive comparison never matched and direct execution was a no-op.
if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  await buildDmgAssets();
}
