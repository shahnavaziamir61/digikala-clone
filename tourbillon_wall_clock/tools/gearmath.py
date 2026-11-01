#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gearmath.py -- pure involute / cycloidal spur-gear geometry.

Standard relations used (see docs/CALCULATIONS.md for the derivations):

    pitch diameter          d   = m * z
    base diameter           db  = d * cos(alpha)
    addendum                ha  = m              (full-depth, ha* = 1)
    dedendum                hf  = 1.25 m         (c* = 0.25 bottom clearance)
    outside diameter        da  = d + 2 ha
    root diameter           df  = d - 2 hf
    centre distance (ext.)  a   = m (z1 + z2) / 2
    centre distance (int.)  a   = m (zRing - zPinion) / 2
    speed ratio             i   = z2 / z1         (driven / driver)
    circular tooth thickness s  = pi m / 2 + 2 x m tan(alpha) - backlash/2
    tip thickness           sa  = da ( s/d + inv(alpha_a) - inv(alpha) )
    involute function       inv(a) = tan(a) - a
    contact ratio           eps = ( sqrt(ra1^2-rb1^2) + sqrt(ra2^2-rb2^2)
                                    - a sin(alpha) ) / ( pi m cos(alpha) )
    undercut limit          zmin = 2 ha* / sin^2(alpha)

Units: millimetre, degree.
"""

import math

HA_COEFF = 1.0          # addendum coefficient ha*
C_COEFF = 0.25          # bottom clearance coefficient c*


def inv(a_rad):
    """Involute function inv(alpha) = tan(alpha) - alpha."""
    return math.tan(a_rad) - a_rad


def pitch_d(m, z):
    return m * z


def base_d(m, z, pa_deg):
    return m * z * math.cos(math.radians(pa_deg))


def outside_d(m, z, internal=False, x=0.0):
    d = m * z + 2.0 * x * m
    return d - 2.0 * HA_COEFF * m if internal else d + 2.0 * HA_COEFF * m


def root_d(m, z, internal=False, x=0.0):
    d = m * z + 2.0 * x * m
    return d + 2.0 * (HA_COEFF + C_COEFF) * m if internal else d - 2.0 * (HA_COEFF + C_COEFF) * m


def blank_d(m, z, internal=False, rim_allowance=0.0):
    """Physical blank diameter used for collision checks."""
    if internal:
        return m * z + 2.0 * (HA_COEFF + rim_allowance)
    return outside_d(m, z, internal=False) + rim_allowance


def centre_distance(m, z1, z2, x1=0.0, x2=0.0, internal=False):
    if internal:
        return 0.5 * m * (abs(z1 - z2) + 2.0 * (x1 - x2))
    return 0.5 * m * (z1 + z2 + 2.0 * (x1 + x2))


def min_teeth_undercut(pa_deg, ha=HA_COEFF):
    s = math.sin(math.radians(pa_deg))
    return 2.0 * ha / (s * s)


def tooth_thickness_pitch(m, pa_deg, backlash, x=0.0):
    return (math.pi * m / 2.0
            + 2.0 * x * m * math.tan(math.radians(pa_deg))
            - backlash / 2.0)


def tip_thickness(m, z, pa_deg, backlash, x=0.0):
    d = m * z + 2.0 * x * m
    db = base_d(m, z, pa_deg)
    da = d + 2.0 * HA_COEFF * m
    if da <= db or d <= 0:
        return 0.0
    s = tooth_thickness_pitch(m, pa_deg, backlash, x)
    alpha = math.radians(pa_deg)
    alpha_a = math.acos(min(1.0, db / da))
    return da * (s / d + inv(alpha_a) - inv(alpha))


def contact_ratio_external(m, z1, z2, pa_deg, a=None):
    alpha = math.radians(pa_deg)
    d1, d2 = pitch_d(m, z1), pitch_d(m, z2)
    rb1, rb2 = 0.5 * d1 * math.cos(alpha), 0.5 * d2 * math.cos(alpha)
    ra1, ra2 = 0.5 * d1 + HA_COEFF * m, 0.5 * d2 + HA_COEFF * m
    if a is None:
        a = centre_distance(m, z1, z2)
    t1 = ra1 ** 2 - rb1 ** 2
    t2 = ra2 ** 2 - rb2 ** 2
    if t1 < 0 or t2 < 0:
        return 0.0
    return (math.sqrt(t1) + math.sqrt(t2) - a * math.sin(alpha)) / (math.pi * m * math.cos(alpha))


def contact_ratio_internal(m, z_ring, z_pin, pa_deg, a=None):
    """Ring (internal) gear meshing with an external pinion."""
    alpha = math.radians(pa_deg)
    d_r, d_p = pitch_d(m, z_ring), pitch_d(m, z_pin)
    rb_r, rb_p = 0.5 * d_r * math.cos(alpha), 0.5 * d_p * math.cos(alpha)
    ra_p = 0.5 * d_p + HA_COEFF * m           # pinion tip (outside)
    rf_r = 0.5 * d_r + HA_COEFF * m           # ring tip points INWARD -> larger radius
    if a is None:
        a = centre_distance(m, z_ring, z_pin, internal=True)
    t1 = rf_r ** 2 - rb_r ** 2
    t2 = ra_p ** 2 - rb_p ** 2
    if t1 < 0 or t2 < 0:
        return 0.0
    return (math.sqrt(t1) - math.sqrt(t2) + a * math.sin(alpha)) / (math.pi * m * math.cos(alpha))


# cycloidal_contact_estimate() was removed.  It returned a hard-coded 1.30 and
# was reported as "not computed", which is exactly the kind of unproven number
# this project is not allowed to contain.  cycloidal_contact_ratio() below
# measures eps from the generated tooth profiles instead.


def undercut_needed_shift(m, z, pa_deg):
    """Minimum positive profile shift x that removes undercut for z < zmin."""
    zmin = min_teeth_undercut(pa_deg)
    if z >= zmin:
        return 0.0
    return (zmin - z) / zmin * HA_COEFF


def profile_choice(z, pa_deg):
    """Per-wheel indication only.  NOT sufficient on its own: a cycloidal
    pinion is conjugate ONLY with a cycloidal wheel sharing the same describing
    circle, so the decision that matters is per MESH -- see mesh_profile()."""
    return "involute" if z >= min_teeth_undercut(pa_deg) else "cycloidal"


def mesh_profile(z1, z2, pa_deg):
    """Tooth system of a MESH.  If either member is below the involute undercut
    limit, BOTH members are made cycloidal with one shared describing circle of
    diameter m*z_pinion/2.  This is why every mesh in this movement is
    cycloidal: every one of them contains a pinion with z <= 16 < 17.10."""
    if min(z1, z2) < min_teeth_undercut(pa_deg):
        return "cycloidal"
    return "involute"


def mesh_describing_r(m, z1, z2):
    """Describing-circle radius shared by both members of a cycloidal mesh."""
    return cyclo_describing_r(m, min(z1, z2))


def mesh_record(driver, driven, z1, z2, m, pa_deg=20.0, backlash=0.08,
                internal=False, x1=0.0, x2=0.0, level="", note=""):
    """Full mesh record -- every column requested in section 5 of the brief.

    The tooth system is a property of the MESH, not of either wheel: if one
    member is below the involute undercut limit, both are generated cycloidally
    from ONE shared describing circle, otherwise the two profiles are not
    conjugate and the velocity ratio would not be constant.
    """
    a = centre_distance(m, z1, z2, x1, x2, internal)
    system = "involute" if internal else mesh_profile(z1, z2, pa_deg)
    rr = mesh_describing_r(m, z1, z2) if system == "cycloidal" else 0.0
    p1 = p2 = system if not internal else (system, "involute-ring")
    if internal:
        p1, p2 = system, "involute-ring"
    if system == "involute":
        eps = (contact_ratio_internal(m, z1, z2, pa_deg, a) if internal
               else contact_ratio_external(m, z1, z2, pa_deg, a))
        eps_source = "computed (involute, closed form)"
    else:
        eps = cycloidal_contact_ratio(m, z1, z2, rr, 0.0)
        eps_source = ("computed numerically from the generated cycloidal "
                      "profiles (shared describing circle rr = %.4f mm)" % rr)

    zmin = min_teeth_undercut(pa_deg)
    return dict(
        driver=driver, driven=driven,
        z_driver=z1, z_driven=z2,
        module=m, pressure_angle=pa_deg,
        mesh_type="internal" if internal else "external",
        tooth_system=system, describing_circle_r=round(rr, 4),
        profile_driver=p1, profile_driven=p2,
        d_driver=round(pitch_d(m, z1), 4), d_driven=round(pitch_d(m, z2), 4),
        db_driver=round(base_d(m, z1, pa_deg), 4),
        db_driven=round(base_d(m, z2, pa_deg), 4),
        da_driver=round(outside_d(m, z1, internal and False, x1), 4),
        da_driven=round(outside_d(m, z2, internal, x2), 4),
        df_driver=round(root_d(m, z1, False, x1), 4),
        df_driven=round(root_d(m, z2, internal, x2), 4),
        centre_distance=round(a, 4),
        ratio=round(z2 / z1, 6),
        contact_ratio=round(eps, 3), contact_ratio_source=eps_source,
        tooth_thickness_pitch=round(tooth_thickness_pitch(m, pa_deg, backlash, x1), 4),
        backlash=backlash,
        undercut_driver=bool(z1 < zmin and system != "cycloidal"),
        undercut_driven=bool(z2 < zmin and system != "cycloidal"),
        tip_thickness_driver=round(
            tip_thickness(m, z1, pa_deg, backlash, x1) if system == "involute"
            else cycloidal_tip_thickness(m, z1, rr, backlash), 4),
        tip_thickness_driven=round(
            tip_thickness(m, z2, pa_deg, backlash, x2) if system == "involute"
            else cycloidal_tip_thickness(m, z2, rr, backlash), 4),
        z_min_undercut=round(zmin, 2),
        level=level, note=note,
    )


# ---------------------------------------------------------------------------
# 2-D polygon / circle helpers used by the layout collision checker
# ---------------------------------------------------------------------------

def circles_overlap(c1, r1, c2, r2, margin=0.0):
    return math.hypot(c1[0] - c2[0], c1[1] - c2[1]) < (r1 + r2 - margin)


def point_in_circle(p, c, r):
    return math.hypot(p[0] - c[0], p[1] - c[1]) <= r


# ===========================================================================
# CYCLOIDAL TOOTH GEOMETRY
#
# This is the system the whole train actually uses, and the reason is a
# conjugacy requirement, not taste: a cycloidal pinion is ONLY conjugate with a
# cycloidal wheel generated by the SAME describing circle.  Mixing an involute
# wheel with a cycloidal pinion produces non-conjugate action and variable
# velocity ratio.  Every mesh in this movement therefore declares one
# describing circle, shared by both members:
#
#     describing-circle diameter = half the PINION's pitch diameter
#     =>  rr = m * z_pinion / 4
#
# With that choice rr = r_pinion / 2 exactly, and the pinion's dedendum flank
# (a hypocycloid) degenerates to a STRAIGHT RADIAL LINE -- the classical
# watchmaking "radial flank" / Lane pinion leaf.  The mating wheel uses the
# same rr, so its flank is a true curved hypocycloid and its face a true
# epicycloid.
#
# Closed forms used below, with A = r +/- rr and k = A / rr:
#   epicycloid  (face,  rolling OUTSIDE r):
#       P(t) = ((r+rr) cos t - rr cos((r+rr)t/rr),
#               (r+rr) sin t - rr sin((r+rr)t/rr))
#       |P|^2 = (r+rr)^2 + rr^2 - 2 (r+rr) rr cos(t r / rr)
#   hypocycloid (flank, rolling INSIDE r):
#       P(t) = ((r-rr) cos t + rr cos((r-rr)t/rr),
#               (r-rr) sin t - rr sin((r-rr)t/rr))
#       |P|^2 = (r-rr)^2 + rr^2 + 2 (r-rr) rr cos(t r / rr)
# Both start at (r, 0) when t = 0, i.e. exactly on the pitch circle.
# ===========================================================================

def cyclo_describing_r(m, z_pinion):
    """Radius of the describing circle shared by both members of a mesh."""
    return pitch_d(m, z_pinion) / 4.0


def cyclo_face_t_max(r, m, rr):
    """Rolling angle (deg) at which the addendum epicycloid reaches r + m."""
    c = ((r + rr) ** 2 + rr ** 2 - (r + m) ** 2) / (2.0 * (r + rr) * rr)
    return math.degrees(math.acos(max(-1.0, min(1.0, c)))) * rr / r


def cyclo_flank_t_max(r, m, rr):
    """Rolling angle (deg) at which the dedendum hypocycloid reaches r - 1.25m.
    For rr == r/2 the hypocycloid is a straight radial line and |P| = r cos t."""
    rf = r - 1.25 * m
    if rr >= r / 2.0 - 1e-12:
        return math.degrees(math.acos(max(-1.0, min(1.0, rf / r))))
    c = (rf ** 2 - (r - rr) ** 2 - rr ** 2) / (2.0 * (r - rr) * rr)
    return math.degrees(math.acos(max(-1.0, min(1.0, c)))) * rr / r


def cyclo_epi(r, rr, t_deg):
    t = math.radians(t_deg)
    k = (r + rr) / rr
    return ((r + rr) * math.cos(t) - rr * math.cos(k * t),
            (r + rr) * math.sin(t) - rr * math.sin(k * t))


def cyclo_hypo(r, rr, t_deg):
    t = math.radians(t_deg)
    k = (r - rr) / rr
    return ((r - rr) * math.cos(t) + rr * math.cos(k * t),
            (r - rr) * math.sin(t) - rr * math.sin(k * t))


def rot2(p, deg):
    a = math.radians(deg)
    return (p[0] * math.cos(a) - p[1] * math.sin(a),
            p[0] * math.sin(a) + p[1] * math.cos(a))


def half_angle_at_pitch(m, z, bl):
    """Half tooth thickness as an ANGLE at the pitch circle, degrees.
    Identical for both tooth systems: the thickness is set by the circular
    pitch minus the declared backlash."""
    r = pitch_d(m, z) / 2.0
    return math.degrees((tooth_thickness_pitch(m, 20.0, bl) / 2.0) / r)


def cycloidal_tooth_poly(m, z, rr, bl, n=12):
    """One cycloidal tooth, apex on +X, as an OPEN chain
    root(-phi) -> flank -> pitch(-phi) -> face -> tip -> face -> pitch(+phi)
    -> flank -> root(+phi).  Mirrored exactly by gear_generator.scad."""
    r = pitch_d(m, z) / 2.0
    rf = max(r - 1.25 * m, 0.35 * r)
    phi = half_angle_at_pitch(m, z, bl)
    radial = rr >= r / 2.0 - 1e-12

    tf = cyclo_face_t_max(r, m, rr)
    face_neg = [rot2(cyclo_epi(r, rr, tf * i / n), -phi) for i in range(n + 1)]
    face_pos = [(face_neg[n - i][0], -face_neg[n - i][1]) for i in range(n + 1)]

    if radial:
        # hypocycloid degenerates to a straight radial line
        flank_neg = [(rf * math.cos(math.radians(phi)), -rf * math.sin(math.radians(phi))),
                     (r * math.cos(math.radians(phi)), -r * math.sin(math.radians(phi)))]
        flank_pos = [(r * math.cos(math.radians(phi)), r * math.sin(math.radians(phi))),
                     (rf * math.cos(math.radians(phi)), rf * math.sin(math.radians(phi)))]
    else:
        th = cyclo_flank_t_max(r, m, rr)
        h = [rot2(cyclo_hypo(r, rr, th * i / n), -phi) for i in range(n + 1)]
        flank_neg = list(reversed(h))                       # root -> pitch
        flank_pos = [(p[0], -p[1]) for p in h]              # pitch -> root
    return flank_neg + face_neg + face_pos + flank_pos


def cycloidal_tip_thickness(m, z, rr, bl):
    """Tip thickness of a cycloidal tooth, as an ARC LENGTH in mm, read off the
    generated epicycloid rather than from an involute formula.  The face is an
    epicycloid, so its polar angle at the tip circle is measured directly and
    subtracted from the half tooth angle at the pitch circle."""
    r = pitch_d(m, z) / 2.0
    ra = r + m
    phi = half_angle_at_pitch(m, z, bl)
    tf = cyclo_face_t_max(r, m, rr)
    px, py = cyclo_epi(r, rr, tf)
    flare = math.degrees(math.atan2(py, px))
    return 2.0 * math.radians(max(0.0, phi - flare)) * ra


def invol(a_deg):
    return math.tan(math.radians(a_deg)) - math.radians(a_deg)


def alpha_at_radius(rb, rr_):
    return math.degrees(math.acos(max(-1.0, min(1.0, rb / max(rr_, rb)))))


def involute_half_angle(m, z, bl, rr_):
    """Half angular tooth thickness of an involute tooth at radius rr_, degrees.
    phi(r) = s/(2r) + inv(alpha) - inv(alpha_r), all terms converted to degrees."""
    r = pitch_d(m, z) / 2.0
    rb = base_d(m, z, 20.0) / 2.0
    phi_r = math.degrees((tooth_thickness_pitch(m, 20.0, bl) / 2.0) / r)
    a_r = alpha_at_radius(rb, max(rr_, rb))
    return max(0.0005, phi_r + math.degrees(inv(20.0) - inv(a_r)))


def involute_tooth_poly(m, z, bl, n=14):
    """One involute tooth, apex on +X, as an OPEN chain.  Mirrored exactly by
    involute_tooth_poly() in gear_generator.scad."""
    rf = pitch_d(m, z) / 2.0 - 1.25 * m
    ra = pitch_d(m, z) / 2.0 + m
    rb = base_d(m, z, 20.0) / 2.0
    r0 = max(rf, rb)
    a0 = involute_half_angle(m, z, bl, r0)
    neg, pos = [], []
    for i in range(n):
        rr_ = r0 + (ra - r0) * i / (n - 1)
        a = math.radians(involute_half_angle(m, z, bl, rr_))
        neg.append((rr_ * math.cos(a), -rr_ * math.sin(a)))
    for i in range(n):
        rr_ = r0 + (ra - r0) * (n - 1 - i) / (n - 1)
        a = math.radians(involute_half_angle(m, z, bl, rr_))
        pos.append((rr_ * math.cos(a), rr_ * math.sin(a)))
    return ([(rf * math.cos(math.radians(a0)), -rf * math.sin(math.radians(a0)))]
            + neg + pos +
            [(rf * math.cos(math.radians(a0)), rf * math.sin(math.radians(a0)))])


_CONTACT_CACHE = {}


def cycloidal_contact_ratio(m, z1, z2, rr, bl=0.0, n=12, coarse=80, tol=2e-3):
    """NUMERICAL contact ratio of a cycloidal mesh, measured from the actual
    generated tooth profiles rather than assumed.

    Definition used: follow ONE driver tooth.  Rotate the driver through two of
    its own pitches and find the rotation interval over which that tooth stays
    in contact with some tooth of the driven wheel (gap <= tol).  Divide the
    interval by one driver pitch.  eps >= 1 means a new pair takes over before
    the old one lets go, i.e. the train never loses drive.

    Search: a coarse sweep brackets the interval, then each end is refined by
    bisection, which is both faster and more accurate than a fine uniform sweep.
    This replaces the old 'conservative constant 1.30, not computed'.
    """
    key = (round(m, 6), z1, z2, round(rr, 6), round(bl, 6))
    if key in _CONTACT_CACHE:
        return _CONTACT_CACHE[key]

    cd = pitch_d(m, z1) / 2.0 + pitch_d(m, z2) / 2.0
    p1, p2 = 360.0 / z1, 360.0 / z2
    t0 = cycloidal_tooth_poly(m, z1, rr, bl, n)
    phase2 = 180.0 - round(180.0 / p2) * p2 + p2 / 2.0
    # select the driven teeth that actually point back at the driver, i.e.
    # whose direction is within 2.5 pitches of 180 deg (the line of centres).
    # d180() folds an angle into (-180, 180].
    def d180(x):
        return ((x + 180.0) % 360.0) - 180.0
    near = [j for j in range(z2) if abs(d180(phase2 + j * p2 - 180.0)) <= 2.5 * p2]
    base2 = [cycloidal_tooth_poly(m, z2, rr, bl, n) for j in near]
    ang2 = [phase2 + near[k] * p2 for k in range(len(near))]
    ratio = float(z1) / float(z2)

    def gap(theta):
        ca, sa = math.cos(math.radians(theta)), math.sin(math.radians(theta))
        A = [(q[0] * ca - q[1] * sa, q[0] * sa + q[1] * ca) for q in t0]
        best = 1e9
        for k in range(len(base2)):
            th2 = math.radians(ang2[k] - theta * ratio)
            cb, sb = math.cos(th2), math.sin(th2)
            B = [(cd + q[0] * cb - q[1] * sb, q[0] * sb + q[1] * cb) for q in base2[k]]
            for i in range(len(A) - 1):
                for j in range(len(B) - 1):
                    d = _seg_seg_dist(A[i], A[i + 1], B[j], B[j + 1])
                    if d < best:
                        best = d
                        if best <= tol:
                            return best
        return best

    lo, hi = -2.0 * p1, 2.0 * p1
    step = (hi - lo) / coarse
    inside = [lo + step * i for i in range(coarse + 1) if gap(lo + step * i) <= tol]
    if not inside:
        _CONTACT_CACHE[key] = 0.0
        return 0.0

    def refine(a, b, want_inside):
        """move the boundary between a (inside) and b (outside)"""
        for _ in range(34):
            mid = 0.5 * (a + b)
            if (gap(mid) <= tol) == want_inside:
                a = mid
            else:
                b = mid
        return a

    start = refine(inside[0], inside[0] - step, True)
    end = refine(inside[-1], inside[-1] + step, True)
    eps = (end - start) / p1
    _CONTACT_CACHE[key] = eps
    return eps


def _seg_seg_dist(p1, p2, q1, q2):
    """Minimum distance between two segments (0 if they cross)."""
    if _segs_cross(p1, p2, q1, q2):
        return 0.0
    return min(_pt_seg(p1, q1, q2), _pt_seg(p2, q1, q2),
               _pt_seg(q1, p1, p2), _pt_seg(q2, p1, p2))


def _segs_cross(p1, p2, q1, q2):
    def side(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    d1, d2 = side(q1, q2, p1), side(q1, q2, p2)
    d3, d4 = side(p1, p2, q1), side(p1, p2, q2)
    return ((d1 > 0) != (d2 > 0)) and ((d3 > 0) != (d4 > 0))


def _pt_seg(p, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    L2 = vx * vx + vy * vy
    if L2 < 1e-18:
        return math.hypot(p[0] - a[0], p[1] - a[1])
    t = max(0.0, min(1.0, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / L2))
    return math.hypot(p[0] - (a[0] + t * vx), p[1] - (a[1] + t * vy))
