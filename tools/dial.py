#!/usr/bin/env python3
"""Draws the night dial in index.html.

Run from the repository root:  python3 tools/dial.py

It rewrites the block between the "dial:start" and "dial:end" comments.
Geometry is in SVG units around a centre of (300, 300). Midnight is at the
top and the hours run clockwise, once round in 24 hours. Colours that the
page can theme are set by class in index.html; only the dusk and dawn taper
is coloured here, because each step has its own width and colour.
"""
import math
import pathlib
import random
import re

C = 300
BAND = 250          # the sky band, where the events sit
EVENTS = [          # (hour, minute, who) for the example night
    (23, 42, "agent"), (1, 7, "agent"), (2, 30, "agent"), (3, 18, "agent"),
    (8, 5, "person"), (8, 40, "person"),
]
NIGHT = (0x39, 0x42, 0x72)
ROSE = (0xA8, 0x56, 0x74)
DAY = (0x9F, 0x74, 0x49)
TAPER_HOURS = 1.5    # how long night takes to fall and to lift
TAPER_STEPS = 28


def pt(hours, r):
    a = math.radians(hours / 24 * 360)
    return C + r * math.sin(a), C - r * math.cos(a)


def n(v):
    return ("%.1f" % v).rstrip("0").rstrip(".")


def arc(h0, h1, attrs=""):
    x0, y0 = pt(h0, BAND)
    x1, y1 = pt(h1, BAND)
    large = 1 if (h1 - h0) % 24 > 12 else 0
    return '<path d="M %s %s A %d %d 0 %d 1 %s %s"%s/>' % (n(x0), n(y0), BAND, BAND, large, n(x1), n(y1), attrs)


def hexa(rgb):
    return "#%02X%02X%02X" % rgb


def taper(start, rising, fill):
    """One filled shape whose width eases between the day line and the night band."""
    outer, inner = [], []
    for k in range(TAPER_STEPS + 1):
        t = k / TAPER_STEPS
        s = t * t * (3 - 2 * t)
        half = (3 + 17 * (s if rising else 1 - s)) / 2
        h = start + t * TAPER_HOURS
        outer.append(pt(h, BAND + half))
        inner.append(pt(h, BAND - half))
    points = outer + inner[::-1]
    d = "M " + " L ".join("%s %s" % (n(x), n(y)) for x, y in points) + " Z"
    return '<path d="%s" fill="url(#%s)"/>' % (d, fill)


def gradient(name, start, colours):
    x0, y0 = pt(start, BAND)
    x1, y1 = pt(start + TAPER_HOURS, BAND)
    stops = "".join('<stop offset="%s" stop-color="%s"/>' % (o, hexa(c)) for o, c in zip(("0", ".5", "1"), colours))
    return '<linearGradient id="%s" gradientUnits="userSpaceOnUse" x1="%s" y1="%s" x2="%s" y2="%s">%s</linearGradient>' % (name, n(x0), n(y0), n(x1), n(y1), stops)


def sky():
    dusk, dawn = 18, 8 - TAPER_HOURS
    night = ' stroke="%s" stroke-width="20"' % hexa(NIGHT)
    day = ' stroke="%s" stroke-width="3"' % hexa(DAY)
    parts = [arc(dusk + TAPER_HOURS - 0.004, 1, night), arc(1, dawn + 0.004, night), arc(8 - 0.004, 18.004, day)]
    parts += [taper(dusk, True, "dial-dusk"), taper(dawn, False, "dial-dawn")]
    rand = random.Random(11)
    span = 24 - TAPER_HOURS * 2 - 10 - 0.4      # the hours of full night, less a margin
    for _ in range(44):
        h = (dusk + TAPER_HOURS + 0.2 + rand.random() * span) % 24
        x, y = pt(h, BAND + rand.uniform(-7.5, 7.5))
        parts.append('<circle cx="%s" cy="%s" r="%s" opacity="%s"/>' % (n(x), n(y), n(0.5 + rand.random() ** 2 * 0.9), n(0.3 + rand.random() * 0.6)))
    return parts


def hours():
    out = []
    for h in range(24):
        x, y = pt(h, 204)
        if h == 0:
            out.append('<text class="cardinal" x="300" y="%s" text-anchor="middle">Midnight</text>' % n(y + 6))
        elif h == 12:
            out.append('<text class="cardinal" x="300" y="%s" text-anchor="middle">Noon</text>' % n(y + 6))
        elif h == 6:
            out.append('<text class="cardinal side" x="%d" y="306" text-anchor="middle">6 AM</text>' % (C + 201))
        elif h == 18:
            out.append('<text class="cardinal side" x="%d" y="306" text-anchor="middle">6 PM</text>' % (C - 201))
        else:
            out.append('<text x="%s" y="%s" text-anchor="middle">%d</text>' % (n(x), n(y + 6), h % 12 or 12))
    return out


def marks():
    out = []
    for i, (hh, mm, who) in enumerate(EVENTS):
        h = hh + mm / 60
        a = math.radians(h / 24 * 360)
        c, s = math.cos(a), math.sin(a)
        x, y = pt(h, BAND)
        l0, l1 = pt(h, 262), pt(h, 271)
        tx, ty = pt(h, 277)
        anchor = ' text-anchor="end"' if s < 0 else ""
        tx += -5 if s < 0 else 5
        ty += 6 - 8 * c if c > 0 else 6 - 6 * c
        label = "%d:%02d %s" % (hh % 12 or 12, mm, "AM" if hh < 12 else "PM")
        out.append(
            '<g class="mark by-%s" data-i="%d" aria-hidden="true">'
            '<circle class="hit" cx="%s" cy="%s" r="20"/>'
            '<line class="lead" x1="%s" y1="%s" x2="%s" y2="%s"/>'
            '<circle class="dot" cx="%s" cy="%s" r="7.5"/>'
            '<text x="%s" y="%s"%s>%s</text></g>'
            % (who, i, n(x), n(y), n(l0[0]), n(l0[1]), n(l1[0]), n(l1[1]), n(x), n(y), n(tx), n(ty), anchor, label)
        )
    return out


def build():
    pad = "            "
    rows = [
        '<svg class="dial" viewBox="-20 0 640 576" role="img" aria-labelledby="dial-title dial-desc">',
        '  <title id="dial-title">One example night on a 24-hour dial</title>',
        '  <desc id="dial-desc">Midnight is at the top. Four agent events fall between 11:42 PM and 3:18 AM, and two decisions by people follow at 8:05 and 8:40 AM. A marker shows your local time. Two small dials show how many proposals are waiting for sign-off and the current phase of the moon.</desc>',
        "  <defs>",
        '    <mask id="dial-sweep" maskUnits="userSpaceOnUse" x="0" y="0" width="600" height="600"><circle class="sweep" cx="300" cy="300" r="250" fill="none" stroke="#fff" stroke-width="44" transform="rotate(180 300 300)"/></mask>',
        '    <radialGradient id="dial-glow"><stop offset="0" stop-color="#EEECE4" stop-opacity=".5"/><stop offset="1" stop-color="#EEECE4" stop-opacity="0"/></radialGradient>',
        "    " + gradient("dial-dusk", 18, (DAY, ROSE, NIGHT)),
        "    " + gradient("dial-dawn", 8 - TAPER_HOURS, (NIGHT, ROSE, DAY)),
        "  </defs>",
        '  <circle class="bezel" cx="300" cy="300" r="264"/>',
        '  <circle class="guide" cx="300" cy="300" r="260"/>',
        '  <circle class="guide" cx="300" cy="300" r="240"/>',
        '  <g class="sky" mask="url(#dial-sweep)" fill="none">',
    ]
    rows += ["    " + p for p in sky()]
    rows += [
        "  </g>",
        '  <circle class="rail" cx="300" cy="300" r="234"/>',
        '  <circle class="rail" cx="300" cy="300" r="226"/>',
        '  <circle class="ticks-quarter" cx="300" cy="300" r="230"/>',
        '  <circle class="ticks-hour" cx="300" cy="300" r="230"/>',
        '  <g class="hours" aria-hidden="true">',
    ]
    rows += ["    " + t for t in hours()]
    rows += [
        "  </g>",
        '  <circle class="pearls" cx="300" cy="300" r="180"/>',
        '  <circle class="seconds" cx="300" cy="120" r="3.2"/>',
        '  <circle class="rail" cx="300" cy="300" r="175"/>',
        '  <circle class="rays" cx="300" cy="300" r="147"/>',
        '  <g class="sub" transform="translate(300 182)" aria-hidden="true">',
        '    <circle class="sub-face" r="38"/><circle class="sub-ticks sub-ticks-count" r="33"/>',
        '    <text class="dial-count" y="7" text-anchor="middle">3</text>',
        '    <text class="sub-label" y="24" text-anchor="middle">waiting</text>',
        "  </g>",
        '  <g class="sub" transform="translate(300 418)" aria-hidden="true">',
        '    <circle class="sub-face" r="38"/><circle class="sub-ticks sub-ticks-moon" r="33"/>',
        '    <circle class="moon-star" cx="-25" cy="-11" r=".9"/><circle class="moon-star" cx="24" cy="-15" r="1.1"/><circle class="moon-star" cx="26" cy="12" r=".8"/><circle class="moon-star" cx="-23" cy="16" r="1"/>',
        '    <circle class="moon-dark" r="19"/><path class="moon-lit" d="M 0 -19 A 19 19 0 0 1 0 19 Z"/>',
        "  </g>",
        '  <g aria-hidden="true">',
        '    <text class="dial-label" x="300" y="258" text-anchor="middle">Your time</text>',
        '    <text class="dial-time" x="300" y="322" text-anchor="middle">12:00 AM</text>',
        '    <text class="dial-state is-night" x="300" y="356" text-anchor="middle">After hours</text>',
        "  </g>",
        '  <g class="now" display="none" aria-hidden="true">',
        '    <path d="M 295.5 139 L 304.5 139 L 300 128 Z" opacity=".7"/><path d="M 294 79 L 306 79 L 300 61 Z"/>',
        '    <circle class="now-glow" cx="300" cy="50" r="22"/><circle class="now-bead" cx="300" cy="50" r="8"/>',
        "  </g>",
    ]
    rows += ["  " + m for m in marks()]
    rows.append("</svg>")
    return "\n".join(pad + r for r in rows)


def main():
    page = pathlib.Path(__file__).resolve().parent.parent / "index.html"
    html = page.read_text()
    block = "<!-- dial:start (generated by tools/dial.py) -->\n" + build() + "\n            <!-- dial:end -->"
    marked = re.compile(r"<!-- dial:start.*?<!-- dial:end -->", re.S)
    first = re.compile(r'<svg class="dial".*?</svg>', re.S)
    pattern = marked if marked.search(html) else first
    html, count = pattern.subn(lambda _: block, html, count=1)
    if count != 1:
        raise SystemExit("dial block not found in index.html")
    page.write_text(html)
    print("dial written: %d bytes" % len(block))


if __name__ == "__main__":
    main()
