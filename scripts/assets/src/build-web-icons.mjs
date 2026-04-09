// Generate the web favicon set from the canonical Polish (red) icon SVG.
//
// Outputs (all into web/public/):
//   favicon.svg              — vector source, modern browsers prefer this
//   favicon.ico              — multi-size 16/32/48 PNG-in-ICO
//   favicon.png              — 32×32 PNG fallback
//   apple-touch-icon.png     — 180×180 PNG (Apple's recommended size)
//
// Web favicons stay tied to the Polish brand red — if/when we ever want a
// per-page icon set, this is the function to extend.
import { writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { VARIANTS } from './variants.mjs';
import { buildIconSvg } from './build-icon-svg.mjs';
import { svgToPng } from './rasterize.mjs';
import { packIco } from './pack-ico.mjs';

const __dir = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dir, '../../..');
const WEB_PUBLIC = resolve(REPO_ROOT, 'web/public');

export function buildWebIcons() {
  const svg = buildIconSvg(VARIANTS.polish);

  // Vector source for modern browsers.
  const svgPath = resolve(WEB_PUBLIC, 'favicon.svg');
  writeFileSync(svgPath, svg);
  console.log(`  favicon.svg  ${svg.length.toLocaleString()} bytes`);

  // 32×32 PNG fallback.
  const png32 = svgToPng(svg, 32);
  writeFileSync(resolve(WEB_PUBLIC, 'favicon.png'), png32);
  console.log(`  favicon.png  ${png32.length.toLocaleString()} bytes`);

  // Apple touch icon — Apple recommends 180×180.
  const png180 = svgToPng(svg, 180);
  writeFileSync(resolve(WEB_PUBLIC, 'apple-touch-icon.png'), png180);
  console.log(`  apple-touch-icon.png  ${png180.length.toLocaleString()} bytes`);

  // Multi-size .ico for legacy browsers and Windows shell. 16/32/48 is
  // what index.html already advertises in its <link sizes> attribute.
  const png16 = svgToPng(svg, 16);
  const png48 = svgToPng(svg, 48);
  const ico = packIco([
    { size: 16, png: png16 },
    { size: 32, png: png32 },
    { size: 48, png: png48 },
  ]);
  writeFileSync(resolve(WEB_PUBLIC, 'favicon.ico'), ico);
  console.log(`  favicon.ico  ${ico.length.toLocaleString()} bytes (16+32+48)`);
}
