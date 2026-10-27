# Radiant Robotics brand kit

## Logo files

Everything in `logo/` is a true vector SVG. The wordmark is Inter Bold converted
to outlines, so it looks the same everywhere without the font installed. Use the
SVG wherever you can. High-resolution PNGs with transparent backgrounds are in
`logo/png/` for tools that don't accept SVG.

| File | Use it for |
| --- | --- |
| `radiant-robotics-horizontal.svg` | Default logo on white or light backgrounds |
| `radiant-robotics-stacked.svg` | Square-ish spaces: posters, shirts, banners |
| `radiant-robotics-horizontal-reversed.svg` / `-stacked-reversed.svg` | Dark backgrounds |
| `radiant-robotics-stacked-mark.svg` / `-stacked-mark-reversed.svg` | Alternate stacked logo: the mark, scaled so its R starts both words, followed by "adiant" over "obotics" |
| `radiant-robotics-horizontal-black.svg` / `-white.svg` | One-color printing, engraving, embroidery |
| `radiant-robotics-mark.svg` | Small spaces where the full name won't fit |
| `radiant-robotics-mark-reversed.svg` | The mark on dark backgrounds |
| `radiant-robotics-mark-tile.svg` | App icons, social avatars, favicon |
| `radiant-robotics-burst.svg` / `-burst-reversed.svg` | The half starburst alone, as a decorative graphic |
| `radiant-robotics-burst-full.svg` / `-burst-full-reversed.svg` | The complete starburst: stickers, patterns, backgrounds |

Leave clear space around the logo at least the height of the lowercase "a".
Don't stretch, recolor, rotate, or add effects to it.

### The mark

The mark is the starburst beside a single R. The R is gold above the burst's
center line and purple below, and the burst's horizontal ray, mirrored and
slightly enlarged, is cut through it, so the light seems to shine through the
letter. The R keeps its sharp corners; only the corners the ray cut leaves are
rounded.

## Colors

| Name | Hex | Use |
| --- | --- | --- |
| Radiant Gold | `#E5A14C` | "Radiant", accents, primary buttons (with dark text) |
| Radiant Purple | `#70598B` | "Robotics", links, secondary buttons |
| Night | `#1E1630` | Dark backgrounds, footer |
| Lavender | `#B9A7D6` | Purple's stand-in on dark backgrounds |
| Ink | `#1B1426` | Body text, one-color logo |

Gold is too light for text on white. For gold text on a light background use
`#8F5A14`.

## Typography

[Inter](https://rsms.me/inter/) for everything. Headings in Bold or ExtraBold
with slightly tight letter spacing; body text in Regular.

## Rebuilding the files

The SVGs, PNGs, favicons, and social preview image are all generated:

```bash
pip install fonttools uharfbuzz shapely
brand/tools/export.sh path/to/Inter-Bold.ttf
```

Change ray angles or sizes in the `RAYS` table in `tools/build_logos.py`, the
mark's ray cut with `MARK_RAY_PAD` and `MARK_CUT_FILLET`, and the social image
layout in `tools/og-image.html`.
