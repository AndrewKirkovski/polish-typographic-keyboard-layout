"""Build printable A4 keyboard layout reference sheets as PDF.

Reads the overlay JSON files (polish_typographic.json, russian_typographic.json)
and renders a landscape A4 PDF with all four layers shown on each key.

Usage:
    python build_pdf.py                                   # all layouts, all styles
    python build_pdf.py --layout polish --style color      # Polish color only
    python build_pdf.py --layout russian --style bw        # Russian B/W only

Prerequisites:
    pip install reportlab
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Any

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

try:
    import qrcode
except ImportError:
    qrcode = None  # type: ignore[assignment]
HAS_QRCODE = qrcode is not None


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

_version_path = os.path.join(SCRIPT_DIR, "VERSION")
if os.path.exists(_version_path):
    with open(_version_path, encoding="utf-8") as _vf:
        VERSION = _vf.read().strip()
else:
    VERSION = "dev"

_reconfigure = getattr(sys.stdout, "reconfigure", None)
if _reconfigure is not None:
    _reconfigure(encoding="utf-8", errors="replace")

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

KEYBOARD_ROWS: list[list[tuple[str, float]]] = [
    [("`", 1), ("1", 1), ("2", 1), ("3", 1), ("4", 1), ("5", 1),
     ("6", 1), ("7", 1), ("8", 1), ("9", 1), ("0", 1), ("-", 1),
     ("=", 1), ("_bs", 2)],
    [("_tab", 1.5), ("Q", 1), ("W", 1), ("E", 1), ("R", 1), ("T", 1),
     ("Y", 1), ("U", 1), ("I", 1), ("O", 1), ("P", 1), ("[", 1),
     ("]", 1), ("\\", 1.5)],
    [("_caps", 1.75), ("A", 1), ("S", 1), ("D", 1), ("F", 1), ("G", 1),
     ("H", 1), ("J", 1), ("K", 1), ("L", 1), (";", 1), ("'", 1),
     ("_enter", 2.25)],
    [("_lsh", 2.25), ("Z", 1), ("X", 1), ("C", 1), ("V", 1), ("B", 1),
     ("N", 1), ("M", 1), (",", 1), (".", 1), ("/", 1), ("_rsh", 2.75)],
    [("_lc", 1.25), ("_lw", 1.25), ("_la", 1.25), ("_sp", 6.25),
     ("_ra", 1.25), ("_rw", 1.25), ("_mn", 1.25), ("_rc", 1.25)],
]

MODIFIER_LABELS: dict[str, str] = {
    "_bs": "Backspace", "_tab": "Tab", "_caps": "Caps Lock",
    "_enter": "Enter", "_lsh": "Shift", "_rsh": "Shift",
    "_lc": "Ctrl", "_rc": "Ctrl", "_lw": "Win", "_rw": "Win",
    "_la": "Alt", "_ra": "AltGr", "_sp": "", "_mn": "Menu",
}

DEAD_KEY_DISPLAY: dict[str, str] = {
    "grave": "`", "circumflex": "^", "ring": "\u00B0",
    "breve": "\u02D8", "cedilla": "\u00B8", "double-acute": "\u02DD",
    "diaeresis": "\u00A8", "tilde": "~", "caron": "\u02C7",
    "acute": "\u00B4", "acute-2": "\u00B4",
}

COLOR_ALTGR = HexColor("#c4362c")
COLOR_SHIFT_ALTGR = HexColor("#d68820")
COLOR_PL = HexColor("#1f6e38")
COLOR_RU = HexColor("#1f6e9e")
COLOR_DEAD = HexColor("#7c5cbf")
COLOR_BASE = HexColor("#333333")
COLOR_SHIFT = HexColor("#666666")
COLOR_MOD_BG = HexColor("#f0eee9")
COLOR_MOD_BG_DARK = HexColor("#e5e1da")
COLOR_KEY_BG = HexColor("#ffffff")
COLOR_KEY_BG_DARK = HexColor("#f8f7f4")
COLOR_KEY_BORDER = HexColor("#d8d4cc")


def _get_display_char(entry: Any) -> tuple[str, bool]:
    if entry is None:
        return ("", False)
    if isinstance(entry, str):
        return (entry, False)
    char = entry.get("char", "")
    if not char:
        return ("", False)
    if char.startswith("dk:"):
        dk_name = char[3:]
        display = DEAD_KEY_DISPLAY.get(dk_name) or dk_name
        return (display, True)
    return (char, False)


def _get_source(entry: Any) -> str:
    if entry is None or isinstance(entry, str):
        return ""
    return entry.get("source", "")


def _color_for_label(layer: str, source: str, is_dead: bool) -> Color:
    if is_dead:
        return COLOR_DEAD
    if source == "PL":
        return COLOR_PL
    if source == "RU":
        return COLOR_RU
    if layer == "altgr":
        return COLOR_ALTGR
    if layer == "shift_altgr":
        return COLOR_SHIFT_ALTGR
    if layer == "shift":
        return COLOR_SHIFT
    return COLOR_BASE


def _register_font() -> str:
    for name, filename in [
        ("NotoSans", "NotoSans-Regular.ttf"),
        ("JetBrainsMono", "JetBrainsMono-Regular.ttf"),
    ]:
        path = os.path.join(SCRIPT_DIR, "scripts", "assets", "fonts", filename)
        if os.path.exists(path):
            pdfmetrics.registerFont(TTFont(name, path))
            return name
    return "Helvetica"


def _draw_key_bg(c: Canvas, x: float, y: float, w: float, h: float,
                 r: float, is_modifier: bool, is_color: bool) -> None:
    if is_color:
        if is_modifier:
            c.setFillColor(COLOR_MOD_BG)
        else:
            c.setFillColor(COLOR_KEY_BG)
        c.setStrokeColor(COLOR_KEY_BORDER)
        c.setLineWidth(0.5)
        c.roundRect(x, y, w, h, r, fill=1, stroke=1)
        if is_modifier:
            c.setFillColor(COLOR_MOD_BG_DARK)
            c.roundRect(x, y, w, h * 0.15, r * 0.5, fill=1, stroke=0)
        else:
            c.setFillColor(COLOR_KEY_BG_DARK)
            c.roundRect(x, y, w, h * 0.12, r * 0.5, fill=1, stroke=0)
    else:
        c.setFillColor(COLOR_KEY_BG)
        c.setStrokeColor(HexColor("#aaaaaa"))
        c.setLineWidth(0.4)
        c.roundRect(x, y, w, h, r, fill=1, stroke=1)


def build_pdf(layout_name: str, style: str, output_dir: str,
              font_name: str) -> str:
    layout_info = LAYOUTS[layout_name]
    json_path = os.path.join(SCRIPT_DIR, layout_info["json"])

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    layers = data["layers"]
    is_color = (style == "color")

    page_w, page_h = landscape(A4)
    margin = 15 * mm
    usable_w = page_w - 2 * margin

    total_units = 15.0
    gap = 1.5 * mm
    key_unit = (usable_w - gap * 13) / total_units

    header_h = 18 * mm
    footer_h = 8 * mm
    legend_h = 10 * mm
    usable_h = page_h - 2 * margin
    keyboard_h = usable_h - header_h - footer_h - legend_h
    row_count = len(KEYBOARD_ROWS)
    key_h = min(key_unit * 0.95, (keyboard_h - gap * (row_count - 1)) / row_count)

    font_size_base = min(9, key_unit * 0.42)
    font_size_altgr = min(8.5, key_unit * 0.38)
    font_size_mod = min(6.5, key_unit * 0.3)

    suffix = "color" if is_color else "bw"
    out_name = f"{layout_name}_typographic_{suffix}.pdf"
    out_path = os.path.join(output_dir, out_name)

    c = Canvas(out_path, pagesize=landscape(A4))
    c.setTitle(f"{layout_info['title']} v{VERSION} — {suffix.upper()}")

    header_y = page_h - margin - 6 * mm
    c.setFont(font_name, 14)
    c.setFillColor(black)
    c.drawString(margin, header_y, f"{layout_info['title']}  v{VERSION}")
    c.setFont(font_name, 7.5)
    c.setFillColor(HexColor("#888888"))
    c.drawString(margin, header_y - 11, "Keyboard layout reference  |  ANSI US")

    legend_y = header_y - 11 - legend_h
    legend_x = margin
    c.setFont(font_name, 7)

    if is_color:
        legend_items: list[tuple[Color, str]] = [
            (COLOR_ALTGR, "AltGr (bottom-right)"),
            (COLOR_SHIFT_ALTGR, "Shift+AltGr (top-right)"),
            (COLOR_PL if layout_name == "polish" else COLOR_RU,
             "Polish" if layout_name == "polish" else "Ukrainian/Belarusian"),
            (COLOR_DEAD, "Dead key"),
        ]
        for color, label in legend_items:
            c.setFillColor(color)
            swatch = 3 * mm
            c.rect(legend_x, legend_y, swatch, swatch, fill=1, stroke=0)
            legend_x += swatch + 1.5 * mm
            c.setFillColor(black)
            c.drawString(legend_x, legend_y + 0.5 * mm, label)
            legend_x += c.stringWidth(label, font_name, 7) + 4 * mm
    else:
        bw_legend = "AltGr (bottom-right)  |  Shift+AltGr (top-right)"
        c.setFillColor(HexColor("#666666"))
        c.drawString(legend_x, legend_y + 0.5 * mm, bw_legend)

    kb_top = legend_y - 2 * mm

    for row_idx, row in enumerate(KEYBOARD_ROWS):
        row_y = kb_top - (row_idx + 1) * (key_h + gap)
        key_x = margin

        for key_id, width_units in row:
            key_w = key_unit * width_units + gap * (width_units - 1) if width_units > 1 else key_unit
            is_modifier = key_id.startswith("_")

            _draw_key_bg(c, key_x, row_y, key_w, key_h, 2.5,
                         is_modifier, is_color)

            if is_modifier:
                mod_label = MODIFIER_LABELS.get(key_id, "")
                if mod_label:
                    c.setFont(font_name, font_size_mod)
                    c.setFillColor(HexColor("#888888") if is_color else HexColor("#666666"))
                    tw = c.stringWidth(mod_label, font_name, font_size_mod)
                    c.drawString(key_x + (key_w - tw) / 2,
                                 row_y + key_h / 2 - font_size_mod / 3,
                                 mod_label)
            else:
                inset_x = 2.5 * mm
                inset_y = 2 * mm

                label_positions: list[tuple[str, float, float, str, float]] = [
                    ("base",        key_x + inset_x,
                                    row_y + inset_y,
                                    "left", font_size_base),
                    ("shift",       key_x + inset_x,
                                    row_y + key_h - inset_y - font_size_base,
                                    "left", font_size_base),
                    ("altgr",       key_x + key_w - inset_x,
                                    row_y + inset_y,
                                    "right", font_size_altgr),
                    ("shift_altgr", key_x + key_w - inset_x,
                                    row_y + key_h - inset_y - font_size_altgr,
                                    "right", font_size_altgr),
                ]

                for layer_name, lx, ly, align, fsize in label_positions:
                    layer_data = layers.get(layer_name, {})
                    entry = layer_data.get(key_id)
                    display, is_dead = _get_display_char(entry)
                    if not display:
                        continue

                    source = _get_source(entry) if layer_name in ("altgr", "shift_altgr") else ""
                    cur_size = fsize

                    if is_color:
                        color = _color_for_label(layer_name, source, is_dead)
                        c.setFillColor(color)
                    else:
                        if layer_name in ("base", "shift"):
                            c.setFillColor(HexColor("#333333") if layer_name == "base" else HexColor("#777777"))
                        else:
                            c.setFillColor(black)

                    c.setFont(font_name, cur_size)
                    tw = c.stringWidth(display, font_name, cur_size)
                    draw_x = lx - tw if align == "right" else lx
                    c.drawString(draw_x, ly, display)

            key_x += key_w + gap

    site_url = "https://polish-typographic.com/"
    footer_y = margin + 2 * mm
    qr_size = 12 * mm

    if qrcode is not None:
        qr = qrcode.QRCode(box_size=1, border=0)
        qr.add_data(site_url)
        qr.make(fit=True)
        matrix = qr.get_matrix()
        n = len(matrix)
        cell = qr_size / n
        qr_x = page_w - margin - qr_size
        qr_y = footer_y - 2 * mm
        c.setFillColor(black)
        for r, row in enumerate(matrix):
            for col_idx, val in enumerate(row):
                if val:
                    c.rect(qr_x + col_idx * cell, qr_y + (n - 1 - r) * cell,
                           cell, cell, fill=1, stroke=0)

    c.setFont(font_name, 6.5)
    c.setFillColor(HexColor("#999999"))
    c.drawString(margin, footer_y, site_url)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    right_text = f"v{VERSION}  |  {date_str}"
    tw = c.stringWidth(right_text, font_name, 6.5)
    right_edge = (page_w - margin - qr_size - 3 * mm) if HAS_QRCODE else (page_w - margin)
    c.drawString(right_edge - tw, footer_y, right_text)

    c.save()
    return out_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate printable A4 keyboard layout reference PDFs.")
    parser.add_argument(
        "--layout", choices=["polish", "russian", "all"], default="all")
    parser.add_argument(
        "--style", choices=["color", "bw", "all"], default="all")
    parser.add_argument(
        "--output-dir", default="dist")
    args = parser.parse_args()

    output_dir = os.path.join(SCRIPT_DIR, args.output_dir)
    os.makedirs(output_dir, exist_ok=True)

    font_name = _register_font()

    layout_targets = list(LAYOUTS.keys()) if args.layout == "all" else [args.layout]
    style_targets = ["color", "bw"] if args.style == "all" else [args.style]

    generated: list[str] = []
    for ln in layout_targets:
        for st in style_targets:
            print(f"Building {ln} ({st})...")
            out_path = build_pdf(ln, st, output_dir, font_name)
            size_kb = os.path.getsize(out_path) / 1024
            print(f"  -> {out_path} ({size_kb:.0f} KB)")
            generated.append(out_path)

    print(f"\nDone. Generated {len(generated)} PDF(s).")


if __name__ == "__main__":
    main()
