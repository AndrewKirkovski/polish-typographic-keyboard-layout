// Build an SVG string for one icon variant. The "K" glyph is baked in as a
// vector path so the resulting SVG has zero font dependency at render time.
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { extractGlyph } from './extract-glyph.mjs';

const __dir = dirname(fileURLToPath(import.meta.url));
const FONT = resolve(__dir, '../fonts/DMSerifDisplay-Italic.ttf');

// Canonical 1024×1024 user-unit space; resvg rescales when rasterising.
const SIZE = 1024;
const RADIUS = 192;     // 96 px @ 512 base, scaled 2×
const LETTER_EM = 920;  // matches the original favicon ratio (340/512 ≈ 0.66 of canvas → ~680 at 1024;
                        //   opentype.js em-square is larger than the visible cap height,
                        //   so we tune down to ~0.9× to land at the same optical size)
const LETTER_BASELINE_NUDGE = 20;

/**
 * @param {{ gradient: [string,string], letter: string }} variant
 * @returns {string} SVG markup
 */
export function buildIconSvg(variant) {
  const [c1, c2] = variant.gradient;
  const { d, bbox } = extractGlyph(FONT, variant.letter, LETTER_EM);

  // Centre the glyph optically inside the 1024 box. Italic glyphs lean right,
  // so we shift left a touch from pure geometric centre. Round to 3 decimals
  // so the committed SVG diffs stay clean if the glyph geometry shifts by an
  // imperceptible fraction.
  const glyphW = bbox.x2 - bbox.x1;
  const glyphH = bbox.y2 - bbox.y1;
  const tx = +((SIZE - glyphW) / 2 - bbox.x1 - 24).toFixed(3);
  const ty = +((SIZE - glyphH) / 2 - bbox.y1 + LETTER_BASELINE_NUDGE).toFixed(3);

  return `<svg xmlns="http://www.w3.org/2000/svg" width="${SIZE}" height="${SIZE}" viewBox="0 0 ${SIZE} ${SIZE}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="${c1}"/>
      <stop offset="100%" stop-color="${c2}"/>
    </linearGradient>
    <clipPath id="rounded">
      <rect width="${SIZE}" height="${SIZE}" rx="${RADIUS}" ry="${RADIUS}"/>
    </clipPath>
    <filter id="letterShadow" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur in="SourceAlpha" stdDeviation="12"/>
      <feOffset dx="0" dy="8"/>
      <feComponentTransfer><feFuncA type="linear" slope="0.18"/></feComponentTransfer>
      <feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <g clip-path="url(#rounded)">
    <rect width="${SIZE}" height="${SIZE}" fill="url(#bg)"/>
    <rect width="${SIZE}" height="6" fill="rgba(255,255,255,0.18)"/>
    <rect y="${SIZE - 6}" width="${SIZE}" height="6" fill="rgba(0,0,0,0.12)"/>
    <g transform="translate(${tx}, ${ty})" filter="url(#letterShadow)">
      <path d="${d}" fill="#ffffff"/>
    </g>
  </g>
</svg>
`;
}
