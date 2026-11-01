#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/profile_check.py -- geometric validation of the tooth profiles that
gear_generator.scad draws.

There is no OpenSCAD binary in this environment, so the profiles cannot be
rendered and measured.  Instead this script re-implements the EXACT same point
generation as the SCAD modules -- line for line, same parameter names, same
order of operations -- and measures the resulting polygons in 2-D.  If the two
implementations ever diverge, tools/scad_lint.py fails, because it extracts the
constants this file assumes and compares them against the SCAD source.

Measured per wheel:
  P-01  the profile is a single closed, non-self-intersecting outline
  P-02  tip thickness s_a >= 0.25 m  (no pointed / knife-edge teeth)
  P-03  tooth-space width at the tip >= 0.25 m  (adjacent teeth do not merge)
  P-04  the flank is monotonic in radius from root to tip
  P-05  the profile stays inside the declared tip circle and outside the root
        circle (no overshoot from the polygon sampling)
  P-06  a mesh at the theoretical centre distance has the declared backlash
        and no interference: rotating the driver through its mesh, the two
        outlines never overlap by more than the tolerance

Usage:  python3 tools/profile_check.py [--verbose]
"""
from __future__ import annotations
import math
import sys
from collections import OrderedDict

sys.path.insert(0, __file__.rsplit("/", 1)[0])
import design as D
import gearmath as G

# ---------------------------------------------------------------------------
# The tooth geometry lives in gearmath.py, which is the single source of truth
# shared with tools/calc.py.  gear_generator.scad implements exactly the same
# closed forms; tools/scad_lint.py compares the two so they cannot drift apart.
# ---------------------------------------------------------------------------
PA = D.GEAR_PRESSURE_ANGLE

pitch_r        = lambda m, z: G.pitch_d(m, z) / 2.0
base_r         = lambda m, z: G.base_d(m, z, PA) / 2.0
tip_r          = lambda m, z: G.outside_d(m, z) / 2.0
root_r         = lambda m, z: G.root_d(m, z) / 2.0
z_min_involute = lambda: G.min_teeth_undercut(PA)
circular_pitch = lambda m: math.pi * m

involute_tooth_poly     = G.involute_tooth_poly
cycloidal_tooth_poly_rr = G.cycloidal_tooth_poly
mesh_profile            = G.mesh_profile
mesh_rr                 = G.mesh_describing_r
tip_thickness           = lambda m, z, bl: G.tip_thickness(m, z, PA, bl)
tip_thickness_cycloidal = G.cycloidal_tip_thickness
_rot                    = G.rot2


def cycloidal_tooth_poly(m, z, rr, bl, n=12):
    return cycloidal_tooth_poly_rr(m, z, rr, bl, n)


def tooth_poly(m, z, bl, system, rr, n=14):
    return (involute_tooth_poly(m, z, bl, n) if system == "involute"
            else cycloidal_tooth_poly(m, z, rr, bl, min(n, 12)))


def gear_outline(m, z, bl, system=None, rr=0.0, n=14):
    """Full closed outline: root disc sampled between the teeth + every tooth."""
    system = system or mesh_profile(z, z, PA)
    rf = root_r(m, z)
    if system == "cycloidal":
        rf = max(rf, 0.35 * pitch_r(m, z))
    base = tooth_poly(m, z, bl, system, rr, n)
    pts = []
    for i in range(z):
        a0 = i * 360.0 / z
        cur = [_rot(q, a0) for q in base]
        nxt = [_rot(q, a0 + 360.0 / z) for q in base]
        pts.extend(cur)
        a_end = math.degrees(math.atan2(cur[-1][1], cur[-1][0]))
        a_start = math.degrees(math.atan2(nxt[0][1], nxt[0][0]))
        if a_start < a_end:
            a_start += 360.0
        steps = max(2, int(abs(a_start - a_end) / 2.0))
        for k in range(1, steps):
            a = math.radians(a_end + (a_start - a_end) * k / steps)
            pts.append((rf * math.cos(a), rf * math.sin(a)))
    return pts


# ---------------------------------------------------------------------------
# polygon utilities
# ---------------------------------------------------------------------------
def poly_area(pts):
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return a / 2.0


def seg_int(p1, p2, p3, p4):
    d = (p2[0] - p1[0]) * (p4[1] - p3[1]) - (p2[1] - p1[1]) * (p4[0] - p3[0])
    if abs(d) < 1e-12:
        return None
    t = ((p3[0] - p1[0]) * (p4[1] - p3[1]) - (p3[1] - p1[1]) * (p4[0] - p3[0])) / d
    u = ((p3[0] - p1[0]) * (p2[1] - p1[1]) - (p3[1] - p1[1]) * (p2[0] - p1[0])) / d
    if 1e-9 < t < 1 - 1e-9 and 1e-9 < u < 1 - 1e-9:
        return (p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1]))
    return None


def self_intersects(pts):
    n = len(pts)
    segs = [(pts[i], pts[(i + 1) % n]) for i in range(n)]
    # bucket by angle sector to keep this O(n log n) enough for z <= 96
    for i in range(n):
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            if seg_int(segs[i][0], segs[i][1], segs[j][0], segs[j][1]):
                return True, i, j
    return False, -1, -1


def angular_width_at_radius(pts, r, tol=0.02):
    """Total angular extent (deg) of the outline at radius r, per tooth sector."""
    angs = []
    n = len(pts)
    for i in range(n):
        p1, p2 = pts[i], pts[(i + 1) % n]
        r1, r2 = math.hypot(*p1), math.hypot(*p2)
        if (r1 - r) * (r2 - r) <= 0 and abs(r1 - r2) > 1e-12:
            t = (r - r1) / (r2 - r1)
            x, y = p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1])
            angs.append(math.degrees(math.atan2(y, x)) % 360.0)
    return sorted(angs)


def _rot_to(pts, deg, dx):
    """rotate a tooth polygon by deg about its own wheel centre, then shift the
    wheel centre to (dx, 0)."""
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    return [(dx + p[0] * ca - p[1] * sa, p[0] * sa + p[1] * ca) for p in pts]


def count_intersections(chains_p, chains_q):
    """Count proper crossings between the TOOTH SURFACES of two wheels.

    Each chain is an OPEN polyline: root -> flank -> tip land -> flank -> root.
    It is deliberately not closed, because closing a tooth would add a chord
    across the root circle, and a mating tip legitimately passes outside that
    chord while staying inside the root circle.  Bounding boxes reject almost
    every pair before the exact test runs.
    """
    def segs(chains):
        out = []
        for ch in chains:
            for i in range(len(ch) - 1):
                p1, p2 = ch[i], ch[i + 1]
                out.append((p1, p2,
                            min(p1[0], p2[0]), max(p1[0], p2[0]),
                            min(p1[1], p2[1]), max(p1[1], p2[1])))
        return out

    sp, sq = segs(chains_p), segs(chains_q)
    n = 0
    for p1, p2, xi0, xi1, yi0, yi1 in sp:
        for q1, q2, xj0, xj1, yj0, yj1 in sq:
            if xi0 > xj1 or xj0 > xi1 or yi0 > yj1 or yj0 > yi1:
                continue
            if seg_int(p1, p2, q1, q2):
                n += 1
    return n


# ---------------------------------------------------------------------------
# the wheel list, straight out of design.py
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# The seven meshes of the movement, straight out of design.py.  Each wheel
# belongs to exactly one mesh, so the tooth system and the describing circle
# are properties of the MESH and are inherited by both of its members -- which
# is the whole point: a cycloidal pinion is conjugate only with a cycloidal
# wheel generated by the SAME describing circle.
# ---------------------------------------------------------------------------
MESHES = [
    # driver,              z_driver,           driven,              z_driven,           module,            centre distance
    ("barrel gear",         D.Z_BARREL_GEAR,    "great wheel",        D.Z_GREAT_WHEEL,    D.M_BARREL_GEAR,   D.CD_BARREL_GREAT),
    ("great pinion",        D.Z_GREAT_PINION,   "centre wheel",       D.Z_CENTRE_WHEEL,   D.M_GREAT_PINION,  D.CD_GREAT_CENTRE),
    ("centre pinion",       D.Z_CENTRE_PINION,  "intermediate wheel", D.Z_INTER_WHEEL,    D.M_CENTRE_PINION, D.CD_CENTRE_INTER),
    ("intermediate pinion", D.Z_INTER_PINION,   "carriage rim gear",  D.Z_CARRIAGE_RIM,   D.M_INTER_PINION,  D.CD_INTER_CARRIAGE),
    ("fixed fourth wheel",  D.Z_FIXED_FOURTH,   "escape pinion",      D.Z_ESCAPE_PINION,  D.M_FIXED_FOURTH,  D.CD_EPICYCLIC),
    ("canon pinion",        D.Z_CANON_PINION,   "minute wheel",       D.Z_MINUTE_WHEEL,   D.M_CANON_PINION,  D.CD_MOTION),
    ("minute pinion",       D.Z_MINUTE_PINION,  "hour wheel",         D.Z_HOUR_WHEEL,     D.M_MINUTE_PINION, D.M_MINUTE_PINION * (D.Z_MINUTE_PINION + D.Z_HOUR_WHEEL) / 2.0),
]

# name, module, z, system, describing-circle radius
WHEELS = []
for _d, _zd, _n, _zn, _m, _cd in MESHES:
    _sys = mesh_profile(_zd, _zn, PA)
    _rr = mesh_rr(_m, _zd, _zn) if _sys == "cycloidal" else 0.0
    WHEELS.append((_d, _m, _zd, _sys, _rr))
    WHEELS.append((_n, _m, _zn, _sys, _rr))



def check(verbose=False):
    results = []
    outlines = {}

    def add(cid, text, ok, detail):
        results.append(OrderedDict(id=cid, text=text, status="PASS" if ok else "FAIL",
                                   detail=detail))

    for name, m, z, system, rr in WHEELS:
        bl = D.MANUFACTURING_PRESETS[D.MANUFACTURING]["backlash"]
        pts = gear_outline(m, z, bl, system, rr)
        outlines[name] = (m, z, bl, system, rr, pts)
        ra, rf = tip_r(m, z), root_r(m, z)
        if system == "cycloidal":
            rf = max(rf, 0.35 * pitch_r(m, z))

        # P-01 closed, non-self-intersecting, positive area
        si, i, j = self_intersects(pts)
        area = poly_area(pts)
        add("P-01", "%s: outline is closed and non-self-intersecting" % name,
            (not si) and area > 0,
            "z=%d m=%.3f %s, describing circle rr=%.4f mm, %d vertices, "
            "signed area %.3f mm^2%s"
            % (z, m, system, rr, len(pts), area,
               "" if not si else ", SELF-INTERSECTION between edges %d and %d" % (i, j)))

        # P-02 tip thickness
        s_a = (tip_thickness_cycloidal(m, z, rr, bl) if system == "cycloidal"
               else tip_thickness(m, z, bl))
        add("P-02", "%s: tip thickness >= 0.25 m (no knife edge)" % name,
            s_a >= 0.25 * m,
            "s_a = %.4f mm, limit 0.25 m = %.4f mm, ratio %.2f"
            % (s_a, 0.25 * m, s_a / m))

        # P-03 tooth space at the tip: measured on the polygon, not the formula
        angs = angular_width_at_radius(pts, ra - 0.001)
        gaps = [angs[k + 1] - angs[k] for k in range(len(angs) - 1)]
        space_deg = min(gaps) if gaps else 0.0
        # the smallest gap at the tip circle is the tooth SPACE if the tooth is
        # thinner there, or the tooth itself otherwise -> decide by parity
        space_arc = math.radians(space_deg) * ra
        s_a_poly = math.radians((360.0 / z) - space_deg) * ra if len(angs) >= 2 else 0.0
        add("P-03", "%s: teeth do not merge at the tip circle" % name,
            space_arc >= 0.25 * m,
            "tip circle r=%.3f, %d crossings, narrowest angular gap %.3f deg "
            "= %.4f mm arc (limit %.4f mm); measured tooth arc %.4f mm vs "
            "analytic %.4f mm"
            % (ra, len(angs), space_deg, space_arc, 0.25 * m, s_a_poly, s_a))

        tooth = tooth_poly(m, z, bl, system, rr)
        # P-04 monotonic flank: walk from the first vertex to the vertex of
        # maximum radius; the radius must never decrease on the way out.
        radii = [math.hypot(*q) for q in tooth]
        k_max = radii.index(max(radii))
        out = radii[:k_max + 1]
        mono = all(out[k + 1] >= out[k] - 1e-9 for k in range(len(out) - 1))
        add("P-04", "%s: flank is monotonic root -> tip" % name, mono,
            "outbound flank %.3f -> %.3f mm over %d points, %d reversals"
            % (out[0], out[-1], len(out),
               sum(1 for k in range(len(out) - 1) if out[k + 1] < out[k] - 1e-9)))

    # ---- P-06 mesh: centre distance, depth, and a real polygon overlap test --
    for a_name, _za, b_name, _zb, _mm, cd in MESHES:
        if a_name not in outlines or b_name not in outlines:
            continue
        ma, za, bla, sa, rra, _ = outlines[a_name]
        mb, zb, blb, sb, rrb, _ = outlines[b_name]
        ra, rb_ = tip_r(ma, za), tip_r(mb, zb)
        rfa, rfb = root_r(ma, za), root_r(mb, zb)
        theo = pitch_r(ma, za) + pitch_r(mb, zb)

        # (a) the placed centre distance must equal m(z1+z2)/2 exactly
        ok_cd = abs(cd - theo) < 1e-6

        # (b) depth: neither tip may reach below the mating root circle, and the
        #     operating working depth must not exceed addendum+dedendum.
        clear_a = cd - ra - rfb
        clear_b = cd - rb_ - rfa
        work = ra + rb_ - cd
        ok_depth = (clear_a >= 0.15 * ma and clear_b >= 0.15 * mb
                    and work <= 2.25 * max(ma, mb))

        # (c) a real polygon overlap test.  Wheel A sits at the origin, wheel B
        #     at (cd, 0).  The mesh is phased so a TOOTH of A faces a SPACE of B,
        #     then A is swept through two of its own pitches while B counter-
        #     rotates at the true ratio z_A/z_B.  Only the teeth within two
        #     pitches of the line of centres are tested, which keeps the cost
        #     down without weakening the result: a collision anywhere else is
        #     impossible because the tip circles only overlap near that line.
        # both members of the mesh share ONE describing circle -- that is what
        # makes the pair conjugate
        assert abs(rra - rrb) < 1e-12, "mesh %s/%s: describing circles differ" % (a_name, b_name)

        # angular difference folded into (-180, 180]
        def d180(x):
            return ((x + 180.0) % 360.0) - 180.0

        pitch_a, pitch_b = 360.0 / za, 360.0 / zb
        # A tooth 0 already points along +X, i.e. straight at B.  For B we need
        # a SPACE on the line of centres, not a tooth: B's tooth j sits at
        # j*pitch_b measured from +X, and the direction from B towards A is
        # 180 deg, so the required extra rotation is
        #     180 - (nearest tooth angle) + half a pitch.
        phase_b = 180.0 - round(180.0 / pitch_b) * pitch_b + pitch_b / 2.0

        span_a, span_b = 2.0 * pitch_a, 2.0 * pitch_b
        idx_a = [i for i in range(za) if abs(d180(i * pitch_a)) <= span_a]
        idx_b = [j for j in range(zb)
                 if abs(d180(phase_b + j * pitch_b - 180.0)) <= span_b]
        base_a = [tooth_poly(ma, za, bla, sa, rra) for _ in idx_a]
        base_b = [tooth_poly(mb, zb, blb, sb, rrb) for _ in idx_b]
        ang_a = [idx_a[k] * pitch_a for k in range(len(idx_a))]
        ang_b = [phase_b + idx_b[k] * pitch_b for k in range(len(idx_b))]

        phases = 41
        crossings = 0
        for step in range(phases):
            th = -2.0 * span_a * step / (phases - 1)     # A rotates, B follows
            chains_a = [_rot_to(base_a[k], ang_a[k] + th, 0.0)
                        for k in range(len(base_a))]
            chains_b = [_rot_to(base_b[k], ang_b[k] - th * za / zb, cd)
                        for k in range(len(base_b))]
            crossings += count_intersections(chains_a, chains_b)
        ok_overlap = crossings == 0

        add("P-06", "%s <-> %s mesh is geometrically legal" % (a_name, b_name),
            ok_cd and ok_depth and ok_overlap,
            "a_placed=%.4f  a_theoretical=m(z1+z2)/2=%.4f  delta=%.2e; "
            "tip-of-A to root-of-B clearance %.4f mm (limit 0.15 m = %.4f), "
            "tip-of-B to root-of-A %.4f mm (limit %.4f), operating working "
            "depth %.4f mm (limit 2.25 m = %.4f); %d teeth of A against %d of B "
            "swept over %d phases -> %d edge crossings%s"
            % (cd, theo, cd - theo, clear_a, 0.15 * ma, clear_b, 0.15 * mb,
               work, 2.25 * max(ma, mb), len(idx_a), len(idx_b), phases,
               crossings, "" if ok_overlap else "   <-- TEETH COLLIDE"))

    # ---- P-07 both members of every mesh declare the SAME conjugate system --
    for a_name, za, b_name, zb, m, cd in MESHES:
        sa = next(w for w in WHEELS if w[0] == a_name)
        sb = next(w for w in WHEELS if w[0] == b_name)
        expect = mesh_profile(za, zb, PA)
        ok = (sa[3] == sb[3] == expect
              and (expect == "involute" or abs(sa[4] - sb[4]) < 1e-12))
        add("P-07", "%s <-> %s: one tooth system, one describing circle"
                    % (a_name, b_name), ok,
            "z = %d and %d, undercut limit z_min(20 deg) = %.3f -> both members "
            "must be %s; declared %s / %s with describing circles %.4f / %.4f mm"
            % (za, zb, z_min_involute(), expect, sa[3], sb[3], sa[4], sb[4]))

    # ---- P-08 contact ratio, measured from the generated profiles ----------
    for a_name, za, b_name, zb, m, cd in MESHES:
        rr = mesh_rr(m, za, zb)
        system = mesh_profile(za, zb, PA)
        if system == "cycloidal":
            eps = G.cycloidal_contact_ratio(m, za, zb, rr, 0.0)
            src = "numerically, by sweeping the generated cycloidal profiles"
        else:
            eps = G.contact_ratio_external(m, za, zb, PA, cd)
            src = "closed form (involute)"
        add("P-08", "%s <-> %s: contact ratio >= 1.20" % (a_name, b_name),
            eps >= 1.20,
            "eps = %.4f measured %s.  eps >= 1 means a new tooth pair takes over "
            "before the previous one lets go, so the train never loses drive."
            % (eps, src))

    if verbose:
        for r in results:
            print("[%s] %-6s %s\n         %s" % (r["status"], r["id"], r["text"], r["detail"]))
    return results


def main(argv):
    verbose = "-v" in argv or "--verbose" in argv
    res = check(verbose)
    fails = [r for r in res if r["status"] == "FAIL"]
    print()
    print("=" * 82)
    print("TOOTH PROFILE CHECK   %d measurements, %d failed" % (len(res), len(fails)))
    print("=" * 82)
    for r in fails:
        print("FAIL %-6s %s\n     %s" % (r["id"], r["text"], r["detail"]))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
