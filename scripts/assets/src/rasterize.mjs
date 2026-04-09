// SVG string -> PNG buffer via @resvg/resvg-js. No system fonts needed.
import { Resvg } from '@resvg/resvg-js';

/**
 * @param {string} svg
 * @param {number} size  target width/height in pixels (square output)
 * @returns {Buffer}
 */
export function svgToPng(svg, size) {
  const resvg = new Resvg(svg, {
    fitTo: { mode: 'width', value: size },
    background: 'rgba(0, 0, 0, 0)',
  });
  return resvg.render().asPng();
}
