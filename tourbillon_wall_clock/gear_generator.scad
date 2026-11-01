// ===========================================================================
//  gear_generator.scad  --  real tooth profiles for OpenSCAD.
//
//  NOTHING IN THIS FILE DRAWS RECTANGLES IN A CIRCLE.  Two conjugate systems
//  are implemented, and tools/design.py declares which one every wheel uses:
//
//   1. INVOLUTE   (gear_involute_2d)  -- used wherever z >= z_min, where
//      z_min = 2 / sin^2(alpha) = 17.099 at alpha = 20 deg.
//        flank : involute of the base circle   r_b = r cos(alpha)
//        tip   : addendum circle               r_a = r + m
//        root  : dedendum circle               r_f = r - 1.25 m
//        thickness : half the circular pitch at the pitch circle MINUS half the
//                    declared backlash, so the assembled mesh actually has the
//                    backlash that was asked for.
//
//   2. CYCLOIDAL (gear_cycloidal_2d)  -- used for every pinion with z < 17.099
//      (z = 8, 10, 12 in this train).  An involute tooth at those counts is
//      undercut into a knife edge, so the flanks are generated the classical
//      watchmaking way, with a describing circle of radius r/2:
//        dedendum flank : hypocycloid, which for rr = r/2 degenerates exactly
//                         to a STRAIGHT RADIAL LINE (the Lane radial-flank
//                         system, standard for watch pinion leaves).
//        addendum face  : epicycloid on the same describing circle.
//      calc.py check C-10 asserts that the declared system and the tooth count
//      agree, and tools/profile_check.py re-derives both profiles in Python
//      and measures tip thickness and tooth-space width.
//
//  Both generators are 2-D so that every wheel in the project shares one code
//  path; the 3-D wrappers extrude them and add rim, web, spokes, hub and bore.
// ===========================================================================

include <parameters.scad>

// ---------------------------------------------------------------------------
// 1.  DERIVED TOOTH GEOMETRY  (pure functions -- also used by the validators)
// ---------------------------------------------------------------------------

function pitch_r(m, z)       = m * z / 2;
function base_r(m, z, a=GEAR_PRESSURE_ANGLE) = pitch_r(m, z) * cos(a);
function tip_r(m, z)         = pitch_r(m, z) + m;
function root_r(m, z)        = pitch_r(m, z) - 1.25 * m;
function z_min_involute(a=GEAR_PRESSURE_ANGLE) = 2 / pow(sin(a), 2);
function circular_pitch(m)   = PI * m;
function tooth_thick(m, bl)  = circular_pitch(m) / 2 - bl / 2;

// involute function inv(x) = tan(x) - x, argument in DEGREES
function invol(a_deg) = tan(a_deg) - a_deg * PI / 180;

// pressure angle of the involute at radius rr
function alpha_at(rb, rr) = acos(min(1, rb / max(rr, rb)));

// HALF angular thickness of an involute tooth at radius rr, in DEGREES.
//   phi(r_r) = s/(2 r) + inv(alpha) - inv(alpha_r)
// where inv(x) = tan(x) - x is the involute function and returns RADIANS, so
// every term is converted to degrees before being added.  (OpenSCAD's acos and
// tan both take and return degrees, hence the explicit PI/180 factors.)
function half_angle_involute(m, z, bl, rr) =
    let (r     = pitch_r(m, z),
         rb    = base_r(m, z),
         a_r   = alpha_at(rb, max(rr, rb)),                    // degrees
         phi_r = (tooth_thick(m, bl) / 2) / r * 180 / PI,      // degrees
         dphi  = (invol(GEAR_PRESSURE_ANGLE) - invol(a_r)) * 180 / PI)
      max(0.0005, phi_r + dphi);

// tip thickness of an involute tooth, as an ARC LENGTH (mm) -- this is what
// check C-09 tests against 0.25 m so that no tooth comes out pointed.
function tip_thickness(m, z, bl) =
    2 * half_angle_involute(m, z, bl, tip_r(m, z)) * PI / 180 * tip_r(m, z);

// half angular thickness of a CYCLOIDAL tooth.  The flank is radial, so the
// half angle is constant from root to pitch circle and then grows by the
// epicycloid flare cyclo_flare_deg() up to the tip.
function half_angle_cycloidal_pitch(m, z, bl) =
    let (r = pitch_r(m, z)) (tooth_thick(m, bl) / 2) / r * 180 / PI;

// polar angle reached by the addendum epicycloid, measured from its own
// starting point on the pitch circle.  Rolling circle rr = r/2 gives
//   R(t) = r * sqrt(2.5 - 1.5 cos 2t),   theta(t) = atan2(1.5 sin t - 0.5 sin 3t,
//                                                         1.5 cos t - 0.5 cos 3t)
// and t_max is where R(t) = r + m.
function cyclo_t_max(m, z) =
    let (c = pow(1 + m / pitch_r(m, z), 2))
      acos(max(-1, min(1, (2.5 - c) / 1.5))) / 2;

function cyclo_flare_deg(m, z) =
    let (t = cyclo_t_max(m, z))
      atan2(1.5 * sin(t) - 0.5 * sin(3 * t), 1.5 * cos(t) - 0.5 * cos(3 * t)) * 180 / PI;

function tip_thickness_cycloidal(m, z, bl) =
    let (a = half_angle_cycloidal_pitch(m, z, bl) + cyclo_flare_deg(m, z))
      2 * a * PI / 180 * tip_r(m, z);

// ---------------------------------------------------------------------------
// 2.  INVOLUTE TOOTH OUTLINE
// Vertex order matters: the loop must run root(-) -> tip(-) -> tip(+) -> root(+)
// so that the tip land is a real edge and the polygon is simple.  Below the base
// circle the involute does not exist, so the flank is closed off with a short
// RADIAL segment down to the root circle.
module involute_tooth_poly(m, z, bl, n=14) {
    rf   = root_r(m, z);
    ra   = tip_r(m, z);
    rb   = base_r(m, z);
    r0   = max(rf, rb);
    a_r0 = half_angle_involute(m, z, bl, r0);
    flank_neg = [for (i = [0:n-1])
        let (rr = r0 + (ra - r0) * i / (n - 1),
             a  = half_angle_involute(m, z, bl, rr)) [rr * cos(a), -rr * sin(a)]];
    flank_pos = [for (i = [0:n-1])
        let (rr = r0 + (ra - r0) * (n - 1 - i) / (n - 1),
             a  = half_angle_involute(m, z, bl, rr)) [rr * cos(a), rr * sin(a)]];
    polygon(concat([ [rf * cos(a_r0), -rf * sin(a_r0)] ],
                   flank_neg, flank_pos,
                   [ [rf * cos(a_r0),  rf * sin(a_r0)] ]));
}

module gear_involute_2d(m, z, bl=GEAR_BACKLASH, bore=0, n=14) {
    rf = root_r(m, z);
    difference() {
        union() {
            circle(r = rf);
            for (i = [0 : z-1]) rotate(i * 360 / z) involute_tooth_poly(m, z, bl, n);
        }
        if (bore > 0) circle(d = bore);
    }
}

// ---------------------------------------------------------------------------
// 3.  CYCLOIDAL TOOTH OUTLINE  --  THE SYSTEM THIS TRAIN ACTUALLY USES
//
//     Conjugacy rule, and the reason this file is written the way it is:
//     a cycloidal pinion is ONLY conjugate with a cycloidal wheel generated by
//     the SAME describing circle.  Mixing an involute wheel with a cycloidal
//     pinion gives non-conjugate action and a variable velocity ratio, so
//     EVERY mesh in this movement declares one describing circle shared by
//     both of its members:
//
//         describing-circle diameter = half the PINION's pitch diameter
//         rr = m * z_pinion / 4          (exported as CYCLO_RR_<mesh>)
//
//     For the pinion that makes rr = r/2 exactly, and its dedendum hypocycloid
//     degenerates to a STRAIGHT RADIAL LINE -- the classical watchmaking
//     radial-flank pinion leaf.  The mating wheel uses the same rr, so its
//     flank is a true curved hypocycloid and its face a true epicycloid.
//
//     Closed forms (t in degrees, OpenSCAD trig is degree-based):
//       epicycloid  (face, rolling OUTSIDE r)
//           P(t) = [ (r+rr) cos t - rr cos((r+rr)t/rr),
//                    (r+rr) sin t - rr sin((r+rr)t/rr) ]
//           |P|^2 = (r+rr)^2 + rr^2 - 2 (r+rr) rr cos(t r / rr)
//       hypocycloid (flank, rolling INSIDE r)
//           P(t) = [ (r-rr) cos t + rr cos((r-rr)t/rr),
//                    (r-rr) sin t - rr sin((r-rr)t/rr) ]
//           |P|^2 = (r-rr)^2 + rr^2 + 2 (r-rr) rr cos(t r / rr)
//     Both pass exactly through (r, 0) at t = 0, i.e. through the pitch point.
//     tools/profile_check.py re-derives these same polygons in Python and
//     sweeps the meshes to prove zero tooth collisions.
// ---------------------------------------------------------------------------

function cyclo_face_t_max(r, m, rr) =
    acos(min(1, max(-1, ((r + rr) * (r + rr) + rr * rr - (r + m) * (r + m))
                        / (2 * (r + rr) * rr)))) * rr / r;

function cyclo_flank_t_max(r, m, rr) =
    rr >= r / 2 - 1e-12
      ? acos(min(1, max(-1, (r - 1.25 * m) / r)))                       // radial
      : acos(min(1, max(-1, ((r - 1.25 * m) * (r - 1.25 * m)
                             - (r - rr) * (r - rr) - rr * rr)
                            / (2 * (r - rr) * rr)))) * rr / r;

function cyclo_epi(r, rr, t)  = [ (r + rr) * cos(t) - rr * cos((r + rr) / rr * t),
                                  (r + rr) * sin(t) - rr * sin((r + rr) / rr * t) ];
function cyclo_hypo(r, rr, t) = [ (r - rr) * cos(t) + rr * cos((r - rr) / rr * t),
                                  (r - rr) * sin(t) - rr * sin((r - rr) / rr * t) ];

// half tooth thickness as an ANGLE at the pitch circle (deg); the same for both
// systems, because the thickness is fixed by the circular pitch less backlash.
function half_angle_at_pitch(m, z, bl) =
    let (r = pitch_r(m, z)) (tooth_thick(m, bl) / 2) / r * 180 / PI;

// One cycloidal tooth, apex on +X, as a closed loop:
//   root(-phi) -> flank -> pitch(-phi) -> face -> tip land -> face ->
//   pitch(+phi) -> flank -> root(+phi)
module cycloidal_tooth_poly(m, z, rr, bl, n=12) {
    r      = pitch_r(m, z);
    rf     = max(root_r(m, z), 0.35 * r);
    phi    = half_angle_at_pitch(m, z, bl);
    radial = rr >= r / 2 - 1e-12;
    tf     = cyclo_face_t_max(r, m, rr);
    th     = cyclo_flank_t_max(r, m, rr);

    function rot(p, a) = [p[0]*cos(a) - p[1]*sin(a), p[0]*sin(a) + p[1]*cos(a)];

    face_neg = [for (i = [0:n]) rot(cyclo_epi(r, rr, tf * i / n), -phi)];
    face_pos = [for (i = [0:n]) [face_neg[n - i][0], -face_neg[n - i][1]]];

    // hypocycloid sampled on the -phi side, then reversed for the outbound run
    // and mirrored about +X for the return run -- exactly what
    // gearmath.cycloidal_tooth_poly() does.
    hypo = [for (i = [0:n]) rot(cyclo_hypo(r, rr, th * i / n), -phi)];
    flank_neg = radial
        ? [ [rf * cos(phi), -rf * sin(phi)], [r * cos(phi), -r * sin(phi)] ]
        : [for (i = [n:-1:0]) hypo[i]];
    flank_pos = radial
        ? [ [r * cos(phi), r * sin(phi)], [rf * cos(phi), rf * sin(phi)] ]
        : [for (i = [0:n]) [hypo[i][0], -hypo[i][1]]];

    polygon(concat(flank_neg, face_neg, face_pos, flank_pos));
}

module gear_cycloidal_2d(m, z, rr, bl=GEAR_BACKLASH, bore=0, n=12) {
    rf = max(root_r(m, z), 0.35 * pitch_r(m, z));
    difference() {
        union() {
            circle(r = rf);
            for (i = [0 : z-1]) rotate(i * 360 / z) cycloidal_tooth_poly(m, z, rr, bl, n);
        }
        if (bore > 0) circle(d = bore);
    }
}

// tip thickness of a cycloidal tooth, as an arc length (mm), measured from the
// generated profile rather than from a formula: the face is an epicycloid, so
// its polar angle at the tip is read straight off the curve.
function tip_thickness_cycloidal(m, z, rr, bl) =
    let (r   = pitch_r(m, z),
         phi = half_angle_at_pitch(m, z, bl),
         tf  = cyclo_face_t_max(r, m, rr),
         p   = cyclo_epi(r, rr, tf),
         flare = atan2(p[1], p[0]))
      2 * (phi - flare) * PI / 180 * tip_r(m, z);

// ---------------------------------------------------------------------------
// 4.  DISPATCH
// ---------------------------------------------------------------------------
// rr is REQUIRED for a cycloidal wheel: it is the describing circle of the
// MESH, not a property of the wheel alone.  Passing it explicitly makes it
// impossible to draw a pinion that is not conjugate with its wheel.
module gear_2d(m, z, bl=GEAR_BACKLASH, bore=0, system="cycloidal", rr=0, n=14) {
    if (system == "involute") gear_involute_2d(m, z, bl, bore, n);
    else {
        assert(rr > 0, "gear_2d: a cycloidal wheel needs the describing circle rr of its mesh");
        gear_cycloidal_2d(m, z, rr, bl, bore, n);
    }
}

// Every mesh of this movement is cycloidal, because every mesh contains a
// pinion below the involute undercut limit z_min = 17.10 at 20 deg.  The
// describing circle of a mesh is shared by BOTH of its members and equals
// m * z_pinion / 4 (describing-circle DIAMETER = half the pinion's pitch
// diameter).  gearmath.mesh_describing_r() computes the same value and calc.py
// exports it as CYCLO_RR_*; this function exists so a caller can derive it from
// the tooth counts instead of looking up a constant, and scad_lint.py checks
// that the two agree.
function mesh_rr(m, z1, z2) = m * min(z1, z2) / 4;

// ---------------------------------------------------------------------------
// 5.  3-D WHEEL  --  toothed rim + web/spokes + hub + bore
// ---------------------------------------------------------------------------
module gear_3d(m, z, thk, hub_d, hub_h, bore_d, rr, spokes=0, spoke_w=2.0,
               z0=0, system="cycloidal", bl=GEAR_BACKLASH,
               lightening=0.0, show_teeth=SHOW_GEAR_TEETH, n=14) {
    r_tip = tip_r(m, z);
    r_rim = max(hub_d / 2 + 1.0, r_tip * 0.74);
    render() union() {
        translate([0, 0, z0])
            linear_extrude(height = thk, convexity = 14)
                if (show_teeth)
                    gear_2d(m, z, bl, bore_d, system, rr, n);
                else
                    difference() {
                        circle(r = pitch_r(m, z));
                        if (bore_d > 0) circle(d = bore_d);
                    }

        if (spokes > 0)
            translate([0, 0, z0])
                linear_extrude(height = thk, convexity = 12)
                    difference() {
                        union() {
                            circle(r = r_rim);
                            circle(d = hub_d);
                            for (i = [0 : spokes-1]) rotate(i * 360 / spokes)
                                hull() {
                                    translate([hub_d/2 - EPS, -spoke_w/2]) square([EPS, spoke_w]);
                                    translate([r_rim  - EPS, -spoke_w/2]) square([EPS, spoke_w]);
                                }
                        }
                        for (i = [0 : spokes-1]) rotate((i + 0.5) * 360 / spokes)
                            translate([(hub_d/2 + r_rim) / 2, 0])
                                scale([(1 - lightening * 0.45), 1])
                                    circle(r = (r_rim - hub_d/2 - 2.0) / 2);
                        if (bore_d > 0) circle(d = bore_d);
                    }

        if (hub_h > thk + EPS) translate([0, 0, z0]) tube(od = hub_d, id = bore_d, h = hub_h);
    }
}

// ---------------------------------------------------------------------------
// 6.  3-D PINION  --  a watch pinion is cut from the arbor blank, so the arbor
//     IS the hub and runs the full height.
// ---------------------------------------------------------------------------
module pinion_3d(m, z, thk, arbor_d, total_h, rr, z_tooth=0, bl=GEAR_BACKLASH,
                 show_teeth=SHOW_GEAR_TEETH, n=12) {
    union() {
        cylinder(d = arbor_d, h = total_h);
        translate([0, 0, z_tooth])
            linear_extrude(height = thk, convexity = 14)
                if (show_teeth) gear_cycloidal_2d(m, z, rr, bl, 0, n);
                else            circle(r = pitch_r(m, z));
    }
}

// ---------------------------------------------------------------------------
// 7.  ESCAPE WHEEL  --  15-tooth Swiss CLUB tooth.
//     Not involute, not cycloidal, and NOT decorative: this is the standard
//     club construction.
//
//       r_root  root circle (valley between teeth)
//       r_tip   tip circle
//       The club is: a rising flank, an IMPULSE face inclined to the radius, a
//       short flat club face at the tip, and a LOCKING face inclined back to
//       the root with a sharp inner corner that the pallet stone locks against.
//
//     MANUFACTURABILITY: the impulse and locking faces need Ra < 0.2 um and
//     > 60 HRC or the lever will not unlock consistently.  This module gives
//     correct GEOMETRY; the part must be wire-EDM or laser cut from hardened
//     1.4034 and lapped.  It cannot be 3-D printed.
// ---------------------------------------------------------------------------
module escape_wheel_2d(z=Z_ESCAPE_WHEEL, r_tip=ESCAPE_WHEEL_OD / 2,
                       r_root=ESCAPE_WHEEL_OD / 2 - 2.6, bore=0) {
    pitch = 360 / z;
    difference() {
        union() {
            circle(r = r_root);
            for (i = [0 : z-1]) rotate(i * pitch) polygon([
                [ r_root * cos(-pitch/2 + 0.8),          r_root * sin(-pitch/2 + 0.8) ],
                [ r_root * cos(-2.4),                    r_root * sin(-2.4) ],
                [ (r_tip - 1.15) * cos(-0.9),            (r_tip - 1.15) * sin(-0.9) ],
                [  r_tip * cos(0.9),                     r_tip * sin(0.9) ],
                [  r_tip * cos(pitch * 0.30),            r_tip * sin(pitch * 0.30) ],
                [ r_root * cos(pitch/2 - 0.8),           r_root * sin(pitch/2 - 0.8) ]
            ]);
        }
        if (bore > 0) circle(d = bore);
    }
}

module escape_wheel_3d(thk, hub_d, bore_d, z0=0) {
    render() union() {
        translate([0, 0, z0])
            linear_extrude(height = thk, convexity = 14)
                if (SHOW_GEAR_TEETH) escape_wheel_2d(bore = bore_d);
                else difference() { circle(r = ESCAPE_WHEEL_OD/2 - 1.0); circle(d = bore_d); }
        translate([0, 0, z0]) tube(od = hub_d, id = bore_d, h = thk);
    }
}

// ---------------------------------------------------------------------------
// 8.  FIXED FOURTH WHEEL  --  an ordinary involute wheel; what makes it
//     special is that it does NOT rotate.  It is bolted to the main plate on a
//     stub arbor and the escape pinion rolls around it as the carriage turns.
// ---------------------------------------------------------------------------
module fixed_fourth_2d(bl=GEAR_BACKLASH) {
    gear_cycloidal_2d(M_FIXED_FOURTH, Z_FIXED_FOURTH, CYCLO_RR_EPICYCLIC, bl,
                      bore = FIXED_4TH_BOSS_D + FIT_CLEARANCE);
}

// ---------------------------------------------------------------------------
// 9.  RATCHET  --  saw-tooth winding wheel (asymmetric so the click holds)
// ---------------------------------------------------------------------------
module ratchet_wheel_2d(z=Z_RATCHET, m=M_RATCHET, bore=0) {
    r = pitch_r(m, z); ra = r + m; rf = r - 1.25 * m;
    difference() {
        union() {
            circle(r = rf);
            for (i = [0 : z-1]) rotate(i * 360 / z) polygon([
                [rf, -1.05 * m], [ra, -0.30 * m], [ra, 0.30 * m], [rf, 1.05 * m]
            ]);
        }
        if (bore > 0) circle(d = bore);
    }
}

// ---------------------------------------------------------------------------
// 10. SELF-TEST.  Run:  openscad -o /dev/null -D '_SELFTEST=true;' gear_generator.scad
//     (or tools/scad_lint.py, which parses the same numbers out of this file).
// ---------------------------------------------------------------------------
_SELFTEST = false;

module _selftest() {
    echo("involute undercut limit z_min at 20 deg =", z_min_involute());
    echo("NOTE: every mesh of this train is CYCLOIDAL because every mesh");
    echo("      contains a pinion with z < z_min.  Both members of a mesh");
    echo("      share ONE describing circle rr = m * z_pinion / 4.");
    for (row = [["barrel gear / great wheel",   M_BARREL_GEAR,   Z_BARREL_GEAR,   Z_GREAT_WHEEL],
                ["great pinion / centre wheel", M_GREAT_PINION,  Z_GREAT_PINION,  Z_CENTRE_WHEEL],
                ["centre pinion / inter wheel", M_CENTRE_PINION, Z_CENTRE_PINION, Z_INTER_WHEEL],
                ["inter pinion / carriage rim", M_INTER_PINION,  Z_INTER_PINION,  Z_CARRIAGE_RIM],
                ["fixed fourth / escape pinion",M_FIXED_FOURTH,  Z_ESCAPE_PINION, Z_FIXED_FOURTH],
                ["canon pinion / minute wheel", M_CANON_PINION,  Z_CANON_PINION,  Z_MINUTE_WHEEL],
                ["minute pinion / hour wheel",  M_MINUTE_PINION, Z_MINUTE_PINION, Z_HOUR_WHEEL]])
        echo(row[0], "  m=", row[1], " z_pinion=", row[2], " z_wheel=", row[3],
             "  rr=", mesh_rr(row[1], row[2], row[3]),
             "  pinion s_tip=", tip_thickness_cycloidal(row[1], row[2], mesh_rr(row[1], row[2], row[3]), GEAR_BACKLASH),
             "  wheel  s_tip=", tip_thickness_cycloidal(row[1], row[3], mesh_rr(row[1], row[2], row[3]), GEAR_BACKLASH));
}

if (_SELFTEST) _selftest();
