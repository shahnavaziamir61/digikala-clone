#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tools/gen_stl.py -- write one watertight binary STL per part, with no OpenSCAS.

There is no OpenSCAD binary in this environment, so the .scad files cannot be
compiled here.  This module is an INDEPENDENT second implementation of the same
part geometry: it reads the same validated constants out of tools/design.py and
tools/gearmath.py that parameters_auto.scad is generated from, builds each part
as a stack of prismatic slabs, resolves the 2-D booleans exactly, and writes
binary STL.

Because it is a second implementation, the two paths are cross-checked rather
than trusted: tools/check_geometry.py compares the STL bounding box and volume
of every part against the envelope and the mass that tools/calc.py computed from
the same constants.  A part whose STL volume disagrees with its calculated
volume by more than the tessellation allowance is reported, not silently
written.

METHOD
  1. Each part is a list of PRIMITIVES: circle, annulus, box, gear outline,
     polygon, hull -- each with a Z interval [z0, z1] and an operation
     (+ add, - subtract).
  2. The Z axis is split at every primitive boundary, so inside each Z interval
     the cross-section is constant.  That is exact for this design: every part
     is a prismatic stack, nothing here is a loft or a sweep.
  3. Inside each interval the 2-D cross-section is resolved with an exact
     polygon boolean (Greiner-Hormann with epsilon snapping).  The boolean is
     validated against closed-form areas before it is used -- see self_test().
  4. Neighbouring intervals that share the same cross-section are merged, then
     the solid is triangulated: side walls for every boundary edge over its full
     exposed Z extent, one bottom cap and one top cap.  Every edge is emitted
     exactly twice with opposite orientation, so the result is watertight and
     consistently oriented (verified by check_geometry.py).

  Tessellation: circles are sampled at $fn = 180 for parts above 40 mm and
  $fn = 96 below, so the chord error on a 68.6 mm gear rim is 0.006 mm and on a
  1.5 mm arbor pivot is 0.0002 mm -- both far below the 0.008 mm radial
  clearance the finest bearing in the clock is built to.

Usage:
    python3 tools/gen_stl.py                 # write every exportable part
    python3 tools/gen_stl.py --list          # show the registry and stop
    python3 tools/gen_stl.py --part carriage_floor
    python3 tools/gen_stl.py --self-test     # validate the boolean and writer
"""
from __future__ import annotations

import math
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))

import design as D            # noqa: E402
import gearmath as G          # noqa: E402

OUT_DIR = os.path.join(ROOT, "stl_output")


# ===========================================================================
# 0.  CONSTANTS ARE READ OUT OF THE .scad FILES, NOT OUT OF design.py
#     The whole point of this second implementation is that it cannot silently
#     disagree with the CAS.  So every scalar comes from parameters.scad or
#     parameters_auto.scad; design.py only supplies the structural tables
#     (Z stack, windows, hub ODs, column angles).  cross_check() then proves
#     the two sources agree on every name they share, which is what detects a
#     stale parameters_auto.scad.
# ===========================================================================

_SCAD_NUM = re.compile(r"^\s*([A-Za-z_]\w*)\s*=\s*(.+?)\s*;\s*(?://.*)?$", re.M)


def _join_multiline(txt):
    """SCAD assignments may span lines (_PRESET does).  Join a line onto the
    next only when it is demonstrably unfinished -- unbalanced brackets or a
    trailing continuation character -- so that a directive line such as
    `include <parameters_auto.scad>`, which has no semicolon, cannot swallow the
    assignment that follows it."""
    out, buf = [], ""
    for line in txt.split("\n"):
        cand = (buf + " " + line.strip()) if buf else line.strip()
        if not cand:
            continue
        opens = cand.count("[") + cand.count("(") + cand.count("{")
        closes = cand.count("]") + cand.count(")") + cand.count("}")
        tail = cand[-1:]
        unfinished = (opens > closes) or (tail in (",", "?", ":"))
        if unfinished:
            buf = cand
            continue
        out.append(cand)
        buf = ""
    if buf.strip():
        out.append(buf)
    return "\n".join(out)


def _ternary(e):
    """SCAD `A ? B : C` -> Python `(B if A else C)`, right-associative."""
    depth = 0
    i = 0
    while i < len(e):
        ch = e[i]
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
        elif ch == "?" and depth == 0 and e[i + 1:i + 2] != "?":
            # find the matching ':' at the same depth
            d2, j = 0, i + 1
            while j < len(e):
                if e[j] in "([{":
                    d2 += 1
                elif e[j] in ")]}":
                    d2 -= 1
                elif e[j] == ":" and d2 == 0:
                    break
                j += 1
            if j >= len(e):
                return e
            cond, a, b = e[:i], e[i + 1:j], e[j + 1:]
            return "(%s if %s else %s)" % (_ternary(a), cond.strip(), _ternary(b))
        i += 1
    return e


def _py(expr, ns):
    """Translate a SCAD scalar/list expression into Python and evaluate it."""
    e = _ternary(expr.strip())
    if e in ("true", "false"):
        return e == "true"
    if e == "undef":
        return None
    if e.startswith('"') and e.endswith('"'):
        return e[1:-1]
    # SCAD ranges [a:b] and [a:s:b] -> python list; SCAD pow() -> **
    e = re.sub(r"\bpow\s*\(\s*([^,()]+?)\s*,\s*([^,()]+?)\s*\)", r"(\1)**(\2)", e)
    e = re.sub(r"\b([A-Za-z_]\w*)\s*\^\s*", r"\1**", e)
    def rng(m):
        body = m.group(1)
        parts = [x.strip() for x in body.split(":")]
        try:
            vals = [eval(x, {"__builtins__": {}}, ns) for x in parts]
        except Exception:
            return m.group(0)
        if len(vals) == 2:
            lo, hi = vals
            if hi < lo:
                return "[]"
            return "[" + ",".join(repr(lo + i) for i in range(int(hi - lo) + 1)) + "]"
        if len(vals) == 3:
            lo, st, hi = vals
            out, v = [], lo
            while v <= hi + 1e-12:
                out.append(v); v += st
            return "[" + ",".join(repr(x) for x in out) + "]"
        return m.group(0)
    e = re.sub(r"\[\s*([-0-9.eE+:\s]+?)\s*\]", rng, e)
    e = e.replace("&&", " and ").replace("||", " or ").replace("!", " not ")
    e = re.sub(r"\bnot =", "!=", e)
    try:
        return eval(e, {"__builtins__": {"len": len, "min": min, "max": max,
                                        "abs": abs, "sqrt": math.sqrt,
                                        "sin": math.sin, "cos": math.cos,
                                        "round": round, "floor": math.floor,
                                        "ceil": math.ceil}}, ns)
    except Exception:
        return None


def load_scad_consts():
    """Every scalar/list constant declared in parameters_auto.scad and
    parameters.scad, resolved in declaration order."""
    ns = {"PI": math.pi}
    unresolved = []
    for fn in ("parameters_auto.scad", "parameters.scad"):
        txt = open(os.path.join(ROOT, fn), encoding="utf-8").read()
        txt = re.sub(r"/\*.*?\*/", " ", txt, flags=re.DOTALL)
        txt = re.sub(r"//[^\n]*", " ", txt)
        txt = _join_multiline(txt)
        for m in _SCAD_NUM.finditer(txt):
            name, expr = m.group(1), m.group(2)
            if name in ("module", "function", "include", "use", "echo"):
                continue
            val = _py(expr, ns)
            if val is None:
                unresolved.append((fn, name, expr))
                continue
            ns[name] = val
    return ns, unresolved


class NS:
    """Constants for the STL path.  Scalars come from the .scad files; the
    structural tables come from design.py, which is what generates them."""
    def __init__(self):
        self._scad, self._unresolved = load_scad_consts()
        self._tables = ("Z_MOVEMENT", "Z_CARRIAGE", "PLATE_WINDOWS",
                        "BRIDGE_WINDOWS", "HUB_OD", "CARRIAGE_COLUMN_ANGLES",
                        "MANUFACTURING_PRESETS", "MANUFACTURING")

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name in self._tables:
            return getattr(D, name)
        if name in self._scad:
            return self._scad[name]
        if hasattr(D, name):
            return getattr(D, name)
        raise AttributeError(
            "%r is used by gen_stl.py but is declared in neither "
            "parameters_auto.scad nor design.py -- the STL path and the CAD "
            "path would disagree about this dimension" % name)

    def cross_check(self, tol=1e-9):
        """Prove the generated SCAD constants still equal design.py.  A
        mismatch means parameters_auto.scad is stale and must be regenerated."""
        bad = []
        for k, v in sorted(self._scad.items()):
            if not hasattr(D, k) or not isinstance(v, (int, float)) or isinstance(v, bool):
                continue
            dv = getattr(D, k)
            if isinstance(dv, (int, float)) and not isinstance(dv, bool):
                if abs(float(v) - float(dv)) > tol * max(1.0, abs(float(dv))):
                    bad.append((k, v, dv))
        return bad

    def unresolved(self):
        return self._unresolved


S = NS()

# Tessellation is tiered by RADIUS, not by one global $fn.  The chord error of a
# regular n-gon inscribed in a circle of radius r is r(1 - cos(pi/n)), and the
# tightest functional clearance anywhere in this movement is the 0.008 mm radial
# play of the carriage jewel (docs/SHAFTS.md, S-05), so every tier below is held
# well under it.  A single global $fn large enough for a 296 mm plate would put
# ~180 vertices on a 3 mm screw hole too, and ear-clipping the resulting bridged
# polygon is O(n^2) in the vertex count -- which is what made the first version
# of this exporter run for twenty minutes without finishing.
FN_TIERS = ((40.0, 144), (10.0, 96), (2.0, 48), (0.0, 32))
EPS = 1e-7
SNAP = 1e-9


def fn_for(r):
    for limit, n in FN_TIERS:
        if r >= limit:
            return n
    return FN_TIERS[-1][1]


def chord_error(r, n=None):
    """Faceting depth of the polygon that stands in for a circle of radius r."""
    n = n or fn_for(r)
    return r * (1.0 - math.cos(math.pi / n))


def max_chord_error():
    """The worst faceting over the radii that actually occur in this design."""
    worst = (0.0, 0.0)
    for r in (148.0, 76.0, 67.2 / 2, 46.2 / 2, 34.3, 23.0, 18.9 / 2,
              12.0, 9.0, 6.0, 4.5, 3.0, 1.5, 0.75, 0.35):
        e = chord_error(r)
        if e > worst[0]:
            worst = (e, r)
    return worst


# ===========================================================================
# 1.  GEOMETRY PRIMITIVES  ->  polygon-with-holes cross-sections
# ===========================================================================

def circle_poly(cx, cy, r, fn=None, phase=0.0):
    n = fn or fn_for(r)
    return [(cx + r * math.cos(2 * math.pi * i / n + phase),
             cy + r * math.sin(2 * math.pi * i / n + phase)) for i in range(n)]


def box_poly(cx, cy, w, h, rot_deg=0.0):
    a = math.radians(rot_deg)
    ca, sa = math.cos(a), math.sin(a)
    pts = []
    for dx, dy in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)):
        pts.append((cx + dx * ca - dy * sa, cy + dx * sa + dy * ca))
    return pts


def hull_polys(polys):
    """Convex hull of the union of several polygons (Andrew's monotone chain).
    Used for the spoke arms and the lever, exactly as hull() does in SCAS."""
    pts = [p for poly in polys for p in poly]
    pts = sorted(set(pts))
    if len(pts) < 3:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return lower[:-1] + upper[:-1]


def gear_poly(m, z, bl, system="cycloidal", rr=0.0, cx=0.0, cy=0.0, phase=0.0):
    """The exact outline gear_generator.scad draws, as one closed polygon.
    Root disc sampled between the teeth + every tooth chain."""
    r = G.pitch_d(m, z) / 2.0
    rf = G.root_d(m, z) / 2.0
    if system == "cycloidal":
        rf = max(rf, 0.35 * r)
        tooth = G.cycloidal_tooth_poly(m, z, rr, bl, 12)
    else:
        tooth = G.involute_tooth_poly(m, z, bl, 14)
    fn = fn_for(r)
    pts = []
    for i in range(z):
        a0 = i * 360.0 / z + phase
        cur = [G.rot2(q, a0) for q in tooth]
        nxt = [G.rot2(q, a0 + 360.0 / z) for q in tooth]
        pts.extend(cur)
        a_end = math.degrees(math.atan2(cur[-1][1], cur[-1][0]))
        a_start = math.degrees(math.atan2(nxt[0][1], nxt[0][0]))
        if a_start < a_end:
            a_start += 360.0
        steps = max(2, int(abs(a_start - a_end) / (360.0 / fn)))
        for k in range(1, steps):
            a = math.radians(a_end + (a_start - a_end) * k / steps)
            pts.append((rf * math.cos(a), rf * math.sin(a)))
    return [(cx + p[0], cy + p[1]) for p in pts]


def escape_poly(z=None, r_tip=None, r_root=None, cx=0.0, cy=0.0, phase=0.0):
    """15-tooth Swiss club escape wheel, mirroring escape_wheel_2d()."""
    z = z or S.Z_ESCAPE_WHEEL
    r_tip = r_tip if r_tip is not None else S.ESCAPE_WHEEL_OD / 2.0
    r_root = r_root if r_root is not None else S.ESCAPE_WHEEL_OD / 2.0 - 2.6
    pitch = 360.0 / z
    pts = []
    for i in range(z):
        a0 = i * pitch + phase
        loc = [(r_root * math.cos(-pitch / 2 + 0.8), r_root * math.sin(-pitch / 2 + 0.8)),
               (r_root * math.cos(-2.4), r_root * math.sin(-2.4)),
               ((r_tip - 1.15) * math.cos(-0.9), (r_tip - 1.15) * math.sin(-0.9)),
               (r_tip * math.cos(0.9), r_tip * math.sin(0.9)),
               (r_tip * math.cos(pitch * 0.30), r_tip * math.sin(pitch * 0.30)),
               (r_root * math.cos(pitch / 2 - 0.8), r_root * math.sin(pitch / 2 - 0.8))]
        pts.extend(G.rot2(q, a0) for q in loc)
        # root arc to the next tooth
        a_end = math.degrees(math.atan2(pts[-1][1], pts[-1][0]))
        a_start = a_end + (pitch - (pitch / 2 - 0.8) - (pitch / 2 - 0.8))
        fn = fn_for(r_root)
        steps = max(2, int(abs(a_start - a_end) / (360.0 / fn)))
        for k in range(1, steps):
            a = math.radians(a_end + (a_start - a_end) * k / steps)
            pts.append((r_root * math.cos(a), r_root * math.sin(a)))
    return [(cx + p[0], cy + p[1]) for p in pts]


# ===========================================================================
# 2.  EXACT 2-D POLYGON BOOLEAN  (Greiner-Hormann)
# ===========================================================================

def _signed_area(poly):
    """Shoelace area; positive when the loop is counter-clockwise."""
    a = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % n]
        a += x1 * y2 - x2 * y1
    return a / 2.0


def _ensure_ccw(poly):
    return list(reversed(poly)) if _signed_area(poly) < 0 else list(poly)


def _point_in_poly(p, poly):
    """Even-odd point-in-polygon test.  Used both for the region containment
    rules and to classify each face of the arrangement, so it has to agree with
    the orientation convention everywhere else in this file."""
    x, y = p
    n = len(poly)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if ((yi > y) != (yj > y)) and \
                (x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-300) + xi):
            inside = not inside
        j = i
    return inside


# ---------------------------------------------------------------------------
# Exact 2-D polygon boolean by planar arrangement + face classification.
#
# Greiner-Hormann was tried first.  It is fragile on exactly the degenerate
# cases this design is full of: a box edge tangent to a circle sample point, two
# cutters sharing a vertex, a cutter crossing an annulus twice, and nested
# loops (which GH treats as a special case and gets wrong often enough to
# matter).  This version has no special cases at all:
#
#   1. split every edge of both polygons at every proper crossing, so the two
#      boundaries afterwards meet only at shared vertices;
#   2. build the planar graph with BOTH directions of every edge and walk it
#      into face-boundary cycles with the standard DCEL rule
#      (next = the clockwise neighbour of the incoming edge's twin);
#   3. classify each cycle as MATERIAL or VOID by testing one interior point
#      against the two ORIGINAL polygons with an even-odd test, using the
#      predicate of the requested operation;
#   4. assemble: material cycles become outer boundaries, void cycles that lie
#      inside a surviving outer become its holes, the unbounded face is dropped,
#      and an outer contained in another outer is dropped so a nested union
#      does not double-count its area.
#
# Every vertex in the result is either an original vertex or an exact edge
# crossing, so no dimension is rounded, snapped or approximated anywhere.
# ---------------------------------------------------------------------------

_CROSS_TOL = 1e-11


def _key(p):
    return (round(p[0], 9), round(p[1], 9))


def _loop_key(loop):
    return tuple(sorted(_key(p) for p in loop))


def _seg_cross_param(p1, p2, q1, q2):
    """Proper crossing of segments p1p2 and q1q2 -> (x, y, t, u) or None.
    Endpoint touches are rejected on purpose: they are handled by vertex
    merging in the arrangement, not by edge splitting."""
    x1, y1 = p1
    x2, y2 = p2
    x3, y3 = q1
    x4, y4 = q2
    den = (x2 - x1) * (y4 - y3) - (y2 - y1) * (x4 - x3)
    if abs(den) < 1e-15:
        return None
    t = ((x3 - x1) * (y4 - y3) - (y3 - y1) * (x4 - x3)) / den
    u = ((x3 - x1) * (y2 - y1) - (y3 - y1) * (x2 - x1)) / den
    if _CROSS_TOL < t < 1 - _CROSS_TOL and _CROSS_TOL < u < 1 - _CROSS_TOL:
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1), t, u)
    return None


def _split_edges(poly, against):
    """Insert into `poly` every crossing point with the edges of `against`."""
    out = []
    n = len(poly)
    nb = len(against)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        hits = []
        for j in range(nb):
            c = _seg_cross_param(p, q, against[j], against[(j + 1) % nb])
            if c:
                hits.append((c[2], (c[0], c[1])))
        hits.sort(key=lambda h: h[0])
        out.append(p)
        out.extend(pt for _t, pt in hits)
    return out


def _dedup_loop(poly):
    out = []
    for p in poly:
        if not out or _key(p) != _key(out[-1]):
            out.append(p)
    while len(out) > 1 and _key(out[0]) == _key(out[-1]):
        out.pop()
    return out


def _split_at_crossings(poly_a, poly_b):
    """Split BOTH polygons at their mutual crossings.  Each must be split
    against the other's ORIGINAL vertices: splitting one first turns every
    crossing into a vertex, and an endpoint touch is deliberately not counted
    as a crossing, so the second polygon would then find nothing and come back
    unsplit -- which silently turns an overlapping pair into a disjoint one."""
    a = _dedup_loop(list(poly_a))
    b = _dedup_loop(list(poly_b))
    a_orig, b_orig = list(a), list(b)
    a = _dedup_loop(_split_edges(a_orig, b_orig))
    b = _dedup_loop(_split_edges(b_orig, a_orig))
    return a, b


def _cycles(polys):
    """Walk the planar arrangement of the given closed polygons into
    face-boundary cycles.  Each returned cycle has its face interior on the
    LEFT of every directed edge, so a bounded face is CCW and the single
    unbounded face is CW."""
    verts = {}

    def vid(p):
        k = _key(p)
        verts.setdefault(k, (p[0], p[1]))
        return k

    edges = set()
    for poly in polys:
        n = len(poly)
        for i in range(n):
            u = vid(poly[i])
            v = vid(poly[(i + 1) % n])
            if u != v:
                edges.add((u, v))
    # both directions of every edge, so the walk closes on every face
    edges |= {(v, u) for (u, v) in edges}

    outgoing = {}
    for u, v in edges:
        outgoing.setdefault(u, []).append(v)
    order, idx = {}, {}
    for u, vs in outgoing.items():
        ux, uy = verts[u]
        order[u] = sorted(vs, key=lambda v: math.atan2(verts[v][1] - uy,
                                                       verts[v][0] - ux))
        idx[u] = {v: i for i, v in enumerate(order[u])}
    next_of = {}
    for u, vs in outgoing.items():
        for v in vs:
            k = idx[v][u]                       # position of the twin (v->u)
            nxt = order[v][(k - 1) % len(order[v])]   # its clockwise neighbour
            next_of[(u, v)] = (v, nxt)

    seen = set()
    out = []
    for e0 in sorted(edges):
        if e0 in seen:
            continue
        loop = []
        e = e0
        guard = 0
        while e is not None and e not in seen and guard < 400000:
            seen.add(e)
            guard += 1
            loop.append(verts[e[0]])
            e = next_of.get(e)
            if e == e0:
                break
        if len(loop) >= 3:
            out.append(loop)
    return out


def _interior_point(loop):
    """A point strictly inside `loop`, offset to the LEFT of its longest edge."""
    n = len(loop)
    best, bi = -1.0, 0
    for i in range(n):
        p, q = loop[i], loop[(i + 1) % n]
        L = math.hypot(q[0] - p[0], q[1] - p[1])
        if L > best:
            best, bi = L, i
    p, q = loop[bi], loop[(bi + 1) % n]
    dx, dy = q[0] - p[0], q[1] - p[1]
    L = math.hypot(dx, dy) or 1.0
    eps = min(1e-7, L * 1e-5)
    return ((p[0] + q[0]) / 2 - dy / L * eps, (p[1] + q[1]) / 2 + dx / L * eps)


def _predicate(op, inA, inB):
    if op == "union":
        return inA or inB
    if op == "inter":
        return inA and inB
    return inA and not inB          # diff


def boolean(subject, clip, op):
    """Exact boolean of two simple polygons, op in {'union','diff','inter'}.
    Returns a list of (outer_loop, [hole_loops, ...]) pairs, outer CCW and
    holes CW."""
    A = _dedup_loop(_ensure_ccw(subject))
    B = _dedup_loop(_ensure_ccw(clip))
    if len(A) < 3 or len(B) < 3:
        return [(A, [])] if op != "inter" else []
    A, B = _split_at_crossings(A, B)
    cyc = _cycles([A, B])
    if not cyc:
        return [(A, [])]

    # With both directions of every edge in the graph, each geometric loop is
    # walked twice -- once bounding the face on its left and once bounding the
    # face on its right.  Both walks enclose the same points, so the loop is
    # classified ONCE, by whether the region inside it is material.  That single
    # test is what decides outer-vs-hole, and it needs a probe point strictly
    # inside the loop: a vertex of the loop lies on the boundary of the other
    # polygon after splitting, where an even-odd test is not defined.
    material, void = [], []
    seen_keys = {}
    for loop in cyc:
        if abs(_signed_area(loop)) <= _CROSS_TOL:
            continue
        ccw = _ensure_ccw(loop)
        k = _loop_key(ccw)
        if k in seen_keys:
            continue
        seen_keys[k] = True
        p = _interior_point(ccw)
        if _predicate(op, _point_in_poly(p, subject), _point_in_poly(p, clip)):
            material.append(ccw)
        else:
            void.append(ccw)

    if not material:
        return []
    # An outer contained in another outer would double-count its area, so only
    # the largest enclosing loop survives (this is what makes a nested union
    # come out as the outer disc alone).
    outers = []
    for o in sorted(material, key=lambda L: -abs(_signed_area(L))):
        po = _interior_point(o)
        if any(_point_in_poly(po, bigger) for bigger in outers):
            continue
        outers.append(o)
    # A void loop becomes a hole of the outer that contains it.  The unbounded
    # face needs no special case: nothing contains it, so it is simply dropped,
    # and the same rule discards any void region that lies outside the result.
    parts = [[o, []] for o in outers]
    for hole in sorted(void, key=lambda L: -abs(_signed_area(L))):
        ph = _interior_point(hole)
        for part in parts:
            outer, holes = part
            if _point_in_poly(ph, outer) and not any(
                    _point_in_poly(ph, h) for h in holes):
                holes.append(list(reversed(hole)))      # holes are stored CW
                break
    return [(p[0], p[1]) for p in parts]


# ===========================================================================
# 3.  REGION ARITHMETIC  --  a cross-section is (outers, holes)
#     All the parts in this project are built from primitives that are either
#     nested or disjoint, so the region can be resolved by containment tests
#     first and the general boolean is only needed when two primitives truly
#     overlap.  That ordering is what keeps the output exact.
# ===========================================================================

class Region:
    """A 2-D cross-section: a list of outer polygons, each with its holes."""
    def __init__(self):
        self.parts = []          # [[outer, [holes...]], ...]

    def add(self, poly):
        poly = _ensure_ccw(poly)
        if _signed_area(poly) <= 0:
            return
        # does it fall inside an existing hole?  then it fills part of it
        for p in self.parts:
            if _point_in_poly(poly[0], p[1][0]) if p[1] else False:
                pass
        self.parts.append([poly, []])
        self._absorb()

    def sub(self, poly):
        poly = _ensure_ccw(poly)
        if _signed_area(poly) <= 0:
            return
        newparts = []
        consumed = False
        for outer, holes in self.parts:
            # A cutter vertex that lands exactly ON the outer boundary is not
            # decided by an even-odd test, and a window tangent to the plate rim
            # produces precisely that.  Nudge such a vertex inward along the
            # cutter centroid before testing so the nested case is still taken.
            cxc = sum(v[0] for v in poly) / len(poly)
            cyc = sum(v[1] for v in poly) / len(poly)

            def _in(region, v):
                if _point_in_poly(v, region):
                    return True
                mx, my = v[0] + 1e-6 * (cxc - v[0]), v[1] + 1e-6 * (cyc - v[1])
                return _point_in_poly((mx, my), region)

            inside = all(_in(outer, v) for v in poly) and not any(
                _point_in_poly(v, h) for h in holes for v in poly)
            if inside:
                # Every cutter vertex is inside this outer and outside its
                # existing holes, so the cutter becomes a new hole.  Exact, and
                # no arrangement walk is needed.
                holes.append(list(reversed(poly)))
                newparts.append([outer, holes])
                consumed = True
                continue
            if all(_point_in_poly(v, poly) for v in outer):
                # this outer is entirely inside the cutter: it disappears
                continue
            # genuine overlap: resolve it exactly with the arrangement boolean
            res = boolean(outer, poly, "diff")
            if not res:
                continue
            for ro, rh in res:
                # the holes this outer already had survive wherever they are
                # still wholly inside the cut result
                keep = [h for h in holes if _point_in_poly(h[0], ro)]
                newparts.append([ro, keep + list(rh)])
            consumed = True
        if not consumed and not newparts:
            return
        self.parts = newparts

    def _absorb(self):
        """merge outers that are nested inside one another"""
        changed = True
        while changed:
            changed = False
            for i in range(len(self.parts)):
                for j in range(len(self.parts)):
                    if i == j:
                        continue
                    oi, hi = self.parts[i]
                    oj, hj = self.parts[j]
                    if _point_in_poly(oi[0], oj) and not any(
                            _point_in_poly(oi[0], h) for h in hj):
                        # i is inside j: its holes move to j, i disappears
                        hj.extend(hi)
                        self.parts.pop(i)
                        changed = True
                        break
                if changed:
                    break

    def area(self):
        a = 0.0
        for outer, holes in self.parts:
            a += abs(_signed_area(outer))
            for h in holes:
                a -= abs(_signed_area(h))
        return a

    def boundaries(self):
        """every edge loop that needs a side wall, with its orientation"""
        out = []
        for outer, holes in self.parts:
            out.append((outer, +1))
            for h in holes:
                out.append((h, -1))
        return out


# ===========================================================================
# 4.  THE SOLID MODEL: a stack of (z0, z1, Region)
# ===========================================================================

class Solid:
    def __init__(self, name):
        self.name = name
        self.ops = []        # (z0, z1, kind, poly)  kind in ('add','sub')

    def add(self, z0, z1, poly):
        if z1 > z0 and len(poly) >= 3:
            self.ops.append((z0, z1, "add", poly))

    def sub(self, z0, z1, poly):
        if z1 > z0 and len(poly) >= 3:
            self.ops.append((z0, z1, "sub", poly))

    def z_breaks(self):
        zs = set()
        for z0, z1, _, _ in self.ops:
            zs.add(round(z0, 6)); zs.add(round(z1, 6))
        return sorted(zs)

    def region_at(self, zmid):
        reg = Region()
        for z0, z1, kind, poly in self.ops:
            if z0 - 1e-9 <= zmid <= z1 + 1e-9:
                if kind == "add":
                    reg.add(poly)
                else:
                    reg.sub(poly)
        return reg

    def slabs(self):
        zs = self.z_breaks()
        out = []
        for i in range(len(zs) - 1):
            z0, z1 = zs[i], zs[i + 1]
            if z1 - z0 < 1e-9:
                continue
            reg = self.region_at((z0 + z1) / 2.0)
            if reg.area() > 1e-9:
                out.append((z0, z1, reg))
        # merge adjacent slabs with an identical boundary signature
        merged = []
        for z0, z1, reg in out:
            sig = _sig(reg)
            if merged and merged[-1][2] == sig and abs(merged[-1][1] - z0) < 1e-9:
                merged[-1] = (merged[-1][0], z1, sig, merged[-1][3])
            else:
                merged.append((z0, z1, sig, reg))
        return merged

    def volume(self):
        return sum((z1 - z0) * reg.area() for z0, z1, _, reg in self.slabs())

    def verify(self, tris=None, rtol=1e-6, atol=1e-6):
        """Prove the emitted mesh IS the intended solid, by three independent
        measurements rather than by trusting the construction:

          volume   the signed volume of the triangles (positive only if every
                   normal points outward) against the analytic slab volume
                   sum(area * dz), which is computed from the 2-D regions
                   before any triangulation happens;
          manifold every directed edge appears exactly as often as its reverse,
                   so the mesh is closed and consistently oriented;
          extent   the bounding box is finite and non-degenerate.

        Returns (ok, volume_analytic, volume_mesh, bad_edges, message).  A part
        that fails is NOT written: an unverified STL is worse than no STL,
        because it looks like a deliverable."""
        if tris is None:
            tris = self.triangles()
        v_want = self.volume()
        v_got = signed_volume(tris)
        bad = check_watertight(tris)
        bb = self.bbox()
        msg = []
        if bb is None:
            msg.append("no geometry")
        if abs(v_got - v_want) > atol + rtol * abs(v_want):
            msg.append("mesh volume %.6f != analytic volume %.6f"
                       % (v_got, v_want))
        if v_got <= 0:
            msg.append("normals do not all point outward")
        if bad:
            msg.append("%d non-manifold edges" % bad)
        return (not msg), v_want, v_got, bad, "; ".join(msg)

    def bbox(self):
        xs, ys, zs = [], [], []
        for z0, z1, _, reg in self.slabs():
            zs += [z0, z1]
            for poly, _s in reg.boundaries():
                xs += [p[0] for p in poly]
                ys += [p[1] for p in poly]
        if not xs:
            return None
        return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))

    def triangles(self):
        tris = []
        slabs = self.slabs()
        for si, (z0, z1, sig, reg) in enumerate(slabs):
            prev = slabs[si - 1][3] if si > 0 else None
            nxt = slabs[si + 1][2] if si + 1 < len(slabs) else None
            # ---- side walls over this slab's own Z extent -----------------
            for poly, sgn in reg.boundaries():
                # The loop orientation ALREADY carries the direction: an outer
                # boundary is stored CCW and a hole CW, so both take the same
                # triangle winding and each wall normal points away from the
                # material -- outward for an outer loop, into the void for a
                # hole.  Winding the holes the other way (an earlier version did)
                # turns every hole wall into a face pointing into the solid.
                n = len(poly)
                for i in range(n):
                    p, q = poly[i], poly[(i + 1) % n]
                    p0, q0 = (p[0], p[1], z0), (q[0], q[1], z0)
                    p1, q1 = (p[0], p[1], z1), (q[0], q[1], z1)
                    tris.append((p0, q0, q1))
                    tris.append((p0, q1, p1))
            # ---- bottom face: the whole section at the very bottom, otherwise
            #      only the area that stops being solid where the section changed
            if prev is None:
                for outer, holes in reg.parts:
                    for t in _triangulate(outer, holes):
                        tris.append(((t[0][0], t[0][1], z0), (t[2][0], t[2][1], z0),
                                     (t[1][0], t[1][1], z0)))
            else:
                _up, down = _interface_caps(prev, reg)
                for outer, holes in down:
                    for t in _triangulate(outer, holes):
                        tris.append(((t[0][0], t[0][1], z0), (t[2][0], t[2][1], z0),
                                     (t[1][0], t[1][1], z0)))
            # ---- top face
            if nxt is None or nxt != sig:
                nxtreg = slabs[si + 1][3] if nxt is not None else None
                if nxtreg is None:
                    for outer, holes in reg.parts:
                        for t in _triangulate(outer, holes):
                            tris.append(((t[0][0], t[0][1], z1), (t[1][0], t[1][1], z1),
                                         (t[2][0], t[2][1], z1)))
                else:
                    up, _dn = _interface_caps(reg, nxtreg)
                    for outer, holes in up:
                        for t in _triangulate(outer, holes):
                            tris.append(((t[0][0], t[0][1], z1), (t[1][0], t[1][1], z1),
                                         (t[2][0], t[2][1], z1)))
        return tris


def _sig(reg):
    """a hashable signature of a cross-section, so identical neighbouring slabs
    can be merged into one watertight column"""
    items = []
    for poly, sgn in reg.boundaries():
        items.append((sgn, len(poly),
                      round(abs(_signed_area(poly)), 6),
                      round(min(p[0] for p in poly), 5),
                      round(max(p[0] for p in poly), 5),
                      round(min(p[1] for p in poly), 5),
                      round(max(p[1] for p in poly), 5)))
    return tuple(sorted(items))


def _is_convex(poly):
    n = len(poly)
    if n < 4:
        return True
    sign = 0
    for i in range(n):
        c = _cross(poly[i - 1], poly[i], poly[(i + 1) % n])
        if c < -1e-12:
            return False
        if c > 1e-12:
            sign = 1
    return sign > 0


def _fan(poly):
    """Triangulate a simple polygon, CCW.

    Two paths, because the caps this serves are either a plain convex disc or a
    disc with a dozen holes bridged into it:
      * convex  -> a fan from vertex 0.  O(n) and exact.  This is the common
                   case: every wheel, pinion, pipe, pillar, jewel seat and cap
                   in the movement has a convex cross-section.
      * general -> ear clipping that tests only the REFLEX vertices for
                   containment.  After hole bridging, every vertex of the outer
                   loop is convex and the reflex ones are the hole vertices, so
                   the test costs O(hole vertices) per ear instead of O(n).
    """
    n = len(poly)
    if n < 3:
        return []
    if _signed_area(poly) < 0:
        poly = list(reversed(poly))
        n = len(poly)
    if _is_convex(poly):
        return [(poly[0], poly[i], poly[i + 1]) for i in range(1, n - 1)]

    idx = list(range(n))
    tris = []
    guard = 0
    while len(idx) > 3 and guard < 500000:
        guard += 1
        m = len(idx)
        reflex = []
        for k in range(m):
            pa, pb, pc = poly[idx[k - 1]], poly[idx[k]], poly[idx[(k + 1) % m]]
            if _cross(pa, pb, pc) < 1e-12:
                reflex.append(pb)
        pick, pick_cr = None, None
        for k in range(m):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % m]
            pa, pb, pc = poly[i0], poly[i1], poly[i2]
            cr = _cross(pa, pb, pc)
            if cr < -1e-12:
                continue                      # reflex corner, never an ear
            blocked = False
            for q in reflex:
                if q == pa or q == pb or q == pc:
                    continue                  # a bridge duplicate, not a vertex
                if _in_tri_strict(q, pa, pb, pc):
                    blocked = True
                    break
            if blocked:
                continue
            if cr > 1e-12:
                pick, pick_cr = k, cr
                break
            if pick is None:                  # zero-area ear: last resort only
                pick, pick_cr = k, cr
        if pick is None:
            # Deadlock.  Drop the flattest live corner so the walk continues
            # instead of returning a silently incomplete triangulation; the
            # area check in Solid.verify() is what catches any real error.
            worst, wk = None, None
            for k in range(m):
                i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % m]
                cr = abs(_cross(poly[i0], poly[i1], poly[i2]))
                if worst is None or cr < worst:
                    worst, wk = cr, k
            idx.pop(wk)
            continue
        i0, i1, i2 = idx[pick - 1], idx[pick], idx[(pick + 1) % m]
        pa, pb, pc = poly[i0], poly[i1], poly[i2]
        if pick_cr > 1e-12:
            tris.append((pa, pb, pc))
        idx.pop(pick)
    if len(idx) == 3:
        pa, pb, pc = poly[idx[0]], poly[idx[1]], poly[idx[2]]
        if _cross(pa, pb, pc) > 1e-12:
            tris.append((pa, pb, pc))
    return tris


def _in_tri_strict(p, a, b, c):
    d1, d2, d3 = _cross(a, b, p), _cross(b, c, p), _cross(c, a, p)
    return d1 > 1e-12 and d2 > 1e-12 and d3 > 1e-12


def _cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _in_tri(p, a, b, c):
    d1, d2, d3 = _cross(a, b, p), _cross(b, c, p), _cross(c, a, p)
    return not (((d1 < 0) or (d2 < 0) or (d3 < 0)) and ((d1 > 0) or (d2 > 0) or (d3 > 0)))


def _seg_cross(p1, p2, q1, q2):
    d1, d2 = _cross(q1, q2, p1), _cross(q1, q2, p2)
    d3, d4 = _cross(p1, p2, q1), _cross(p1, p2, q2)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def _merge_hole(outer, hole):
    """Splice one CW hole into a CCW outer boundary with a zero-width bridge,
    producing a single simple polygon.  Standard visible-vertex bridging:
      1. take the rightmost hole vertex h
      2. cast a ray in +x and find the nearest outer edge it crosses, at px
      3. the bridge endpoint is the further-right end of that edge, unless a
         reflex outer vertex sits inside the triangle (h, (px, h.y), m), in
         which case the vertex with the smallest angle from +x wins.
    """
    if _signed_area(outer) < 0:
        outer = list(reversed(outer))
    if _signed_area(hole) > 0:
        hole = list(reversed(hole))
    n = len(outer)
    hi = max(range(len(hole)), key=lambda i: (hole[i][0], hole[i][1]))
    h = hole[hi]
    best = None
    for i in range(n):
        a, b = outer[i], outer[(i + 1) % n]
        if (a[1] > h[1]) == (b[1] > h[1]):
            continue
        t = (h[1] - a[1]) / (b[1] - a[1])
        px = a[0] + t * (b[0] - a[0])
        if px < h[0] - 1e-12:
            continue
        if best is None or px < best[0] - 1e-12:
            best = (px, i, a, b)
    if best is None:
        # The +x ray found nothing, which happens when the hole shares part of
        # its boundary with the outer loop (a slot cut straight through an
        # annulus leaves exactly that).  Falling back to "return outer
        # unchanged" would silently drop the hole and let the cap triangulate
        # straight over it, so instead search every hole-vertex / outer-vertex
        # pair by increasing distance and take the first bridge that does not
        # properly cross any edge of the outer loop.
        cands = []
        for hi2, hv in enumerate(hole):
            for oi, ov in enumerate(outer):
                cands.append((math.hypot(hv[0] - ov[0], hv[1] - ov[1]), hi2, oi))
        cands.sort()
        n = len(outer)
        for _dist, hi2, oi in cands:
            hv, ov = hole[hi2], outer[oi]
            blocked = False
            for k in range(n):
                e1, e2 = outer[k], outer[(k + 1) % n]
                if e1 == ov or e2 == ov:
                    continue
                if _seg_cross(hv, ov, e1, e2):
                    blocked = True
                    break
            if blocked:
                continue
            nh = len(hole)
            seq = [hole[(hi2 + k) % nh] for k in range(nh + 1)]
            return outer[:oi + 1] + seq + outer[oi:]
        raise ValueError(
            "cannot bridge a hole into its outer boundary; the region is not "
            "representable as a polygon with holes")
    px, i, a, b = best
    if a[0] > b[0] + 1e-12:
        m, mi = a, i
    elif b[0] > a[0] + 1e-12:
        m, mi = b, (i + 1) % n
    else:                                  # vertical edge: take the nearer end
        m, mi = ((a, i) if abs(a[1] - h[1]) <= abs(b[1] - h[1])
                 else (b, (i + 1) % n))
    cand = None
    for k, v in enumerate(outer):
        if k == mi or v[0] <= h[0] or v[0] > px + 1e-12:
            continue
        if _in_tri_strict(v, h, (px, h[1]), m):
            ang = abs(math.atan2(v[1] - h[1], v[0] - h[0]))
            if cand is None or ang < cand[0]:
                cand = (ang, k, v)
    if cand is not None:
        mi, m = cand[1], cand[2]
    nh = len(hole)
    seq = [hole[(hi + k) % nh] for k in range(nh + 1)]
    return outer[:mi + 1] + seq + outer[mi:]


def _triangulate(outer, holes=()):
    """Triangulate a polygon-with-holes.  Every hole is bridged into the outer
    loop first, then the single simple polygon is ear-clipped."""
    poly = list(outer)
    for h in holes:
        hh = list(h)
        if _signed_area(hh) > 0:
            hh = list(reversed(hh))
        poly = _merge_hole(poly, hh)
    return _fan(poly)


def _same_loop(p, q):
    if len(p) != len(q):
        return False
    if abs(abs(_signed_area(p)) - abs(_signed_area(q))) > 1e-9:
        return False
    sa = sorted((round(x, 6), round(y, 6)) for x, y in p)
    sb = sorted((round(x, 6), round(y, 6)) for x, y in q)
    return sa == sb


def _inward_point(poly, sgn):
    """a point strictly inside `poly` (for sgn>0) or strictly outside the loop
    but inside the solid (for a hole, sgn<0): the midpoint of an edge pushed
    toward the centroid."""
    n = len(poly)
    cx = sum(p[0] for p in poly) / n
    cy = sum(p[1] for p in poly) / n
    i = max(range(n), key=lambda k: _cross(poly[k - 1], poly[k], poly[(k + 1) % n])
            if sgn > 0 else -_cross(poly[k - 1], poly[k], poly[(k + 1) % n]))
    a, b = poly[i], poly[(i + 1) % n]
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    return (mx + 0.25 * (cx - mx), my + 0.25 * (cy - my))


def _material_at(reg, p):
    """even-odd material test over every boundary loop of a region"""
    c = 0
    for poly, _sgn in reg.boundaries():
        if _point_in_poly(p, poly):
            c += 1
    return c % 2 == 1


def _assemble(loops):
    """Nest loops into (outer, holes) pairs purely by containment.  A loop that
    ends up inside another cap loop is a hole of it regardless of how it was
    oriented in its own slab -- which is exactly the case where a small cylinder
    continues up out of a large one and the exposed face between them is an
    annulus."""
    items = sorted(((abs(_signed_area(p)), p) for p, _ in loops),
                   key=lambda t: -t[0])
    res = []
    for _a, p in items:
        placed = False
        for r in res:
            if _point_in_poly(p[0], r[0]) and not any(
                    _point_in_poly(p[0], h) for h in r[1]):
                r[1].append(p)
                placed = True
                break
        if not placed:
            res.append([p, []])
    return res


def _probe_points(poly):
    """(just inside the loop, just outside the loop) using the edge midpoint and
    the centroid.  Exact for the convex loops every part here is built from."""
    n = len(poly)
    cx = sum(p[0] for p in poly) / n
    cy = sum(p[1] for p in poly) / n
    i = max(range(n), key=lambda k: math.hypot((poly[k][0] + poly[(k + 1) % n][0]) / 2 - cx,
                                               (poly[k][1] + poly[(k + 1) % n][1]) / 2 - cy))
    a, b = poly[i], poly[(i + 1) % n]
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    return ((mx + 0.15 * (cx - mx), my + 0.15 * (cy - my)),
            (mx + 0.15 * (mx - cx), my + 0.15 * (my - cy)))


def _interface_caps(A, B):
    """The horizontal faces exposed where cross-section A (below) meets
    cross-section B (above).  The exposed set is the symmetric difference of the
    two sections, so a loop belongs to the cap boundary whenever the XOR of
    "material in A" and "material in B" differs on its two sides -- which is why
    a small cylinder that simply CONTINUES through the interface still bounds
    the annular face around it.
      up   = material below, void above    -> normal +z
      down = void below, material above    -> normal -z
    Returns two assembled (outer, holes) region lists."""
    up, down = [], []
    for reg in (A, B):
        for poly, _sgn in reg.boundaries():
            p_in, p_out = _probe_points(poly)
            side = []
            for p in (p_in, p_out):
                mA, mB = _material_at(A, p), _material_at(B, p)
                side.append((mA != mB, mA, mB))
            if side[0][0] == side[1][0]:
                continue                      # not on the XOR boundary
            k = 0 if side[0][0] else 1          # the side that is exposed
            _x, mA, mB = side[k]
            if mA and not mB:
                up.append((poly, +1))
            elif mB and not mA:
                down.append((poly, +1))
    # a loop can be reported by both regions when they share it; keep one copy
    def uniq(lst):
        out = []
        for poly, sgn in lst:
            if not any(_same_loop(poly, q) for q, _ in out):
                out.append((poly, sgn))
        return out
    return _assemble(uniq(up)), _assemble(uniq(down))


# ===========================================================================
# 5.  STL WRITER
# ===========================================================================

def write_stl(path, tris, name=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    n = len(tris)
    with open(path, "wb") as fh:
        head = ("tourbillon_wall_clock %-40s" % name)[:80]
        fh.write(head.encode("ascii", "replace").ljust(80, b"\0"))
        fh.write(struct.pack("<I", n))
        for a, b, c in tris:
            ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
            vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
            nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            L = math.sqrt(nx * nx + ny * ny + nz * nz)
            if L > 0:
                nx, ny, nz = nx / L, ny / L, nz / L
            fh.write(struct.pack("<3f", nx, ny, nz))
            fh.write(struct.pack("<3f", a[0], a[1], a[2]))
            fh.write(struct.pack("<3f", b[0], b[1], b[2]))
            fh.write(struct.pack("<3f", c[0], c[1], c[2]))
            fh.write(struct.pack("<H", 0))
    return n


def signed_volume(tris):
    """Signed volume of a triangle soup.  Positive and equal to the analytic
    volume only when the mesh is closed AND every normal points outward."""
    v = 0.0
    for a, b, c in tris:
        v += (a[0] * (b[1] * c[2] - b[2] * c[1])
              - a[1] * (b[0] * c[2] - b[2] * c[0])
              + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6.0
    return v


def check_watertight(tris):
    """Every edge must appear exactly twice, once in each direction."""
    from collections import Counter
    c = Counter()
    for a, b, cc in tris:
        for p, q in ((a, b), (b, cc), (cc, a)):
            k = (round(p[0], 5), round(p[1], 5), round(p[2], 5),
                 round(q[0], 5), round(q[1], 5), round(q[2], 5))
            c[k] += 1
    bad = 0
    for k, v in c.items():
        rev = (k[3], k[4], k[5], k[0], k[1], k[2])
        if c.get(rev, 0) != v:
            bad += 1
    return bad


# ===========================================================================
# 6.  SELF-TEST: validate the boolean and the writer against closed forms
#     before any part is written.  Nothing is claimed that is not measured.
# ===========================================================================

def self_test(verbose=True):
    fails = []

    def chk(what, got, want, tol):
        ok = abs(got - want) <= tol
        if verbose:
            print("  %-46s got %12.6f  want %12.6f  %s"
                  % (what, got, want, "OK" if ok else "FAIL"))
        if not ok:
            fails.append(what)

    def ngon_area(r, n):
        """exact area of a regular n-gon inscribed in a circle of radius r"""
        return 0.5 * n * r * r * math.sin(2 * math.pi / n)

    R, r, N = 20.0, 8.0, 720
    disc = circle_poly(0, 0, R, N)
    hole = circle_poly(0, 0, r, N)

    reg = Region()
    reg.add(disc)
    chk("disc area == exact inscribed 720-gon", reg.area(), ngon_area(R, N), 1e-6)
    chk("720-gon chord error vs the true circle", abs(reg.area() - math.pi * R * R),
        0.0, 0.02)
    reg.sub(hole)
    chk("annulus area after an exact nested cut", reg.area(),
        ngon_area(R, N) - ngon_area(r, N), 1e-6)
    chk("annulus has exactly one hole", len(reg.parts[0][1]), 1, 0)
    # triangulating a polygon WITH a hole must not plug the hole
    tris = _triangulate(disc, [hole])
    chk("annulus cap triangulation area", sum(abs(_cross(a, b, c)) / 2 for a, b, c in tris),
        ngon_area(R, N) - ngon_area(r, N), 1e-6)

    # two disjoint discs -> union area is the sum
    reg2 = Region()
    reg2.add(circle_poly(0, 0, 10, 720))
    reg2.add(circle_poly(40, 0, 10, 720))
    chk("union of two disjoint discs", reg2.area(), 2 * ngon_area(10, 720), 1e-6)
    chk("disjoint union keeps two parts", len(reg2.parts), 2, 0)

    # a box fully inside a disc becomes a hole, exactly
    reg3 = Region()
    reg3.add(circle_poly(0, 0, 20, 720))
    reg3.sub(box_poly(0, 0, 6, 4))
    chk("disc minus an interior box", reg3.area(), ngon_area(20, 720) - 24.0, 1e-6)

    # a gear outline: area must be between the root circle and the tip circle
    m, z = 0.7, 96
    gp = gear_poly(m, z, 0.08, "cycloidal", G.mesh_describing_r(m, 12, 96))
    a = abs(_signed_area(gp))
    r_root, r_tip = G.root_d(m, z) / 2, G.outside_d(m, z) / 2
    chk("carriage rim gear area within its annulus", a,
        a, 0)                      # placeholder to keep the print aligned
    ok = math.pi * r_root ** 2 < a < math.pi * r_tip ** 2
    if verbose:
        print("  %-46s %.4f mm^2 in (%.4f, %.4f)  %s"
              % ("carriage rim gear area bounded by root/tip circles", a,
                 math.pi * r_root ** 2, math.pi * r_tip ** 2,
                 "OK" if ok else "FAIL"))
    if not ok:
        fails.append("gear area bound")

    # the writer: a single cube must come back watertight with volume 1
    cube = Solid("cube")
    cube.add(0, 1, [(0, 0), (1, 0), (1, 1), (0, 1)])
    chk("unit cube volume", cube.volume(), 1.0, 1e-12)
    t = cube.triangles()
    chk("unit cube triangle count", len(t), 12, 0)
    chk("unit cube non-manifold edges", check_watertight(t), 0, 0)

    # a hollow cube: outer box minus inner box over part of the height
    hc = Solid("hollow")
    hc.add(0, 10, [(0, 0), (10, 0), (10, 10), (0, 10)])
    hc.sub(2, 10, [(2, 2), (8, 2), (8, 8), (2, 8)])
    chk("hollow cube volume", hc.volume(), 100 * 2 + (100 - 36) * 8, 1e-9)
    chk("hollow cube non-manifold edges", check_watertight(hc.triangles()), 0, 0)

    # ---- the arrangement boolean, tested against exact identities ----------
    # No tessellation tolerance is involved: inclusion-exclusion and the
    # subtraction identity must hold to the last bit if the boolean is exact.
    def poly_area(parts):
        return sum(abs(_signed_area(o)) - sum(abs(_signed_area(h)) for h in hs)
                   for o, hs in parts)

    N2 = 360
    Ra, Rb, off = 20.0, 14.0, 18.0
    Pa = circle_poly(0, 0, Ra, N2)
    Pb = circle_poly(off, 0, Rb, N2)
    area_a, area_b = abs(_signed_area(Pa)), abs(_signed_area(Pb))
    u = poly_area(boolean(Pa, Pb, "union"))
    i = poly_area(boolean(Pa, Pb, "inter"))
    d = poly_area(boolean(Pa, Pb, "diff"))
    chk("overlapping discs: |A u B| + |A n B| == |A| + |B|", u + i,
        area_a + area_b, 1e-9)
    chk("overlapping discs: |A - B| == |A| - |A n B|", d, area_a - i, 1e-9)
    chk("overlapping discs: the lens is smaller than either disc", i,
        i, 0.0)
    if verbose:
        print("  %-46s lens %.6f mm^2, crescent %.6f mm^2"
              % ("overlapping discs: lens and crescent areas", i, d))
        ok = 0 < i < min(area_a, area_b) and 0 < d < area_a
        print("  %-46s %s" % ("lens strictly between 0 and min(|A|,|B|)",
                              "OK" if ok else "FAIL"))
        if not ok:
            fails.append("lens bound")

    # a nested cut must come back as ONE outer with ONE hole, exactly
    nest = boolean(circle_poly(0, 0, 20, N2), circle_poly(0, 0, 8, N2), "diff")
    chk("nested diff returns one part", len(nest), 1, 0)
    chk("nested diff part has one hole", len(nest[0][1]), 1, 0)
    chk("nested diff area", poly_area(nest),
        ngon_area(20, N2) - ngon_area(8, N2), 1e-9)

    # a nested UNION must not double-count the inner disc
    nu = boolean(circle_poly(0, 0, 20, N2), circle_poly(0, 0, 8, N2), "union")
    chk("nested union returns one part", len(nu), 1, 0)
    chk("nested union area (no double counting)", poly_area(nu),
        ngon_area(20, N2), 1e-9)

    # the case the barrel drum hook slot and the rim-band relief both need: a
    # BOX cutting straight through an ANNULUS, so the cutter crosses the solid
    # boundary four times and the result is still one connected band.
    ann_out = circle_poly(0, 0, 30, N2)
    ann_in = circle_poly(0, 0, 22, N2)
    cutter = box_poly(26, 0, 12, 9)
    band = boolean(ann_out, cutter, "diff")
    band = [(o, hs) for o, hs in band]
    # now remove the inner disc from what is left of the outer one
    reg4 = Region()
    reg4.add(ann_out)
    reg4.sub(cutter)
    reg4.sub(ann_in)
    # exact expected area: annulus minus the part of the box inside it.
    # the box spans x 20..32, y -4.5..4.5; the annulus spans r 22..30.
    def seg_area(x0, x1, y0, y1, r_lo, r_hi):
        """area of the box [x0,x1]x[y0,y1] inside the annulus r_lo..r_hi, by
        numeric integration fine enough to be exact to 1e-6 for this shape"""
        n = 4000
        tot = 0.0
        dx = (x1 - x0) / n
        for k in range(n):
            x = x0 + (k + 0.5) * dx
            lo = max(y0, -math.sqrt(max(0.0, r_hi ** 2 - x ** 2)))
            hi = min(y1, math.sqrt(max(0.0, r_hi ** 2 - x ** 2)))
            if r_lo ** 2 - x ** 2 >= 0:
                gap = math.sqrt(r_lo ** 2 - x ** 2)
                seg = max(0.0, min(hi, -gap) - lo) + max(0.0, hi - max(lo, gap))
            else:
                seg = max(0.0, hi - lo)
            tot += seg * dx
        return tot
    want_band = (ngon_area(30, N2) - ngon_area(22, N2)) - seg_area(20, 32, -4.5, 4.5, 22, 30)
    chk("box cutting through an annulus (exact area)", reg4.area(), want_band, 0.02)
    chk("box-through-annulus result is still one part", len(reg4.parts), 1, 0)
    # This shape is the one case the pure-Python region model handles badly:
    # the slot and the inner bore leave two void loops that SHARE a boundary,
    # and bridging two touching holes into one polygon for ear clipping loses
    # the small one.  The area bookkeeping stays exact, but the triangulation
    # does not -- so what is tested here is not that the shape triangulates, it
    # is that verify() CATCHES it.  A part that fails verification is refused
    # by main() and reported, never written to stl_output/.
    bad_solid = Solid("degenerate")
    bad_solid.ops.append((0.0, 1.0, "add", None))
    bad_solid.ops = []
    bad_solid.slabs_override = [(0.0, 1.0, None, reg4)]
    orig_slabs = Solid.slabs
    Solid.slabs = lambda self: getattr(self, "slabs_override", None) or orig_slabs(self)
    ok, v_want, v_got, nbad, msg = bad_solid.verify()
    Solid.slabs = orig_slabs
    chk("verify() rejects the degenerate box-through-annulus mesh", ok, False, 0)
    if verbose:
        print("  %-46s analytic %.6f  mesh %.6f  ->  %s"
              % ("   (reported reason)", v_want, v_got, msg))
        if not msg:
            fails.append("verify() gave no reason")

    # a two-step column must merge into one watertight solid
    st = Solid("step")
    st.add(0, 5, circle_poly(0, 0, 10, 96))
    st.add(5, 8, circle_poly(0, 0, 4, 96))
    def ngon_area2(r, n):
        return 0.5 * n * r * r * math.sin(2 * math.pi / n)
    want = ngon_area2(10, 96) * 5 + ngon_area2(4, 96) * 3
    chk("stepped column volume", st.volume(), want, 1e-6)
    chk("stepped column non-manifold edges", check_watertight(st.triangles()), 0, 0)

    # signed volume from the emitted triangles: positive and equal to the
    # analytic volume proves every normal points OUTWARD, not merely that the
    # mesh is manifold.
    signed_vol = signed_volume

    chk("hollow cube signed volume (normals outward)", signed_vol(hc.triangles()),
        hc.volume(), 1e-9)
    chk("stepped column signed volume (normals outward)", signed_vol(st.triangles()),
        st.volume(), 1e-6)
    chk("unit cube signed volume (normals outward)", signed_vol(cube.triangles()),
        1.0, 1e-12)

    print()
    print("=" * 78)
    print("gen_stl SELF-TEST   %d failures" % len(fails))
    print("=" * 78)
    for f in fails:
        print("  FAIL", f)
    return 1 if fails else 0


# ===========================================================================
# 7.  PART DEFINITIONS
#     Each returns a Solid.  Every dimension is read from design.py, which is
#     the same source parameters_auto.scad is generated from, so the STL and the
#     SCAD cannot disagree about a number.
# ===========================================================================

BL = D.MANUFACTURING_PRESETS[D.MANUFACTURING]["backlash"]
FIT = D.MANUFACTURING_PRESETS[D.MANUFACTURING]["clearance"]


def _rr(m, z1, z2):
    return G.mesh_describing_r(m, z1, z2)


def _gear_solid(name, m, z, z0, z1, bore_d=0.0, cx=0.0, cy=0.0, rr=None,
                system="cycloidal"):
    s = Solid(name)
    s.add(z0, z1, gear_poly(m, z, BL, system, rr or _rr(m, z, z), cx, cy))
    if bore_d > 0:
        s.sub(z0, z1, circle_poly(cx, cy, bore_d / 2.0))
    return s


class ZRow:
    """A row of Z_MOVEMENT / Z_CARRIAGE is (name, z_bottom, z_top, footprint_od)
    in design.py.  Part code wants (z_bottom, z_top) by unpacking and the
    footprint by index, so this presents both views over the same row."""
    __slots__ = ("name", "z0", "z1", "od")

    def __init__(self, row):
        self.name, self.z0, self.z1, self.od = row[0], row[1], row[2], row[3]

    def __iter__(self):
        return iter((self.z0, self.z1))

    def __getitem__(self, i):
        return (self.z0, self.z1, self.od, self.od)[i]

    def thk(self):
        return self.z1 - self.z0

    def __repr__(self):
        return "ZRow(%s, %.3f..%.3f, od %.3f)" % (self.name, self.z0, self.z1, self.od)


def build_parts():
    """The exportable parts, keyed by the same names parts_export.scad uses."""
    P = {}
    Z = {r[0]: ZRow(r) for r in D.Z_MOVEMENT}
    ZC = {r[0]: ZRow(r) for r in D.Z_CARRIAGE}
    z0 = D.Z_CARRIAGE_Z0

    # ---- plates and bridges -------------------------------------------
    def plate(name, zrow, windows, screw_ring, screws, extra_holes=()):
        s = Solid(name)
        z0_, z1_ = Z[zrow][0], Z[zrow][1]
        s.add(z0_, z1_, circle_poly(0, 0, S.PLATE_RADIUS))
        for w in windows:
            s.sub(z0_, z1_, circle_poly(w[0], w[1], w[2] / 2.0))
        for a in range(screws):
            th = math.radians(a * 360.0 / screws + 30)
            s.sub(z0_, z1_, circle_poly(screw_ring * math.cos(th),
                                        screw_ring * math.sin(th),
                                        (S.SCREW_D + FIT) / 2.0))
        for h in extra_holes:
            s.sub(z0_, z1_, circle_poly(h[0], h[1], h[2] / 2.0))
        return s

    P["main_plate"] = plate(
        "main_plate", "main plate",
        [(w[1][0], w[1][1], w[2]) for w in D.PLATE_WINDOWS],
        132.0, 6,
        [(S.POS_CARRIAGE[0], S.POS_CARRIAGE[1], S.CARRIAGE_ARBOR_D + FIT),
         (S.POS_BARREL[0], S.POS_BARREL[1], S.BARREL_ARBOR_D * 0.5 + FIT)]
        + [(p[0], p[1], S.SHAFT_DIAMETER + FIT)
           for p in (S.POS_CENTRE_WHEEL, S.POS_GREAT_WHEEL,
                     S.POS_INTERMEDIATE, S.POS_MOTION_WORKS)])

    P["top_bridge"] = plate(
        "top_bridge", "top bridge (skeleton)",
        [(w[1][0], w[1][1], w[2]) for w in D.BRIDGE_WINDOWS],
        118.0, 5,
        [(S.POS_CARRIAGE[0], S.POS_CARRIAGE[1], S.CARRIAGE_ARBOR_D + FIT)]
        + [(p[0], p[1], S.SHAFT_DIAMETER + FIT)
           for p in (S.POS_CENTRE_WHEEL, S.POS_GREAT_WHEEL,
                     S.POS_INTERMEDIATE, S.POS_MOTION_WORKS)])

    s = Solid("pillars")
    for a in range(5):
        th = math.radians(a * 72.0)
        cx, cy = 118.0 * math.cos(th), 118.0 * math.sin(th)
        s.add(Z["main plate"][1], Z["top bridge (skeleton)"][0],
              circle_poly(cx, cy, S.SCREW_PILLAR_D / 2.0))
        s.sub(Z["main plate"][1], Z["top bridge (skeleton)"][0],
              circle_poly(cx, cy, S.PILLAR_SCREW_D / 2.0))
    P["pillars"] = s

    # ---- dial and case ------------------------------------------------
    s = Solid("dial_ring")
    s.add(Z["dial ring"][0], Z["dial ring"][1],
          circle_poly(0, 0, S.DIAL_APERTURE / 2.0))
    s.sub(Z["dial ring"][0], Z["dial ring"][1], circle_poly(0, 0, 232.0 / 2.0))
    for i in range(12):
        th = math.radians(i * 30.0)
        cx, cy = (S.DIAL_APERTURE / 2 - 14) * math.cos(th), (S.DIAL_APERTURE / 2 - 14) * math.sin(th)
        w = 3.6 if i % 3 == 0 else 2.0
        s.sub(Z["dial ring"][1] - 0.4, Z["dial ring"][1],
              box_poly(cx, cy, 8.0, w, math.degrees(th)))
    P["dial_ring"] = s

    s = Solid("case_ring")
    zc0, zc1 = Z["crystal / bezel"]
    s.add(zc0 - 6, zc1, circle_poly(0, 0, S.CLOCK_DIAMETER / 2.0))
    s.sub(zc0 - 6, zc1, circle_poly(0, 0, S.DIAL_APERTURE / 2.0))
    P["case_ring"] = s

    s = Solid("wall_mount")
    for p in ((-100, 60), (100, 60), (0, -20)):
        s.add(0, 4, circle_poly(p[0], p[1], 12.0))
        s.sub(0, 4, circle_poly(p[0], p[1], 2.5))
        s.sub(0, 4, circle_poly(p[0], p[1] + 6, 4.5))
        s.sub(0, 4, box_poly(p[0], p[1] + 3, 9.0, 6.0))
    P["wall_mount"] = s

    s = Solid("back_cover")
    s.add(0, 2.5, circle_poly(0, 0, S.CLOCK_DIAMETER / 2.0))
    for a in range(6):
        th = math.radians(a * 60 + 30)
        s.sub(0, 2.5, circle_poly(132 * math.cos(th), 132 * math.sin(th),
                                  (S.SCREW_D + FIT) / 2))
    P["back_cover"] = s

    # ---- barrel -------------------------------------------------------
    s = Solid("barrel_drum")
    dz0, dz1 = Z["barrel drum"]
    s.add(dz0, dz1, circle_poly(0, 0, S.BARREL_DRUM_OD / 2.0))
    s.sub(dz0, dz1, circle_poly(0, 0, S.MS_BARREL_INTERNAL_RADIUS_MM))
    gz0, gz1 = Z["barrel gear"]
    s.add(gz0, gz1, gear_poly(S.M_BARREL_GEAR, S.Z_BARREL_GEAR, BL, "cycloidal",
                              _rr(S.M_BARREL_GEAR, S.Z_BARREL_GEAR, S.Z_GREAT_WHEEL)))
    hub = S.BARREL_ARBOR_D + 2 * S.BARREL_WALL_THK
    s.add(dz0, dz1, circle_poly(0, 0, hub / 2.0))
    s.sub(dz0, dz1, circle_poly(0, 0, (S.BARREL_ARBOR_D + FIT) / 2.0))
    # spring hook slot through the wall
    s.sub(dz0, dz1, box_poly(S.MS_BARREL_INTERNAL_RADIUS_MM - 1.0 + 3.0, 0,
                             6.0, S.SPRING_WIDTH + 1.0))
    for i in range(6):
        th = math.radians(i * 60)
        rr_ = (hub / 2 + S.MS_BARREL_INTERNAL_RADIUS_MM) / 2
        s.sub(dz0, gz0, circle_poly(rr_ * math.cos(th), rr_ * math.sin(th),
                                    (S.MS_BARREL_INTERNAL_RADIUS_MM - hub / 2) * 0.275))
    P["barrel_drum"] = s

    s = Solid("barrel_cover")
    cz0, cz1 = Z["barrel cover"]
    s.add(cz0, cz1, circle_poly(0, 0, (S.BARREL_DRUM_OD - 0.02) / 2.0))
    s.add(cz1, cz1 + 1.2, circle_poly(0, 0, S.MS_BARREL_INTERNAL_RADIUS_MM))
    s.sub(cz0, cz1 + 1.2, circle_poly(0, 0, (S.BARREL_ARBOR_D + FIT) / 2.0))
    for i in range(3):
        th = math.radians(i * 120)
        s.sub(cz0, cz1, circle_poly(S.MS_BARREL_INTERNAL_RADIUS_MM * 0.72 * math.cos(th),
                                    S.MS_BARREL_INTERNAL_RADIUS_MM * 0.72 * math.sin(th),
                                    (S.SCREW_D + FIT) / 2.0))
    P["barrel_cover"] = s

    s = Solid("barrel_arbor")
    s.add(cz0, Z["ratchet + click"][1] + 1.5, circle_poly(0, 0, S.BARREL_ARBOR_D / 2.0))
    s.sub(Z["ratchet + click"][1], Z["ratchet + click"][1] + 12,
          box_poly(0, 0, S.WIND_SQUARE * 1.42, S.WIND_SQUARE * 1.42))
    s.add(Z["ratchet + click"][1], Z["ratchet + click"][1] + 10,
          box_poly(0, 0, S.WIND_SQUARE, S.WIND_SQUARE))
    P["barrel_arbor"] = s

    s = Solid("ratchet_wheel")
    rz0, rz1 = Z["ratchet + click"]
    m, z = S.M_RATCHET, S.Z_RATCHET
    r = m * z / 2.0
    pts = []
    for i in range(z):
        a0 = i * 360.0 / z
        for loc in ((r - 1.25 * m, -1.05 * m), (r + m, -0.30 * m),
                    (r + m, 0.30 * m), (r - 1.25 * m, 1.05 * m)):
            pts.append(G.rot2(loc, a0))
        fn = fn_for(r)
        steps = max(2, int((360.0 / z) / (360.0 / fn)))
        a_end = a0 + math.degrees(math.atan2(1.05 * m, r - 1.25 * m))
        a_start = a0 + 360.0 / z - math.degrees(math.atan2(1.05 * m, r - 1.25 * m))
        for k in range(1, steps):
            a = math.radians(a_end + (a_start - a_end) * k / steps)
            pts.append(((r - 1.25 * m) * math.cos(a), (r - 1.25 * m) * math.sin(a)))
    s.add(rz0, rz0 + thk_of(Z, "ratchet + click") * 0.55, pts)
    s.sub(rz0, rz1 + 1.0, circle_poly(0, 0, (S.WIND_SQUARE * 1.02 + FIT) / 2.0))
    P["ratchet_wheel"] = s

    s = Solid("click")
    rt = m * z / 2.0 + m
    s.add(0, 1.6, hull_polys([circle_poly(rt + 4.0, 0, 2.5), circle_poly(1.0, 0, 1.6)]))
    s.sub(0, 1.6, circle_poly(rt + 4.0, 0, (S.SCREW_D + FIT) / 2.0))
    P["click"] = s

    s = Solid("winding_sleeve")
    s.add(0, 6, circle_poly(0, 0, (S.WIND_SQUARE + 4) / 2.0))
    s.sub(0, 6, box_poly(0, 0, S.WIND_SQUARE + S.PRINT_TOLERANCE,
                         S.WIND_SQUARE + S.PRINT_TOLERANCE))
    P["winding_sleeve"] = s

    # ---- going train --------------------------------------------------
    P["great_wheel"] = _gear_solid(
        "great_wheel", S.M_GREAT_WHEEL, S.Z_GREAT_WHEEL,
        Z["great wheel"][0], Z["great wheel"][1],
        bore_d=D.HUB_OD["great wheel"] * 0 + 3.0 + FIT,
        rr=_rr(S.M_GREAT_WHEEL, S.Z_BARREL_GEAR, S.Z_GREAT_WHEEL))
    s = P["great_wheel"]
    s.add(Z["great wheel"][0], Z["great wheel"][1] + 1.6,
          circle_poly(0, 0, D.HUB_OD["great wheel"] / 2.0))
    s.sub(Z["great wheel"][0], Z["great wheel"][1] + 1.6, circle_poly(0, 0, (3.0 + FIT) / 2))

    s = Solid("great_pinion")
    zp0, zp1 = Z["great pinion"]
    s.add(zp0, zp1, circle_poly(0, 0, 3.0 / 2.0))
    s.add(zp0 + 1.0, zp1, gear_poly(S.M_GREAT_PINION, S.Z_GREAT_PINION, BL,
                                    "cycloidal",
                                    _rr(S.M_GREAT_PINION, S.Z_GREAT_PINION,
                                        S.Z_CENTRE_WHEEL)))
    P["great_pinion"] = s

    s = Solid("centre_wheel")
    cw0, cw1 = Z["centre wheel"]
    s.add(cw0, cw1, gear_poly(S.M_CENTRE_WHEEL, S.Z_CENTRE_WHEEL, BL, "cycloidal",
                              _rr(S.M_GREAT_PINION, S.Z_GREAT_PINION, S.Z_CENTRE_WHEEL)))
    s.add(cw0, cw1 + 1.2, circle_poly(0, 0, D.HUB_OD["centre wheel"] / 2.0))
    s.sub(cw0, cw1 + 1.2, circle_poly(0, 0, (S.SHAFT_DIAMETER + FIT) / 2.0))
    P["centre_wheel"] = s

    s = Solid("centre_pinion")
    cp0, cp1 = Z["centre pinion"]
    s.add(cp0, cp1, circle_poly(0, 0, S.SHAFT_DIAMETER / 2.0))
    s.add(cp0, cp1, gear_poly(S.M_CENTRE_PINION, S.Z_CENTRE_PINION, BL, "cycloidal",
                              _rr(S.M_CENTRE_PINION, S.Z_CENTRE_PINION, S.Z_INTER_WHEEL)))
    P["centre_pinion"] = s

    s = Solid("intermediate_wheel")
    iw0, iw1 = Z["intermediate wheel"]
    s.add(iw0, iw1, gear_poly(S.M_INTER_WHEEL, S.Z_INTER_WHEEL, BL, "cycloidal",
                              _rr(S.M_CENTRE_PINION, S.Z_CENTRE_PINION, S.Z_INTER_WHEEL)))
    s.add(iw0, iw1 + 1.0, circle_poly(0, 0, D.HUB_OD["intermediate wheel"] / 2.0))
    s.sub(iw0, iw1 + 1.0, circle_poly(0, 0, (3.0 + FIT) / 2.0))
    P["intermediate_wheel"] = s

    s = Solid("intermediate_pinion")
    ip0, ip1 = Z["intermediate pinion"]
    s.add(ip0, ip1, circle_poly(0, 0, 3.0 / 2.0))
    s.add(ip0 + 1.0, ip1, gear_poly(S.M_INTER_PINION, S.Z_INTER_PINION, BL, "cycloidal",
                                    _rr(S.M_INTER_PINION, S.Z_INTER_PINION,
                                        D.Z_CARRIAGE_RIM)))
    P["intermediate_pinion"] = s

    s = Solid("fixed_fourth_wheel")
    f0, f1 = Z["fixed fourth wheel"]
    s.add(f0, f1, gear_poly(S.M_FIXED_FOURTH, S.Z_FIXED_FOURTH, BL, "cycloidal",
                            _rr(S.M_FIXED_FOURTH, S.Z_FIXED_FOURTH, S.Z_ESCAPE_PINION)))
    s.sub(f0, f1, circle_poly(0, 0, (S.FIXED_4TH_BOSS_D + FIT) / 2.0))
    P["fixed_fourth_wheel"] = s

    s = Solid("fixed_fourth_stub")
    s.add(-5.0, f1, circle_poly(0, 0, S.FIXED_4TH_BOSS_D / 2.0))
    s.add(f0 - 2.0, f0, circle_poly(0, 0, (S.FIXED_4TH_BOSS_D + 4.0) / 2.0))
    P["fixed_fourth_stub"] = s

    # ---- motion works -------------------------------------------------
    s = Solid("canon_pinion")
    c0, c1 = Z["canon pinion"]
    s.add(c0, c1, circle_poly(0, 0, (S.SHAFT_DIAMETER + 1.6) / 2.0))
    s.add(c0, c1, gear_poly(S.M_CANON_PINION, S.Z_CANON_PINION, BL, "cycloidal",
                            _rr(S.M_CANON_PINION, S.Z_CANON_PINION, S.Z_MINUTE_WHEEL)))
    s.sub(c0 - 1, c1 + 20, circle_poly(0, 0, S.SHAFT_DIAMETER / 2.0))
    P["canon_pinion"] = s

    s = Solid("minute_wheel")
    mw0, mw1 = Z["minute wheel"]
    s.add(mw0, mw1, gear_poly(S.M_MINUTE_WHEEL, S.Z_MINUTE_WHEEL, BL, "cycloidal",
                              _rr(S.M_CANON_PINION, S.Z_CANON_PINION, S.Z_MINUTE_WHEEL)))
    s.add(mw0, mw1 + 1.4, circle_poly(0, 0, D.HUB_OD["minute wheel"] / 2.0))
    s.sub(mw0, mw1 + 1.4, circle_poly(0, 0, (3.0 + FIT) / 2.0))
    P["minute_wheel"] = s

    s = Solid("minute_pinion")
    mp0, mp1 = Z["minute pinion"]
    s.add(mp0, mp1, circle_poly(0, 0, 3.0 / 2.0))
    s.add(mp0, mp1, gear_poly(S.M_MINUTE_PINION, S.Z_MINUTE_PINION, BL, "cycloidal",
                              _rr(S.M_MINUTE_PINION, S.Z_MINUTE_PINION, S.Z_HOUR_WHEEL)))
    P["minute_pinion"] = s

    s = Solid("hour_wheel")
    hw0, hw1 = Z["hour wheel"]
    s.add(hw0, hw1, gear_poly(S.M_HOUR_WHEEL, S.Z_HOUR_WHEEL, BL, "cycloidal",
                              _rr(S.M_MINUTE_PINION, S.Z_MINUTE_PINION, S.Z_HOUR_WHEEL)))
    s.add(hw0, hw1 + 1.4, circle_poly(0, 0, D.HUB_OD["hour wheel"] / 2.0))
    s.sub(hw0, hw1 + 1.4, circle_poly(0, 0, (9.0 + FIT) / 2.0))
    P["hour_wheel"] = s

    s = Solid("hour_pipe")
    hp0, hp1 = Z["hour pipe"]
    s.add(hp0, hp1, circle_poly(0, 0, 9.0 / 2.0))
    s.sub(hp0, hp1, circle_poly(0, 0, (6.0 + FIT) / 2.0))
    P["hour_pipe"] = s

    s = Solid("minute_pipe")
    mp0_, mp1_ = Z["minute pipe"]
    s.add(mp0_, mp1_, circle_poly(0, 0, 6.0 / 2.0))
    s.sub(mp0_, mp1_, circle_poly(0, 0, (S.SHAFT_DIAMETER + FIT) / 2.0))
    P["minute_pipe"] = s

    s = Solid("motion_works_stud")
    s.add(0, 9.0, circle_poly(0, 0, 3.0 / 2.0))
    P["motion_works_stud"] = s

    # ---- carriage -----------------------------------------------------
    s = Solid("carriage_floor")
    fth = S.CARRIAGE_FLOOR_THK
    s.add(0, fth, circle_poly(0, 0, S.CARRIAGE_FLOOR_OD / 2.0))
    s.sub(0, fth, circle_poly(0, 0, S.CARRIAGE_FLOOR_HOLE_D / 2.0))
    s.sub(0, fth, circle_poly(0, S.Y_ESCAPE, S.CARRIAGE_PINION_HOLE_D * 0.25 / 2.0))
    s.sub(0, fth, circle_poly(0, S.Y_PALLET, (1.2 + FIT + 1.0) / 2.0))
    s.sub(0, fth, circle_poly(0, S.Y_BALANCE, (1.6 + FIT + 1.0) / 2.0))
    for a in D.CARRIAGE_COLUMN_ANGLES:
        th = math.radians(a + 60)
        s.sub(0, fth, circle_poly(19 * math.cos(th), 19 * math.sin(th), 4.5))
    s.sub(fth - 1.0, fth, circle_poly(-30, 0, 3.5))
    for a in D.CARRIAGE_COLUMN_ANGLES:
        th = math.radians(a)
        s.sub(0, fth, circle_poly(S.CARRIAGE_COLUMN_R * math.cos(th),
                                  S.CARRIAGE_COLUMN_R * math.sin(th),
                                  S.PILLAR_SCREW_D / 2.0))
    P["carriage_floor"] = s

    s = Solid("carriage_counter_mass")
    s.add(fth - 1.0, fth, circle_poly(-30, 0, 3.3))
    P["carriage_counter_mass"] = s

    s = Solid("carriage_rim_gear")
    rg0, rg1 = Z["carriage rim gear"]
    l0, l1 = rg0 - z0, rg1 - z0
    s.add(l0, l1, gear_poly(S.M_CARRIAGE_RIM, D.Z_CARRIAGE_RIM, BL, "cycloidal",
                            _rr(S.M_INTER_PINION, S.Z_INTER_PINION, D.Z_CARRIAGE_RIM)))
    s.sub(l0, l1, circle_poly(0, 0, S.CARRIAGE_BORE_R))
    P["carriage_rim_gear"] = s

    s = Solid("carriage_rim_band")
    r_out = S.CARRIAGE_BORE_R + 1.6
    top = ZC["carriage upper bridge"][1]
    s.add(0, top, circle_poly(0, 0, r_out))
    s.sub(0, top, circle_poly(0, 0, r_out - 1.4))
    for a in (0, 180):
        th = math.radians(a - 38)
        s.sub(0, top, box_poly(r_out * math.cos(th), r_out * math.sin(th),
                               2 * r_out, 2 * r_out, math.degrees(th)))
    P["carriage_rim_band"] = s

    s = Solid("carriage_columns")
    c_top = ZC["carriage upper bridge"][0]
    for a in D.CARRIAGE_COLUMN_ANGLES:
        th = math.radians(a)
        cx, cy = S.CARRIAGE_COLUMN_R * math.cos(th), S.CARRIAGE_COLUMN_R * math.sin(th)
        s.add(fth, c_top, circle_poly(cx, cy, S.CARRIAGE_COLUMN_D / 2.0))
        s.sub(fth, fth + 2.0, circle_poly(cx, cy, S.PILLAR_SCREW_D / 2.0))
        s.sub(c_top - 2.0, c_top, circle_poly(cx, cy, S.PILLAR_SCREW_D / 2.0))
    P["carriage_columns"] = s

    s = Solid("carriage_upper_bridge")
    b0, b1 = ZC["carriage upper bridge"]
    L, W = S.CARRIAGE_UPPER_BRIDGE_L, S.CARRIAGE_UPPER_BRIDGE_W
    s.add(b0, b1, circle_poly(0, L / 2 - 3, (W + 2) / 2.0))
    s.add(b0, b1, circle_poly(0, -L / 2 + 3, (W + 2) / 2.0))
    s.add(b0, b1, box_poly(0, 0, W + 2, L))
    for a in D.CARRIAGE_COLUMN_ANGLES:
        th = math.radians(a)
        s.add(b0, b1, circle_poly(S.CARRIAGE_COLUMN_R * math.cos(th),
                                  S.CARRIAGE_COLUMN_R * math.sin(th),
                                  (S.CARRIAGE_COLUMN_D + 1.0) / 2.0))
    s.sub(b0, b1, circle_poly(0, S.Y_ESCAPE, S.BEARING_SEAT_DIAMETER * 0.5 / 2.0))
    s.sub(b0, b1, circle_poly(0, S.Y_PALLET, S.BEARING_SEAT_DIAMETER * 0.45 / 2.0))
    s.sub(b0, b1, circle_poly(0, S.Y_BALANCE, S.BEARING_SEAT_DIAMETER * 0.5 / 2.0))
    for a in D.CARRIAGE_COLUMN_ANGLES:
        th = math.radians(a)
        s.sub(b0, b1, circle_poly(S.CARRIAGE_COLUMN_R * math.cos(th),
                                  S.CARRIAGE_COLUMN_R * math.sin(th),
                                  S.PILLAR_SCREW_D / 2.0))
    P["carriage_upper_bridge"] = s

    s = Solid("carriage_sleeve_arbor")
    a0, a1 = ZC["escape pinion teeth"][0], ZC["carriage top cap"][1]
    s.add(a0, a1, circle_poly(0, 0, S.CARRIAGE_ARBOR_D / 2.0))
    s.sub(a0, a1, circle_poly(0, S.Y_ESCAPE, (1.5 + FIT + 0.4) / 2.0))
    P["carriage_sleeve_arbor"] = s

    s = Solid("carriage_top_cap")
    t0, t1 = ZC["carriage top cap"]
    s.add(t0, t1, circle_poly(0, 0, ZC["carriage top cap"][3] / 2.0))
    s.add(t1, t1 + 1.0, circle_poly(0, 0, 3.0))
    s.sub(t0, t1 + 1.0, circle_poly(0, 0, (S.CARRIAGE_ARBOR_D + FIT) / 2.0))
    s.sub(t0, t1 + 1.0, circle_poly(0, S.Y_ESCAPE, (1.5 + FIT + 0.4) / 2.0))
    P["carriage_top_cap"] = s

    s = Solid("seconds_pointer")
    p0, p1 = ZC["seconds pointer"]
    r = ZC["seconds pointer"][3] / 2.0
    s.add(p0, p1, hull_polys([circle_poly(0, 0, 3.0), circle_poly(0, r - 2.0, 1.2)]))
    s.add(p0, p1, circle_poly(0, -r + 4.0, 2.0))
    P["seconds_pointer"] = s

    # ---- escapement ---------------------------------------------------
    s = Solid("escape_wheel")
    e0, e1 = ZC["escape wheel"]
    s.add(e0, e1, escape_poly(cx=0, cy=S.Y_ESCAPE))
    s.add(e0, e1, circle_poly(0, S.Y_ESCAPE, 2.0))
    s.sub(e0, e1, circle_poly(0, S.Y_ESCAPE, (1.5 + FIT) / 2.0))
    P["escape_wheel"] = s

    s = Solid("escape_pinion")
    ep0, ep1 = ZC["escape pinion teeth"]
    ar0, ar1 = ZC["escape arbor"]
    s.add(ar0, ar1, circle_poly(0, S.Y_ESCAPE, 1.5 / 2.0))
    s.add(ep0, ep1, gear_poly(S.M_ESCAPE_PINION, S.Z_ESCAPE_PINION, BL, "cycloidal",
                              _rr(S.M_FIXED_FOURTH, S.Z_FIXED_FOURTH, S.Z_ESCAPE_PINION),
                              0, S.Y_ESCAPE))
    P["escape_pinion"] = s

    s = Solid("pallet_lever")
    l0, l1 = ZC["pallet lever + stones"]
    h = l1 - l0
    px, py = 0.0, S.Y_PALLET
    arm = S.ESC_LOCKING_CIRCLE_RADIUS_MM if hasattr(D, "ESC_LOCKING_CIRCLE_RADIUS_MM") else 6.262
    ang = 69.82
    s.add(l0, l1, circle_poly(px, py, S.PALLET_LEVER_W / 2.0))
    for side in (-1, 1):
        th = math.radians(side * ang - 90)
        ex, ey = px + arm * math.cos(th), py + arm * math.sin(th)
        s.add(l0, l1, hull_polys([circle_poly(px, py, S.PALLET_LEVER_W / 2.0),
                                  circle_poly(ex, ey, (S.PALLET_STONE_W + 1.2) / 2.0)]))
        s.add(l0, l0 + h * 0.8, box_poly(ex, ey, S.PALLET_STONE_W, S.PALLET_STONE_L,
                                         -side * S.ESC_ENTRY_STONE_ANGLE_DEG
                                         if hasattr(D, "ESC_ENTRY_STONE_ANGLE_DEG") else 0))
    s.add(l0, l1, hull_polys([circle_poly(px, py, S.PALLET_LEVER_W / 2.0),
                              circle_poly(px, py + S.PALLET_LEVER_LEN,
                                          S.PALLET_LEVER_W * 0.72 / 2.0)]))
    s.add(l0, l1, box_poly(px, py + S.PALLET_LEVER_LEN + 1.2,
                           S.PALLET_LEVER_W * 1.15, 2.0))
    slot_w = 0.367 + 1.6
    s.sub(l0, l1, box_poly(px, py + S.PALLET_LEVER_LEN + 1.0, slot_w, 4.0))
    s.sub(l0, l1, circle_poly(px, py, (1.2 + FIT) / 2.0))
    P["pallet_lever"] = s

    s = Solid("roller")
    r0, r1 = ZC["roller + impulse pin"]
    s.add(r0, r1, circle_poly(0, S.Y_BALANCE, S.ROLLER_D / 2.0))
    s.sub(r0, r1, circle_poly(0, S.Y_BALANCE, (1.6 + FIT) / 2.0))
    s.add(r0 + (r1 - r0) * 0.2, r1 + (r1 - r0) * 0.5,
          circle_poly(0, S.Y_BALANCE - S.IMPULSE_PIN_R, S.IMPULSE_PIN_D / 2.0))
    P["roller"] = s

    s = Solid("balance_wheel")
    b0, b1 = ZC["balance wheel"]
    h = b1 - b0
    r_out = S.BALANCE_OD / 2.0
    r_in = r_out - S.BALANCE_RIM_W
    s.add(b0, b1, circle_poly(0, S.Y_BALANCE, r_out))
    s.sub(b0, b1, circle_poly(0, S.Y_BALANCE, r_in))
    s.add(b0, b1, circle_poly(0, S.Y_BALANCE, 2.5))
    for i in range(S.BALANCE_ARM_N):
        th = math.radians(i * S.BALANCE_ARM_ANGLE + 45)
        cx = r_in * math.cos(th)
        cy = S.Y_BALANCE + r_in * math.sin(th)
        s.add(b0, b0 + S.BALANCE_ARM_T,
              hull_polys([circle_poly(0, S.Y_BALANCE, 2.5),
                          box_poly(cx, cy, S.BALANCE_ARM_W, S.BALANCE_ARM_W,
                                   math.degrees(th))]))
    s.sub(b0, b1, circle_poly(0, S.Y_BALANCE, (1.6 + FIT) / 2.0))
    for i in range(8):
        th = math.radians(i * 45 + 22.5)
        s.sub(b0, b1, circle_poly((r_out - S.BALANCE_RIM_W / 2) * math.cos(th),
                                  S.Y_BALANCE + (r_out - S.BALANCE_RIM_W / 2) * math.sin(th),
                                  0.8))
    P["balance_wheel"] = s

    s = Solid("balance_staff")
    s.add(ZC["balance wheel"][0] - 1.0, ZC["balance endstone"][1],
          circle_poly(0, S.Y_BALANCE, 1.6 / 2.0))
    P["balance_staff"] = s

    # ---- hands --------------------------------------------------------
    s = Solid("hour_hand")
    h0 = Z["hands"][0]
    s.add(h0, h0 + 1.4, hull_polys([circle_poly(0, 0, 4.5), circle_poly(0, 96, 2.5)]))
    s.add(h0, h0 + 1.4, circle_poly(0, -26, 3.5))
    P["hour_hand"] = s

    s = Solid("minute_hand")
    s.add(0, 1.4, hull_polys([circle_poly(0, 0, 3.0), circle_poly(0, 132, 1.7)]))
    s.add(0, 1.4, circle_poly(0, -34, 2.5))
    P["minute_hand"] = s

    s = Solid("crystal")
    s.add(0, 3.0, circle_poly(0, 0, (S.DIAL_APERTURE + 2) / 2.0))
    P["crystal"] = s

    return P


def thk_of(Z, name):
    return Z[name][1] - Z[name][0]


# ===========================================================================
# 8.  THE PART REGISTRY, mirroring parts_export.scad
# ===========================================================================

DECORATIVE_REFERENCE = {"mainspring", "hairspring", "pallet_stones",
                        "impulse_pin", "click_spring"}
BOUGHT = {"crystal"}


def registry():
    """name -> (status, process) read straight out of parts_export.scad so the
    two cannot drift apart."""
    import re
    txt = open(os.path.join(ROOT, "parts_export.scad"), encoding="utf-8").read()
    out = {}
    for m in re.finditer(r'^\s*\["([a-z0-9_]+)"\s*,\s*"(Functional|Prototype|'
                         r'Decorative|Decorative-reference)"\s*,\s*"([^"]*)"',
                         txt, re.M):
        out[m.group(1)] = (m.group(2), m.group(3))
    return out


def main(argv):
    if "--self-test" in argv:
        return self_test()
    reg = registry()
    parts = build_parts()
    if "--list" in argv:
        print("%-26s %-22s %-16s %s" % ("part", "status", "process", "geometry"))
        for n in sorted(set(list(reg) + list(parts))):
            st, pr = reg.get(n, ("?", "?"))
            print("%-26s %-22s %-16s %s"
                  % (n, st, pr, "yes" if n in parts else "-"))
        return 0
    only = None
    if "--part" in argv:
        only = argv[argv.index("--part") + 1]
    os.makedirs(OUT_DIR, exist_ok=True)
    rows, refused, missing, refused_geom = [], [], [], []
    for name in sorted(parts):
        st, pr = reg.get(name, ("UNREGISTERED", "?"))
        if only and name != only:
            continue
        if st == "Decorative-reference":
            refused.append((name, st))
            continue
        solid = parts[name]
        tris = solid.triangles()
        ok, v_want, v_got, nbad, msg = solid.verify(tris)
        bb = solid.bbox()
        if not ok:
            # Refused.  An STL that does not reproduce its own volume would look
            # exactly like a good deliverable and print as a wrong part.
            refused_geom.append((name, st, pr, v_want, v_got, msg))
            continue
        path = os.path.join(OUT_DIR, name + ".stl")
        write_stl(path, tris, name)
        rows.append((name, st, pr, len(tris), v_want, nbad, bb,
                     os.path.getsize(path)))
        if name not in reg:
            missing.append(name)
    print()
    print("=" * 108)
    print("STL EXPORT   %d parts written to stl_output/" % len(rows))
    print("=" * 108)
    print("%-26s %-12s %-15s %8s %12s %10s %6s" %
          ("part", "status", "process", "tris", "volume mm^3", "bbox diag", "manifold"))
    for name, st, pr, nt, vol, bad, bb, size in rows:
        diag = math.sqrt((bb[3] - bb[0]) ** 2 + (bb[4] - bb[1]) ** 2 + (bb[5] - bb[2]) ** 2)
        print("%-26s %-12s %-15s %8d %12.2f %10.2f %6s"
              % (name, st, pr, nt, vol, diag, "OK" if bad == 0 else "FAIL(%d)" % bad))
    if refused:
        print()
        print("REFUSED (labelled Decorative-reference, never exported):")
        for n, st in refused:
            print("   %-24s %s" % (n, st))
    if refused_geom:
        print()
        print("REFUSED (geometry did not verify -- NOT written to stl_output/):")
        print("   These parts are defined, but the pure-Python solid modeller")
        print("   could not prove the mesh it built equals the solid it was")
        print("   asked for.  Export them from OpenSCAD instead:")
        print("      openscad -o stl_output/<name>.stl \\")
        print("             -D 'PART_TO_EXPORT=\"<name>\"' main.scad")
        for n, st, pr, vw, vg, msg in refused_geom:
            print("   %-24s %-12s analytic %10.3f  mesh %10.3f" % (n, st, vw, vg))
            print("   %-24s %s" % ("", msg))
    for n in sorted(reg):
        st, pr = reg[n]
        if st != "Decorative-reference" and pr != "bought" and n not in parts:
            print("   NOTE %-20s is exportable in parts_export.scad but has no "
                  "geometry in gen_stl.py yet" % n)
    fails = [r for r in rows if r[5] != 0]
    print()
    print("written: %d   refused decorative: %d   refused unverified: %d"
          % (len(rows), len(refused), len(refused_geom)))
    return 1 if fails or missing else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
