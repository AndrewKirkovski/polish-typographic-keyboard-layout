// Build an SVG string for one icon variant. Glyphs are baked in as vector
// paths so the resulting SVG has zero font dependency at render time.
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { extractGlyph } from './extract-glyph.mjs';

const __dir = dirname(fileURLToPath(import.meta.url));
const FONT = resolve(__dir, '../fonts/DMSerifDisplay-Italic.ttf');

const SIZE = 1024;
const RADIUS = 192;
const LETTER_EM = 600;
const LETTER_BASELINE_NUDGE = 20;
const LETTER_GAP = 20;
const ITALIC_SHIFT = -16;

/**
 * @param {{ gradient: [string,string], letter: string }} variant
 * @returns {string} SVG markup
 */
export function buildIconSvg(variant) {
  const [c1, c2] = variant.gradient;
  const chars = [...variant.letter];

  const glyphs = chars.map(ch => extractGlyph(FONT, ch, LETTER_EM));

  let totalW = 0;
  for (let i = 0; i < glyphs.length; i++) {
    totalW += glyphs[i].advance;
    if (i < glyphs.length - 1) totalW += LETTER_GAP;
  }

  let maxTop = Infinity, maxBottom = -Infinity;
  for (const g of glyphs) {
    if (g.bbox.y1 < maxTop) maxTop = g.bbox.y1;
    if (g.bbox.y2 > maxBottom) maxBottom = g.bbox.y2;
  }
  const glyphH = maxBottom - maxTop;

  const startX = (SIZE - totalW) / 2 + ITALIC_SHIFT;
  const ty = +((SIZE - glyphH) / 2 - maxTop + LETTER_BASELINE_NUDGE).toFixed(3);

  let paths = '';
  let curX = startX;
  for (let i = 0; i < glyphs.length; i++) {
    const g = glyphs[i];
    const gx = +(curX).toFixed(3);
    paths += `\n      <path d="${g.d}" fill="#ffffff" transform="translate(${gx}, ${ty})"/>`;
    curX += g.advance;
    if (i < glyphs.length - 1) curX += LETTER_GAP;
  }

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
      <feGaussianBlur in="SourceAlpha" stdDeviation="8"/>
      <feOffset dx="0" dy="6"/>
      <feComponentTransfer><feFuncA type="linear" slope="0.18"/></feComponentTransfer>
      <feMerge><feMergeNode/><feMergeNode in="SourceGraphic"/></feMerge>
    </filter>
  </defs>
  <g clip-path="url(#rounded)">
    <rect width="${SIZE}" height="${SIZE}" fill="url(#bg)"/>
    <rect width="${SIZE}" height="6" fill="rgba(255,255,255,0.18)"/>
    <rect y="${SIZE - 6}" width="${SIZE}" height="6" fill="rgba(0,0,0,0.12)"/>
    <g filter="url(#letterShadow)">${paths}
    </g>
  </g>
</svg>
`;
}
