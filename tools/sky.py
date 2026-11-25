"""Draws sky.svg, the star field behind the night ground of every page.

Run from the site folder:

  python3 tools/sky.py            write sky.svg
  python3 tools/sky.py --check    exit 1 if sky.svg is out of date

site.css sets the file as the body's background, where it repeats, so the stars
run from the top of each page down to the dawn. They are placed by a seeded
generator: the file is the same on every run. The brighter stars at the top of
each page and the ones above the dawn are drawn by site.js on top of these.
Colors are read from site.css (--moon, --agent, --lamp).
"""
import pathlib
import random
import re
import sys

SITE = pathlib.Path(__file__).resolve().parent.parent
W, H = 1600, 1800          # one tile, in CSS pixels
COUNT = 480                # about one star in every 6,000 square pixels
EDGE = 3                   # keep stars off the seam between tiles


def draw():
    css = (SITE / "site.css").read_text(encoding="utf-8")
    color = {}
    for name in ("moon", "agent", "lamp"):
        m = re.search(r"--%s:\s*(#[0-9A-Fa-f]{6})\s*;" % name, css)
        if not m:
            raise SystemExit("--%s not found in site.css" % name)
        color[name] = m.group(1)
    rand = random.Random(2026).random
    stars = {name: [] for name in color}
    for _ in range(COUNT):
        x = EDGE + rand() * (W - 2 * EDGE)
        y = EDGE + rand() * (H - 2 * EDGE)
        r = 0.35 + rand() ** 3 * 1.15
        alpha = 0.18 + rand() * 0.48
        tint = ("moon", "moon", "moon", "moon", "agent", "lamp")[int(rand() * 6)]
        stars[tint].append('<circle cx="%.1f" cy="%.1f" r="%.2f" opacity="%.2f"/>' % (x, y, r, alpha))
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (W, H, W, H)]
    for name in ("moon", "agent", "lamp"):
        out.append('<g fill="%s">' % color[name])
        out.extend(stars[name])
        out.append("</g>")
    out.append("</svg>")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    path, svg = SITE / "sky.svg", draw()
    if "--check" in sys.argv[1:]:
        if not path.exists() or path.read_text(encoding="utf-8") != svg:
            raise SystemExit("sky: sky.svg is out of date. Run python3 tools/sky.py")
        print("sky: up to date")
    else:
        path.write_text(svg, encoding="utf-8")
        print("sky: wrote sky.svg (%d stars, %d bytes)" % (COUNT, len(svg)))
