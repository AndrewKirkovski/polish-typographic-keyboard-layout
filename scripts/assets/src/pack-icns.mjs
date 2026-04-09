// Hand-rolled .icns writer. The format is trivial: a 'icns' magic, big-endian
// uint32 total length, then a sequence of (4-byte type code, BE uint32 entry
// length including header, payload bytes). Since macOS 10.7, every ic0X / ic1X
// type accepts a PNG payload — we never need the legacy ARGB / RLE encoding.

/**
 * @param {Array<{ type: string, png: Buffer }>} entries
 *        e.g. [{ type: 'ic04', png: <16x16 PNG buffer> }, ...]
 * @returns {Buffer} bytes of the .icns file
 */
export function packIcns(entries) {
  const chunks = [];
  for (const { type, png } of entries) {
    if (type.length !== 4) {
      throw new Error(`icns type code must be 4 bytes, got "${type}"`);
    }
    const header = Buffer.alloc(8);
    header.write(type, 0, 'ascii');
    header.writeUInt32BE(png.length + 8, 4); // length includes the header
    chunks.push(header, png);
  }
  const body = Buffer.concat(chunks);
  const out = Buffer.alloc(8 + body.length);
  out.write('icns', 0, 'ascii');
  out.writeUInt32BE(out.length, 4);
  body.copy(out, 8);
  return out;
}
