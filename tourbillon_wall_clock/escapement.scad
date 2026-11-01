// ===========================================================================
//  escapement.scad  --  Swiss lever escapement: escape wheel, elongated escape
//                       pinion, pallet lever with two ruby stones, roller and
//                       impulse pin, balance wheel and hairspring.
//
//  ALL COORDINATES IN THIS FILE ARE LOCAL TO THE CARRIAGE.  The carriage
//  origin is the carriage rotation axis (which is also the fixed fourth wheel's
//  axis), +Y points towards the balance, and local z = 0 is the underside of
//  the carriage floor.  tourbillon_cage.scad places this whole assembly at
//  POS_CARRIAGE with local z = 0 at global Z_CARRIAGE_Z0.
//
//  WHY A SWISS LEVER (and why it is inside the carriage):
//    - it is self-locking, so it needs no detent spring and it starts by itself
//    - its geometry is fully determined by tooth counts and angles, so it can
//      be laid out rather than guessed
//    - it is the only escapement with proven behaviour in a rotating carriage
//    A detent / chronometer escapement was rejected: not self-starting.
//    A Potter or fixed-ring escapement was rejected: it removes the fixed
//    fourth wheel, and with it the 1 rpm kinematic closure this design needs.
//
//  THE KINEMATIC CLOSURE, which is what makes this a tourbillon and not just a
//  rotating platform:
//      the fixed fourth wheel does not turn              omega_4 = 0
//      the escape pinion is carried around it            omega_c = 1 rpm
//      so the escape pinion is driven at                 omega_e/c = z4/zEP = 4
//      the escape wheel turns at                         4 + 1 = 5 rpm absolute
//      15 teeth x (4 rev/min / 60) = 1 tooth per second  ->  f = 1.000 Hz
//      and omega_c = f * zEP / (zE * z4) = 1*10/(15*40) = 1/60 rev/s = 1 rpm
//  The carriage rate is DERIVED from the balance frequency, not assumed.
//
//  MANUFACTURABILITY -- read this before printing anything:
//    The escape wheel and the two pallet stones CANNOT be 3-D printed.  The
//    impulse faces need Ra < 0.2 um and > 60 HRC or the lever will not unlock
//    consistently.  They are modelled here with correct geometry and must be
//    wire-EDM or laser cut from hardened 1.4034 and lapped (BOM B-11/B-12).
//    The hairspring is a bought part wound to the measured balance inertia; it
//    is drawn as a reference spiral and is labelled Decorative-reference.
// ===========================================================================

include <parameters.scad>
include <gear_generator.scad>

// ---------------------------------------------------------------------------
// 0.  LOCAL POSITIONS AND DERIVED LEVER GEOMETRY
// ---------------------------------------------------------------------------
ESC_POS   = [0, Y_ESCAPE];      // escape wheel + escape pinion, coaxial
PAL_POS   = [0, Y_PALLET];      // pallet lever arbor
BAL_POS   = [0, Y_BALANCE];     // balance staff

ARBOR_ESCAPE_D = 1.5;           // escape arbor, S-06 in docs/SHAFTS.md
ARBOR_PALLET_D = 1.2;           // pallet arbor, S-07
ARBOR_BALANCE_D= 1.6;           // balance staff, S-08

// The two engaged teeth straddle the line of centres by 1.5 tooth pitches, so
// the locking corner sits at psi = 1.5 * (360/zE) from it, on the tip circle.
// ESC_LOCKING_CIRCLE_RADIUS_MM is the distance from the pallet arbor to that
// corner and is also the lever arm on the escape side; it is computed by
// tools/calc.py, exported, and checked by C-29.
ESC_STONE_ARM_LEN   = ESC_LOCKING_CIRCLE_RADIUS_MM;
ESC_STONE_ARM_ANGLE = atan2(ESCAPE_WHEEL_OD / 2 * sin(1.5 * ESC_TOOTH_PITCH_ANGLE_DEG),
                            ESC_ESCAPE_TO_PALLET_DISTANCE_MM
                            - ESCAPE_WHEEL_OD / 2 * cos(1.5 * ESC_TOOTH_PITCH_ANGLE_DEG));

// ---------------------------------------------------------------------------
// 1.  ESCAPE PINION  --  the planet of the epicyclic.
//     It is rigid with the escape wheel and it is ELONGATED: the toothed
//     section hangs BELOW the carriage floor (local z -5.0 .. -2.6) so that it
//     can reach the fixed fourth wheel, which is bolted to the main plate,
//     while the plain arbor continues up through the floor to carry the escape
//     wheel.  This is the Helwig flying-tourbillon arrangement.
//
//     Why the toothed section is short and low: at local z -5.0 .. -2.6 the
//     pinion sweeps a ring of r <= 13.95 mm about the carriage axis, and the
//     intermediate wheel's teeth stop 14.70 mm from that axis and run at
//     global Z 4.0 .. 6.0, which is ABOVE the pinion teeth and BELOW the
//     carriage floor.  calc.py check C-18c proves the two never meet.
// ---------------------------------------------------------------------------
module escape_pinion(show_teeth = SHOW_GEAR_TEETH) {
    z_tooth0 = Z_CARRIAGE[0][0];                 // -5.0
    h_tooth  = Z_CARRIAGE[0][1] - Z_CARRIAGE[0][0];   // 2.4
    color(C_PINION)
    translate(ESC_POS)
        rotate(-ang_escape_rel())
            translate([0, 0, z_tooth0]) {
                // plain arbor, full height
                cylinder(d = ARBOR_ESCAPE_D,
                         h = Z_CARRIAGE[1][1] - Z_CARRIAGE[0][0]);
                // toothed section
                linear_extrude(height = h_tooth, convexity = 12)
                    if (show_teeth)
                        gear_cycloidal_2d(M_ESCAPE_PINION, Z_ESCAPE_PINION,
                                          CYCLO_RR_EPICYCLIC, GEAR_BACKLASH, 0, 12);
                    else
                        circle(r = pitch_r(M_ESCAPE_PINION, Z_ESCAPE_PINION));
            }
}

// ---------------------------------------------------------------------------
// 2.  ESCAPE WHEEL  --  15 club teeth.  NOT printable, see the header.
// ---------------------------------------------------------------------------
module escape_wheel(show_teeth = SHOW_GEAR_TEETH) {
    z0 = cz(Z_CARRIAGE[3][0]) - Z_CARRIAGE_Z0;    // local 2.0
    color(C_ESCAPE)
    translate(ESC_POS)
        rotate(-ang_escape_rel())
            translate([0, 0, z0])
                escape_wheel_3d(ESCAPE_WHEEL_THK, hub_d = 4.0,
                                bore_d = fit(ARBOR_ESCAPE_D), z0 = 0);
}

module escape_arbor_upper() {
    // the part of the escape arbor above the floor: carries the wheel and
    // pivots in the carriage upper bridge
    color(C_ARBOR)
    translate(ESC_POS)
        translate([0, 0, 0])
            cylinder(d = ARBOR_ESCAPE_D, h = Z_CARRIAGE[1][1]);
}

// ---------------------------------------------------------------------------
// 3.  PALLET LEVER  --  inline Swiss lever with two ruby stones.
//
//     The lever is a three-armed part:
//       arm 1 and 2 : the two pallet arms, splayed at +/-ESC_STONE_ARM_ANGLE
//                     from the -Y direction, each ESC_STONE_ARM_LEN long, so
//                     that the stone's locking corner lands exactly on the
//                     engaged escape tooth (that IS the locking circle).
//       arm 3       : the fork arm, along +Y, PALLET_LEVER_LEN long, ending in
//                     two horns with a slot of ESC_FORK_SLOT_WIDTH_MM.
//     The ratio fork arm / stone arm is ESC_LEVER_RATIO = 1.8365.
//
//     The lever swings only ESC_LEVER_SWING_DEG = 1.83 deg peak to peak, set by
//     the banking angle; that is what the fork slot width is derived from.
// ---------------------------------------------------------------------------
module pallet_stone(side = 1) {
    // STATUS: NOT PRINTABLE.  Synthetic ruby, cemented into the lever and
    // lapped.  Drawn to its real 2.6 x 1.6 mm so the lever arms are sized by
    // something other than guesswork.
    color(C_RUBY)
    translate([side * PALLET_STONE_W / 2, 0, 0])
        rotate([0, 0, -side * ESC_ENTRY_STONE_ANGLE_DEG])
            cube([PALLET_STONE_W, PALLET_STONE_L, thk(Z_CARRIAGE[4]) * 0.8],
                 center = true);
}

module pallet_lever(angle_deg = 0) {
    h = thk(Z_CARRIAGE[4]);                       // 2.0
    z0 = Z_CARRIAGE[4][0];                        // local 2.2
    color(C_PINION)
    translate(PAL_POS)
        translate([0, 0, z0])
            rotate(angle_deg) {
                // ---- hub ----
                cylinder(d = PALLET_LEVER_W, h = h);
                cylinder(d = fit(ARBOR_PALLET_D), h = h + 2 * EPS);
                // ---- the two pallet arms, splayed towards the escape wheel ----
                for (side = [-1, 1])
                    hull() {
                        cylinder(d = PALLET_LEVER_W, h = h);
                        translate([side * ESC_STONE_ARM_LEN
                                        * sin(ESC_STONE_ARM_ANGLE),
                                   -ESC_STONE_ARM_LEN
                                        * cos(ESC_STONE_ARM_ANGLE), 0])
                            cylinder(d = PALLET_STONE_W + 1.2, h = h);
                    }
                // ---- the stones themselves ----
                for (side = [-1, 1])
                    translate([side * ESC_STONE_ARM_LEN * sin(ESC_STONE_ARM_ANGLE),
                               -ESC_STONE_ARM_LEN * cos(ESC_STONE_ARM_ANGLE),
                               h / 2])
                        rotate([0, 0, -side * ESC_ENTRY_STONE_ANGLE_DEG])
                            pallet_stone(side);
                // ---- fork arm towards the balance ----
                hull() {
                    cylinder(d = PALLET_LEVER_W, h = h);
                    translate([0, PALLET_LEVER_LEN, 0])
                        cylinder(d = PALLET_LEVER_W * 0.72, h = h);
                }
                // ---- fork horns + slot ----
                translate([0, PALLET_LEVER_LEN, 0])
                    difference() {
                        union() {
                            cube([PALLET_LEVER_W * 0.9, 3.2, h], center = true);
                            translate([0, 1.2, 0])
                                cube([PALLET_LEVER_W * 1.15, 2.0, h], center = true);
                        }
                        // the slot the impulse pin runs in
                        translate([0, 1.0, 0])
                            cube([ESC_FORK_SLOT_WIDTH_MM + IMPULSE_PIN_D,
                                  4.0, h + 2 * EPS], center = true);
                    }
                // ---- banking pins: these set the 6 deg total swing ----
                for (side = [-1, 1])
                    translate([side * 3.4, 1.6, 0]) cylinder(d = 0.8, h = h + 1.0);
            }
}

module pallet_arbor() {
    color(C_ARBOR)
    translate(PAL_POS)
        translate([0, 0, Z_CARRIAGE[4][0] - 0.6])
            cylinder(d = ARBOR_PALLET_D, h = thk(Z_CARRIAGE[4]) + 1.6);
}

// ---------------------------------------------------------------------------
// 4.  ROLLER + IMPULSE PIN  --  mounted on the balance staff, it is what the
//     fork actually pushes.  Impulse-pin circle r = 3.5 mm.
// ---------------------------------------------------------------------------
module roller(angle_deg = 0) {
    z0 = Z_CARRIAGE[5][0];
    h  = thk(Z_CARRIAGE[5]);
    color(C_PINION)
    translate(BAL_POS)
        translate([0, 0, z0])
            rotate(angle_deg) {
                difference() {
                    union() {
                        cylinder(d = ROLLER_D, h = h);
                        // the impulse pin, on the side facing the lever
                        translate([0, -IMPULSE_PIN_R, h * 0.2])
                            cylinder(d = IMPULSE_PIN_D, h = h * 1.5);
                    }
                    cylinder(d = fit(ARBOR_BALANCE_D), h = h + 2 * EPS);
                }
            }
}

// ---------------------------------------------------------------------------
// 5.  BALANCE WHEEL  --  the oscillator.  1.000 Hz with the hairspring below.
//     Two arms at 90 deg (BALANCE_ARM_N = 2, BALANCE_ARM_ANGLE = 90) so that
//     the carriage columns at 150/240/330 deg stay clear of them; that angular
//     choice is checked by C-15h.
// ---------------------------------------------------------------------------
module balance_wheel(angle_deg = 0) {
    z0 = Z_CARRIAGE[6][0];
    h  = thk(Z_CARRIAGE[6]);
    r_out = BALANCE_OD / 2;
    r_in  = r_out - BALANCE_RIM_W;
    color(C_BALANCE)
    translate(BAL_POS)
        translate([0, 0, z0])
            rotate(angle_deg) {
                difference() {
                    union() {
                        tube(od = BALANCE_OD, id = 2 * r_in, h = h);
                        for (i = [0:BALANCE_ARM_N-1])
                            rotate(i * BALANCE_ARM_ANGLE + 45)
                                hull() {
                                    cylinder(d = 5.0, h = BALANCE_ARM_T);
                                    translate([r_in, 0, 0])
                                        cube([BALANCE_ARM_W, BALANCE_ARM_W, BALANCE_ARM_T],
                                             center = true);
                                }
                        cylinder(d = 5.0, h = h);          // collet
                    }
                    cylinder(d = fit(ARBOR_BALANCE_D), h = h + 2 * EPS);
                    // poising / timing screws.  These are the adjustment
                    // interface: the carriage must be poised to <= 12360 mg-mm
                    // (calc.py C-27) and the rate trimmed by moving these.
                    for (i = [0:7])
                        rotate(i * 45 + 22.5)
                            translate([r_out - BALANCE_RIM_W / 2, 0, -EPS])
                                cylinder(d = 1.6, h = h + 2 * EPS);
                }
            }
}

module balance_staff() {
    color(C_ARBOR)
    translate(BAL_POS)
        translate([0, 0, Z_CARRIAGE[6][0] - 1.0])
            cylinder(d = ARBOR_BALANCE_D,
                     h = Z_CARRIAGE[9][1] - Z_CARRIAGE[6][0] + 2.0);
}

// ---------------------------------------------------------------------------
// 6.  HAIRSPRING  --  REFERENCE SPIRAL, NOT A MANUFACTURABLE PART.
//     STATUS: Decorative-reference.  The real part is bought or wound to the
//     MEASURED inertia of the finished balance (BOM B-03), because the required
//     stiffness is only 0.02633 N-mm/rad and a spring that is 0.01 mm too thick
//     is twice too stiff.  The calculated values are:
//         active length 246.2 mm, 3.73 turns, OD 26, ID 16,
//         t = 0.06, b = 1.8, inner bending stress 750 MPa (limit 1400)
//     It is drawn so the assembly is complete and the clearances can be seen.
// ---------------------------------------------------------------------------
module hairspring(turns = OSC_HAIRSPRING_TURNS_AT_MEAN_RADIUS, show = true) {
    if (show) {
        r_id = HAIRSPRING_ID / 2;
        r_od = HAIRSPRING_OD / 2;
        steps = 420;
        color(C_HAIRSPRING, 0.95)
        translate(BAL_POS)
            translate([0, 0, Z_CARRIAGE[7][0]])
                for (i = [0:steps-1])
                    let (t0 = i / steps, t1 = (i + 1) / steps,
                         a0 = t0 * turns * 360, a1 = t1 * turns * 360,
                         rr0 = r_id + (r_od - r_id) * t0,
                         rr1 = r_id + (r_od - r_id) * t1)
                        hull() {
                            translate([rr0 * cos(a0), rr0 * sin(a0), 0])
                                cube([HAIRSPRING_T, HAIRSPRING_T, HAIRSPRING_B], center = true);
                            translate([rr1 * cos(a1), rr1 * sin(a1), 0])
                                cube([HAIRSPRING_T, HAIRSPRING_T, HAIRSPRING_B], center = true);
                        }
    }
}

module hairspring_stud() {
    // the fixed outer anchor.  It is clamped by the carriage upper bridge, NOT
    // by the main plate: the whole oscillator turns with the carriage, which is
    // the entire point of a tourbillon.
    color(C_PINION)
    translate(BAL_POS)
        translate([HAIRSPRING_OD / 2, 0, Z_CARRIAGE[7][0] - 0.4])
            cylinder(d = 2.0, h = HAIRSPRING_B + 0.8);
}

// ---------------------------------------------------------------------------
// 7.  THE WHOLE ESCAPEMENT, in carriage-local coordinates
//     angle_balance_deg / angle_lever_deg are GEOMETRIC ANIMATION inputs only.
// ---------------------------------------------------------------------------
module escapement(show_teeth = SHOW_GEAR_TEETH, show_hairspring = true,
                  angle_balance_deg = 0, angle_lever_deg = 0) {
    escape_pinion(show_teeth);
    escape_arbor_upper();
    escape_wheel(show_teeth);
    pallet_arbor();
    pallet_lever(angle_lever_deg);
    roller(angle_balance_deg);
    balance_wheel(angle_balance_deg);
    balance_staff();
    hairspring_stud();
    hairspring(show = show_hairspring);
}
