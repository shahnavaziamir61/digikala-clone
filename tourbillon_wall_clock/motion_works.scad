// ===========================================================================
//  motion_works.scad  --  the hand train: canon pinion, minute wheel, minute
//                         pinion, hour wheel, hour pipe and minute pipe.
//
//     centre arbor (1 rev/hour)
//        -> CANON PINION   z=16  m=0.72   friction fit on the centre arbor
//        -> MINUTE WHEEL   z=64  m=0.72   on a stud at (28.8, 0)      i = 4
//           MINUTE PINION  z=16  m=0.90   rigid with the minute wheel
//        -> HOUR WHEEL     z=48  m=0.90   concentric with the centre arbor i = 3
//        total  4 x 3 = 12.000 exactly   (checked by C-07)
//
//  WHY THE TWO MESHES HAVE DIFFERENT MODULES -- this is not sloppiness, it is
//  forced.  The hour wheel has to be concentric with the centre arbor, and the
//  minute wheel and minute pinion share one stud, so BOTH meshes must span the
//  same stud-to-centre distance:
//        m1 (16 + 64) / 2  ==  m2 (16 + 48) / 2
//        m1 * 80           ==  m2 * 64      ->   m1 = 0.8 * m2
//  With one module for the whole motion works the two distances would be 36.0
//  and 28.8 mm and the train would not assemble at all.  calc.py check C-07b
//  asserts the equality so this cannot silently regress.
//
//  The canon pinion is a FRICTION fit on the centre arbor.  That is the
//  standard arrangement and it is functional: it lets the hands be set without
//  back-driving the train.  Its friction torque is NOT calculated here -- it is
//  set during adjustment (docs/ASSEMBLY.md) -- so the fit is declared
//  Prototype and must be tuned on the real part.
// ===========================================================================

include <parameters.scad>
include <gear_generator.scad>

MOTION_STUD_D   = 3.0;      // minute-wheel stud, S-09 in docs/SHAFTS.md
CANON_PIPE_ID   = SHAFT_DIAMETER;        // friction fit on the 4 mm centre arbor
HOUR_PIPE_OD    = 9.0;
MINUTE_PIPE_OD  = 6.0;

// ---------------------------------------------------------------------------
// 1.  CANON PINION  --  z = 10 .. 12, on the centre arbor
// ---------------------------------------------------------------------------
module canon_pinion(show_teeth = SHOW_GEAR_TEETH) {
    thk_p = 2.0;
    color(C_PINION)
    rotate(-ang_centre())
        translate([0, 0, dz(ZR_CANON_PINION)])
            difference() {
                pinion_3d(M_CANON_PINION, Z_CANON_PINION, thk_p,
                          CANON_PIPE_ID + 1.6, thk_p + 16.0,
                          rr = mesh_rr(M_CANON_PINION, Z_CANON_PINION, Z_MINUTE_WHEEL),
                          show_teeth = show_teeth);
                // the friction bore: deliberately left at the nominal arbor
                // diameter, NOT fit(), because the grip comes from the fit
                cylinder(d = CANON_PIPE_ID, h = thk_p + 18 * EPS);
            }
}

// ---------------------------------------------------------------------------
// 2.  MINUTE WHEEL + MINUTE PINION  --  one rigid part on the stud
// ---------------------------------------------------------------------------
module minute_wheel(show_teeth = SHOW_GEAR_TEETH) {
    bore = fit(MOTION_STUD_D);
    color(C_WHEEL)
    translate([POS_MOTION_WORKS[0], POS_MOTION_WORKS[1], 0])
        rotate(-ang_centre() * Z_CANON_PINION / Z_MINUTE_WHEEL)
            gear_3d(M_MINUTE_WHEEL, Z_MINUTE_WHEEL, 2.0,
                    hub_d = hub_od("minute wheel"), hub_h = 3.4, bore_d = bore,
                    rr = mesh_rr(M_CANON_PINION, Z_CANON_PINION, Z_MINUTE_WHEEL),
                    spokes = 4, spoke_w = 2.4, z0 = dz(ZR_MINUTE_WHEEL),
                    system = "cycloidal", lightening = 0.3,
                    show_teeth = show_teeth);
}

module minute_pinion(show_teeth = SHOW_GEAR_TEETH) {
    color(C_PINION)
    translate([POS_MOTION_WORKS[0], POS_MOTION_WORKS[1], 0])
        rotate(-ang_centre() * Z_CANON_PINION / Z_MINUTE_WHEEL)
            translate([0, 0, dz(ZR_MINUTE_PINION)])
                pinion_3d(M_MINUTE_PINION, Z_MINUTE_PINION, 2.0, MOTION_STUD_D,
                          2.6, rr = mesh_rr(M_MINUTE_PINION, Z_MINUTE_PINION,
                                            Z_HOUR_WHEEL),
                          show_teeth = show_teeth);
}

module motion_works_stud() {
    // the stud is pressed into the top bridge and peened over; it does not turn
    color(C_ARBOR)
    translate([POS_MOTION_WORKS[0], POS_MOTION_WORKS[1], ZR_TOP_BRIDGE[0]])
        cylinder(d = MOTION_STUD_D, h = ZR_MINUTE_PINION[1] - ZR_TOP_BRIDGE[0] + 1.0);
}

// ---------------------------------------------------------------------------
// 3.  HOUR WHEEL  --  concentric with the centre arbor, turns on the minute pipe
// ---------------------------------------------------------------------------
module hour_wheel(show_teeth = SHOW_GEAR_TEETH) {
    bore = fit(MINUTE_PIPE_OD);
    color(C_WHEEL)
    rotate(-ang_hour())
        gear_3d(M_HOUR_WHEEL, Z_HOUR_WHEEL, 2.0,
                hub_d = hub_od("hour wheel"), hub_h = 3.4, bore_d = bore,
                rr = mesh_rr(M_MINUTE_PINION, Z_MINUTE_PINION, Z_HOUR_WHEEL),
                spokes = 4, spoke_w = 2.6, z0 = dz(ZR_HOUR_WHEEL),
                system = "cycloidal", lightening = 0.25,
                show_teeth = show_teeth);
}

// ---------------------------------------------------------------------------
// 4.  THE TWO COAXIAL PIPES that carry the hands up through the bridge
//     hour pipe   9 mm, z = 14 .. 29,  turns with the hour wheel
//     minute pipe 6 mm, z = 12 .. 30,  turns with the centre arbor and passes
//                                    THROUGH the hour pipe
//     Both pass through the 13 mm "centre pipes" window in the top bridge,
//     which C-18b sizes against exactly these two members.
// ---------------------------------------------------------------------------
module hour_pipe() {
    color(C_PINION)
    rotate(-ang_hour())
        translate([0, 0, dz(ZR_HOUR_PIPE)])
            difference() {
                cylinder(d = HOUR_PIPE_OD, h = thk(ZR_HOUR_PIPE));
                translate([0, 0, -EPS])
                    cylinder(d = fit(MINUTE_PIPE_OD), h = thk(ZR_HOUR_PIPE) + 2 * EPS);
            }
}

module minute_pipe() {
    color(C_PINION)
    rotate(-ang_centre())
        translate([0, 0, dz(ZR_MINUTE_PIPE)])
            difference() {
                cylinder(d = MINUTE_PIPE_OD, h = thk(ZR_MINUTE_PIPE));
                translate([0, 0, -EPS])
                    cylinder(d = fit(SHAFT_DIAMETER), h = thk(ZR_MINUTE_PIPE) + 2 * EPS);
            }
}

// ---------------------------------------------------------------------------
// 5.  THE WHOLE HAND TRAIN
// ---------------------------------------------------------------------------
module motion_works(show_teeth = SHOW_GEAR_TEETH) {
    canon_pinion(show_teeth);
    minute_wheel(show_teeth);
    minute_pinion(show_teeth);
    motion_works_stud();
    hour_wheel(show_teeth);
    hour_pipe();
    minute_pipe();
}
