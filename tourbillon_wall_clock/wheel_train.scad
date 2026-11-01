// ===========================================================================
//  wheel_train.scad  --  every rotating wheel and pinion of the going train,
//                        plus the stationary fixed fourth wheel.
//
//  Power path (see the frozen architecture in tools/design.py):
//
//    mainspring -> BARREL DRUM + BARREL GEAR  (mainspring_barrel.scad)
//               -> GREAT WHEEL / GREAT PINION      i = 4.0
//               -> CENTRE WHEEL / CENTRE PINION    i = 6.0     1 rev per HOUR
//               -> INTERMEDIATE WHEEL / PINION     i = 7.5
//               -> CARRIAGE RIM GEAR               i = 8.0     1 rev per MINUTE
//               -> (inside the carriage) FIXED FOURTH WHEEL, ESCAPE PINION,
//                  ESCAPE WHEEL, PALLET LEVER, BALANCE      (escapement.scad,
//                  tourbillon_cage.scad)
//
//  Tooth geometry: EVERY mesh is cycloidal, and both members of a mesh share
//  ONE describing circle CYCLO_RR_*.  See gear_generator.scad for why that is
//  a conjugacy requirement and not a stylistic choice.
//
//  Each part is drawn at its true position in the dial plane and its true Z
//  band, so assembly.scad only has to call these modules without further
//  transforms.  Rotation angles come from parameters.scad and are GEOMETRIC
//  ANIMATION ONLY -- they are not a kinematic solution.
// ===========================================================================

include <parameters.scad>
include <gear_generator.scad>

// ---------------------------------------------------------------------------
// Arbor blanks.  A watch pinion is cut from its arbor, so the pinion modules
// take the arbor diameter and the total arbor height and draw both in one go.
// The diameters are the ones validated in docs/SHAFTS.md (S-01 .. S-09).
// ---------------------------------------------------------------------------
ARBOR_GREAT_D     = 3.0;
ARBOR_CENTRE_D    = SHAFT_DIAMETER;         // 4.0
ARBOR_INTER_D     = 3.0;
ARBOR_FIXED4_D    = FIXED_4TH_BOSS_D;   // 5.0 stub arbor, bolted, does not turn
ARBOR_MOTION_D    = 3.5;

// ---------------------------------------------------------------------------
// 1.  GREAT WHEEL + GREAT PINION  (one rigid part on one arbor)
//     The wheel is at the back of the train and the pinion sits on top of it,
//     both between Z 2.0 and 8.6.
// ---------------------------------------------------------------------------
module great_wheel(show_teeth = SHOW_GEAR_TEETH) {
    z_w = dz(ZR_GREAT_WHEEL);
    h_w = thk(ZR_GREAT_WHEEL);
    z_p = dz(ZR_GREAT_PINION);
    h_p = ZR_GREAT_PINION[1] - (z_w + h_w);       // pinion teeth above the wheel
    bore = fit(ARBOR_GREAT_D);
    color(C_WHEEL)
    rotate(-ang_great())
        gear_3d(M_GREAT_WHEEL, Z_GREAT_WHEEL, h_w,
                hub_d = hub_od("great wheel"), hub_h = h_w + 1.6, bore_d = bore,
                rr = CYCLO_RR_BARREL_GREAT, spokes = 5, spoke_w = 4.0, z0 = z_w,
                system = "cycloidal", lightening = 0.35, show_teeth = show_teeth);
}

module great_pinion(show_teeth = SHOW_GEAR_TEETH) {
    // rigid with the great wheel: same arbor, same angle
    thk_p = ZR_GREAT_PINION[1] - dz(ZR_GREAT_PINION);
    color(C_PINION)
    rotate(-ang_great())
        translate([0, 0, dz(ZR_GREAT_PINION)])
            pinion_3d(M_GREAT_PINION, Z_GREAT_PINION, thk_p, ARBOR_GREAT_D,
                      thk_p + 2.0, rr = CYCLO_RR_GREAT_CENTRE, z_tooth = 1.0,
                      show_teeth = show_teeth);
}

module great_wheel_arbor() {
    color(C_ARBOR)
    translate([0, 0, dz(ZR_GREAT_WHEEL) - 1.5])
        cylinder(d = ARBOR_GREAT_D, h = ZR_GREAT_PINION[1] - dz(ZR_GREAT_WHEEL) + 3.0);
}

// ---------------------------------------------------------------------------
// 2.  CENTRE WHEEL + CENTRE PINION  --  one revolution per HOUR.
//     This is the reference member of the whole clock: every other speed in the
//     train is derived from it, and the hand train hangs off its arbor.
// ---------------------------------------------------------------------------
module centre_wheel(show_teeth = SHOW_GEAR_TEETH) {
    bore = fit(ARBOR_CENTRE_D);
    color(C_WHEEL)
    rotate(-ang_centre())
        gear_3d(M_CENTRE_WHEEL, Z_CENTRE_WHEEL, thk(ZR_CENTRE_WHEEL),
                hub_d = hub_od("centre wheel"), hub_h = thk(ZR_CENTRE_WHEEL) + 1.2,
                bore_d = bore, rr = CYCLO_RR_GREAT_CENTRE,
                spokes = 4, spoke_w = 3.0, z0 = dz(ZR_CENTRE_WHEEL),
                system = "cycloidal", lightening = 0.30, show_teeth = show_teeth);
}

module centre_pinion(show_teeth = SHOW_GEAR_TEETH) {
    thk_p = ZR_CENTRE_PINION[1] - dz(ZR_CENTRE_PINION);
    color(C_PINION)
    rotate(-ang_centre())
        translate([0, 0, dz(ZR_CENTRE_PINION)])
            pinion_3d(M_CENTRE_PINION, Z_CENTRE_PINION, thk_p, ARBOR_CENTRE_D,
                      thk_p, rr = CYCLO_RR_CENTRE_INTER, z_tooth = 0,
                      show_teeth = show_teeth);
}

module centre_arbor() {
    // spans the whole movement: it carries the hands at the front and the
    // canon pinion friction fit, so it is the longest arbor in the clock
    color(C_ARBOR)
    translate([0, 0, dz(ZR_CENTRE_PINION) - 2.0])
        cylinder(d = ARBOR_CENTRE_D, h = ZR_MINUTE_PIPE[1] - dz(ZR_CENTRE_PINION) + 2.0);
}

// ---------------------------------------------------------------------------
// 3.  INTERMEDIATE WHEEL + PINION
//     This stage exists only because a single 60:1 centre-to-carriage reduction
//     cannot fit inside a 70 mm carriage envelope (LIMITATIONS L-01).  It is
//     the reason the intermediate wheel is the tightest part of the layout: its
//     teeth must stop short of the swept ring of the carriage's escape arbor,
//     which is what calc.py check C-18c proves.
// ---------------------------------------------------------------------------
module intermediate_wheel(show_teeth = SHOW_GEAR_TEETH) {
    bore = fit(ARBOR_INTER_D);
    color(C_WHEEL)
    translate([POS_INTERMEDIATE[0], POS_INTERMEDIATE[1], 0])
        rotate(ang_intermediate())
            gear_3d(M_INTER_WHEEL, Z_INTER_WHEEL, thk(ZR_INTER_WHEEL),
                    hub_d = hub_od("intermediate wheel"),
                    hub_h = thk(ZR_INTER_WHEEL) + 1.0, bore_d = bore,
                    rr = CYCLO_RR_CENTRE_INTER, spokes = 0, z0 = dz(ZR_INTER_WHEEL),
                    system = "cycloidal", show_teeth = show_teeth);
}

module intermediate_pinion(show_teeth = SHOW_GEAR_TEETH) {
    thk_p = ZR_INTER_PINION[1] - dz(ZR_INTER_PINION);
    color(C_PINION)
    translate([POS_INTERMEDIATE[0], POS_INTERMEDIATE[1], 0])
        rotate(ang_intermediate())
            translate([0, 0, dz(ZR_INTER_PINION)])
                pinion_3d(M_INTER_PINION, Z_INTER_PINION, thk_p, ARBOR_INTER_D,
                          thk_p + 1.0, rr = CYCLO_RR_INTER_CARRIAGE, z_tooth = 1.0,
                          show_teeth = show_teeth);
}

module intermediate_arbor() {
    color(C_ARBOR)
    translate([POS_INTERMEDIATE[0], POS_INTERMEDIATE[1], dz(ZR_INTER_WHEEL) - 1.0])
        cylinder(d = ARBOR_INTER_D, h = ZR_INTER_PINION[1] - dz(ZR_INTER_WHEEL) + 2.0);
}

// ---------------------------------------------------------------------------
// 4.  FIXED FOURTH WHEEL  --  THE SUN OF THE EPICYCLIC.
//     It does NOT rotate.  It is bolted to the main plate on a stub arbor and
//     sits exactly concentric with the carriage axis; the escape pinion, which
//     is carried by the carriage, rolls around it.  That single fact is what
//     closes the kinematics:
//
//         omega_escape/carriage = z4 / zEP = 40/10 = 4.0
//         omega_carriage        = f * zEP / (zE * z4) = 1 * 10 / (15 * 40)
//                               = 1/60 rev/s = EXACTLY 1 rpm
//
//     If it were free to turn, the escapement would receive no drive at all.
// ---------------------------------------------------------------------------
module fixed_fourth_wheel() {
    color(C_PINION)
    translate([POS_FIXED_FOURTH[0], POS_FIXED_FOURTH[1], 0])
        // no rotate(): this member is stationary by definition
        linear_extrude(height = thk(ZR_FIXED_FOURTH), convexity = 14)
            translate([0, 0])
                if (SHOW_GEAR_TEETH)
                    gear_cycloidal_2d(M_FIXED_FOURTH, Z_FIXED_FOURTH,
                                      CYCLO_RR_EPICYCLIC, GEAR_BACKLASH,
                                      bore = fit(ARBOR_FIXED4_D));
                else
                    difference() {
                        circle(r = pitch_r(M_FIXED_FOURTH, Z_FIXED_FOURTH));
                        circle(d = fit(ARBOR_FIXED4_D));
                    }
}

module fixed_fourth_stub() {
    // stub arbor + boss + two screws into the main plate.  This is the reaction
    // member for the whole escapement, so it is bolted, not pressed.
    color(C_ARBOR)
    translate([POS_FIXED_FOURTH[0], POS_FIXED_FOURTH[1], 0]) {
        // the stub itself, plus a wider root that the two plate screws clamp
        cylinder(d = ARBOR_FIXED4_D, h = dz(ZR_FIXED_FOURTH) + thk(ZR_FIXED_FOURTH));
        translate([0, 0, dz(ZR_FIXED_FOURTH) - 2.0])
            cylinder(d = ARBOR_FIXED4_D + 4.0, h = 2.0);
    }
}

// ---------------------------------------------------------------------------
// 5.  CONVENIENCE GROUPS
// ---------------------------------------------------------------------------
module going_train(show_teeth = SHOW_GEAR_TEETH) {
    translate([POS_GREAT_WHEEL[0], POS_GREAT_WHEEL[1], 0]) {
        great_wheel(show_teeth); great_pinion(show_teeth); great_wheel_arbor();
    }
    centre_wheel(show_teeth); centre_pinion(show_teeth); centre_arbor();
    intermediate_wheel(show_teeth); intermediate_pinion(show_teeth);
    intermediate_arbor();
    fixed_fourth_wheel(); fixed_fourth_stub();
}
