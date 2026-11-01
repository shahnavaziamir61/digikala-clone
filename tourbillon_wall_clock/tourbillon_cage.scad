// ===========================================================================
//  tourbillon_cage.scad  --  the rotating carriage: rim gear, floor, columns,
//                            upper bridge, sleeve arbor, endstone, top cap and
//                            the seconds pointer.
//
//  ARCHITECTURE: a RIM-DRIVEN, single-axis flying carriage (Helwig / IWC
//  Portugiesere Mystere style), NOT a Breguet under-carriage.  The reason is
//  geometric and is recorded as LIMITATIONS L-01: at a 70 mm carriage the
//  classical Breguet pinion-under-the-cage would have to sit at a radius where
//  the fixed fourth wheel already is, and the two cannot coexist.  Here the
//  drive is applied at the rim instead:
//
//      intermediate pinion (z=12, m=0.70) -> carriage rim gear (z=96, m=0.70)
//      i = 8.0 exactly, centre distance 37.8 mm, carriage = 1.000 rpm
//
//  The carriage is the SECONDS hand: one revolution per minute, derived from
//  the balance frequency, not chosen.  The seconds pointer at the top is
//  therefore a real functional indicator, and the dial aperture is cut so the
//  whole carriage is visible from the front.
//
//  MASS AND POISE (all computed by tools/calc.py, all reported in
//  docs/CALCULATIONS.md):
//      carriage alone            24.089 g   (floor 6.99, rim band 8.41,
//                                            upper bridge 2.02, columns 1.93,
//                                            sleeve arbor 4.74)
//      everything that rotates   33.677 g   (+ balance 6.80, escapement 2.69)
//      J about the carriage axis 1.5048e-5 kg m^2
//      un-poised static moment    72.785 g-mm  -> CoM 2.161 mm off axis
//      gravity torque at that CoM 7.14e-4 N-m = 0.60 x the available escape
//                               torque, i.e. it would dominate the escapement
//      REQUIRED poise           <= 12360.5 mg-mm  (CoM <= 0.367 mm)
//      counter-mass to achieve it  2.43 g at r = 30 mm
//     So the carriage is deliberately NOT symmetric: the balance sits at
//     +Y = 14 mm and the escape wheel at -Y = 11.25 mm, and the resulting
//     static moment must be removed by the counter-mass below.
//
//  MATERIAL: Ti-6Al-4V, machined.  STATUS: Prototype for the printed version.
//  A printed carriage cannot be poised to 0.367 mm and is not a timekeeping
//  part; see docs/LIMITATIONS.md L-05.
// ===========================================================================

include <parameters.scad>
include <gear_generator.scad>
include <escapement.scad>

// ---------------------------------------------------------------------------
// 1.  CARRIAGE RIM GEAR  --  the drive interface.
//     An annulus: bore r = CARRIAGE_BORE_R (32.22), root r 32.725, tip r 34.30.
//     It shares the describing circle of its mesh with the intermediate pinion.
// ---------------------------------------------------------------------------
module carriage_rim_gear(show_teeth = SHOW_GEAR_TEETH) {
    z0 = dz(ZR_RIM_GEAR) - Z_CARRIAGE_Z0;          // local 0.0
    h  = thk(ZR_RIM_GEAR);                          // 1.6
    color(C_CARRIAGE)
    translate([0, 0, z0])
        difference() {
            linear_extrude(height = h, convexity = 14)
                if (show_teeth)
                    gear_cycloidal_2d(M_CARRIAGE_RIM, Z_CARRIAGE_RIM,
                                      CYCLO_RR_INTER_CARRIAGE, GEAR_BACKLASH, 0, 14);
                else
                    circle(r = pitch_r(M_CARRIAGE_RIM, Z_CARRIAGE_RIM));
            translate([0, 0, -EPS])
                cylinder(r = CARRIAGE_BORE_R, h = h + 2 * EPS);
        }
}

// ---------------------------------------------------------------------------
// 2.  CARRIAGE FLOOR / LOWER PLATE  --  the main structural member.
//     OD 62, thickness 1.6, with a 30 mm central opening.  That opening is not
//     cosmetic: the fixed fourth wheel and the elongated escape pinion both
//     live inside it, and the escape pinion's toothed section hangs BELOW the
//     floor to reach the stationary wheel.  1.6 mm is also the thinnest
//     functional wall anywhere in the clock, which is why check C-32 rules out
//     FDM for this part.
// ---------------------------------------------------------------------------
module carriage_floor() {
    color(C_CARRIAGE)
    translate([0, 0, 0])
        difference() {
            cylinder(d = CARRIAGE_FLOOR_OD, h = CARRIAGE_FLOOR_THK);
            translate([0, 0, -EPS])
                cylinder(d = CARRIAGE_FLOOR_HOLE_D,
                         h = CARRIAGE_FLOOR_THK + 2 * EPS);
            // escape-pinion passage: the pinion is at Y = -11.25 and its arbor
            // is 1.5 mm, but the toothed section below needs a 5.4 mm hole
            translate([ESC_POS[0], ESC_POS[1], -EPS])
                cylinder(d = CARRIAGE_PINION_HOLE_D * 0.25,
                         h = CARRIAGE_FLOOR_THK + 2 * EPS);
            // pallet arbor and balance staff passages
            translate([PAL_POS[0], PAL_POS[1], -EPS])
                cylinder(d = fit(ARBOR_PALLET_D) + 1.0,
                         h = CARRIAGE_FLOOR_THK + 2 * EPS);
            translate([BAL_POS[0], BAL_POS[1], -EPS])
                cylinder(d = fit(ARBOR_BALANCE_D) + 1.0,
                         h = CARRIAGE_FLOOR_THK + 2 * EPS);
            // lightening: three pockets between the bearing seats.  Mass
            // matters here -- every gram at r = 23 mm adds to the static moment
            // that has to be poised away.
            for (a = CARRIAGE_COLUMN_ANGLES)
                rotate(a + 60)
                    translate([19, 0, -EPS])
                        cylinder(d = 9.0, h = CARRIAGE_FLOOR_THK + 2 * EPS);
            // counter-mass pocket at 90 deg from the balance, r = 30.
            // 2.43 g of brass here brings the static moment inside spec.
            rotate(180)
                translate([30, 0, CARRIAGE_FLOOR_THK - 1.0])
                    cylinder(d = 7.0, h = 1.0 + EPS);
            // column and bridge fixing screws
            for (a = CARRIAGE_COLUMN_ANGLES)
                rotate(a)
                    translate([CARRIAGE_COLUMN_R, 0, -EPS])
                        cylinder(d = PILLAR_SCREW_D, h = CARRIAGE_FLOOR_THK + 2 * EPS);
        }
}

module carriage_counter_mass() {
    // STATUS: functional, but its exact mass is set on the poising tool, not
    // by this model.  2.43 g at r = 30 is the CALCULATED starting point.
    color(C_WHEEL)
    rotate(180)
        translate([30, 0, CARRIAGE_FLOOR_THK - 1.0])
            cylinder(d = 6.6, h = 1.0);
}

// ---------------------------------------------------------------------------
// 3.  RIM BAND  --  ties the floor to the rim gear and to the upper bridge,
//     and provides the outer cylindrical surface the carriage runs in.
// ---------------------------------------------------------------------------
module carriage_rim_band() {
    r_out = CARRIAGE_BORE_R + 1.6;
    color(C_CARRIAGE)
    difference() {
        translate([0, 0, 0])
            tube(od = 2 * r_out, id = 2 * (r_out - 1.4),
                 h = Z_CARRIAGE[8][1]);            // floor underside to bridge top
        // open the sectors where the escape wheel and the balance need room,
        // and where the pallet lever swings
        for (a = [0, 180]) rotate(a)
            translate([0, 0, -EPS])
                rotate(-38) cube([2 * r_out, 2 * r_out, Z_CARRIAGE[8][1] + 2 * EPS]);
    }
}

// ---------------------------------------------------------------------------
// 4.  COLUMNS  --  three, at r = 23, angles 150 / 240 / 330 deg.
//     NOT evenly spaced at 120 deg, and that is deliberate: the balance wheel
//     (r 14 at y = +14, so it reaches r = 28 from the carriage axis) and the
//     escape wheel (r 10 at y = -11.25) only leave the arcs
//     ~[135, 255] and ~[285, 405] free at r = 23.  Check C-15h verifies each
//     column clears both, with the clearance reported per column.
// ---------------------------------------------------------------------------
module carriage_columns() {
    z0 = CARRIAGE_FLOOR_THK;
    h  = Z_CARRIAGE[8][0] - z0;                     // floor top to bridge underside
    color(C_CARRIAGE)
    for (a = CARRIAGE_COLUMN_ANGLES)
        rotate(a)
            translate([CARRIAGE_COLUMN_R, 0, z0]) {
                difference() {
                    cylinder(d = CARRIAGE_COLUMN_D, h = h);
                    // threaded at both ends for the poising / assembly screws
                    translate([0, 0, -EPS])
                        cylinder(d = PILLAR_SCREW_D, h = 2.0 + EPS);
                    translate([0, 0, h - 2.0])
                        cylinder(d = PILLAR_SCREW_D, h = 2.0 + EPS);
                }
            }
}

// ---------------------------------------------------------------------------
// 5.  UPPER BRIDGE  --  40 x 5 x 1.6, spanning the escape arbor, the pallet
//     arbor and the balance staff.  This is the upper bearing seat for all
//     three, so its hole positions ARE the coaxiality spec (checked by C-14,
//     C-15, C-15b).
// ---------------------------------------------------------------------------
module carriage_upper_bridge() {
    z0 = Z_CARRIAGE[8][0];
    h  = thk(Z_CARRIAGE[8]);
    color(C_CARRIAGE)
    translate([0, 0, z0])
        difference() {
            hull() {
                translate([0, CARRIAGE_UPPER_BRIDGE_L / 2 - 3, 0])
                    cylinder(d = CARRIAGE_UPPER_BRIDGE_W + 2, h = h);
                translate([0, -CARRIAGE_UPPER_BRIDGE_L / 2 + 3, 0])
                    cylinder(d = CARRIAGE_UPPER_BRIDGE_W + 2, h = h);
                for (a = CARRIAGE_COLUMN_ANGLES)
                    rotate(a) translate([CARRIAGE_COLUMN_R, 0, 0])
                        cylinder(d = CARRIAGE_COLUMN_D + 1.0, h = h);
            }
            // jewel seats: escape arbor, pallet arbor, balance staff
            translate(ESC_POS) cylinder(d = BEARING_SEAT_DIAMETER * 0.5,
                                        h = h + 2 * EPS);
            translate(PAL_POS) cylinder(d = BEARING_SEAT_DIAMETER * 0.45,
                                        h = h + 2 * EPS);
            translate(BAL_POS) cylinder(d = BEARING_SEAT_DIAMETER * 0.5,
                                        h = h + 2 * EPS);
            for (a = CARRIAGE_COLUMN_ANGLES)
                rotate(a) translate([CARRIAGE_COLUMN_R, 0, -EPS])
                    cylinder(d = PILLAR_SCREW_D, h = h + 2 * EPS);
        }
}

module carriage_jewels() {
    // STATUS: bought, not printed.  Ruby jewels are the only acceptable upper
    // bearing for the escape, pallet and balance arbors: a printed hole is not
    // a precision bearing (see LIMITATIONS L-07 and docs/SHAFTS.md).
    color(C_RUBY)
    for (p = [ESC_POS, PAL_POS, BAL_POS])
        translate([p[0], p[1], Z_CARRIAGE[8][1] - 0.8])
            cylinder(d = 2.6, h = 0.8);
}

module balance_endstone() {
    // sapphire endstone taking the axial thrust of the balance staff
    color(C_RUBY)
    translate(BAL_POS)
        translate([0, 0, Z_CARRIAGE[9][0]])
            cylinder(d = Z_CARRIAGE[9][2], h = thk(Z_CARRIAGE[9]));
}

// ---------------------------------------------------------------------------
// 6.  SLEEVE ARBOR  --  the carriage's own rotation axis.
//     OD 8, running in a lower ball race against the main plate and an upper
//     ruby jewel in the top bridge.  Radial play <= 0.015 mm, axial 0.03-0.05.
//     This is the single most demanding bearing in the clock: it carries the
//     whole rotating assembly at 1 rpm and any wobble shows directly as a rate
//     error.  It MUST be hardened steel, lapped (S-05).
// ---------------------------------------------------------------------------
module carriage_sleeve_arbor() {
    color(C_ARBOR)
    translate([0, 0, Z_CARRIAGE[0][0]])            // local -5.0
        difference() {
            cylinder(d = CARRIAGE_ARBOR_D, h = Z_CARRIAGE[10][1] - Z_CARRIAGE[0][0]);
            // the escape pinion passes through it, coaxially
            translate([ESC_POS[0], ESC_POS[1], -EPS])
                cylinder(d = fit(ARBOR_ESCAPE_D) + 0.4,
                         h = Z_CARRIAGE[10][1] + 2 * EPS);
        }
}

module carriage_top_cap() {
    z0 = Z_CARRIAGE[10][0];
    color(C_CARRIAGE)
    translate([0, 0, z0])
        difference() {
            union() {
                cylinder(d = Z_CARRIAGE[10][2], h = thk(Z_CARRIAGE[10]));
                translate([0, 0, thk(Z_CARRIAGE[10])])
                    cylinder(d = 6.0, h = 1.0);      // the polished boss you see
            }
            translate([ESC_POS[0], ESC_POS[1], -EPS])
                cylinder(d = fit(ARBOR_ESCAPE_D) + 0.4,
                         h = thk(Z_CARRIAGE[10]) + 3 * EPS);
            translate([0, 0, -EPS])
                cylinder(d = fit(CARRIAGE_ARBOR_D), h = thk(Z_CARRIAGE[10]) + 3 * EPS);
        }
}

// ---------------------------------------------------------------------------
// 7.  SECONDS POINTER  --  the carriage turns once a minute, so this is a real
//     seconds indicator, not decoration.  It has to stay inside the 74 mm
//     bridge window that the top bridge provides (checked by C-18b).
// ---------------------------------------------------------------------------
module seconds_pointer() {
    z0 = Z_CARRIAGE[11][0];
    h  = thk(Z_CARRIAGE[11]);
    color(C_HANDS)
    translate([0, 0, z0]) {
        hull() {
            cylinder(d = 6.0, h = h);
            translate([0, Z_CARRIAGE[11][2] / 2 - 2.0, 0]) cylinder(d = 2.4, h = h);
        }
        // counterpoise tail
        translate([0, -Z_CARRIAGE[11][2] / 2 + 4.0, 0]) cylinder(d = 4.0, h = h);
    }
}

// ---------------------------------------------------------------------------
// 8.  THE COMPLETE CARRIAGE, placed on the movement.
//     Local z = 0 sits at global Z_CARRIAGE_Z0, and the whole thing rotates
//     about POS_CARRIAGE, which is also POS_FIXED_FOURTH -- that coincidence is
//     the design, not an accident, and it is what C-04 checks.
// ---------------------------------------------------------------------------
module tourbillon_carriage(show_teeth = SHOW_GEAR_TEETH, show_hairspring = true,
                           angle_deg = 0, angle_balance_deg = 0,
                           angle_lever_deg = 0, show_escapement = true) {
    translate([POS_CARRIAGE[0], POS_CARRIAGE[1], Z_CARRIAGE_Z0])
        rotate(angle_deg) {
            carriage_rim_gear(show_teeth);
            carriage_floor();
            carriage_counter_mass();
            carriage_rim_band();
            carriage_columns();
            carriage_upper_bridge();
            carriage_jewels();
            carriage_sleeve_arbor();
            balance_endstone();
            carriage_top_cap();
            seconds_pointer();
            if (show_escapement)
                escapement(show_teeth, show_hairspring,
                           angle_balance_deg, angle_lever_deg);
        }
}
