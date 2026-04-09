// Hand-rolled .ico writer. The format is similar in spirit to .icns:
//
//   ICONDIR header (6 bytes)
//     reserved : uint16 = 0
//     type     : uint16 = 1 (icon)
//     count    : uint16 = number of images
//   ICONDIRENTRY * count (16 bytes each)
//     width    : uint8  (0 means 256)
//     height   : uint8  (0 means 256)
//     palette  : uint8  = 0
//     reserved : uint8  = 0
//     planes   : uint16 = 1
//     bpp      : uint16 = 32
//     bytes    : uint32 = payload length
//     offset   : uint32 = where the payload starts in the file
//   PNG payloads, in the same order as the directory entries.
//
// Modern Windows / browsers all accept PNG payload inside ICO entries, so we
// never have to encode BMP/DIB.

/**
 * @param {Array<{ size: number, png: Buffer }>} images
 * @returns {Buffer}
 */
export function packIco(images) {
  const HEADER_SIZE = 6;
  const ENTRY_SIZE = 16;
  const dirSize = HEADER_SIZE + ENTRY_SIZE * images.length;

  const header = Buffer.alloc(HEADER_SIZE);
  header.writeUInt16LE(0, 0); // reserved
  header.writeUInt16LE(1, 2); // type = icon
  header.writeUInt16LE(images.length, 4);

  const entries = Buffer.alloc(ENTRY_SIZE * images.length);
  let offset = dirSize;
  for (let i = 0; i < images.length; i++) {
    const { size, png } = images[i];
    if (size > 256) {
      throw new Error(`ico entries cannot exceed 256px (got ${size})`);
    }
    const base = i * ENTRY_SIZE;
    entries.writeUInt8(size === 256 ? 0 : size, base + 0);
    entries.writeUInt8(size === 256 ? 0 : size, base + 1);
    entries.writeUInt8(0, base + 2);              // palette colours
    entries.writeUInt8(0, base + 3);              // reserved
    entries.writeUInt16LE(1, base + 4);            // colour planes
    entries.writeUInt16LE(32, base + 6);           // bits per pixel
    entries.writeUInt32LE(png.length, base + 8);   // payload bytes
    entries.writeUInt32LE(offset, base + 12);      // payload offset
    offset += png.length;
  }

  return Buffer.concat([header, entries, ...images.map((i) => i.png)]);
}
