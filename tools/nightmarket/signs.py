#!/usr/bin/env python3
"""Print the Night Market's eleven original sign faces (flat, opaque sRGB).

Run with system Python: python3 tools/nightmarket/signs.py [--proof sheet.png]
Dependencies: Pillow, Pycairo, PyGObject with librsvg. All of the printed art is
drawn below. No source photographs, other image assets or engine captures are read.
"""

import argparse
import math
import random
import sys
from contextlib import contextmanager
from pathlib import Path
from xml.sax.saxutils import escape

import cairo
import gi
from PIL import Image, ImageDraw, ImageFont, PngImagePlugin

gi.require_version("Rsvg", "2.0")
from gi.repository import Rsvg


OUT = Path(__file__).resolve().parents[2] / "assets" / "NightMarket" / "Signs"

# Type case for the market's punched-metal script. Letter names are sort keys,
# not Latin transliterations. Each master is 24 units high; counters are cutouts.
SORTS = {
    "A": (21, "M8 1H13L21 22H0Z M10.4 8.5L6.1 17.8H14.4Z M16 0H20L21 5H18Z"),
    "B": (19, "M0 0H12L19 7L8 17L12 21L9 24L1 17L12 7L9 4H2Z M13 15H18V20H13Z"),
    "C": (19, "M8 0H13V9H19V23H14V14H4L0 10Z M6 14H10V23H2V19H6Z"),
    "D": (19, "M0 3H11V0H16V5H19V23H14V9H5V20H0Z M8 12H11V23H8Z"),
    "E": (19, "M2 1H18V6H6V10H14V15H7V23H2Z M12 18H18L15 23H11Z"),
    "F": (21, "M1 1H20V18L15 23H5V18H13L15 16V6H1Z M0 9H10V14H0Z"),
    "G": (19, "M4 0H16L19 3V20L15 24H0V19H12L14 17V6L12 5H6V9H10V14H1V4Z"),
    "H": (20, "M1 2H6V16L12 10V0H17V9H20V14H15L5 24H1Z M12 18H18V23H12Z"),
    "I": (9, "M4 0H9V5H4Z M1 7H8V24H3V12H0Z"),
    "J": (19, "M1 1H16L19 5V11H14V7L12 6H1Z M13 11H19L11 24H5Z M1 12H6V17H1Z"),
    "K": (20, "M0 0H6L14 8L10 12L5 7V19H11V24H0Z M14 12H20V23H15Z"),
    "L": (17, "M0 2H14L17 5V21H12V8L10 7H0Z M0 11H7V16H4V23H0Z"),
    "M": (23, "M1 2H6V7H10V1H15V8H22V23H17V13H13V20H8V12H6V23H1Z"),
    "N": (19, "M0 7L7 0L18 9V22H13V11L7 6L4 9L10 14V23H5V17L0 13Z"),
    "O": (22, "M4 1H18L22 5V20L18 23H3L0 20V5Z M7 6L5 8V16L7 18H15L17 16V8L15 6Z M9 9H13V14H9Z"),
    "P": (20, "M1 0H15L20 5V13L16 17H8V12H13L15 10V7L13 5H6V24H1Z"),
    "Q": (21, "M0 2H21L13 15H8L12 23H6L0 12H10L14 7H2Z"),
    "R": (19, "M0 2H12L16 6V11L11 16H7V21L4 24H0V12H8L11 9V7H0Z M13 16H18V23H13Z"),
    "S": (19, "M8 0H17V5H10L5 10L10 14L7 18L0 12V7Z M13 10H19V16L11 24H5L14 14Z"),
    "T": (20, "M2 2H19V7H12V24H7V7H0Z M14 10H20V15H14Z"),
    "U": (20, "M0 1H5V11L10 16L14 12V0H19V14L10 24L0 14Z"),
    "V": (20, "M0 0H6L14 14V3H19V23H13L5 10V16H0Z M0 19H5V24H0Z"),
    "W": (22, "M1 1H6V15H9V6H14V15H17V1H22V18L16 23L12 19L8 23L1 18Z"),
    "X": (18, "M2 1H8L11 6L15 1H18V6L12 13L17 22H11L8 16L3 23H0V18L6 11Z"),
    "Y": (20, "M0 1H6L10 7L15 1H20V6L13 14V23H7V14L0 6Z M0 17H4V22H0Z"),
    "Z": (20, "M1 2H19V7L8 17H18V22H1V17L12 7H1Z M1 10H5V14H1Z"),
}


class Plate:
    def __init__(self, width, height, stock):
        self.w, self.h = width, height
        self.defs = [f'<path id="sort-{k}" d="{d}" fill-rule="evenodd"/>'
                     for k, (_, d) in SORTS.items()]
        self.art = []
        self.rect(0, 0, width, height, stock)

    def path(self, d, ink="none", stroke="none", sw=1, extra=""):
        self.art.append(f'<path d="{d}" fill="{ink}" stroke="{stroke}" '
                        f'stroke-width="{sw}" fill-rule="evenodd" {extra}/>')

    def rect(self, x, y, w, h, ink, stroke="none", sw=1, radius=0):
        self.art.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
                        f'rx="{radius}" fill="{ink}" stroke="{stroke}" stroke-width="{sw}"/>')

    def oval(self, x, y, rx, ry, ink="none", stroke="none", sw=1):
        self.art.append(f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" '
                        f'fill="{ink}" stroke="{stroke}" stroke-width="{sw}"/>')

    def type(self, x, baseline, text, size, ink, *, font="DejaVu Sans Mono",
             weight="normal", space=0, anchor="start"):
        self.art.append(f'<text x="{x}" y="{baseline}" font-family="{font}" '
                        f'font-size="{size}" font-weight="{weight}" letter-spacing="{space}" '
                        f'text-anchor="{anchor}" fill="{ink}">{escape(text)}</text>')

    @contextmanager
    def group(self, attrs):
        self.art.append(f'<g {attrs}>')
        try:
            yield
        finally:
            self.art.append('</g>')

    def word(self, keys, x, y, w, h, ink, *, gap=3.8, stroke="none", sw=1):
        units = sum(SORTS[k][0] for k in keys) + gap * (len(keys) - 1)
        with self.group(f'transform="translate({x} {y}) scale({w / units:.6f} {h / 24:.6f})" '
                        f'fill="{ink}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round"'):
            left = 0
            for key in keys:
                self.art.append(f'<use xlink:href="#sort-{key}" x="{left:.3f}"/>')
                left += SORTS[key][0] + gap

    def dots(self, name, color, pitch, radius, angle=0):
        self.defs.append(f'<pattern id="{name}" patternUnits="userSpaceOnUse" '
                         f'width="{pitch}" height="{pitch}" patternTransform="rotate({angle})">'
                         f'<circle cx="{pitch / 2}" cy="{pitch / 2}" r="{radius}" fill="{color}"/></pattern>')
        return f'url(#{name})'

    def wear(self, seed, count, color, opacity=0.32, margin=0):
        """Sparse pinholes and short scratches in the print, not illumination."""
        rng = random.Random(seed)
        cuts = []
        for i in range(count):
            x, y = rng.uniform(margin, self.w - margin), rng.uniform(0, self.h)
            w = rng.uniform(.18, 1.3) * (3.4 if i % 19 == 0 else 1)
            h = rng.uniform(.22, .68)
            cuts.append(f'M{x:.1f} {y:.1f}l{w:.1f} {-.22*h:.2f} '
                        f'{-.16*w:.2f} {h:.2f} {-w:.1f} 0Z')
        self.path(''.join(cuts), color, extra=f'opacity="{opacity}"')

    def render(self):
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
               f'viewBox="0 0 {self.w} {self.h}"><defs>{"".join(self.defs)}</defs>'
               f'{"".join(self.art)}</svg>')
        # Supersample the drawn letterforms before the final 2 px/design-unit print.
        w, h = self.w * 4, self.h * 4
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, w, h)
        viewport = Rsvg.Rectangle()
        viewport.width, viewport.height = w, h
        Rsvg.Handle.new_from_data(svg.encode()).render_document(cairo.Context(surface), viewport)
        surface.flush()
        raw_mode = 'BGRX' if sys.byteorder == 'little' else 'XRGB'
        raster = Image.frombytes('RGB', (w, h), bytes(surface.get_data()), 'raw', raw_mode,
                                 surface.get_stride(), 1)
        return raster.resize((self.w * 2, self.h * 2), Image.Resampling.LANCZOS)


def rind_can(p):
    """Straight-on three-ink depiction of a returnable tin, not a rendered object."""
    leaf, dark, sage, paper = '#5eaa57', '#194f44', '#a9c869', '#ecdf97'
    with p.group('transform="translate(373 100) rotate(10)"'):
        shell = ('M-43-84H43V-78L38-75 45-68 48-59V62L44 70 40 74 42 79 '
                 '38 83H-38L-42 79-40 74-44 69-48 62V-59L-45-67-38-75-43-78Z')
        p.path(shell, leaf, '#f4c876', 4, 'stroke-linejoin="round"')
        p.path(shell, leaf, dark, 2.3, 'stroke-linejoin="round"')
        p.path('M-42-82H42V-77H-42Z M-40 73H40V78H-40Z', paper, dark, 1)
        for x in range(-37, 40, 4):
            p.path(f'M{x}-82v4m0 152v3', stroke=dark, sw=.6)
        p.path('M-40-73H40L44-68H-44Z M-45 65H45L41 70H-41Z', dark)
        p.path('M-46-60H46M-46 58H46', stroke=paper, sw=2)
        p.path('M-47-51H47V-43H-47Z M-47 46H47V53H-47Z', sage)
        p.type(0, -54, 'BOTTLING UNION / 036', 4.3, dark, weight='bold', space=.55, anchor='middle')
        p.path('M-39-42H39L43-38V36L38 41H-38L-43 36V-38Z', sage, dark, 1.8)
        p.path('M-35-39H35L40-35V33L35 37H-35L-40 33V-35Z', 'none', paper, .9)
        # Two leaves around a notched citrus seed form the bottler's trademark.
        p.oval(0, -15, 19, 17, dark)
        p.path('M-9-21Q-18-16-9-9Q-2-5 0-13Q-2-20-9-21Z '
               'M0-13Q0-24 12-25Q14-17 4-12Z', paper)
        p.path('M-5-5L0-13 5-14 1-7 5-8-2-1Z', leaf)
        p.word('ROD', -32, 7, 64, 17, dark, gap=3)
        p.type(0, 31.7, 'R I N D   /   V O L T', 4.3, dark, weight='bold', anchor='middle')
        p.type(-38, 50.6, 'CITRUS ELECTROLYTE', 3.9, dark, weight='bold', space=.28)
        p.type(37, 63.5, '36 cL', 4.1, paper, anchor='end')
        for x in range(-37, -10, 2):
            p.rect(x, 60.1, .65 if x % 3 else 1.2, 3.1, dark)


def billboard():
    p = Plate(600, 200, '#df6236')
    red, darkred, ivory, maize, green = '#c74832', '#963c2f', '#f6e5b4', '#edac57', '#bdd968'
    screen = p.dots('rind-screen', '#d34f32', 4.2, .78, 21)
    p.path('M0 0H313L260 51H0Z M0 139L289 54 227 137 293 118 222 200H0Z', '#e97b3f')
    p.path('M413 0H600V200H469L425 172 470 150 412 126 476 111 418 91 465 64 408 43 461 26Z', red)
    p.path('M235 0H330L270 60 318 39 237 139 263 74 209 111Z', screen)
    p.path('M18 10H184M431 10H580M18 190H215M462 190H582', stroke=maize, sw=1.2)
    p.oval(26, 29, 10, 10, darkred)
    p.path('M20 28Q20 23 26 22Q29 28 25 31Z M26 31Q27 23 34 24Q33 31 26 32Z', ivory)
    p.type(44, 28, 'SOUTH LOOP BOTTLING WORKS', 7.2, ivory, weight='bold', space=.6)
    p.type(44, 36, 'FRUIT TONICS   /   RETURNABLE SERIES 04', 4.8, darkred, space=.33)
    p.word('BRAJU', 18, 52, 247, 56, ivory, gap=2.7)
    p.path('M18 119H236L229 124H18Z', darkred)
    p.word('NQIL', 21, 134, 73, 14, '#485f3b')
    p.type(105, 146, 'RIND / VOLT', 15, darkred, font='Nimbus Sans Narrow', weight='bold', space=.8)
    p.type(19, 168, 'CITRUS TONIC  ::  BOTTLED ON THE SOUTH LOOP', 6.8, ivory, weight='bold', space=.15)
    p.type(19, 180, 'PRINT 126-B  /  FIVE-CENT DEPOSIT     UNION LABEL  •  36 cL', 4.7, ivory, space=.2)
    for x, y, w in [(281, 20, 32), (292, 26, 12), (260, 144, 26), (271, 151, 11), (425, 178, 21)]:
        p.path(f'M{x} {y}h{w}l-4 3h-{w}Z', maize)
    rind_can(p)
    p.word('UMI', 470, 24, 98, 25, ivory, gap=3)
    p.type(471, 59, 'EXTRACT NO. 06', 6.6, ivory, weight='bold', space=1.1)
    p.path('M470 65H576M490 68H576', stroke=maize, sw=.9)
    p.oval(479, 91, 14, 14, 'none', maize, 1.3)
    p.oval(479, 91, 11, 11, 'none', maize, .5)
    p.type(479, 94.6, '06', 9.5, ivory, weight='bold', anchor='middle')
    p.type(500, 89, 'PULP + PEEL', 6.2, ivory, weight='bold')
    p.type(500, 98, 'BATCH-TESTED', 4.8, maize, space=.4)
    p.word('WPLI', 467, 121, 102, 39, '#426545', stroke=green, sw=1.25, gap=3.2)
    p.type(468, 178, 'DRINK COLD  /  RETURN TIN', 5.6, ivory, space=.4)
    p.wear(620, 610, '#f3b26b', .43)
    return p


def pharmacy():
    p = Plate(460, 200, '#e3ebce')
    ink, jade, sage = '#263d38', '#507669', '#96b7a4'
    p.path('M12 15H123M354 15H449M12 185H121M362 185H448', stroke=sage, sw=1.05)
    p.path('M18 25H23V20H27V25H32V29H27V34H23V29H18Z', jade)
    p.type(39, 29.5, 'DISPENSARY   /   SOUTH BLOCK', 6.5, jade, weight='bold', space=.55)
    p.type(437, 29.5, 'Nº  08  ::  ALL HOURS', 6.1, jade, space=.55, anchor='end')
    p.word('ABCD', 20, 50, 419, 98, ink, gap=2.6)
    p.path('M21 161H198M211 161H438', stroke=sage, sw=1)
    p.word('CIT', 23, 167, 30, 8, jade)
    p.type(62, 174, 'PRESCRIPTIONS  /  TONICS  /  REPAIRS', 5.6, jade, space=.47)
    p.type(438, 174, 'DS–081', 5.8, jade, weight='bold', space=.5, anchor='end')
    p.wear(828, 155, '#98ad91', .24)
    return p


def noodle():
    p = Plate(460, 200, '#771f24')
    hot, gold, clove = '#ff9434', '#ffbc62', '#b13d2c'
    p.path('M12 20L20 12H440L448 20V180L440 188H20L12 180Z', 'none', hot, 5)
    p.path('M22 28L28 22H432L438 28V173L432 178H28L22 172Z', 'none', '#d56034', 1.5)
    p.path('M31 40H79M381 40H431M31 160H81M381 160H431', stroke=clove, sw=1.2)
    p.type(230, 34.5, 'S O U T H    K E T T L E      /      S T A L L   5', 6.9, gold, anchor='middle')
    p.word('SETIA', 44, 51, 372, 88, '#a13726', stroke=hot, sw=1.65, gap=3.7)
    p.oval(151, 157.5, 1.7, 1.7, hot)
    p.oval(309, 157.5, 1.7, 1.7, hot)
    p.word('GVI', 166, 153, 27, 8.3, hot)
    p.type(230, 161, 'BROTH  /  05', 7.4, gold, weight='bold', space=.45, anchor='middle')
    p.word('UEJ', 268, 153, 27, 8.3, hot)
    p.wear(301, 240, '#e18442', .22)
    return p


def marquee():
    p = Plate(320, 320, '#ecc643')
    ink, blue, coral = '#302635', '#a4d8c3', '#cb4c32'
    p.oval(160, 52, 11, 11, 'none', ink, 1.3)
    p.path('M152 53Q156 45 160 46Q165 48 168 53Z M151 56H169', ink, ink, .7)
    p.type(139, 55.5, 'SOL', 6.6, ink, weight='bold', space=.7, anchor='end')
    p.type(181, 55.5, '017', 6.6, ink, weight='bold', space=.8)
    p.word('LOGMI', 33, 78, 254, 46, ink, gap=3)
    p.path('M-2 135H322V169H-2Z', ink)
    p.word('QAWUEFJ', 51, 142, 218, 19, blue, gap=4.1)
    p.path('M30 174H290', stroke='#b18a35', sw=.9)
    p.word('GUICBK', 64, 184, 192, 23, ink, gap=4)
    p.word('QBADI', 91, 219, 138, 21, ink, gap=4)
    p.path('M0 253H320V282H0Z', coral)
    p.type(160, 271, 'SUN PARCEL   •   NIGHT SERVICE', 7, '#ffdda0', weight='bold', space=.5, anchor='middle')
    p.path('M131 291H189', stroke=ink, sw=1)
    p.wear(317, 510, '#a98a35', .31)
    return p


def reel_keeper(p, dark, violet, iris, aqua):
    """The projectionist: cap, square CRT, split work coat and a five-hole reel."""
    # Split tin shins, hinged knee pads, soft uppers, wide work boots.
    p.path('M-27 125L-3 128-5 156-13 184-16 214-25 224-37 218-33 184-35 164Z '
           'M1 128L23 124 28 162 24 185 31 216 25 225 13 222 6 191 9 170-4 153Z', dark)
    p.path('M-29 159L-12 155-16 175-29 180Z M9 163L22 160 21 180 11 184Z '
           'M-28 184L-21 180-24 207-30 211Z M13 188L19 184 25 208 19 210Z', violet)
    p.path('M-30 164l11-3m-12 7 11-3m30 3 10-3m-10 7 9-3', stroke=iris, sw=1.15)
    p.path('M-36 210L-17 211-16 224-20 230H-53V225L-39 218Z '
           'M13 214L30 210 35 220 46 223 49 230H16L12 225Z', dark)
    p.path('M-51 226H-21M18 226H45M-37 216l10 1m45 0 8-1', stroke=iris, sw=1.25)
    # Body and silhouette of a coat with the hem kicked open at one hip.
    p.path('M-7 47L9 46 14 54 31 60 38 76 29 100 26 125 38 144 '
           '18 151 3 144-2 138-10 152-34 148-41 139-33 119-32 82-38 69-27 59-13 55Z', dark)
    p.path('M-24 62L-10 56-2 66-10 98-23 105-28 97-29 73Z '
           'M10 57L25 62 31 75 23 93 6 89 3 75Z M-32 114L-14 111-19 138-34 139Z '
           'M10 111L23 107 30 138 15 142 6 137Z', violet)
    p.path('M-15 53L-7 50 1 64-5 78-15 64-22 65Z M8 51L18 55 12 64 5 70 2 64Z', iris)
    p.path('M-7 77L-11 108M6 75V105M-29 114l16-2-2 11-12 4Z M8 114l17-4 2 12-19 5Z', 'none', iris, 1.5)
    p.path('M-33 108L25 99 26 106-34 116Z', dark)
    p.path('M-4 104L5 103 6 111-4 112Z M-25 78H-16V82H-25Z', iris)
    p.path('M-24 86h6m-6 4h4m36-18 6 2m-7 2 6 2m-7 2 5 2', stroke=aqua, sw=.95)
    # Folded arm and the film tin. Holes are actual cut ink shapes, not a gloss.
    p.path('M-33 64Q-43 64-45 76L-55 94-52 110-39 119-29 112-31 103-40 99-28 84Z', dark)
    p.path('M-39 72L-32 76-40 92-48 94Z M-51 96L-44 94-39 99-44 106Z', violet)
    p.oval(-40, 116, 20, 20, violet, dark, 3)
    p.oval(-40, 116, 16.4, 16.4, 'none', iris, 1.35)
    for i in range(5):
        a = math.tau * i / 5 - math.pi / 2
        p.oval(-40 + 9.5 * math.cos(a), 116 + 9.5 * math.sin(a), 4.1, 4.1, dark)
    p.oval(-40, 116, 2.6, 2.6, aqua)
    p.path('M-32 88L-24 92-23 101-29 109-37 105-38 100Z', dark)
    p.path('M-34 101l6 4m-4-7 6 3', stroke=iris, sw=1.3)
    p.path('M29 63Q39 62 43 78L44 93 53 105 50 111 39 113 27 99 24 85Z '
           'M44 106L53 104 59 115 57 122 54 121 51 115 51 125 47 125 44 116 39 113Z', dark)
    p.path('M32 71L38 74 40 86 33 91 29 85Z M36 97L43 95 49 104 43 107Z', violet)
    p.path('M32 91l8-3m1 20 7-3', stroke=iris, sw=1.2)
    # The CRT face has glass as a flat ink panel, pixel eyelids and service grille.
    p.path('M-9 39L8 40 8 54 2 59-9 52Z', dark)
    p.path('M-6 46h10m-10 4h10', stroke=iris, sw=1.4)
    with p.group('transform="rotate(-6 0 22)"'):
        p.path('M-22 6L19 6 25 11 24 34 17 42H-16L-25 35-27 15Z', violet, dark, 3)
        p.path('M-19 13L11 12 15 16 14 30 11 33-17 34-21 30-22 17Z', dark)
        p.path('M-17 17L10 16 12 18 11 28 8 30-16 30-18 27Z', iris)
        p.path('M-16 21H-5L-7 24H-16Z M1 21H10L8 24H1Z', dark)
        p.path('M-13 32h13M17 26l4-1m-4 4 4-1m-5 4 4-1', stroke=aqua, sw=.95)
        p.oval(18.7, 18.5, 2.5, 2.5, dark)
        p.oval(18.7, 18.5, 1.1, 1.1, aqua)
        p.path('M-26 14H-30L-30 27-25 30Z M-20 6Q-18-8-2-11Q10-13 18 0L28 3 23 8 4 6-21 10Z', dark)
        p.path('M-18 1Q-8-8 0-7L8-3-6-2Z M-23 6L16 2 19 4-22 8Z', violet)
        p.oval(-3, -3, 2.5, 2.5, iris)


def wire_runner(p, dark, violet, iris, aqua):
    """The messenger: monocular dial head, long aerial, overcoat, crossbody satchel."""
    p.path('M-18 127L1 129-1 160-9 187-5 218-14 225-22 220-25 190-17 163Z '
           'M2 128L21 127 21 155 31 183 20 209 16 220 4 219 8 205 16 183 6 160Z', dark)
    p.path('M-16 153l13 5-3 13-12-3Z M-20 182l9 3 3 23-9 3Z '
           'M10 158l10-4 6 22-9 2Z M18 188l9-4-10 24-7-1Z', violet)
    p.oval(-13, 177, 6.4, 6.4, iris, dark, 2)
    p.oval(22, 182.5, 5.3, 5.3, iris, dark, 2)
    p.path('M-13 174v6m30 3h8m-41 26 8-2m15-6 8 2', stroke=dark, sw=1.2)
    p.path('M-24 212L-8 211-4 220-6 226H-32L-41 223-39 219-27 217Z '
           'M5 212L19 215 21 219 33 220 38 225 34 228H2L0 223Z', dark)
    p.path('M-35 222l25 1m16 1h26', stroke=iris, sw=1.1)
    # A knotted signal scarf and the patterned lining visible inside its two tails.
    p.path('M-9 46Q6 43 19 52Q37 62 57 48L62 52Q47 72 21 64L39 76 38 81Q15 77 0 62Z', dark)
    p.path('M16 55Q37 65 54 56Q43 67 24 62Z M9 59L30 73 17 69Z', iris)
    p.path('M-11 47L10 47 18 56 29 64 28 82 20 101 23 120 38 145 '
           '15 150-1 142-10 151-41 147-28 117-26 94-33 76-28 62-16 57Z', dark)
    p.path('M-17 59L-8 54 4 59-8 89-22 102-29 73Z M7 59L18 61 23 72 '
           '16 89 14 104 20 127 28 142 14 143 5 131 0 102Z', violet)
    p.path('M-27 109L-11 98-16 128-29 141-37 141Z M-7 53L8 51 14 55-3 67-12 63Z', violet)
    p.path('M-28 70l11 17m-14-10 10 17m23-22-4 32 10 27M-14 114l-4 14', 'none', iris, 1.25)
    p.path('M-25 62L-18 60 19 109 14 115Z', iris, dark, 1.35)
    p.path('M7 106L28 100 37 107 39 127 13 137 5 132Z', violet, dark, 2.5)
    p.path('M7 108L28 102 35 108 25 117 12 119Z M23 117L28 115 28 121 24 123Z', dark)
    p.path('M12 124l9-3m-8 6 8-3', stroke=iris, sw=1)
    # Bent left arm holds a folded timetable; right elbow and fingers hang free.
    p.path('M-27 63L-35 64-39 81-42 91-49 85-55 87-54 94-42 108-32 104-24 84Z', dark)
    p.path('M-32 69l4 5-8 20-4-2Z M-49 89l6 4-1 6-6-6Z', violet)
    p.path('M-57 64L-43 58-34 79-50 87Z', iris, dark, 2)
    p.path('M-53 68l10-4m-8 8 10-4m-6 10 8-3', stroke=dark, sw=1.1)
    p.path('M-50 81L-42 78-38 81-41 87-49 91-53 87Z', dark)
    p.path('M25 63Q38 66 40 81L43 93 34 111 30 111 25 107 30 92 22 85Z '
           'M26 104L34 106 32 119 26 124 22 122 24 116 20 119 18 116Z', dark)
    p.path('M30 71l5 3 4 12-7 4-4-9Z M33 96l6-2-6 13-5-2Z', violet)
    p.path('M32 91l7-4m-13 25 5 1', stroke=iris, sw=1.25)
    # Long exposed neck bellows and a single big mechanical iris in its dial head.
    p.path('M-9 32L7 34 7 49-1 54-9 48Z', dark)
    p.path('M-7 39h11m-11 4h12m-11 4h11', stroke=iris, sw=1.2)
    p.path('M8 7L19-18 22-17 16 10Z', dark)
    p.oval(21, -18, 2.5, 2.5, iris, dark, 1)
    p.path('M-22 13Q-20-3-4-4Q13-6 21 11L24 23 14 36-8 39-22 30-27 19Z', violet, dark, 3)
    p.path('M-21 8Q-15-5 0-5Q14-6 21 8L12 8-13 13-25 15Z', dark)
    p.path('M-16 6Q-8-2 1-1L9 2Z', iris)
    p.oval(-5, 20, 13, 12, iris, dark, 2)
    p.oval(-5, 20, 8.1, 7.7, violet, dark, 1.8)
    p.path('M-9 20L-5 15 0 19-3 24-8 24Z', dark)
    p.path('M12 16l7-1m-7 5 7-1m-8 5 7-1m-9 5 6-1', stroke=dark, sw=1.55)
    p.path('M-25 16l-5 2 1 10 7 1Z', iris, dark, 1.7)
    p.path('M-10 35l13-1', stroke=aqua, sw=1.2)


def cinema():
    p = Plate(400, 500, '#76ccce')
    dark, purple, lilac, pale = '#352943', '#705589', '#aa91b9', '#b4e6da'
    teal = '#38999f'
    screen = p.dots('duo-dots', '#559da9', 3.6, .64, 23)
    hatching = p.dots('duo-violet', '#806f9c', 2.9, .54, 12)
    p.path('M8 13H392M8 486H392', stroke=dark, sw=1.5)
    p.type(16, 25, 'HATCH / MUNICIPAL PICTURE HOUSE', 6.4, dark, weight='bold', space=.8)
    p.type(384, 25, 'DUAL PROGRAM    076', 6.6, dark, weight='bold', space=.7, anchor='end')
    p.word('QONRJB', 15, 36, 368, 42, dark, gap=2.5)
    p.path('M13 88H389V111H13Z', pale, dark, 1.5)
    p.word('RLI', 22, 94, 38, 10, purple)
    p.type(200, 104.5, 'S P L I T    S I G N A L', 12, dark, font='Nimbus Sans Narrow', weight='bold', anchor='middle')
    p.type(379, 103.5, '2 x 34 MIN', 5.7, dark, weight='bold', anchor='end')
    p.rect(13, 121, 181, 307, '#8cd9d4', dark, 2)
    p.rect(204, 121, 183, 307, '#88cacf', dark, 2)
    # A radio-transmission motif rather than a painted background or lighting.
    p.path('M15 416V357L133 123H156Z M38 426L192 136V162L57 426Z', '#74c8ca')
    p.path('M206 420V386L352 123H374Z M281 426L385 231V247L294 426Z', '#72b9c4')
    p.path('M15 123H109L15 307Z M191 257V426H107Z M207 123H289L207 282Z '
           'M384 314V426H325Z', screen)
    p.oval(104, 229, 61, 61, 'none', teal, 1.05)
    p.oval(299, 220, 58, 58, 'none', purple, .8)
    p.oval(299, 220, 54, 54, 'none', teal, .75)
    p.path('M17 331l92-176 15-9-101 190Z M285 423l47-89h17l-47 89Z', hatching)
    for x, code in [(20, 'A / 01'), (211, 'B / 02')]:
        p.rect(x, 129, 38, 11, dark)
        p.type(x + 4, 137.1, code, 6.3, pale, weight='bold', space=.5)
    with p.group('transform="translate(105 177) scale(1.01)"'):
        reel_keeper(p, dark, purple, lilac, pale)
    with p.group('transform="translate(299 171) scale(1.025)"'):
        wire_runner(p, dark, purple, lilac, pale)
    for x, caption in [(103, 'I.  THE REEL KEEPER'), (296, 'II.  THE WIRE RUNNER')]:
        p.type(x, 421.8, caption, 5.9, dark, weight='bold', space=.72, anchor='middle')
    p.path('M13 437H387V476H13Z', dark)
    p.word('HUPJI', 22, 447, 99, 20, pale, gap=3)
    p.type(145, 454, 'TWO TRANSMISSIONS / ONE TICKET', 6.5, pale, weight='bold', space=.3)
    p.type(145, 465, 'ASSEMBLY 5  •  EVENINGS AT 20.40', 5.7, '#bbabca', space=.35)
    p.path('M351 447H378V466H351Z', 'none', pale, .9)
    p.type(364.5, 459.5, '2 / 1', 6.1, pale, weight='bold', anchor='middle')
    # Regular offset-print scanlines; no CRT glow, falloff or vignette.
    lines = ''.join(f'M9 {y}H391' for y in range(16, 486, 4))
    p.path(lines, stroke=dark, sw=.55, extra='opacity=".28"')
    p.wear(512, 480, pale, .32)
    return p


def menubox():
    p = Plate(180, 540, '#242c3a')
    ochre, pale, rust, midnight = '#ca9553', '#e8cca2', '#926347', '#242c3a'
    p.path('M7 9H173V532H7Z', 'none', rust, 1.4)
    p.word('EVLI', 39, 21, 101, 13, ochre)
    p.type(90, 49, 'RELAY ROASTERS', 6.8, pale, weight='bold', space=1.45, anchor='middle')
    p.rect(27, 62, 126, 333, 'none', ochre, 3.7, 62)
    p.rect(33, 68, 114, 321, 'none', rust, 1.2, 56)
    p.word('T', 67, 88, 45, 42, ochre)
    p.word('RL', 53, 146, 73, 48, ochre, gap=2.8)
    p.word('CU', 54, 209, 71, 43, ochre, gap=2.8)
    p.path('M76 310Q66 302 76 291Q82 284 76 277 M89 309Q82 304 88 295Q96 285 89 278 '
           'M102 304Q99 298 104 293Q110 286 106 280', 'none', ochre, 2.7,
           'stroke-linecap="round"')
    p.path('M115 315Q139 310 127 331Q120 338 112 334', 'none', ochre, 4.7)
    p.path('M63 314H116L113 330Q110 344 89 345Q68 343 66 329Z', ochre)
    p.path('M70 320H108M62 349Q90 354 120 347', stroke=ochre, sw=2.6)
    p.oval(89, 329.4, 5.3, 8.5, midnight)
    p.path('M91 322Q85 328 89 336', 'none', ochre, 1.2)
    p.type(90, 369, 'C A F É', 11, pale, font='Nimbus Sans Narrow', weight='bold', anchor='middle')
    with p.group('transform="translate(18 311) rotate(-90)"'):
        p.type(0, 0, 'FILTER   /   SHORT   /   BLACK', 5.5, rust, space=.6)
    with p.group('transform="translate(162 177) rotate(90)"'):
        p.type(0, 0, 'ROAST  07    •    NO.  234', 5.5, rust, space=.6)
    p.type(90, 415, 'TEL: 392 — 007', 10, ochre, font='Nimbus Sans Narrow', weight='bold', space=.6, anchor='middle')
    p.path('M18 425H162M18 428H162', stroke=rust, sw=1)
    p.rect(10, 439, 160, 91, pale)
    p.word('MIZ', 21, 450, 61, 18, midnight)
    p.word('QWE', 95, 451, 57, 18, midnight)
    p.path('M21 480H158M21 508H158M88 447V501', stroke=rust, sw=.9)
    p.type(21, 494, 'DRIP   03', 8, midnight, weight='bold')
    p.type(96, 494, 'MOKA  05', 8, midnight, weight='bold')
    p.type(90, 521, 'SERVED UNTIL LAST TRAM', 5.5, midnight, space=.75, anchor='middle')
    p.wear(87, 560, '#c9a579', .31)
    return p


def street():
    p = Plate(200, 500, '#d9cfb3')
    brick, paper, blue = '#ae5a50', '#e5d8bb', '#424c57'
    p.rect(9, 10, 182, 339, brick)
    p.path('M18 29V20H181V29M18 330V339H181V330', stroke=paper, sw=1.5)
    p.type(23, 42, 'SERVICE PASSAGE', 7.4, paper, weight='bold', space=1)
    p.type(177, 42, 'S.04', 7, paper, anchor='end')
    p.word('VF', 24, 68, 149, 92, paper, gap=1.8)
    p.path('M31 180H172', stroke='#d09171', sw=1.5)
    p.word('JH', 25, 201, 148, 91, paper, gap=1.8)
    p.path('M23 313H54M144 313H176', stroke='#d89980', sw=1.5)
    p.word('VJI', 70, 308, 59, 11, paper, gap=4)
    p.rect(10, 357, 180, 132, 'none', blue, 1.5)
    p.word('NECI', 19, 368, 106, 23, blue)
    p.type(178, 390, '04', 25, brick, font='Nimbus Sans Narrow', weight='bold', anchor='end')
    p.path('M18 401H182', stroke=blue, sw=1.2)
    p.path('M24 418H34V438L47 426 53 433 29 457 14 441 21 434 24 437Z', blue)
    p.type(64, 424, 'UNDERPASS', 8.2, blue, weight='bold', space=.7)
    p.type(64, 438, 'SOUTH STAIR', 7.8, blue, weight='bold', space=.55)
    p.type(64, 454, 'WALKING ACCESS', 5.9, brick, space=.55)
    p.path('M20 466H178', stroke=blue, sw=.8)
    p.type(20, 479, 'WORKS / 1210', 5.9, blue, space=.7)
    p.type(179, 479, 'REV. 15', 5.9, blue, space=.7, anchor='end')
    p.wear(711, 1080, '#e9d1ab', .58)
    return p


def parking():
    p = Plate(300, 300, '#d4cebb')
    red, bone, graphite = '#b84c46', '#e0dbc7', '#323846'
    p.oval(150, 150, 144, 144, red)
    p.oval(150, 150, 120, 120, bone)
    p.oval(150, 150, 139.5, 139.5, 'none', '#cd7261', .9)
    # Custom P, including its punched counter. The bar joins the annular red ink.
    p.path('M94 72H153Q200 72 200 114Q200 155 155 155H135V214H103V90H94Z '
           'M135 100V128H151Q168 128 168 114Q168 100 151 100Z', graphite)
    p.word('CDI', 178, 178, 29, 11, graphite, gap=4)
    p.type(150, 244, 'CURB ACCESS  /  03', 5.3, graphite, weight='bold', space=.85, anchor='middle')
    p.path('M53 62L70 46 247 236 229 252Z', red)
    p.wear(417, 480, '#c9b79d', .41)
    return p


def ricepaper():
    p = Plate(360, 360, '#f1cd8a')
    dark, vermilion = '#431d1b', '#873025'
    for cx in [90, 270]:
        with p.group(f'transform="translate({cx} 0)"'):
            # Flat ink only. Four sheets repeat the oval seal and notice above a clear foot.
            p.oval(0,124,80,86,'none',dark,5.2)
            p.path('M-49 76L-20 76 -23 85 -30 91 -30 152 -18 152 -18 127 -4 126 -4 174 '
                   '-57 174 -57 166 -49 159Z M10 79H56V175H34V97H10Z M6 113H20V175H6Z',dark)
            p.word('QJHV',-64,230,128,20,vermilion,gap=3.8)
            p.type(0,272,'SOUTH KETTLE  /  04',11,dark,font='Nimbus Sans Narrow',weight='bold',space=.7,anchor='middle')
            p.path('M-71 269V282H71V269','none',dark,3.5)
    p.wear(169, 750, '#c09c67', .24, margin=8)
    return p


def district():
    p = Plate(480, 240, '#ded8c0')
    ink, muted = '#313946', '#676960'
    p.path('M10 17L17 10H463L470 17V223L463 230H17L10 223Z', 'none', ink, 2.3)
    p.word('GJIM', 35, 31, 289, 69, ink, gap=3.2)
    p.type(443, 52, 'WARD', 10, muted, weight='bold', anchor='end', space=.8)
    p.type(443, 69, 'SOUTH', 10, muted, weight='bold', anchor='end', space=.8)
    p.path('M368 79H443M368 84H443', stroke=muted, sw=1)
    p.path('M10 118H470', stroke=ink, sw=2.3)
    p.type(35, 206, '15', 92, ink, font='DejaVu Serif')
    p.path('M210 173H242', stroke=ink, sw=5)
    p.word('KLJ', 367, 157, 74, 20, muted)
    p.type(443, 197, 'STREET REGISTER', 7.3, muted, weight='bold', space=.6, anchor='end')
    p.wear(514, 480, '#acc0ae', .3)
    return p


def water_seal(p, x, y, scale, color):
    with p.group(f'transform="translate({x} {y}) rotate(-11) scale({scale})"'):
        p.oval(0, 0, 22, 22, 'none', color, 1.9)
        p.oval(0, 0, 18.8, 18.8, 'none', color, .65)
        for angle in range(0, 360, 30):
            with p.group(f'transform="rotate({angle})"'):
                p.path('M0-19V-16', stroke=color, sw=.8)
        p.path('M0-13Q-2-8-7-2Q-12 6-5 9Q0 13 6 8Q11 4 6-4Z '
               'M-5 2Q-1 5 4 1Q3 7-2 7Q-5 6-5 2Z', color)
        p.path('M-8 13H8', stroke=color, sw=1.2)


def notices():
    p = Plate(320, 480, '#b7aa8c')
    ink, blue, red = '#48483f', '#536a68', '#a65a47'
    ivory, olive, buff = '#ded3ad', '#c9c2a1', '#c6ae8b'
    # Earlier editions left on the board, peeking through the torn paper edges.
    p.word('CRJF', -9, 2, 320, 67, '#8e896e')
    p.word('VFAJ', 13, 405, 290, 46, '#887e6a')
    p.path('M1 60H318V70H1Z M6 228H317V242H6Z M19 463H309V470H19Z', '#8f8a72')
    p.path('M9 11L97 10 103 13 209 10 295 10 297 61 294 80 298 226 '
           '282 228 277 225 267 232 236 228 202 230 191 227 151 232 140 228 '
           '97 230 85 226 71 230 40 227 25 231 10 227 13 175 9 161Z', ivory)
    water_seal(p, 32, 34, .65, blue)
    p.type(53, 30, 'DISTRICT 15 / PUBLIC WORKS', 7.2, ink, weight='bold', space=.45)
    p.type(53, 41, 'WATER OFFICE   •   MAINTENANCE CIRCULAR', 5.3, blue, space=.25)
    p.type(282, 31, 'W / 14', 7, red, weight='bold', anchor='end')
    p.type(282, 41, '19 NOV', 5.5, ink, anchor='end')
    p.rect(19, 53, 267, 38, blue)
    p.word('VJRK', 24, 61, 113, 22, ivory)
    p.type(278, 71, 'NIGHT WATER', 10, ivory, font='Nimbus Sans Narrow', weight='bold', space=.6, anchor='end')
    p.type(278, 82, 'BOARD 03 / ISSUE 27', 5.2, ivory, space=.45, anchor='end')
    p.rect(20, 101, 122, 92, 'none', blue, 1.1)
    p.type(26, 112, 'A. SERVICE LOOP', 5.1, ink, weight='bold', space=.4)
    p.path('M25 132H57V121H91V141H135M30 173H71V159H87V178H132 '
           'M43 116V188M110 116V184', 'none', '#b2b5a0', 1)
    p.path('M25 165H53L66 152H82V125H111L124 138H136', 'none', blue, 2.8)
    for x, y in [(38, 165), (66, 152), (82, 125), (124, 138)]:
        p.oval(x, y, 3.5, 3.5, ivory, blue, 1.3)
    p.oval(82, 145, 6.5, 6.5, 'none', red, 1.4)
    p.path('M77 150l10-10', stroke=red, sw=1.25)
    p.type(26, 184, 'STOP 04 → 12', 5.6, red, weight='bold')
    p.word('QIMCE', 153, 101, 128, 15, ink)
    p.type(154, 130, 'Supply resumes after', 6.6, ink)
    p.type(154, 140, 'the second bell.', 6.6, ink)
    p.type(154, 151, 'Bring a marked vessel.', 6.4, ink)
    p.path('M153 159H282', stroke=blue, sw=.8)
    p.word('HUBFY', 153, 166, 82, 7, blue)
    p.word('CQJMI', 153, 177, 98, 7, blue)
    p.path('M21 202H285', stroke=ink, sw=1.1)
    p.type(22, 216, 'PUMP OFFICE  /  ISSUED IN DUPLICATE  /  15—07', 5.25, ink, weight='bold', space=.24)
    water_seal(p, 265, 198, .92, red)
    # Two smaller, separately printed sheets. No shadows between the layers.
    p.path('M3 243L31 241 48 245 89 242 110 245 132 241 187 243 '
           '189 292 186 342 190 461 173 459 160 462 151 458 140 463 123 458 '
           '111 462 104 459 90 463 79 459 64 463 51 457 37 462 20 458 4 462Z', olive)
    p.rect(12, 253, 168, 22, red)
    p.type(19, 268.5, 'FILTER EXCHANGE', 11.2, ivory, font='Nimbus Sans Narrow', weight='bold', space=1.2)
    p.word('LEWQ', 15, 283, 114, 19, ink, gap=3.1)
    p.type(173, 299, 'III.', 10, ink, font='DejaVu Serif', anchor='end')
    p.path('M14 311H178', stroke=ink, sw=1.2)
    # Orthographic service drawing of a filter and its replaceable cartridge.
    p.path('M32 331H70V338H32Z M36 340H65V371L61 376H40L36 371Z '
           'M29 327H73V331H29Z M37 376H64V379H37Z', 'none', ink, 1.6)
    p.path('M23 341h9m37 0h11m-37 3v24m5-24v27m5-27v27m5-27v24m23-31h24l7-9h54', 'none', blue, 1)
    p.type(115, 325, 'ELEMENT 12', 5.5, ink, weight='bold')
    p.word('UIK', 87, 344, 58, 10, blue)
    p.type(87, 365, 'Swap at booth 6.', 5.6, ink)
    p.type(87, 375, 'Keep your tag.', 5.6, ink)
    p.path('M14 388H178M14 409H178', stroke=blue, sw=.9)
    p.type(16, 401, 'VALID 17—22   /   QUEUE TICKETS', 5.6, ink, weight='bold', space=.2)
    for i in range(5):
        left = 13 + i * 34
        p.path(f'M{left} 414V457', stroke=ink, sw=.75, extra='stroke-dasharray="2 2"')
        p.type(left + 4, 431, f'{24 + i:02}', 9.4, red, weight='bold')
        p.word('IM', left + 5, 437, 19, 9, blue)
    p.path('M197 233L224 235 231 232 271 235 312 231 314 289 311 315 315 455 '
           '303 458 287 454 274 459 235 455 220 460 195 455 198 413 194 398Z', buff)
    p.path('M203 246H306M203 249H306M203 441H306', stroke=ink, sw=1.1)
    p.type(255, 266, 'BELL TEST', 11.6, ink, font='Nimbus Sans Narrow', weight='bold', space=1, anchor='middle')
    p.type(255, 277, '03 / AFTER DUSK', 5.5, red, weight='bold', space=.4, anchor='middle')
    p.oval(255, 321, 33, 33, 'none', red, 2.6)
    p.oval(255, 321, 29.6, 29.6, 'none', red, .8)
    p.path('M240 331Q245 327 245 319Q245 308 252 306V303H258V306Q265 309 265 319 '
           'Q265 327 270 331V334H240Z M251 336H259Q255 344 251 336Z', ink)
    p.path('M238 311Q233 317 235 322M272 310Q277 316 276 323', 'none', red, 1.4)
    p.word('DEJ', 207, 370, 94, 19, ink)
    p.type(255, 406, 'TOWER  /  SOUTH', 6.8, ink, weight='bold', space=.4, anchor='middle')
    p.type(255, 420, 'KEEP THIS NOTICE', 5.2, red, space=.45, anchor='middle')
    p.wear(2215, 1500, '#9e937a', .46)
    p.wear(3225, 850, '#e7d6b0', .46)
    return p


DESIGNS = (billboard, pharmacy, noodle, marquee, cinema, menubox, street,
           parking, ricepaper, district, notices)


def save_srgb(image, path):
    metadata = PngImagePlugin.PngInfo()
    metadata.add(b'sRGB', b'\x00')  # IEC 61966-2-1; perceptual rendering intent.
    image.save(path, format='PNG', pnginfo=metadata, optimize=True)


def proof_sheet(prints, path):
    sheet = Image.new('RGB', (1476, 846), '#303333')
    pen = ImageDraw.Draw(sheet)
    title = ImageFont.truetype('DejaVuSans.ttf', 23)
    caption = ImageFont.truetype('DejaVuSansMono.ttf', 14)
    small = ImageFont.truetype('DejaVuSansMono.ttf', 12)
    pen.text((24, 15), 'Night Market  /  sign shop', fill='#e5e2d8', font=title)
    pen.text((1450, 28), 'FLAT PRINT PROOFS   /   sRGB   /   11 FACES',
             fill='#bcc4bd', font=small, anchor='rm')
    pen.line((24, 56, 1451, 56), fill='#686d67')
    placements = [('billboard', 24, 79, 540), ('pharmacy', 589, 79, 416), ('noodle', 1034, 79, 416),
                  ('cinema', 24, 325, 288), ('menubox', 341, 325, 120), ('street', 492, 325, 144),
                  ('notices', 669, 325, 240), ('marquee', 953, 325, 205), ('parking', 1213, 325, 205),
                  ('ricepaper', 953, 589, 205), ('district', 1213, 589, 237)]
    for name, x, y, width in placements:
        src = prints[name]
        height = round(width * src.height / src.width)
        sample = src.resize((width, height), Image.Resampling.LANCZOS)
        if name in ('marquee', 'parking'):
            # Preview only: show the centered, circular mesh crop without altering the plate.
            mask = Image.new('L', (4 * width, 4 * height), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 4 * width - 1, 4 * height - 1), fill=255)
            sheet.paste(sample, (x, y), mask.resize(sample.size, Image.Resampling.LANCZOS))
        else:
            sheet.paste(sample, (x, y))
        pen.text((x, y + height + 7), name, fill='#e1e0d6', font=caption)
        pen.text((x, y + height + 25), f'{src.width} × {src.height}', fill='#b4bcb5', font=small)
    path.parent.mkdir(parents=True, exist_ok=True)
    save_srgb(sheet, path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--proof', type=Path, help='also write an inspection sheet outside the asset directory')
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    prints = {}
    for design in DESIGNS:
        name = design.__name__
        image = design().render()
        save_srgb(image, OUT / f'{name}.png')
        print(f'{name}.png: {image.width} x {image.height}')
        if args.proof:
            prints[name] = image
    if args.proof:
        proof_sheet(prints, args.proof)


if __name__ == '__main__':
    main()
