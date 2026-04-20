// Render the macOS bundle icon (and DMG volume icon) from the web
// favicon SVG. The favicon is the canonical "K" logo on the brand-red
// gradient rounded-square; using it for the bundle keeps the whole
// product identity consistent — the DMG window shows the same shape as
// polish-typographic.com's browser tab.
//
// Output: assets/icons/Kirkouski.icns (committed, referenced by
//   build_macos_bundle.py via Info.plist `CFBundleIconFile` and by
//   build_dmg.py via dmgbuild's `icon = ...` setting).
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { svgToPng } from './rasterize.mjs';
import { packIcns } from './pack-icns.mjs';
import { ICNS_ENTRIES, UNIQUE_ICNS_SIZES } from './variants.mjs';

const __dir = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dir, '../../..');
const FAVICON_SVG = resolve(REPO_ROOT, 'web/public/favicon.svg');
const OUT_PATH = resolve(REPO_ROOT, 'assets/icons/Kirkouski.icns');

export function buildBundleIcon() {
  const svg = readFileSync(FAVICON_SVG, 'utf8');

  // Render once per unique pixel size, then reuse buffers for the icns
  // entries that share dimensions (ic11 shares 32 with ic05, etc.).
  const pngBySize = new Map();
  for (const size of UNIQUE_ICNS_SIZES) {
    pngBySize.set(size, svgToPng(svg, size));
  }

  const entries = ICNS_ENTRIES.map(({ type, size }) => ({
    type,
    png: pngBySize.get(size),
  }));
  const icns = packIcns(entries);
  writeFileSync(OUT_PATH, icns);
  console.log(`  Kirkouski.icns  ${icns.length.toLocaleString()} bytes (${UNIQUE_ICNS_SIZES.length} sizes)`);
}

// Allow direct execution: `node src/build-bundle-icon.mjs`. pathToFileURL
// normalises the Windows file:/// (triple-slash) form so the equality
// actually holds — the naive `file://${argv[1]}` construction produces
// two slashes on Windows and the check silently fails.
if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  buildBundleIcon();
}
