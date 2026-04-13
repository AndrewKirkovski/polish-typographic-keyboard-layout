// Single source of truth for icon variants and the macOS .icns size table.

export const VARIANTS = {
  polish: {
    displayName: 'Polish – Kirkouski Typographic',
    letter: 'PL',
    gradient: ['#d4403a', '#b82e28'],
  },
  russian: {
    displayName: 'Russian – Kirkouski Typographic',
    letter: 'RU',
    gradient: ['#3a7fd4', '#2860b8'],
  },
  uspolish: {
    displayName: 'US+Polish – Kirkouski Typographic',
    letter: 'US',
    gradient: ['#a02822', '#6f1814'],
  },
};

// Apple .icns entry table. Modern macOS accepts PNG payload in every type.
// Several entries share pixel dimensions — the renderer dedupes by size.
export const ICNS_ENTRIES = [
  { type: 'ic04', size: 16 },    // 16×16
  { type: 'ic11', size: 32 },    // 16×16@2x
  { type: 'ic05', size: 32 },    // 32×32
  { type: 'ic12', size: 64 },    // 32×32@2x
  { type: 'ic07', size: 128 },   // 128×128
  { type: 'ic13', size: 256 },   // 128×128@2x
  { type: 'ic08', size: 256 },   // 256×256
  { type: 'ic14', size: 512 },   // 256×256@2x
  { type: 'ic09', size: 512 },   // 512×512
];

export const UNIQUE_ICNS_SIZES = [...new Set(ICNS_ENTRIES.map((e) => e.size))];
