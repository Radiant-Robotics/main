"""Build the Radiant Robotics logo SVGs.

The wordmark is set in Inter Bold and converted to outlines, so the SVGs
render identically everywhere without the font installed. The starburst is
drawn from the ray table below.

Usage:
    pip install fonttools uharfbuzz shapely
    python build_logos.py path/to/Inter-Bold.ttf ../

Inter is available from https://rsms.me/inter/ (SIL Open Font License).
"""
import math
import sys
from pathlib import Path

import uharfbuzz as hb
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from shapely.affinity import affine_transform
from shapely.geometry import Polygon, box

GOLD = "#E5A14C"
PURPLE = "#70598B"
WHITE = "#FFFFFF"
LAVENDER = "#B9A7D6"
INK = "#1B1426"

# Rays of the half starburst. Angle is degrees above the leftward horizontal,
# radii are fractions of the burst radius, width is the ray's widest point.
RAYS = [
    # angle, inner, outer, width
    (0, 0.16, 1.00, 0.085),
    (11, 0.49, 0.86, 0.028),
    (21, 0.36, 0.63, 0.030),
    (38, 0.17, 0.97, 0.085),
    (57, 0.33, 0.57, 0.030),
    (81, 0.45, 0.79, 0.026),
    (90, 0.17, 1.00, 0.085),
]


class Font:
    def __init__(self, path):
        self.tt = TTFont(path)
        self.glyphs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.upm = self.tt["head"].unitsPerEm
        self.cap = self.tt["OS/2"].sCapHeight
        blob = hb.Blob.from_file_path(str(path))
        self.hb = hb.Font(hb.Face(blob))

    def text_path(self, text, x, y, scale):
        """SVG path data for `text` with its baseline at (x, y)."""
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, {"kern": True, "liga": True})
        pen = SVGPathPen(self.glyphs, ntos=lambda v: f"{v:.2f}".rstrip("0").rstrip("."))
        cursor = 0
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            name = self.order[info.codepoint]
            tx = x + (cursor + pos.x_offset) * scale
            ty = y - pos.y_offset * scale
            self.glyphs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, tx, ty)))
            cursor += pos.x_advance
        return pen.getCommands(), cursor * scale

    def ink_bounds(self, text):
        """Left side bearing and ink width of `text`, in font units."""
        from fontTools.pens.boundsPen import BoundsPen

        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.hb, buf, {"kern": True})
        xmin, xmax, cursor = math.inf, -math.inf, 0
        for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
            bp = BoundsPen(self.glyphs)
            self.glyphs[self.order[info.codepoint]].draw(bp)
            if bp.bounds:
                xmin = min(xmin, cursor + bp.bounds[0])
                xmax = max(xmax, cursor + bp.bounds[2])
            cursor += pos.x_advance
        return xmin, xmax

    def glyph_polygon(self, char, steps=48):
        """A glyph's outline as a shapely polygon in font units, curves flattened."""
        rec = RecordingPen()
        self.glyphs[self.tt.getBestCmap()[ord(char)]].draw(rec)
        rings, ring = [], []
        for op, args in rec.value:
            if op == "moveTo":
                ring = [args[0]]
            elif op == "lineTo":
                ring.append(args[0])
            elif op == "qCurveTo":
                # TrueType quadratic spline: on-curve points are implied between off-curves.
                pts = [ring[-1], *args]
                for i in range(1, len(pts) - 1):
                    mid = lambda a, b: ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                    p0 = pts[0] if i == 1 else mid(pts[i - 1], pts[i])
                    p2 = pts[-1] if i == len(pts) - 2 else mid(pts[i], pts[i + 1])
                    for k in range(1, steps + 1):
                        t = k / steps
                        ring.append(tuple((1 - t) ** 2 * p0[j] + 2 * t * (1 - t) * pts[i][j] + t * t * p2[j]
                                          for j in (0, 1)))
            elif op in ("closePath", "endPath"):
                rings.append(ring)
        outer = max(rings, key=lambda r: Polygon(r).area)
        return Polygon(outer, [r for r in rings if r is not outer]).buffer(0)


def fmt(v):
    return f"{v:.2f}".rstrip("0").rstrip(".")


def ray_path(cx, cy, radius, angle, inner, outer, width):
    """A tapered kite: blunt point at the inner end, needle at the outer end."""
    a = math.radians(180 - angle)
    ux, uy = math.cos(a), -math.sin(a)  # outward direction (SVG y is down)
    px, py = -uy, ux
    r0, r1, w = inner * radius, outer * radius, width * radius
    shoulder = r0 + w * 0.9
    pts = [
        (cx + ux * r0, cy + uy * r0),
        (cx + ux * shoulder + px * w / 2, cy + uy * shoulder + py * w / 2),
        (cx + ux * r1, cy + uy * r1),
        (cx + ux * shoulder - px * w / 2, cy + uy * shoulder - py * w / 2),
    ]
    return "M" + "L".join(f"{fmt(x)} {fmt(y)}" for x, y in pts) + "Z"


def burst_paths(cx, cy, radius, full=False):
    """Returns (upper rays, horizontal + lower rays) path data.

    `full` mirrors the rays to the right for a complete burst.
    """
    upper, lower = [], []
    for angle, inner, outer, width in RAYS:
        sides = [0, 180] if full and angle != 90 else [0]
        for side in sides:
            # Mirroring across the vertical axis maps angle a to 180 - a.
            a = side - angle if side else angle
            if angle == 0:
                lower.append(ray_path(cx, cy, radius, side, inner, outer, width))
                continue
            upper.append(ray_path(cx, cy, radius, a, inner, outer, width))
            lower.append(ray_path(cx, cy, radius, -a, inner, outer, width))
    return "".join(upper), "".join(lower)


def svg(width, height, layers, title):
    body = "\n".join(f'  <path fill="{fill}" d="{d}"/>' for fill, d in layers if d)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {fmt(width)} {fmt(height)}" '
        f'role="img" aria-label="{title}">\n  <title>{title}</title>\n{body}\n</svg>\n'
    )


# Everything below is measured in "cap units": the cap height of the wordmark is 100.
PAD = 12


def horizontal(font, top, bottom, burst_top, burst_bottom):
    s = 100 / font.cap
    radius = 56
    cx = PAD + radius
    cy = PAD + radius
    baseline = cy + 50
    lsb, _ = font.ink_bounds("Radiant")
    x = cx + 16 - lsb * s
    d_rad, adv = font.text_path("Radiant", x, baseline, s)
    space = font.hb.get_glyph_h_advance(font.hb.get_nominal_glyph(ord(" "))) * s
    rob_x = x + adv + space
    d_rob, _ = font.text_path("Robotics", rob_x, baseline, s)
    _, rob_xmax = font.ink_bounds("Robotics")
    width = rob_x + rob_xmax * s + PAD
    up, low = burst_paths(cx, cy, radius)
    return svg(width, cy + radius + PAD,
               [(burst_top, up), (burst_bottom, low), (top, d_rad), (bottom, d_rob)],
               "Radiant Robotics")


def stacked(font, top, bottom, burst_top, burst_bottom):
    s = 100 / font.cap
    leading = 0.77 * font.upm * s  # baseline to baseline, matches the original lockup
    radius = 100
    cx = PAD + radius
    # The burst centres on the gap between the two lines.
    ascent = 106  # tallest ink in "Radiant" (the d ascender) above its baseline
    base1 = PAD + ascent
    base2 = base1 + leading
    cy = (base1 - 100 + base2) / 2
    burst_top_y = cy - radius
    shift = max(0, PAD - burst_top_y)
    base1, base2, cy = base1 + shift, base2 + shift, cy + shift
    lsb, xmax1 = font.ink_bounds("Radiant")
    lsb2, xmax2 = font.ink_bounds("Robotics")
    x = cx + 26 - lsb * s
    d_rad, _ = font.text_path("Radiant", x, base1, s)
    d_rob, _ = font.text_path("Robotics", x + (lsb - lsb2) * s, base2, s)
    width = x + max(xmax1, xmax2 - lsb2 + lsb) * s + PAD
    height = max(base2, cy + radius) + PAD
    up, low = burst_paths(cx, cy, radius)
    return svg(width, height,
               [(burst_top, up), (burst_bottom, low), (top, d_rad), (bottom, d_rob)],
               "Radiant Robotics")


def poly_path(geom):
    """SVG path data for a shapely polygon or multipolygon."""
    d = ""
    for poly in getattr(geom, "geoms", [geom]):
        if poly.is_empty:
            continue
        for ring in [poly.exterior, *poly.interiors]:
            d += "M" + "L".join(f"{fmt(x)} {fmt(y)}" for x, y in list(ring.coords)[:-1]) + "Z"
    return d


def ray_polygon(cx, cy, radius, angle, inner, outer, width):
    d = ray_path(cx, cy, radius, angle, inner, outer, width)
    return Polygon([tuple(map(float, q.split())) for q in d[1:-1].split("L")])


def round_cut_corners(shape, cutter, r):
    """Cut `cutter` out of `shape` and round the corners the cut creates.

    Rounding opens the whole shape (shrink, then grow back), but only the
    change near the cut is kept, so the letter's own corners stay sharp. The
    cut's own points, such as the tip of a ray, are inside corners and stay sharp.
    """
    cut = shape.difference(cutter)
    opened = cut.buffer(-r, join_style="round", quad_segs=16).buffer(r, join_style="round", quad_segs=16)
    rounded_off = cut.difference(opened).intersection(cutter.buffer(3 * r))
    return cut.difference(rounded_off)


# The mark's R: the burst's horizontal ray, mirrored and a little larger, is cut
# through it so the light seems to shine through the letter.
MARK_RAY_PAD = 3        # cap units added around the ray (wider, and longer at both ends)
MARK_CUT_FILLET = 0.94  # cap units: radius on the corners the cut leaves in the R


def mark(font, tile=None, top=GOLD, bottom=PURPLE, zoom=1.0):
    """Square icon: the burst beside an R, gold above the burst's centre line and
    purple below, with a ray of light cut through it. Used for favicons and avatars."""
    s = 100 / font.cap * zoom
    size = 256
    radius = 92 * zoom
    gap = 18 * zoom
    lsb, xmax = font.ink_bounds("R")
    r_w = (xmax - lsb) * s
    group_w = radius + gap + r_w
    cx = (size - group_w) / 2 + radius
    cy = size / 2
    letter = affine_transform(font.glyph_polygon("R"), [s, 0, 0, -s, cx + gap - lsb * s, cy + 50 * zoom])
    angle, inner, outer, width = RAYS[0]
    grow = MARK_RAY_PAD / 92
    ray = ray_polygon(cx, cy, radius, 180 - angle, inner - grow, outer + grow, width + 2 * grow)
    letter = round_cut_corners(letter, ray, MARK_CUT_FILLET * zoom)
    up, low = burst_paths(cx, cy, radius)
    layers = [(top, up), (bottom, low),
              (top, poly_path(letter.intersection(box(0, 0, size, cy)))),
              (bottom, poly_path(letter.intersection(box(0, cy, size, size))))]
    bg = ""
    if tile:
        bg = f'  <rect width="{size}" height="{size}" rx="56" fill="{tile}"/>\n'
    body = "\n".join(f'  <path fill="{fill}" d="{d}"/>' for fill, d in layers)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" role="img" '
        f'aria-label="Radiant Robotics">\n  <title>Radiant Robotics</title>\n{bg}{body}\n</svg>\n'
    )


def stacked_mark(font, top, bottom, burst_top, burst_bottom):
    """The alternate stacked logo: the mark, scaled so its R spans both lines and
    serves as the R of both words, followed by "adiant" over "obotics"."""
    from shapely.geometry import LineString

    s = 100 / font.cap
    leading = 0.77 * font.upm * s
    k = (100 + leading) / 100        # the R's size relative to the mark's
    radius = 92 * k                  # burst, gap and ray cut keep the mark's proportions
    gap = 18 * k
    cx = PAD + radius
    cy = PAD + radius
    base2 = cy + 50 * k
    base1 = base2 - leading
    lsb, _ = font.ink_bounds("R")
    letter = affine_transform(font.glyph_polygon("R"), [s * k, 0, 0, -s * k, cx + gap - lsb * s * k, base2])
    angle, inner, outer, width = RAYS[0]
    grow = MARK_RAY_PAD / 92
    ray = ray_polygon(cx, cy, radius, 180 - angle, inner - grow, outer + grow, width + 2 * grow)
    # The ray must reach past the R's right edge on the centre line.
    edge = letter.intersection(LineString([(0, cy), (4000, cy)])).bounds[2]
    if (edge + 4 - cx) / radius > outer + grow:
        ray = ray_polygon(cx, cy, radius, 180 - angle, inner - grow, (edge + 4 - cx) / radius, width + 2 * grow)
    letter = round_cut_corners(letter, ray, MARK_CUT_FILLET * k)

    r_right = letter.bounds[2]
    lsb_a, xmax_a = font.ink_bounds("adiant")
    lsb_o, xmax_o = font.ink_bounds("obotics")
    x_a = r_right + 7 - lsb_a * s
    x_o = r_right + 7 - lsb_o * s
    d_a, _ = font.text_path("adiant", x_a, base1, s)
    d_o, _ = font.text_path("obotics", x_o, base2, s)
    width_total = max(x_a + xmax_a * s, x_o + xmax_o * s) + PAD
    up, low = burst_paths(cx, cy, radius)
    return svg(width_total, cy + radius + PAD,
               [(burst_top, up), (burst_bottom, low),
                (top, poly_path(letter.intersection(box(0, 0, 4000, cy)))),
                (bottom, poly_path(letter.intersection(box(0, cy, 4000, 4000)))),
                (top, d_a), (bottom, d_o)],
               "Radiant Robotics")


def burst_only(top=GOLD, bottom=PURPLE):
    """The starburst on its own, for decoration and social graphics."""
    radius = 100
    cx, cy = radius + 4, radius + 4
    up, low = burst_paths(cx, cy, radius)
    return svg(cx + 10, cy + radius + 4, [(top, up), (bottom, low)], "Radiant Robotics starburst")


def burst_full(top=GOLD, bottom=PURPLE):
    """The complete starburst, mirrored left and right."""
    radius = 100
    c = radius + 4
    up, low = burst_paths(c, c, radius, full=True)
    return svg(2 * c, 2 * c, [(top, up), (bottom, low)], "Radiant Robotics starburst")


def main():
    font = Font(sys.argv[1])
    out = Path(sys.argv[2])
    (out / "logo").mkdir(parents=True, exist_ok=True)
    files = {
        "radiant-robotics-horizontal.svg": horizontal(font, GOLD, PURPLE, GOLD, PURPLE),
        "radiant-robotics-stacked.svg": stacked(font, GOLD, PURPLE, GOLD, PURPLE),
        "radiant-robotics-horizontal-reversed.svg": horizontal(font, GOLD, LAVENDER, GOLD, LAVENDER),
        "radiant-robotics-stacked-reversed.svg": stacked(font, GOLD, LAVENDER, GOLD, LAVENDER),
        "radiant-robotics-stacked-mark.svg": stacked_mark(font, GOLD, PURPLE, GOLD, PURPLE),
        "radiant-robotics-stacked-mark-reversed.svg": stacked_mark(font, GOLD, LAVENDER, GOLD, LAVENDER),
        "radiant-robotics-horizontal-black.svg": horizontal(font, INK, INK, INK, INK),
        "radiant-robotics-horizontal-white.svg": horizontal(font, WHITE, WHITE, WHITE, WHITE),
        "radiant-robotics-mark.svg": mark(font),
        "radiant-robotics-mark-reversed.svg": mark(font, bottom=LAVENDER),
        "radiant-robotics-mark-tile.svg": mark(font, tile="#2A1F3D", bottom=LAVENDER, zoom=1.15),
        "radiant-robotics-burst.svg": burst_only(),
        "radiant-robotics-burst-reversed.svg": burst_only(bottom=LAVENDER),
        "radiant-robotics-burst-full.svg": burst_full(),
        "radiant-robotics-burst-full-reversed.svg": burst_full(bottom=LAVENDER),
    }
    for name, content in files.items():
        (out / "logo" / name).write_text(content)
        print("wrote", out / "logo" / name)


if __name__ == "__main__":
    main()
