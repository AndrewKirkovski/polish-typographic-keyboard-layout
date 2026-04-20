// Pre-render the README pipeline diagrams as committed SVGs using
// beautiful-mermaid. GitHub renders mermaid in fenced ```mermaid blocks
// natively, but pre-rendering to SVG gives us:
//
//   * deterministic visuals (no GitHub renderer drift)
//   * dark/light parity (we pick a theme once)
//   * works in any markdown viewer (Obsidian, IDEs, mirrors)
//   * smaller README payload — viewers fetch the SVG once
//
// Outputs are committed under assets/diagrams/. README.md references them
// via standard <img>/![]() links.
//
// Post-processing: beautiful-mermaid emits SVGs that lean on CSS custom
// properties + `color-mix()` + `@import url(...Google Fonts...)`. None of
// those work inside browser <img> sandboxes (CORS-blocked) or in resvg-js
// (no @import / partial color-mix). We pre-resolve every variable to a
// literal sRGB hex and drop the @import so the SVGs are 100% self-contained.
import { renderMermaidSVGAsync } from 'beautiful-mermaid';
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

// Light theme palette derived from beautiful-mermaid's defaults
// (--bg=#FFFFFF, --fg=#27272A) with `color-mix(in srgb, --fg X%, --bg)`
// pre-computed. Recompute these if you change the base palette.
const COLOURS = {
  '--bg':              '#FFFFFF',
  '--fg':              '#27272A',
  '--_text':           '#27272A',
  '--_text-sec':       '#7D7D80',
  '--_text-muted':     '#A8A8AA',
  '--_text-faint':     '#C9C9CA',
  '--_line':           '#939394',
  '--_arrow':          '#47474A',
  '--_node-fill':      '#F8F8F9',
  '--_node-stroke':    '#D4D4D4',
  '--_group-fill':     '#FFFFFF',
  '--_group-hdr':      '#F4F4F4',
  '--_inner-stroke':   '#E5E5E5',
  '--_key-badge':      '#E9E9E9',
};

function inlineCss(svg) {
  let out = svg;
  // Replace `var(--name)` with the literal hex for every variable above.
  // Beautiful-mermaid currently bakes literal hex into all draw attributes,
  // so this only catches stragglers — but it future-proofs against a renderer
  // change that would otherwise silently fall back to black via `currentColor`.
  for (const [name, hex] of Object.entries(COLOURS)) {
    const re = new RegExp(`var\\(${name}\\)`, 'g');
    out = out.replace(re, hex);
  }
  // Strip the entire <style> block — it carries a Google Fonts @import,
  // unresolved color-mix() expressions, and CSS custom property cascades
  // that browser <img> sandboxes can't honour and resvg-js can't compute.
  // After stripping, every drawable attribute is already a literal hex from
  // beautiful-mermaid's per-attribute baking, so the SVG renders identically
  // everywhere with no global styles to interpret.
  out = out.replace(/<style>[\s\S]*?<\/style>\s*/g, '');
  // The root <svg ... style="--bg:#fff;--fg:#27272A;background:var(--bg)">
  // had a `background:var(--bg)` that some renderers ignore on <svg>. Replace
  // the inline style with a flat white background so the canvas is opaque
  // everywhere (Github, Obsidian, IDE previews, resvg).
  out = out.replace(
    /<svg ([^>]*)style="[^"]*"/,
    `<svg $1style="background:#FFFFFF"`,
  );
  // Truncate float-precision noise from beautiful-mermaid's coordinates.
  // The renderer emits things like `682.2025000000001` and `90.89999999999999`
  // — deterministic but ugly, and they bloat the SVGs by ~15%. Three decimals
  // is more than enough for any rendering and keeps git diffs clean.
  out = out.replace(/(\d+\.\d{3})\d+/g, '$1');
  return out;
}

const __dir = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dir, '../../..');
const OUT = resolve(REPO_ROOT, 'assets/diagrams');

// beautiful-mermaid only supports single-line node labels (newlines inside
// [" ... "] get parsed as separate nodes). Keep labels short — the README
// prose around the diagrams carries the long-form explanation.
//
// Shape conventions:
//   `(label)`   rounded rect = source file (input)
//   `[label]`   rectangle    = process / script
//   `([label])` stadium pill = output / artifact
//
// Colours match the project palette: brand red for processes, royal blue
// for sources, deep green for outputs. Tints are kept light enough that
// the labels (in matching dark hue) stay legible.
const SOURCE = 'fill:#e8f1ff,stroke:#3a7fd4,color:#1e3a72';
const PROCESS = 'fill:#fef0ee,stroke:#d4403a,color:#7a1d18';
const OUTPUT = 'fill:#e8faee,stroke:#22a35a,color:#0f4d28';

const DIAGRAMS = {
  // Windows: JSON → C → DLL → installer + zip
  'pipeline-windows': `flowchart LR
    JSON("Layout JSON")
    C["build_kbd_c.py"]
    DLL["compile_kbd.py → DLL"]
    INNO(["Inno Setup .exe installer"])
    ZIP(["zip + install.ps1"])

    JSON --> C --> DLL
    DLL --> INNO
    DLL --> ZIP

    style JSON ${SOURCE}
    style C ${PROCESS}
    style DLL ${PROCESS}
    style INNO ${OUTPUT}
    style ZIP ${OUTPUT}
`,

  // macOS: JSON → keylayout → bundle → single trilingual dmg + zip
  'pipeline-macos': `flowchart LR
    JSON("Full layout JSON")
    KL["build_keylayout.py"]
    ICNS("assets/icons/*.icns")
    DMGBG("assets/dmg/*")
    BUNDLE["build_macos_bundle.py"]
    DMG(["DMG (trilingual, macOS only)"])
    ZIP(["zip"])

    JSON --> KL --> BUNDLE
    ICNS --> BUNDLE
    BUNDLE --> DMG
    DMGBG --> DMG
    BUNDLE --> ZIP

    style JSON ${SOURCE}
    style ICNS ${SOURCE}
    style DMGBG ${SOURCE}
    style KL ${PROCESS}
    style BUNDLE ${PROCESS}
    style DMG ${OUTPUT}
    style ZIP ${OUTPUT}
`,

  // Asset pipeline (icons + favicons + OG image)
  'pipeline-assets': `flowchart LR
    TTF("DMSerifDisplay-Italic.ttf")
    GLYPH["opentype.js → 'K' path"]
    SVG["build-icon-svg.mjs"]
    PNG["resvg-js → PNG"]
    ICNS(["macOS .icns × 3"])
    ICO(["favicon.ico / .png"])
    FSVG(["favicon.svg"])

    OGT("og-template.html")
    PW["Playwright 1200×630"]
    OG(["og-image.png"])

    TTF --> GLYPH --> SVG --> PNG
    PNG --> ICNS
    PNG --> ICO
    SVG --> FSVG
    OGT --> PW --> OG

    style TTF ${SOURCE}
    style OGT ${SOURCE}
    style GLYPH ${PROCESS}
    style SVG ${PROCESS}
    style PNG ${PROCESS}
    style PW ${PROCESS}
    style ICNS ${OUTPUT}
    style ICO ${OUTPUT}
    style FSVG ${OUTPUT}
    style OG ${OUTPUT}
`,
};

export async function buildDiagrams() {
  mkdirSync(OUT, { recursive: true });
  for (const [name, code] of Object.entries(DIAGRAMS)) {
    const raw = await renderMermaidSVGAsync(code, { theme: 'neutral' });
    const svg = inlineCss(raw);
    const path = resolve(OUT, `${name}.svg`);
    writeFileSync(path, svg);
    console.log(`  ${name}.svg  ${svg.length.toLocaleString()} bytes`);
  }
}
