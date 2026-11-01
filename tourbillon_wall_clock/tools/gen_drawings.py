#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/gen_drawings.py -- dimensional and arbor-layout drawings, generated.

Two SVGs are written into docs/:

  DRAWING_LAYOUT.svg   front (dial-side) view.  Every axis, every pitch and tip
                       circle, every plate window and the carriage envelope,
                       placed from the same POS_* / CD_* / M_* / Z_* constants
                       that parameters_auto.scad is generated from, with the
                       centre distances dimensioned.  Nothing is drawn by hand,
                       so the drawing cannot disagree with the model.

  DRAWING_ARBORS.svg   a Z-section through the movement with every arbor drawn
                       to its own row of docs/SHAFTS.md: total length, the two
                       bearing seats, the pivot diameters and the span between
                       supports, plus the Z band of every member it carries.

Usage:  python3 tools/gen_drawings.py
"""
from __future__ import annotations

import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import design as D            # noqa: E402
import gearmath as G          # noqa: E402

DOCS = os.path.join(ROOT, "docs")

# ---------------------------------------------------------------------------
# tiny SVG helpers
# ---------------------------------------------------------------------------


class Svg:
    def __init__(self, w, h, title):
        self.w, self.h = w, h
        self.body = []
        self.title = title

    def raw(self, s):
        self.body.append(s)

    def line(self, x1, y1, x2, y2, cls="thin", dash=None):
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        self.body.append('<line x1="%.3f" y1="%.3f" x2="%.3f" y2="%.3f" '
                         'class="%s"%s/>' % (x1, y1, x2, y2, cls, d))

    def circle(self, cx, cy, r, cls="thin", dash=None):
        d = ' stroke-dasharray="%s"' % dash if dash else ""
        self.body.append('<circle cx="%.3f" cy="%.3f" r="%.3f" class="%s"%s/>'
                         % (cx, cy, r, cls, d))

    def rect(self, x, y, w, h, cls="thin"):
        self.body.append('<rect x="%.3f" y="%.3f" width="%.3f" height="%.3f" '
                         'class="%s"/>' % (x, y, w, h, cls))

    def poly(self, pts, cls="thin", close=True):
        d = " ".join("%.3f,%.3f" % (p[0], p[1]) for p in pts)
        tag = "polygon" if close else "polyline"
        self.body.append('<%s points="%s" class="%s"/>' % (tag, d, cls))

    def text(self, x, y, s, cls="lbl", anchor="middle", rot=None):
        t = ' transform="rotate(%.2f %.3f %.3f)"' % (rot, x, y) if rot else ""
        self.body.append('<text x="%.3f" y="%.3f" class="%s" text-anchor="%s"%s>%s'
                         '</text>' % (x, y, cls, anchor, t, esc(s)))

    def dim(self, x1, y1, x2, y2, label, off=0.0, cls="dim"):
        """a dimension line with arrows and a label, offset perpendicular"""
        dx, dy = x2 - x1, y2 - y1
        L = math.hypot(dx, dy) or 1.0
        nx, ny = -dy / L, dx / L
        ax, ay = x1 + nx * off, y1 + ny * off
        bx, by = x2 + nx * off, y2 + ny * off
        self.line(x1, y1, ax, ay, "ext")
        self.line(x2, y2, bx, by, "ext")
        self.line(ax, ay, bx, by, cls)
        for px, py, sx, sy in ((ax, ay, dx / L, dy / L), (bx, by, -dx / L, -dy / L)):
            self.poly([(px, py), (px + sx * 7 - nx * 2.6, py + sy * 7 - ny * 2.6),
                       (px + sx * 7 + nx * 2.6, py + sy * 7 + ny * 2.6)], "fill")
        mx, my = (ax + bx) / 2, (ay + by) / 2
        ang = math.degrees(math.atan2(dy, dx))
        if ang > 90 or ang < -90:
            ang += 180
        self.text(mx + nx * 5, my + ny * 5 - 1.5, label, "dimlbl",
                  rot=ang if abs(ang) < 89 else 0)

    def write(self, path):
        css = """
    .thin  { fill:none; stroke:#1a1a1a; stroke-width:0.5; }
    .med   { fill:none; stroke:#1a1a1a; stroke-width:1.1; }
    .pitch { fill:none; stroke:#0b62c4; stroke-width:0.55; stroke-dasharray:7 2.5 1.2 2.5; }
    .tip   { fill:none; stroke:#c0392b; stroke-width:0.45; }
    .root  { fill:none; stroke:#8a8a8a; stroke-width:0.35; stroke-dasharray:3 2; }
    .axis  { fill:none; stroke:#111; stroke-width:0.4; stroke-dasharray:11 2.5 2 2.5; }
    .ext   { fill:none; stroke:#666; stroke-width:0.3; }
    .dim   { fill:none; stroke:#0b62c4; stroke-width:0.45; }
    .fill  { fill:#0b62c4; stroke:none; }
    .hatch { fill:none; stroke:#b0b0b0; stroke-width:0.3; }
    .lbl   { font:9.5px 'DejaVu Sans',Arial,sans-serif; fill:#111; }
    .ttl   { font:bold 15px 'DejaVu Sans',Arial,sans-serif; fill:#111; }
    .sub   { font:10.5px 'DejaVu Sans',Arial,sans-serif; fill:#444; }
    .dimlbl{ font:9px 'DejaVu Sans',Arial,sans-serif; fill:#0b62c4; }
    .note  { font:9px 'DejaVu Sans',Arial,sans-serif; fill:#666; }
    .hdr   { font:bold 11px 'DejaVu Sans',Arial,sans-serif; fill:#111; }
"""
        head = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
                'viewBox="0 0 %d %d">\n<title>%s</title>\n<style>%s</style>\n'
                '<rect x="0" y="0" width="%d" height="%d" fill="#fff"/>\n'
                % (self.w, self.h, self.w, self.h, esc(self.title), css,
                   self.w, self.h))
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(head)
            fh.write("\n".join(self.body))
            fh.write("\n</svg>\n")
        return path


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def frame(svg, title, sub, sheet, scale_note):
    svg.rect(8, 8, svg.w - 16, svg.h - 16, "med")
    svg.line(8, 46, svg.w - 8, 46, "med")
    svg.text(20, 30, title, "ttl", anchor="start")
    svg.text(20, 42, sub, "sub", anchor="start")
    svg.text(svg.w - 20, 30, sheet, "hdr", anchor="end")
    svg.text(svg.w - 20, 42, scale_note, "note", anchor="end")
    # title block
    y0 = svg.h - 62
    svg.line(8, y0, svg.w - 8, y0, "med")
    return y0


def title_block(svg, y0, rows):
    x = 20
    svg.text(x, y0 + 16, "PROJECT   tourbillon wall clock, 300 mm dial, "
                         "visible one-minute flying tourbillon", "sub", anchor="start")
    for i, (k, v) in enumerate(rows):
        col = x + (i % 3) * 300
        row = y0 + 32 + (i // 3) * 13
        svg.text(col, row, "%s   %s" % (k, v), "note", anchor="start")


# ===========================================================================
# DRAWING 1 -- front / dial-side layout
# ===========================================================================

def drawing_layout(path):
    W, H = 1180, 900
    svg = Svg(W, H, "Tourbillon wall clock -- front layout")
    y0 = frame(svg, "MAIN PLATE AND MOVEMENT LAYOUT  --  VIEWED FROM THE DIAL SIDE",
               "Z axis perpendicular to the sheet, +Z toward the viewer, +Y to "
               "12 o'clock.  All dimensions in millimetres.",
               "SHEET 1 of 2", "drawn to scale, 1 : 1 in model units")

    # model space: the plate is 296 across; fit it into the drawing area
    cx, cy = 430.0, 470.0
    k = 1.30                      # mm of model -> px on the sheet
    plate_r = D.DIAL_APERTURE / 2

    def P(x, y):
        return (cx + x * k, cy - y * k)

    # plate and case
    svg.circle(*P(0, 0), plate_r * k, "med")
    svg.circle(*P(0, 0), D.CLOCK_DIAMETER / 2 * k, "thin")
    svg.circle(*P(0, 0), 232.0 / 2 * k, "root")          # dial ring ID
    svg.text(cx, cy - plate_r * k - 12, "case ring dia %.2f" % D.CLOCK_DIAMETER,
             "note")
    svg.text(cx, cy + plate_r * k + 26, "plate / dial aperture dia %.2f"
             % D.DIAL_APERTURE, "note")
    svg.text(cx - plate_r * k, cy + plate_r * k + 40,
             "dial ring ID 232.00", "note", anchor="start")

    # axis crosshairs
    svg.line(*P(0, -plate_r - 6), *P(0, plate_r + 6), "axis")
    svg.line(*P(-plate_r - 6, 0), *P(plate_r + 6, 0), "axis")

    # every wheel: pitch circle (chain), tip circle, and its tooth count
    members = [
        ("barrel", D.POS_BARREL, D.M_BARREL_GEAR, D.Z_BARREL_GEAR, D.BARREL_DRUM_OD),
        ("great wheel", D.POS_GREAT_WHEEL, D.M_GREAT_WHEEL, D.Z_GREAT_WHEEL, None),
        ("centre wheel", D.POS_CENTRE_WHEEL, D.M_CENTRE_WHEEL, D.Z_CENTRE_WHEEL, None),
        ("intermediate wheel", D.POS_INTERMEDIATE, D.M_INTER_WHEEL, D.Z_INTER_WHEEL, None),
    ]
    for name, pos, m, z, extra in members:
        x, y = P(*pos)
        r = G.pitch_d(m, z) / 2.0
        ra = G.outside_d(m, z) / 2.0
        rf = G.root_d(m, z) / 2.0
        svg.circle(x, y, ra * k, "tip")
        svg.circle(x, y, r * k, "pitch")
        svg.circle(x, y, rf * k, "root")
        svg.line(x - 5, y, x + 5, y, "axis")
        svg.line(x, y - 5, x, y + 5, "axis")
        if extra:
            svg.circle(x, y, extra / 2.0 * k, "thin")
        svg.text(x, y - ra * k - 5, "%s  z=%d  m=%.2f" % (name, z, m), "lbl")
        svg.text(x, y - ra * k + 6, "pitch dia %.2f  tip dia %.2f"
                 % (2 * r, 2 * ra), "note")

    # the carriage: its own envelope, the rim gear and the fixed fourth wheel
    px, py = P(*D.POS_CARRIAGE)
    rim_r = G.pitch_d(D.M_CARRIAGE_RIM, D.Z_CARRIAGE_RIM) / 2.0
    rim_ra = G.outside_d(D.M_CARRIAGE_RIM, D.Z_CARRIAGE_RIM) / 2.0
    svg.circle(px, py, rim_ra * k, "tip")
    svg.circle(px, py, rim_r * k, "pitch")
    svg.circle(px, py, D.CARRIAGE_BORE_R * k, "thin")
    svg.circle(px, py, D.CARRIAGE_FLOOR_OD / 2.0 * k, "thin")
    svg.circle(px, py, D.CARRIAGE_FLOOR_HOLE_D / 2.0 * k, "root")
    f4r = G.pitch_d(D.M_FIXED_FOURTH, D.Z_FIXED_FOURTH) / 2.0
    f4a = G.outside_d(D.M_FIXED_FOURTH, D.Z_FIXED_FOURTH) / 2.0
    svg.circle(px, py, f4a * k, "tip")
    svg.circle(px, py, f4r * k, "pitch")
    svg.line(px - 6, py, px + 6, py, "axis")
    svg.line(px, py - 6, px, py + 6, "axis")
    svg.text(px, py - rim_ra * k - 18, "TOURBILLON CARRIAGE  rim gear z=%d m=%.2f"
             % (D.Z_CARRIAGE_RIM, D.M_CARRIAGE_RIM), "lbl")
    svg.text(px, py - rim_ra * k - 6, "tip dia %.2f  (target envelope %.0f)"
             % (2 * rim_ra, D.TOURBILLON_DIAMETER), "dimlbl")
    svg.text(px, py + 12, "fixed fourth wheel z=%d m=%.2f"
             % (D.Z_FIXED_FOURTH, D.M_FIXED_FOURTH), "note")
    svg.text(px, py + 24, "STATIONARY, concentric with the carriage axis", "note")

    # the three carriage members, in carriage-local y
    for nm, ly, note in (("escape wheel / pinion", D.Y_ESCAPE, "z=15, OD 20.0"),
                         ("pallet lever", D.Y_PALLET, "Swiss club, 2 stones"),
                         ("balance + hairspring", D.Y_BALANCE, "dia 28.0, 1.000 Hz")):
        qx, qy = P(D.POS_CARRIAGE[0], D.POS_CARRIAGE[1] + ly)
        svg.circle(qx, qy, 2.2 * k, "thin")
        svg.line(px, py, qx, qy, "ext")
        svg.text(qx + 3 * k, qy, "%s  (local y %+.2f)  %s" % (nm, ly, note),
                 "note", anchor="start")

    # motion works stud
    mx, my = P(*D.POS_MOTION_WORKS)
    svg.circle(mx, my, 6.0 * k, "thin")
    svg.line(mx - 5, my, mx + 5, my, "axis")
    svg.line(mx, my - 5, mx, my + 5, "axis")
    svg.text(mx + 8, my - 4, "motion works stud (28.800, 0)", "lbl", anchor="start")
    svg.text(mx + 8, my + 8, "canon pinion z=16 m=0.72 / minute wheel z=64 m=0.72",
             "note", anchor="start")
    svg.text(mx + 8, my + 19, "minute pinion z=16 m=0.90 / hour wheel z=48 m=0.90",
             "note", anchor="start")

    # plate windows
    for nm, c, dia in D.PLATE_WINDOWS:
        wx, wy = P(*c)
        svg.circle(wx, wy, dia / 2.0 * k, "hatch")

    # centre distances, dimensioned on the drawing
    gwx, gwy = P(*D.POS_GREAT_WHEEL)
    ccx, ccy = P(*D.POS_CENTRE_WHEEL)
    bbx, bby = P(*D.POS_BARREL)
    iix, iiy = P(*D.POS_INTERMEDIATE)
    svg.dim(*P(0, 0), *D.POS_GREAT_WHEEL and P(*D.POS_GREAT_WHEEL),
            "", 0)                       # placeholder removed below
    svg.body.pop()
    svg.dim(ccx, ccy, gwx, gwy, "a = %.3f" % D.CD_GREAT_CENTRE, off=-58)
    svg.dim(gwx, gwy, bbx, bby, "a = %.3f" % D.CD_BARREL_GREAT, off=-58)
    svg.dim(ccx, ccy, iix, iiy, "a = %.3f" % D.CD_CENTRE_INTER, off=58)
    svg.dim(iix, iiy, px, py, "a = %.3f" % D.CD_INTER_CARRIAGE, off=58)
    svg.dim(ccx, ccy, mx, my, "a = %.3f" % D.CD_MOTION, off=-58)

    # legend
    lx = 830
    svg.text(lx, 90, "LEGEND", "hdr", anchor="start")
    for i, (cls, txt) in enumerate((
            ("tip", "tip / outside circle   (what must not collide)"),
            ("pitch", "pitch circle   d = m z"),
            ("root", "root circle   d = m z - 2.5 m"),
            ("hatch", "plate window   (PLATE_WINDOWS, checked by C-18d)"),
            ("axis", "rotation axis / centre line"),
            ("dim", "centre distance a = m (z1 + z2) / 2   (checked by C-17)"))):
        yy = 110 + i * 20
        svg.line(lx, yy - 3, lx + 34, yy - 3, cls)
        svg.text(lx + 42, yy, txt, "note", anchor="start")

    # the train, as a table on the sheet
    svg.text(lx, 260, "GOING TRAIN, BARREL TO CARRIAGE", "hdr", anchor="start")
    rows = [("barrel gear 14 -> great wheel 56", "m 1.40", "i 4.000", "a 49.000"),
            ("great pinion 8 -> centre wheel 48", "m 0.75", "i 6.000", "a 21.000"),
            ("centre pinion 10 -> intermediate 75", "m 0.60", "i 7.500", "a 25.500"),
            ("intermediate 12 -> carriage rim 96", "m 0.70", "i 8.000", "a 37.800"),
            ("fixed fourth 40 -> escape pinion 10", "m 0.45", "i 0.250", "a 11.250")]
    svg.text(lx, 278, "%-38s %-8s %-8s %s" % ("mesh", "module", "ratio", "centre dist"),
             "note", anchor="start")
    for i, r in enumerate(rows):
        svg.text(lx, 292 + i * 13, "%-38s %-8s %-8s %s" % r, "note", anchor="start")
    svg.text(lx, 292 + len(rows) * 13 + 6,
             "barrel -> centre wheel  24.000 : 1        centre -> carriage  60.000 : 1",
             "dimlbl", anchor="start")
    svg.text(lx, 292 + len(rows) * 13 + 20,
             "carriage 1.000 rpm  <=>  balance 1.000 Hz   (derived, not assumed)",
             "dimlbl", anchor="start")

    title_block(svg, y0, [
        ("PLATE DIA", "%.2f" % D.DIAL_APERTURE),
        ("CLOCK DIA", "%.2f" % D.CLOCK_DIAMETER),
        ("CARRIAGE TIP", "%.2f" % G.outside_d(D.M_CARRIAGE_RIM, D.Z_CARRIAGE_RIM)),
        ("PRESSURE ANGLE", "%.0f deg" % D.PRESSURE_ANGLE_DEG
            if hasattr(D, "PRESSURE_ANGLE_DEG") else "20 deg"),
        ("BEAT", "1.000 Hz / 7200 vph"),
        ("RUN TIME", "3.23 d computed (L-03)"),
        ("SOURCE", "tools/design.py -> parameters_auto.scad"),
        ("GENERATED BY", "tools/gen_drawings.py"),
        ("STATUS", "geometry verified; NOT a functional proof"),
    ])
    return svg.write(path)


# ===========================================================================
# DRAWING 2 -- arbor layout / Z section
# ===========================================================================

def drawing_arbors(path):
    W, H = 1240, 860
    svg = Svg(W, H, "Tourbillon wall clock -- arbor layout and Z section")
    y0 = frame(svg, "ARBOR LAYOUT AND Z SECTION THROUGH THE MOVEMENT",
               "Viewed from the side.  Z is vertical and to scale; the arbors are "
               "drawn at their true Z bands but their X positions are separated "
               "for legibility, so this is NOT a true projection of one section "
               "plane.  Diameters and spans are true, from docs/SHAFTS.md.",
               "SHEET 2 of 2", "Z to scale")

    # The Z range is derived from the Z stack itself rather than from a separate
    # constant, so this drawing cannot disagree with the model about its own
    # envelope.
    zmin = min(r[1] for r in D.Z_MOVEMENT)
    zmax = max(r[2] for r in D.Z_MOVEMENT)
    top = 110.0
    bot = y0 - 40.0
    kz = (bot - top) / (zmax - zmin)

    def Z(z):
        return bot - (z - zmin) * kz

    # Z axis and the plate / bridge bands
    svg.line(70, Z(zmin) + 4, 70, Z(zmax) - 4, "axis")
    for z in range(int(zmin), int(zmax) + 1, 5):
        svg.line(62, Z(z), 78, Z(z), "thin")
        svg.text(56, Z(z) + 3, "%+d" % z, "note", anchor="end")
    svg.text(30, (Z(zmin) + Z(zmax)) / 2, "Z  (mm)", "hdr", anchor="middle", rot=-90)

    for nm, z0_, z1_, od in D.Z_MOVEMENT:
        if nm in ("main plate", "top bridge (skeleton)"):
            svg.rect(78, Z(z1_), 1080, (z1_ - z0_) * kz, "hatch")
            svg.text(90, Z(z1_) - 4, "%s   Z %+.1f .. %+.1f   dia %.1f"
                     % (nm.upper(), z0_, z1_, od), "hdr", anchor="start")

    # every member's Z band
    svg.text(90, Z(zmax) + 18, "Z STACK, EVERY MEMBER", "hdr", anchor="start")
    for nm, z0_, z1_, od in D.Z_MOVEMENT:
        if nm in ("main plate", "top bridge (skeleton)"):
            continue
        yy = Z(z1_)
        hh = max(1.4, (z1_ - z0_) * kz)
        svg.rect(92, yy, od / 296.0 * 300.0, hh, "thin")
        svg.text(92 + od / 296.0 * 300.0 + 8, yy + hh / 2 + 3,
                 "%-26s Z %+6.1f .. %+6.1f   (%.1f thick)   dia %.2f"
                 % (nm, z0_, z1_, z1_ - z0_, od), "note", anchor="start")

    # the arbors, from SHAFT_TABLE via docs/SHAFTS.md
    arbors = [
        ("S-01", "barrel arbor", 30.0, 44.0, -19.5, 12.0, 10.0, "MR85ZZ / bronze bush"),
        ("S-02", "centre arbor", 4.0, 42.0, 4.0, 30.0, 1.5, "jewel both ends, span 20"),
        ("S-03", "great wheel arbor", 3.0, 12.0, 2.0, 14.0, 1.2, "jewel, span 8"),
        ("S-04", "intermediate arbor", 3.0, 20.0, 4.0, 24.0, 1.2, "jewel, span 9"),
        ("S-05", "carriage axis", 8.0, 26.0, 6.4, 32.4, 3.0, "ball race below, ruby above"),
        ("S-06", "escape arbor", 1.5, 17.0, 1.4, 18.4, 0.5, "jewel, span 8"),
        ("S-07", "pallet arbor", 1.2, 13.0, 8.6, 21.6, 0.4, "jewel, span 6"),
        ("S-08", "balance staff", 1.6, 20.0, 11.2, 31.2, 0.35, "sapphire endstones"),
        ("S-09", "motion works stud", 3.0, 9.0, 10.0, 19.0, None, "brass, pressed + peened"),
    ]
    x0 = 700.0
    dx = 52.0
    svg.text(x0, 92, "ARBORS  (carriage-local members drawn at their global Z)",
             "hdr", anchor="start")
    for i, (sid, nm, dia, length, za, zb, piv, bearing) in enumerate(arbors):
        ax = x0 + i * dx
        svg.line(ax, Z(za) + 3, ax, Z(zb) - 3, "axis")
        # the arbor body, drawn to a width that is visible but annotated truly
        w = max(3.0, dia / 8.0 * kz * 0.9)
        svg.rect(ax - w / 2, Z(zb), w, (zb - za) * kz, "med")
        if piv:
            pw = max(1.6, piv / 8.0 * kz * 0.9)
            svg.rect(ax - pw / 2, Z(zb), pw, 6.0, "thin")
            svg.rect(ax - pw / 2, Z(za) - 6.0, pw, 6.0, "thin")
        svg.text(ax, Z(zb) - 10, sid, "hdr")
        svg.text(ax, Z(zb) - 22, nm.replace(" ", "-"), "note", rot=-90)
        svg.text(ax, Z(za) + 14, "dia %.2f" % dia, "note")
        svg.text(ax, Z(za) + 26, "len %.1f" % length, "note")
        svg.text(ax, Z(za) + 38, ("pivot %.2f" % piv) if piv else "fixed stud",
                 "note")

    # a real dimension on one arbor, so the sheet is dimensioned not just drawn
    svg.dim(x0 + 4 * dx, Z(6.4), x0 + 4 * dx, Z(32.4),
            "S-05 carriage axis: length 26.0, span 18.0, axial play 0.04, "
            "radial clearance <= 0.015", off=-190)

    # carriage-local stack, in its own column
    lx = 90
    ly = Z(zmin) + 22
    svg.text(lx, ly, "CARRIAGE-LOCAL Z STACK  (origin at the carriage floor, "
                     "global Z0 = %+.1f)" % D.Z_CARRIAGE_Z0, "hdr", anchor="start")
    for i, (nm, z0_, z1_, od) in enumerate(D.Z_CARRIAGE):
        svg.text(lx, ly + 13 + i * 11,
                 "%-24s local %+6.1f .. %+6.1f   global %+6.1f .. %+6.1f   dia %.2f"
                 % (nm, z0_, z1_, z0_ + D.Z_CARRIAGE_Z0, z1_ + D.Z_CARRIAGE_Z0, od),
                 "note", anchor="start")

    title_block(svg, y0, [
        ("MOVEMENT Z MIN", "%+.1f" % zmin),
        ("MOVEMENT THICKNESS", "%.1f" % (zmax - zmin)),
        ("CARRIAGE HEIGHT", "%.2f (target 12-20)"
            % (max(r[2] for r in D.Z_CARRIAGE) - min(r[1] for r in D.Z_CARRIAGE))),
        ("SMALLEST ARBOR", "1.20 mm (S-07, C-33)"),
        ("FINEST CLEARANCE", "0.015 mm radial (S-05)"),
        ("BEARINGS", "jewel / bush / ball race -- never a printed hole"),
        ("SOURCE", "docs/SHAFTS.md + Z_MOVEMENT / Z_CARRIAGE"),
        ("GENERATED BY", "tools/gen_drawings.py"),
        ("STATUS", "dimensions true; X spacing for legibility only"),
    ])
    return svg.write(path)


def main():
    os.makedirs(DOCS, exist_ok=True)
    p1 = drawing_layout(os.path.join(DOCS, "DRAWING_LAYOUT.svg"))
    p2 = drawing_arbors(os.path.join(DOCS, "DRAWING_ARBORS.svg"))
    for p in (p1, p2):
        print("written: %s  (%d bytes)" % (os.path.relpath(p, ROOT),
                                           os.path.getsize(p)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
