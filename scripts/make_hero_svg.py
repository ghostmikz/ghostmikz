"""
Single unified terminal window: ASCII portrait on the left, neofetch-style
info panel on the right, one shared title bar + frame + bottom status line
instead of two separately-sized cards. Replaces make_ascii_svg.py +
make_info_card.py as two independent images.

Portrait: python scripts/prep_photo.py <photo>  (writes source-prepped.png)
Then:     python scripts/make_hero_svg.py        (writes hero.svg)
STATIC=1 emits the frozen (no-animation) state for quick previews.
"""
from PIL import Image, ImageEnhance, ImageFilter
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "source-prepped.png")
OUT = os.path.join(HERE, "..", "hero.svg")
STATIC = bool(os.environ.get("STATIC"))

# ---- shared chrome ----------------------------------------------------
PAD = 24
TITLEBAR_H = 50
STATUS_H = 52
GAP = 44  # space between the two columns (divider line runs through it)

BG = "#0d1117"
BG2 = "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#c9d1d9"
KEY = "#ffa657"
SECTION = "#58a6ff"
GREEN = "#3fb950"
ACCENT = "#22d3ee"

# ---- left column: ascii portrait ---------------------------------------
COLS, ROWS = 100, 53
CELL_W, CELL_H = 8, 15
RAMP = " .`:-=+*cs#%@"
CONTRAST, GAMMA, WHITE_FLOOR = 1.25, 1.1, 0.78
ART_W, ART_H = COLS * CELL_W, ROWS * CELL_H
ROW_DUR = STAGGER = 0.11

im = Image.open(SRC).convert("L")
im = im.filter(ImageFilter.UnsharpMask(radius=3, percent=180, threshold=2))
im = ImageEnhance.Contrast(im).enhance(CONTRAST)
im = im.resize((COLS, ROWS), Image.LANCZOS)
px = im.load()

rows_txt = []
for y in range(ROWS):
    chars = []
    for x in range(COLS):
        lum = pow(px[x, y] / 255.0, GAMMA)
        if lum >= WHITE_FLOOR:
            chars.append(" ")
            continue
        idx = max(0, min(len(RAMP) - 1, int((1.0 - lum) * (len(RAMP) - 1) + 0.5)))
        chars.append(RAMP[idx])
    rows_txt.append("".join(chars))

# ---- right column: neofetch rows ---------------------------------------
CARD_W = 740
KEY_X = 0
VAL_X = 150
LINE_H = 40.0
FONT_KV = 21.0
FONT_SEC = 19.0
FONT_HOST = 24.0

ROWS_INFO = [
    ("host",),
    ("kv", "Now", "Software Engineer @ Smart Retail Systems"),
    ("kv", "Focus", "Backend Logic, Algorithmic Efficiency"),
    ("kv", "Edu", "B.Eng Software Engineering, NMIT '28"),
    ("kv", "Systems", "Fedora (Sway), Debian (GNOME)"),
    ("kv", "Workflow", "Terminal-centric, 163 WPM"),
    ("gap",),
    ("sec", "Stack"),
    ("kv", "Languages", "C, C++, C#, Java, JavaScript"),
    ("kv", "Web", "HTML, CSS, Blazor, .NET"),
    ("kv", "Databases", "MySQL"),
    ("kv", "Tools", "Docker, Git, Vim, VS Code"),
    ("gap",),
    ("sec", "Highlights"),
    ("bul", "Competitive programmer: Codeforces & LeetCode"),
    ("bul", "Open to open-source contributions"),
]


def esc(s):
    return html.escape(s)


# measure pure content height (no starting offset) so it can be centered
def measure(rows):
    y = 0.0
    for row in rows:
        if row[0] == "gap":
            y += LINE_H * 0.5
        else:
            y += LINE_H
    return y


content_h = measure(ROWS_INFO)

# ---- canvas geometry ----------------------------------------------------
CANVAS_W = PAD + ART_W + GAP + CARD_W + PAD
BODY_H = max(ART_H, content_h + 20)  # +20 breathing room if text is shorter
CANVAS_H = TITLEBAR_H + BODY_H + STATUS_H + PAD * 0.6

ART_X = PAD
ART_TOP = TITLEBAR_H + (BODY_H - ART_H) / 2

CARD_X = PAD + ART_W + GAP
CARD_TOP = ART_TOP  # top-align with the portrait instead of centering

DIVIDER_X = PAD + ART_W + GAP / 2


def rise(inner, i):
    if STATIC:
        return f"<g>{inner}</g>"
    delay = 0.15 + i * 0.05
    return (f'<g opacity="0" transform="translate(0,5)">{inner}'
            f'<animate attributeName="opacity" from="0" to="1" begin="{delay:.2f}s" dur="0.4s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" from="0 5" to="0 0" '
            f'begin="{delay:.2f}s" dur="0.4s" fill="freeze" calcMode="spline" keySplines="0.2 0.8 0.2 1"/></g>')


parts = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{CANVAS_W:.0f}" height="{CANVAS_H:.0f}" '
    f'viewBox="0 0 {CANVAS_W:.0f} {CANVAS_H:.0f}" font-family="ui-monospace, SFMono-Regular, '
    f'Menlo, Consolas, monospace">',
    '<defs>'
    f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
    f'<rect width="{CANVAS_W:.0f}" height="{CANVAS_H:.0f}" rx="12" fill="url(#bg)"/>',
    f'<rect x="0.5" y="0.5" width="{CANVAS_W-1:.0f}" height="{CANVAS_H-1:.0f}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{CANVAS_W:.0f}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, dotcol in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    parts.append(f'<circle cx="{PAD + i*24}" cy="{TITLEBAR_H/2}" r="8" fill="{dotcol}"/>')
parts.append(f'<text x="{CANVAS_W/2:.0f}" y="{TITLEBAR_H/2 + 7}" fill="{MUTED}" font-size="20" '
             f'text-anchor="middle">ghostmikz@github: ~$ whoami</text>')

# vertical divider between the two columns
parts.append(f'<line x1="{DIVIDER_X:.1f}" y1="{TITLEBAR_H+12}" x2="{DIVIDER_X:.1f}" '
             f'y2="{TITLEBAR_H+BODY_H-12:.1f}" stroke="{FRAME}" stroke-opacity="0.7"/>')

# ---- left: ascii portrait ------------------------------------------------
font_size = CELL_H * 0.86
for ry, line in enumerate(rows_txt):
    y = ART_TOP + ry * CELL_H + CELL_H * 0.74
    row_y = ART_TOP + ry * CELL_H
    delay = ry * STAGGER
    safe = html.escape(line)
    text = (f'<text xml:space="preserve" x="{ART_X}" y="{y:.1f}" fill="{INK}" '
            f'font-size="{font_size:.1f}" textLength="{ART_W}" lengthAdjust="spacing">{safe}</text>')
    if STATIC:
        parts.append(text)
        continue
    parts.append(
        f'<clipPath id="r{ry}"><rect x="{ART_X}" y="{row_y:.1f}" height="{CELL_H}" width="0">'
        f'<animate attributeName="width" from="0" to="{ART_W}" begin="{delay:.3f}s" '
        f'dur="{ROW_DUR:.2f}s" fill="freeze"/></rect></clipPath>'
    )
    parts.append(f'<g clip-path="url(#r{ry})">{text}</g>')
    parts.append(
        f'<rect y="{row_y+1:.1f}" width="{CELL_W}" height="{CELL_H-2}" fill="{INK}" opacity="0">'
        f'<animate attributeName="x" from="{ART_X}" to="{ART_X+ART_W}" begin="{delay:.3f}s" '
        f'dur="{ROW_DUR:.2f}s" fill="freeze"/>'
        f'<set attributeName="opacity" to="0.85" begin="{delay:.3f}s"/>'
        f'<set attributeName="opacity" to="0" begin="{delay+ROW_DUR:.3f}s"/></rect>'
    )

# ---- right: neofetch card --------------------------------------------
y = CARD_TOP + LINE_H * 0.75
for i, row in enumerate(ROWS_INFO):
    kind = row[0]
    if kind == "gap":
        y += LINE_H * 0.5
        continue
    x0 = CARD_X
    if kind == "host":
        inner = (f'<text x="{x0}" y="{y:.1f}" font-size="{FONT_HOST}" font-weight="700">'
                 f'<tspan fill="{GREEN}">ghostmikz</tspan><tspan fill="{MUTED}">@</tspan>'
                 f'<tspan fill="{ACCENT}">github</tspan></text>'
                 f'<line x1="{x0+FONT_HOST*6.7:.0f}" y1="{y-5:.1f}" x2="{x0+CARD_W}" y2="{y-5:.1f}" '
                 f'stroke="{FRAME}" stroke-opacity="0.8"/>')
    elif kind == "sec":
        title = esc(row[1])
        inner = (f'<text x="{x0}" y="{y:.1f}" fill="{SECTION}" font-size="{FONT_SEC}" font-weight="700">'
                 f'&#8212; {title}</text>'
                 f'<line x1="{x0 + FONT_SEC*0.9 + len(row[1])*FONT_SEC*0.63:.0f}" y1="{y-5:.1f}" x2="{x0+CARD_W}" y2="{y-5:.1f}" '
                 f'stroke="{FRAME}" stroke-opacity="0.8"/>')
    elif kind == "kv":
        key, val = esc(row[1]), esc(row[2])
        inner = (f'<text x="{x0}" y="{y:.1f}" fill="{KEY}" font-size="{FONT_KV}" font-weight="700">{key}</text>'
                 f'<text x="{x0+VAL_X}" y="{y:.1f}" fill="{INK}" font-size="{FONT_KV}">{val}</text>')
    elif kind == "bul":
        txt = esc(row[1])
        inner = (f'<circle cx="{x0+FONT_KV*0.19:.1f}" cy="{y-5:.1f}" r="{FONT_KV*0.19:.1f}" fill="{GREEN}"/>'
                 f'<text x="{x0+FONT_KV:.0f}" y="{y:.1f}" fill="{INK}" font-size="{FONT_KV}">{txt}</text>')
    else:
        continue
    parts.append(rise(inner, i))
    y += LINE_H

# ---- shared bottom status bar ------------------------------------------
status_line_y = TITLEBAR_H + BODY_H + PAD * 0.2
status_y = status_line_y + 32
parts.append(f'<line x1="0" y1="{status_line_y:.1f}" x2="{CANVAS_W:.0f}" y2="{status_line_y:.1f}" stroke="{FRAME}"/>')
parts.append(f'<text x="{PAD}" y="{status_y:.1f}" fill="{MUTED}" font-size="20">'
             f'ghostmikz@github:~$ whoami <tspan fill="{INK}">Chingunjav (ghostmikz)</tspan></text>')
parts.append(f'<rect x="{PAD+408}" y="{status_y-18:.1f}" width="11" height="21" fill="{INK}">'
             f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
             f'dur="1s" repeatCount="indefinite"/></rect>')

parts.append("</svg>")
svg = "".join(parts)
with open(OUT, "w") as f:
    f.write(svg)
print("wrote", OUT, len(svg), "bytes;", f"{CANVAS_W:.0f}x{CANVAS_H:.0f}",
      "art_h", ART_H, "content_h", round(content_h))
