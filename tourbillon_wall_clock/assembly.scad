// ===========================================================================
//  assembly.scad  --  the complete clock, every part in its true position.
//
//  Coordinate contract, the same in every file of this project:
//      units  mm
//      origin the centre-wheel axis, in the plane of the FRONT face of the
//             main plate (that face is z = 0)
//      +Y     12 o'clock
//      +Z     towards the dial, i.e. towards the viewer
//  So the default front view is looking down -Z at the dial, which is what the
//  brief asks for, and the tourbillon carriage is visible through the 296 mm
//  dial aperture at (0, -63.3).
//
//  WHAT THIS FILE DOES AND DOES NOT PROVE.
//  It proves position: every axis is at its theoretical centre distance, every
//  part is in its validated Z band, and the 45 checks in tools/calc.py plus the
//  77 profile measurements in tools/profile_check.py cover interference,
//  envelope, tooth conjugacy, contact ratio, spring stress, torque, run time,
//  poise and wall thickness.
//  It does NOT prove the clock keeps time.  Nothing in a CAD model can.  See
//  docs/LIMITATIONS.md.
// ===========================================================================

include <parameters.scad>
include <mainspring_barrel.scad>
include <wheel_train.scad>
include <motion_works.scad>
include <tourbillon_cage.scad>
include <shafts_and_bearings.scad>
include <bridges_and_plates.scad>
include <dial_and_case.scad>

// ---------------------------------------------------------------------------
// 1.  THE MOVEMENT  --  plates, train, barrel, motion works, carriage
// ---------------------------------------------------------------------------
module movement(show_teeth = SHOW_GEAR_TEETH,
                show_spring = true,
                show_hairspring = true,
                angle_balance_deg = 0,
                angle_lever_deg = 0) {
    // ---- static structure ----
    main_plate();
    pillars();

    // ---- power ----
    barrel_assembly(show_spring = show_spring);

    // ---- going train ----
    going_train(show_teeth);

    // ---- hand train ----
    motion_works(show_teeth);

    // ---- the tourbillon ----
    //  The carriage is placed by tourbillon_cage.scad at POS_CARRIAGE, which is
    //  also POS_FIXED_FOURTH: the two must be concentric or the epicyclic does
    //  not close (C-04).  The fixed fourth wheel itself is drawn by
    //  wheel_train.scad and does NOT rotate.
    tourbillon_carriage(show_teeth, show_hairspring,
                        ang_carriage(), angle_balance_deg, angle_lever_deg);

    // ---- bearings and arbors ----
    shafts_and_bearings();

    // ---- upper structure, drawn last so the windows read correctly ----
    top_bridge();
    bridge_jewels();
}

// ---------------------------------------------------------------------------
// 2.  THE COMPLETE CLOCK
// ---------------------------------------------------------------------------
module clock_assembly(show_teeth = SHOW_GEAR_TEETH) {
    movement(show_teeth);
    dial_ring();
    hour_hand();
    minute_hand();
    case_ring();
    crystal();
    wall_mount();
    back_cover();
}

// ---------------------------------------------------------------------------
// 3.  VIEWS.  Set VIEW in parameters.scad or on the command line:
//       openscad -D 'VIEW="back"' assembly.scad
//     A view is a camera transform only; it does not move any part.
// ---------------------------------------------------------------------------
module view_front() { clock_assembly(); }                 // looking down -Z

module view_back() {                                      // looking down +Z
    rotate([0, 180, 0]) clock_assembly();
}

module view_side() {                                      // looking along -X
    rotate([0, -90, 0]) clock_assembly();
}

module view_top() {                                       // looking down -Y
    rotate([-90, 0, 0]) clock_assembly();
}

module view_iso() {
    rotate([55, 0, 30]) clock_assembly();
}

module view_tourbillon() {
    // close-up of the carriage from the dial side, which is the whole point of
    // the design: the tourbillon must be visible from the front.
    translate([-POS_CARRIAGE[0], -POS_CARRIAGE[1], 0])
        rotate([18, 0, 0])
            clock_assembly();
}

module view_by_name(name = VIEW) {
    name == "back"        ? view_back() :
    name == "side"        ? view_side() :
    name == "top"         ? view_top() :
    name == "iso"         ? view_iso() :
    name == "tourbillon"  ? view_tourbillon() :
                            view_front();
}

// ---------------------------------------------------------------------------
// 4.  CROSS SECTION  --  cuts the model with a plane through the carriage axis
//     so the Z stack can be read directly.  Useful for checking that the
//     thickness budget in parameters.scad is what was actually built.
// ---------------------------------------------------------------------------
module section_cut(angle = SECTION_ANGLE) {
    difference() {
        clock_assembly();
        rotate([0, 0, angle])
            translate([0, -2000, MOVEMENT_Z_MIN - 10])
                cube([2000, 4000, MOVEMENT_THICKNESS + 200]);
    }
}

// ---------------------------------------------------------------------------
// 5.  ENTRY POINT for this file on its own
// ---------------------------------------------------------------------------
if (CROSS_SECTION) section_cut();
else               view_by_name(VIEW);
