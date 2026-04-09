// Extract a single glyph from a TTF/OTF as SVG path data using opentype.js.
// One-shot, called per build. Result is cached by (font path, char) so each
// glyph is parsed at most once per process.
import opentype from 'opentype.js';
import { readFileSync } from 'node:fs';

const cache = new Map();

/**
 * @param {string} fontPath  absolute path to a .ttf/.otf
 * @param {string} char      single character to extract
 * @param {number} fontSize  reference size in user units; the path coordinates
 *                           come back at this scale
 * @returns {{ d: string, advance: number, bbox: {x1:number,y1:number,x2:number,y2:number} }}
 */
export function extractGlyph(fontPath, char, fontSize = 1000) {
  const key = `${fontPath}\n${char}\n${fontSize}`;
  const hit = cache.get(key);
  if (hit) return hit;

  const buf = readFileSync(fontPath);
  // opentype.parse needs an ArrayBuffer; slice into the underlying buffer.
  const ab = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
  const font = opentype.parse(ab);

  const glyph = font.charToGlyph(char);
  // getPath(x, y, fontSize): x,y is the glyph baseline origin in user units.
  // We place the baseline at (0, 0); callers translate via SVG transform.
  const path = glyph.getPath(0, 0, fontSize);

  const result = {
    d: path.toPathData(3), // 3 decimal places — plenty for raster output
    advance: (glyph.advanceWidth * fontSize) / font.unitsPerEm,
    bbox: path.getBoundingBox(),
  };
  cache.set(key, result);
  return result;
}
