// ===========================================================================
//  mainspring_barrel.scad  --  going barrel, mainspring, arbor, ratchet, click
//                              and the winding interface.
//
//  This is a GOING BARREL: the drum itself carries the teeth and rotates on a
//  fixed arbor.  Every number below comes from parameters_auto.scad, which
//  tools/calc.py derives and validates; nothing is invented here.
//
//      spring length      L   = FILL * A / (b * t)        = 1029.0 mm
//      coils in drum      n   = L / (pi (r_out + r_arb))  = 3.165
//      turns to discharge N   = L/(2 pi) (1/r_arb - 1/r_out) = 3.231
//      torque, mean       T   = E I S / 2,  S = 1/r_arb + 1/r_out = 521.64 N-mm
//      bending stress     sigma(r) = E t / (2 r)          = 1400 MPa at r_arb
//      stored energy      E_s = 1/2 E I (1/r_arb^2 - 1/r_out^2) L = 10.589 J
//      run time               N / (barrel turns per day)  = 3.23 days
//
//  THE SPRING ITSELF IS NOT PRINTABLE AND IS NOT DRAWN AS A SOLID.  It is a
//  bought part, wound to the calculated 1029 mm length from 0.42 x 18 mm
//  carbon spring steel (see docs/BOM_BOUGHT.csv).  mainspring_coils() below
//  draws it as a reference ARCHIMEDEAN SPIRAL so the packing can be seen; it
//  is labelled Decorative-reference and is excluded from every STL export.
// ===========================================================================

include <parameters.scad>
include <gear_generator.scad>

// ---------------------------------------------------------------------------
// 1.  BARREL DRUM  --  toothed rim, wall, floor, arbor bore, spring hook slot
// ---------------------------------------------------------------------------
BARREL_R_OUT  = MS_BARREL_INTERNAL_RADIUS_MM;                 // 73.5
BARREL_R_ARB  = MS_ARBOR_RADIUS_MM;                           // 30.0
BARREL_TEETH_R = BARREL_DRUM_OD / 2 + M_BARREL_GEAR;          // tip circle

// The drum runs on the arbor through a bronze bush; the bush journal is what
// the friction model in calc.py scores, so its diameter is a real parameter
// and not a guess: it is the arbor's own diameter.
BARREL_BUSH_D = BARREL_ARBOR_D;

module barrel_drum() {
    z0 = dz(ZR_BARREL_DRUM);                                   // -18.0
    h  = thk(ZR_BARREL_DRUM);                                  // 19.5
    color(C_WHEEL)
    translate([0, 0, z0])
        difference() {
            union() {
                // ---- wall ----
                tube(od = BARREL_DRUM_OD, id = 2 * BARREL_R_OUT, h = h);
                // ---- floor at the front of the drum, carrying the teeth ----
                translate([0, 0, h - thk(ZR_BARREL_GEAR)])
                    linear_extrude(height = thk(ZR_BARREL_GEAR), convexity = 14)
                        if (SHOW_GEAR_TEETH)
                            // the barrel gear is a cycloidal pinion-class wheel:
                            // it shares the describing circle of its own mesh
                            gear_cycloidal_2d(M_BARREL_GEAR, Z_BARREL_GEAR,
                                              CYCLO_RR_BARREL_GREAT, GEAR_BACKLASH,
                                              bore = fit(BARREL_ARBOR_D));
                        else
                            difference() {
                                circle(r = BARREL_TEETH_R - M_BARREL_GEAR);
                                circle(d = fit(BARREL_ARBOR_D));
                            }
                // ---- hub / bush journal ----
                tube(od = BARREL_ARBOR_D + 2 * BARREL_WALL_THK, id = fit(BARREL_ARBOR_D), h = h);
            }
            // ---- spring hook slot in the wall (the outer end hooks here) ----
            translate([BARREL_R_OUT - 1.0, -SPRING_WIDTH / 2 - 0.5, h / 2])
                cube([6, SPRING_WIDTH + 1.0, h + 2 * EPS], center = true);
            // ---- lightening pockets: the drum wall must stay stiff, but the
            //      floor between the hub and the rim is doing nothing ----
            for (i = [0:5]) rotate(i * 60)
                translate([(BARREL_ARBOR_D / 2 + BARREL_WALL_THK + BARREL_R_OUT) / 2, 0,
                           h - thk(ZR_BARREL_GEAR) - 1.2])
                    cylinder(d = (BARREL_R_OUT - BARREL_ARBOR_D / 2 - BARREL_WALL_THK) * 0.55,
                             h = 1.2 + EPS);
        }
}

// ---------------------------------------------------------------------------
// 2.  BARREL COVER  --  closes the drum so the spring cannot walk out
// ---------------------------------------------------------------------------
module barrel_cover() {
    z0 = dz(ZR_BARREL_COVER);
    h  = thk(ZR_BARREL_COVER);
    color(C_WHEEL)
    translate([0, 0, z0])
        difference() {
            union() {
                cylinder(d = BARREL_DRUM_OD - 2 * EPS, h = h);
                // spigot that locates in the drum mouth
                translate([0, 0, h - EPS])
                    tube(od = 2 * BARREL_R_OUT, id = fit(BARREL_ARBOR_D), h = 1.2);
            }
            cylinder(d = fit(BARREL_ARBOR_D), h = h + 4 * EPS);
            for (i = [0:2]) rotate(i * 120)
                translate([BARREL_R_OUT * 0.72, 0, -EPS])
                    screw_hole(h + 2 * EPS, d = SCREW_CLEARANCE, head_d = 0);
        }
}

// ---------------------------------------------------------------------------
// 3.  BARREL ARBOR  --  FIXED to the plate; the drum turns on it.
//     Carries the spring's inner hook and the winding square.
// ---------------------------------------------------------------------------
module barrel_arbor() {
    // the arbor spans from behind the drum cover to the ratchet above the plate
    z_bot = dz(ZR_BARREL_COVER);
    z_top = ZR_RATCHET[1] + 1.5;
    color(C_ARBOR)
    translate([0, 0, z_bot]) {
        difference() {
            union() {
                cylinder(d = BARREL_ARBOR_D, h = z_top - z_bot);
                // winding square, reached from the FRONT through the dial
                translate([0, 0, ZR_RATCHET[1] - z_bot])
                    intersection() {
                        cube([WIND_SQUARE, WIND_SQUARE, 12], center = false);
                        cylinder(d = WIND_SQUARE * 1.42, h = 12);
                    }
            }
            // spring inner hook: a slot the strip end drops into
            translate([BARREL_ARBOR_D / 2 - 3.0, -SPRING_THICK / 2 - 0.15,
                       dz(ZR_BARREL_DRUM) - z_bot + 1.0])
                cube([6, SPRING_THICK + 0.3, SPRING_WIDTH + 2 * EPS]);
        }
    }
}

// ---------------------------------------------------------------------------
// 4.  WINDING SLEEVE  --  a 10 mm square socket inside the arbor square, so the
//     key can be inserted from the front without removing the hands.
//     STATUS: Prototype.  It is dimensioned and drawn, but its friction fit on
//     the arbor square has not been validated by test.
// ---------------------------------------------------------------------------
module winding_sleeve() {
    color(C_PINION)
    translate([0, 0, ZR_RATCHET[1]])
        difference() {
            cylinder(d = WIND_SQUARE + 4, h = 6);
            translate([0, 0, -EPS])
                intersection() {
                    cube([WIND_SQUARE + PRINT_TOLERANCE, WIND_SQUARE + PRINT_TOLERANCE, 8]);
                    cylinder(d = (WIND_SQUARE + PRINT_TOLERANCE) * 1.42, h = 8);
                }
        }
}

// ---------------------------------------------------------------------------
// 5.  RATCHET + CLICK  --  winding in one direction only, and the let-down
//     control.  There is NO maintaining power in this design: the train drops
//     while the key is being turned.  That is a declared limitation (L-06).
// ---------------------------------------------------------------------------
module ratchet_wheel() {
    color(C_PINION)
    translate([0, 0, dz(ZR_RATCHET)])
        linear_extrude(height = thk(ZR_RATCHET) * 0.55, convexity = 10)
            ratchet_wheel_2d(Z_RATCHET, M_RATCHET, bore = fit(WIND_SQUARE * 1.02));
}

module click() {
    // pivots on a screw just outside the ratchet tip circle; the nose drops
    // into a saw tooth.  STATUS: Prototype -- the click spring force is not
    // calculated, it must be set by feel during adjustment.
    r_tip = Z_RATCHET * M_RATCHET / 2 + M_RATCHET;
    color(C_PINION)
    translate([r_tip + 4.0, 0, dz(ZR_RATCHET)]) {
        hull() {
            cylinder(d = 5, h = 1.6);
            translate([-r_tip - 4.0 + 1.0, 0, 0]) cylinder(d = 3.2, h = 1.6);
        }
        translate([-r_tip - 4.0 + 1.0, 0, 0]) cylinder(d = SCREW_CLEARANCE, h = 1.6);
    }
}

module click_spring() {
    // STATUS: Decorative-reference.  A flat spring whose rate is not computed;
    // it is drawn so the assembly is complete and it must be sourced, not
    // printed.
    r_tip = Z_RATCHET * M_RATCHET / 2 + M_RATCHET;
    color(C_SPRING)
    translate([r_tip + 4.0, 0, dz(ZR_RATCHET) + 1.6])
        linear_extrude(height = 0.3)
            difference() {
                hull() { circle(d = 5); translate([-9, 0]) circle(d = 3); }
                circle(d = SCREW_CLEARANCE);
            }
}

// ---------------------------------------------------------------------------
// 6.  MAINSPRING  --  REFERENCE SPIRAL ONLY, never exported as a part.
//     Archimedean spiral from r_arb to r_out over the calculated active length.
//     STATUS: Decorative-reference (the real part is bought, B-02).
// ---------------------------------------------------------------------------
module mainspring_coils(coils = MS_COILS_IN_DRUM, show = true) {
    if (!show) ;
    else {
        r0 = BARREL_R_ARB + SPRING_THICK;
        r1 = BARREL_R_OUT;
        steps = 900;
        color(C_SPRING, 0.9)
        translate([0, 0, dz(ZR_BARREL_DRUM) + 1.0])
            for (i = [0:steps-1])
                let (t0 = i / steps, t1 = (i + 1) / steps,
                     a0 = t0 * coils * 360, a1 = t1 * coils * 360,
                     rr0 = r0 + (r1 - r0) * t0, rr1 = r0 + (r1 - r0) * t1)
                    hull() {
                        translate([rr0 * cos(a0), rr0 * sin(a0), 0])
                            cube([SPRING_THICK, SPRING_THICK, SPRING_WIDTH], center = true);
                        translate([rr1 * cos(a1), rr1 * sin(a1), 0])
                            cube([SPRING_THICK, SPRING_THICK, SPRING_WIDTH], center = true);
                    }
    }
}

// ---------------------------------------------------------------------------
// 7.  THE WHOLE BARREL ASSEMBLY, positioned on the plate
// ---------------------------------------------------------------------------
module barrel_assembly(show_spring = true) {
    translate([POS_BARREL[0], POS_BARREL[1], 0]) {
        barrel_arbor();
        barrel_drum();
        barrel_cover();
        ratchet_wheel();
        click();
        click_spring();
        winding_sleeve();
        mainspring_coils(show = show_spring);
    }
}
