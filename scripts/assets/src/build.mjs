// Asset pipeline orchestrator.
//
// Usage:
//   node src/build.mjs all                 # icons + OG image
//   node src/build.mjs icons               # SVGs + .icns for all variants
//   node src/build.mjs icons --svg-only    # SVGs only, skip rasterising
//   node src/build.mjs icons polish        # one variant
//   node src/build.mjs og                  # OG image only
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { VARIANTS, ICNS_ENTRIES, UNIQUE_ICNS_SIZES } from './variants.mjs';
import { buildIconSvg } from './build-icon-svg.mjs';
import { svgToPng } from './rasterize.mjs';
import { packIcns } from './pack-icns.mjs';
import { packIco } from './pack-ico.mjs';
import { buildOgImage } from './build-og.mjs';
import { buildWebIcons } from './build-web-icons.mjs';
import { buildDiagrams } from './build-diagrams.mjs';

const __dir = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dir, '../../..');
const ICONS_OUT = resolve(REPO_ROOT, 'assets/icons');

function buildIcon(name, { svgOnly = false } = {}) {
  const variant = VARIANTS[name];
  if (!variant) throw new Error(`unknown variant: ${name}`);

  const svg = buildIconSvg(variant);
  const svgPath = resolve(ICONS_OUT, `${name}.svg`);
  writeFileSync(svgPath, svg);
  console.log(`  ${name}.svg  ${svg.length.toLocaleString()} bytes`);

  if (svgOnly) return;

  // Render each unique pixel size once; reuse buffers for shared icns types.
  const pngs = Object.fromEntries(
    UNIQUE_ICNS_SIZES.map((size) => [size, svgToPng(svg, size)])
  );
  const entries = ICNS_ENTRIES.map((e) => ({ type: e.type, png: pngs[e.size] }));
  const icns = packIcns(entries);
  const icnsPath = resolve(ICONS_OUT, `${variant.displayName}.icns`);
  writeFileSync(icnsPath, icns);
  console.log(`  ${variant.displayName}.icns  ${icns.length.toLocaleString()} bytes`);

  // Windows DLL icon — multi-size .ico (16/32/48) per layout variant.
  const png16 = pngs[16] ?? svgToPng(svg, 16);
  const png32 = pngs[32] ?? svgToPng(svg, 32);
  const png48 = svgToPng(svg, 48);
  const ico = packIco([
    { size: 16, png: png16 },
    { size: 32, png: png32 },
    { size: 48, png: png48 },
  ]);
  const icoPath = resolve(ICONS_OUT, `${name}.ico`);
  writeFileSync(icoPath, ico);
  console.log(`  ${name}.ico  ${ico.length.toLocaleString()} bytes`);
}

function buildIcons(targets, opts) {
  mkdirSync(ICONS_OUT, { recursive: true });
  const names = targets.length ? targets : Object.keys(VARIANTS);
  for (const name of names) buildIcon(name, opts);
}

async function main() {
  const args = process.argv.slice(2);
  const flags = args.filter((a) => a.startsWith('--'));
  const positional = args.filter((a) => !a.startsWith('--'));
  const target = positional[0] ?? 'all';
  const variantArgs = positional.slice(1);
  const svgOnly = flags.includes('--svg-only');

  if (target === 'all') {
    console.log('Building macOS icons:');
    buildIcons([], { svgOnly });
    console.log('Building web favicons:');
    buildWebIcons();
    console.log('Building README diagrams:');
    await buildDiagrams();
    console.log('Building OG image:');
    await buildOgImage();
  } else if (target === 'icons') {
    console.log('Building macOS icons:');
    buildIcons(variantArgs, { svgOnly });
  } else if (target === 'web') {
    console.log('Building web favicons:');
    buildWebIcons();
  } else if (target === 'diagrams') {
    console.log('Building README diagrams:');
    await buildDiagrams();
  } else if (target === 'og') {
    console.log('Building OG image:');
    await buildOgImage();
  } else if (Object.prototype.hasOwnProperty.call(VARIANTS, target)) {
    // shorthand: `node src/build.mjs polish`
    console.log('Building icons:');
    buildIcons([target], { svgOnly });
  } else {
    console.error(`unknown target: ${target}`);
    console.error('usage: node src/build.mjs [all|icons|web|diagrams|og|<variant>] [variant...] [--svg-only]');
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
