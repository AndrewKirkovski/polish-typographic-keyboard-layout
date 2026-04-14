"""Build printable A4 keyboard layout reference sheets as PDF.

Reads the overlay JSON files (polish_typographic.json, russian_typographic.json)
and renders a landscape A4 PDF with all four layers shown on each key.

Usage:
    python build_pdf.py                                   # all layouts, all styles
    python build_pdf.py --layout polish --style color      # Polish color only
    python build_pdf.py --layout russian --style bw        # Russian B/W only
    python build_pdf.py --layout all --style all           # everything

Prerequisites:
    pip install reportlab
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

# -- ReportLab imports (deferred to give a clear error message) ---------------
try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor, black, Color
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
except ImportError:
    print("ERROR: reportlab is not installed. Run: pip install reportlab",
          file=sys.stderr)
    sys.exit(1)


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# -- Version ------------------------------------------------------------------
_version_path = os.path.join(SCRIPT_DIR, "VERSION")
if os.path.exists(_version_path):
    with open(_version_path, encoding="utf-8") as _vf:
        VERSION = _vf.read().strip()
else:
    VERSION = "dev"

# -- stdout encoding (Windows cp1252 guard) -----------------------------------
_reconfigure = getattr(sys.stdout, "reconfigure", None)
if _reconfigure is not None:
    _reconfigure(encoding="utf-8", errors="replace")

# -- Layout definitions -------------------------------------------------------
LAYOUTS: dict[str, dict[str, Any]] = {
    "polish": {
        "json": "polish_typographic.json",
        "title": "Polish Typographic by Kirkouski",
    },
    "russian": {
        "json": "russian_typographic.json",
        "title": "Russian Typographic by Kirkouski",
    },
}

# Physical ANSI keyboard: rows of (key_id, width_units).
# key_id starting with '_' are modifier keys (no overlay data).
KEYBOARD_ROWS: list[list[tuple[str, float]]] = [
    # Number row
    [("`", 1), ("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1),
     ("6", 1), ("7", 1), ("8", 1), ("9", 1), ("0", 1), ("-", 1),
     ("=", 1), ("_bs", 2)],
    # QWERTY row
    [("_tab", 1.5), ("Q", 1), ("W", 1), ("E", 1), ("R", 1), ("T", 1),
     ("Y", 1), ("U", 1), ("I", 1), ("O", 1), ("P", 1), ("[", 1),
     ("]", 1), ("\\", 1.5)],
    # Home row
    [("_caps", 1.75), ("A", 1), ("S", 1), ("D", 1), ("F", 1), ("G", 1),
     ("H", 1), ("J", 1), ("K", 1), ("L", 1), (";", 1), ("'", 1),
     ("_enter", 2.25)],
    # Bottom row
    [("_lsh", 2.25), ("Z", 1), ("X", 1), ("C", 1), ("V", 1), ("B", 1),
     ("N", 1), ("M", 1), (",", 1), (".", 1), ("/", 1), ("_rsh", 2.75)],
    # Space row
    [("_lc", 1.25), ("_lw", 1.25), ("_la", 1.25), ("_sp", 6.25),
     ("_ra", 1.25), ("_rw", 1.25), ("_mn", 1.25), ("_rc", 1.25)],
]

# Labels for modifier keys
MODIFIER_LABELS: dict[str, str] = {
    "_bs": "Backspace",
    "_tab": "Tab",
    "_caps": "Caps Lock",
    "_enter": "Enter",
    "_lsh": "Shift",
    "_rsh": "Shift",
    "_lc": "Ctrl",
    "_rc": "Ctrl",
    "_lw": "Win",
    "_rw": "Win",
    "_la": "Alt",
    "_ra": "AltGr",
    "_sp": "",
    "_mn": "Menu",
}

# -- Color scheme -------------------------------------------------------------
# Source categories
COLOR_ALTGR = HexColor("#CC3333")        # red   -- BI / MOVE / KI chars
COLOR_SHIFT_ALTGR = HexColor("#CC6600")  # orange -- shift+altgr
COLOR_PL = HexColor("#228833")           # green  -- Polish-specific
COLOR_RU = HexColor("#2255AA")           # blue   -- Russian-specific
COLOR_DEAD = HexColor("#8833AA")         # purple -- dead keys
COLOR_BASE = HexColor("#333333")         # dark gray -- base layer
COLOR_SHIFT = HexColor("#555555")        # mid gray -- shift layer
COLOR_MODIFIER_BG = HexColor("#CCCCCC")  # light gray for modifier keys
COLOR_KEY_BG = HexColor("#FFFFFF")       # white key background
COLOR_KEY_BORDER = HexColor("#888888")   # key border


def _get_display_char(entry: Any) -> tuple[str, bool]:
    """Extract displayable character from a layer entry.

    Returns (display_string, is_dead_key).
    For altgr/shift_altgr layers the entry is a dict with 'char', 'name', 'source'.
    For base/shift layers the entry is a plain string.
    None entries mean the key is unassigned in the overlay.
    """
    if entry is None:
        return ("", False)
    if isinstance(entry, str):
        return (entry, False)
    # dict with char/name/source
    char = entry.get("char", "")
    if not char:
        return ("", False)
    if char.startswith("dk:"):
        # Dead key -- show the dk name abbreviated
        dk_name = char[3:]
        # Map common dead key names to combining/display chars
        dk_display: dict[str, str] = {
            "grave": "\u0300",        # combining grave -> show `
            "circumflex": "\u0302",   # ^
            "ring": "\u030A",         # ring
            "breve": "\u0306",        # breve
            "cedilla": "\u0327",      # cedilla
            "double-acute": "\u030B", # double acute
            "diaeresis": "\u0308",    # diaeresis
            "tilde": "\u0303",        # tilde
            "caron": "\u030C",        # caron
            "acute": "\u0301",        # acute
            "acute-2": "\u0301",      # acute variant
        }
        # Use a dotted circle + combining char if available
        if dk_name in dk_display:
            return ("\u25CC" + dk_display[dk_name], True)
        return (dk_name, True)
    return (char, False)


def _get_source(entry: Any) -> str:
    """Get the source category from an altgr/shift_altgr entry."""
    if entry is None or isinstance(entry, str):
        return ""
    return entry.get("source", "")


def _color_for_label(layer: str, source: str, is_dead: bool) -> Color:
    """Pick color based on layer and source category."""
    if is_dead:
        return COLOR_DEAD
    if source == "PL":
        return COLOR_PL
    if source == "RU":
        return COLOR_RU
    if layer in ("altgr",):
        return COLOR_ALTGR
    if layer in ("shift_altgr",):
        return COLOR_SHIFT_ALTGR
    if layer == "shift":
        return COLOR_SHIFT
    return COLOR_BASE


def _register_font() -> str:
    """Register JetBrains Mono and return the font name."""
    font_path = os.path.join(SCRIPT_DIR, "scripts", "assets", "fonts",
                             "JetBrainsMono-Regular.ttf")
    if not os.path.exists(font_path):
        print(f"WARNING: Font not found at {font_path}, using Helvetica",
              file=sys.stderr)
        return "Helvetica"
    pdfmetrics.registerFont(TTFont("JetBrainsMono", font_path))
    return "JetBrainsMono"


def _draw_rounded_rect(c: Canvas, x: float, y: float, w: float, h: float,
                        r: float, fill_color: Color, stroke_color: Color) -> None:
    """Draw a rounded rectangle (key shape)."""
    c.setFillColor(fill_color)
    c.setStrokeColor(stroke_color)
    c.setLineWidth(0.5)
    c.roundRect(x, y, w, h, r, fill=1, stroke=1)


def build_pdf(layout_name: str, style: str, output_dir: str,
              font_name: str) -> str:
    """Build a single PDF for the given layout and style.

    Returns the output file path.
    """
    layout_info = LAYOUTS[layout_name]
    json_path = os.path.join(SCRIPT_DIR, layout_info["json"])

    if not os.path.exists(json_path):
        print(f"ERROR: {json_path} not found.", file=sys.stderr)
        sys.exit(1)

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    layers = data["layers"]
    is_color = (style == "color")

    # Page setup: landscape A4
    page_w, page_h = landscape(A4)
    margin = 15 * mm
    usable_w = page_w - 2 * margin
    usable_h = page_h - 2 * margin

    # Calculate key unit size based on available width
    # Row 0 has 15 units total width (13 x 1 + 1 x 2 = 15)
    total_units = 15.0
    gap = 1.5 * mm
    # key_unit * total_units + gap * (num_keys - 1) = usable_w
    # For row 0: 14 keys -> 13 gaps
    num_keys_row0 = 14
    key_unit = (usable_w - gap * (num_keys_row0 - 1)) / total_units

    # Vertical layout
    row_count = len(KEYBOARD_ROWS)
    # Reserve space for header and footer
    header_h = 18 * mm
    footer_h = 10 * mm
    legend_h = 12 * mm
    keyboard_h = usable_h - header_h - footer_h - legend_h
    key_h = min(key_unit * 0.95, (keyboard_h - gap * (row_count - 1)) / row_count)

    # Output file
    suffix = "color" if is_color else "bw"
    out_name = f"{layout_name}_typographic_{suffix}.pdf"
    out_path = os.path.join(output_dir, out_name)

    c = Canvas(out_path, pagesize=landscape(A4))
    c.setTitle(f"{layout_info['title']} v{VERSION} - {suffix.upper()} reference sheet")

    # -- Header ---------------------------------------------------------------
    header_y = page_h - margin - 6 * mm
    c.setFont(font_name, 14)
    c.setFillColor(black)
    c.drawString(margin, header_y, f"{layout_info['title']}  v{VERSION}")

    c.setFont(font_name, 8)
    c.setFillColor(HexColor("#666666"))
    c.drawString(margin, header_y - 11, "Keyboard layout reference sheet  |  ANSI US physical layout")

    # -- Legend ---------------------------------------------------------------
    legend_y = header_y - 11 - legend_h - 2 * mm
    legend_x = margin
    swatch_size = 3 * mm

    if is_color:
        legend_items: list[tuple[Color, str]] = [
            (COLOR_BASE, "Base"),
            (COLOR_SHIFT, "Shift"),
            (COLOR_ALTGR, "AltGr"),
            (COLOR_SHIFT_ALTGR, "Shift+AltGr"),
            (COLOR_PL if layout_name == "polish" else COLOR_RU,
             "Polish" if layout_name == "polish" else "Russian"),
            (COLOR_DEAD, "Dead key"),
        ]
    else:
        legend_items = [
            (COLOR_BASE, "Base (normal)"),
            (COLOR_BASE, "Shift (gray)"),
            (COLOR_BASE, "AltGr (bold)"),
            (COLOR_BASE, "Shift+AltGr (italic)"),
        ]

    c.setFont(font_name, 7)
    for color, label in legend_items:
        if is_color:
            c.setFillColor(color)
            c.rect(legend_x, legend_y, swatch_size, swatch_size, fill=1, stroke=0)
            legend_x += swatch_size + 1.5 * mm
        c.setFillColor(black)
        c.drawString(legend_x, legend_y + 0.5 * mm, label)
        legend_x += c.stringWidth(label, font_name, 7) + 5 * mm

    # -- Keyboard -------------------------------------------------------------
    # Start from top of keyboard area
    kb_top = legend_y - 3 * mm
    font_size_small = min(6.5, key_unit * 0.3)
    font_size_mod = min(6, key_unit * 0.28)

    for row_idx, row in enumerate(KEYBOARD_ROWS):
        row_y = kb_top - (row_idx + 1) * (key_h + gap)
        key_x = margin

        for key_id, width_units in row:
            key_w = key_unit * width_units + gap * (width_units - 1) if width_units > 1 else key_unit
            is_modifier = key_id.startswith("_")

            # Key background
            bg = COLOR_MODIFIER_BG if is_modifier else COLOR_KEY_BG
            _draw_rounded_rect(c, key_x, row_y, key_w, key_h, 2,
                               fill_color=bg, stroke_color=COLOR_KEY_BORDER)

            if is_modifier:
                # Modifier key label
                mod_label = MODIFIER_LABELS.get(key_id, "")
                if mod_label:
                    c.setFont(font_name, font_size_mod)
                    c.setFillColor(HexColor("#666666"))
                    text_w = c.stringWidth(mod_label, font_name, font_size_mod)
                    c.drawString(key_x + (key_w - text_w) / 2,
                                 row_y + key_h / 2 - font_size_mod / 3,
                                 mod_label)
            else:
                # Character key -- draw up to 4 labels
                # Layout:  shift (TL)      shift_altgr (TR)
                #          base  (BL)      altgr       (BR)
                inset_x = 2.5 * mm
                inset_y = 2 * mm

                label_positions: list[tuple[str, float, float, str]] = [
                    # (layer_name, x, y, alignment)
                    ("base",        key_x + inset_x,
                                    row_y + inset_y,
                                    "left"),
                    ("shift",       key_x + inset_x,
                                    row_y + key_h - inset_y - font_size_small,
                                    "left"),
                    ("altgr",       key_x + key_w - inset_x,
                                    row_y + inset_y,
                                    "right"),
                    ("shift_altgr", key_x + key_w - inset_x,
                                    row_y + key_h - inset_y - font_size_small,
                                    "right"),
                ]

                for layer_name, lx, ly, align in label_positions:
                    layer_data = layers.get(layer_name, {})
                    entry = layer_data.get(key_id)
                    display, is_dead = _get_display_char(entry)
                    if not display:
                        continue

                    source = _get_source(entry) if layer_name in ("altgr", "shift_altgr") else ""

                    cur_size = font_size_small
                    if is_color:
                        color = _color_for_label(layer_name, source, is_dead)
                        c.setFillColor(color)
                        c.setFont(font_name, cur_size)
                    else:
                        # BW style uses font variations + gray levels
                        c.setFillColor(black)
                        cur_size = font_size_small
                        if layer_name == "base":
                            cur_size = font_size_small
                        elif layer_name == "shift":
                            c.setFillColor(HexColor("#666666"))
                            cur_size = font_size_small
                        elif layer_name == "altgr":
                            # Bold not available with single font weight;
                            # use slightly larger size as emphasis
                            cur_size = font_size_small + 0.5
                        elif layer_name == "shift_altgr":
                            c.setFillColor(HexColor("#444444"))
                            cur_size = font_size_small - 0.5
                        c.setFont(font_name, cur_size)

                        # Underline for Polish/Russian chars in BW mode
                        if source in ("PL", "RU"):
                            text_w = c.stringWidth(display, font_name, cur_size)
                            draw_x = lx if align == "left" else lx - text_w
                            c.setStrokeColor(black)
                            c.setLineWidth(0.4)
                            c.line(draw_x, ly - 0.8, draw_x + text_w, ly - 0.8)

                    # Draw the text
                    text_w = c.stringWidth(display, font_name, cur_size)
                    if align == "right":
                        c.drawString(lx - text_w, ly, display)
                    else:
                        c.drawString(lx, ly, display)

            key_x += key_w + gap

    # -- Footer ---------------------------------------------------------------
    footer_y = margin + 2 * mm
    c.setFont(font_name, 6.5)
    c.setFillColor(HexColor("#999999"))
    c.drawString(margin, footer_y,
                 "github.com/AKirkouski/polish-typographic-keyboard-layout")

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    right_text = f"Generated {date_str}  |  v{VERSION}"
    text_w = c.stringWidth(right_text, font_name, 6.5)
    c.drawString(page_w - margin - text_w, footer_y, right_text)

    c.save()
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate printable A4 keyboard layout reference PDFs.")
    parser.add_argument(
        "--layout", choices=["polish", "russian", "all"], default="all",
        help="Which layout to generate (default: all)")
    parser.add_argument(
        "--style", choices=["color", "bw", "all"], default="all",
        help="Color or black-and-white output (default: all)")
    parser.add_argument(
        "--output-dir", default="dist",
        help="Output directory (default: dist)")
    args = parser.parse_args()

    output_dir = os.path.join(SCRIPT_DIR, args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    font_name = _register_font()

    # Determine targets
    layout_targets = list(LAYOUTS.keys()) if args.layout == "all" else [args.layout]
    style_targets = ["color", "bw"] if args.style == "all" else [args.style]

    generated: list[str] = []
    for layout_name in layout_targets:
        for style in style_targets:
            print(f"Building {layout_name} ({style})...")
            out_path = build_pdf(layout_name, style, output_dir, font_name)
            size_kb = os.path.getsize(out_path) / 1024
            print(f"  -> {out_path} ({size_kb:.0f} KB)")
            generated.append(out_path)

    print(f"\nDone. Generated {len(generated)} PDF(s).")


if __name__ == "__main__":
    main()
