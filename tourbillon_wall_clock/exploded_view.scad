// ===========================================================================
//  exploded_view.scad  --  the same parts as assembly.scad, pulled apart along
//                          Z in ASSEMBLY ORDER.
//
//  The offsets below are not cosmetic: they are the sequence a watchmaker
//  actually has to follow, because later parts can only be reached once earlier
//  ones are in.  Read top to bottom and you have the build order; the same
//  order is written out as prose in docs/ASSEMBLY.md.
//
//      1  back cover, wall mount              (nothing depends on them)
//      2  main plate                          (the datum: z = 0 is its face)
//      3  barrel arbor + bushes, fixed fourth (pressed / bolted into the plate)
//      4  great wheel arbor, intermediate arbor, motion-works stud
//      5  mainspring into the drum, then the drum onto the arbor
//      6  going train wheels and pinions
//      7  motion works
//      8  carriage: floor, rim gear, columns, then the escapement inside it,
//         then the upper bridge and cap  --  this sub-assembly is built and
//         POISED OFF THE CLOCK, then dropped onto its axis
//      9  pillars, then the top bridge
//     10  dial ring, hands, case, crystal
//
//  EXPLODE_FACTOR scales every offset, so the view can be tightened for a
//  drawing or opened up for a presentation.  EXPLODED_VIEW in parameters.scad
//  turns it on globally.
// ===========================================================================

include <parameters.scad>
include <assembly.scad>

// ---------------------------------------------------------------------------
// Exploded offsets, in millimetres along +Z, per assembly stage.
// The stage numbers above are the indices.
// ---------------------------------------------------------------------------
EXPLODE_STEP = [
     0.0,     // 0  reference: nothing moves
   -46.0,     // 1  back cover and wall mount go BACK
     0.0,     // 2  main plate stays: it is the datum
    14.0,     // 3  barrel arbor, bushes, fixed fourth stub
    24.0,     // 4  the three plain arbors and the motion-works stud
    40.0,     // 5  mainspring + barrel drum + cover + ratchet
    56.0,     // 6  going train wheels and pinions
    72.0,     // 7  motion works
    96.0,     // 8  the whole carriage sub-assembly
   132.0,     // 9  pillars and top bridge
   168.0      // 10 dial, hands, case, crystal
];

function ex(stage) = EXPLODE_STEP[stage] * EXPLODE_FACTOR;

// ---------------------------------------------------------------------------
// The carriage explodes internally as well: its own stack is 18 mm tall and the
// escapement is unreachable unless the upper bridge, cap and balance come off
// first.  These are LOCAL offsets added on top of ex(8).
// ---------------------------------------------------------------------------
CAR_EXLODE = [
    ["seconds pointer",      34.0],
    ["carriage top cap",     30.0],
    ["balance endstone",     26.0],
    ["carriage upper bridge",22.0],
    ["hairspring",           17.0],
    ["balance wheel",        13.0],
    ["roller",                9.0],
    ["pallet lever",          6.0],
    ["escape wheel",          3.0],
    ["carriage columns",      0.0],
    ["carriage floor",        0.0],
    ["carriage rim gear",    -4.0],
    ["escape pinion",        -8.0]
];

function car_ex(name) =
    let (h = [for (e = CAR_EXLODE) if (e[0] == name) e[1]])
    (len(h) > 0 ? h[0] : 0.0) * EXPLODE_FACTOR;

// ---------------------------------------------------------------------------
// STAGE 1 -- back cover and wall mount
// ---------------------------------------------------------------------------
module exploded_stage1() {
    translate([0, 0, ex(1)]) {
        back_cover();
        wall_mount();
    }
}

// ---------------------------------------------------------------------------
// STAGE 2 -- main plate (the datum, does not move)
// ---------------------------------------------------------------------------
module exploded_stage2() {
    main_plate();
}

// ---------------------------------------------------------------------------
// STAGE 3 -- everything pressed or bolted into the plate
// ---------------------------------------------------------------------------
module exploded_stage3() {
    translate([0, 0, ex(3)]) {
        barrel_bearings();
        fixed_fourth_stub();
        fixed_fourth_wheel();
        plate_jewels();
    }
}

// ---------------------------------------------------------------------------
// STAGE 4 -- the plain arbors
// ---------------------------------------------------------------------------
module exploded_stage4() {
    translate([0, 0, ex(4)]) {
        shaft_S02_great_arbor();
        shaft_S03_intermediate_arbor();
        shaft_S01_centre_arbor();
        centre_arbor();
        intermediate_arbor();
        great_wheel_arbor();
        shaft_S05_motion_stud();
    }
}

// ---------------------------------------------------------------------------
// STAGE 5 -- the barrel
// ---------------------------------------------------------------------------
module exploded_stage5() {
    translate([POS_BARREL[0], POS_BARREL[1], ex(5)]) {
        mainspring_coils();
        barrel_drum();
        barrel_cover();
        barrel_arbor();
        ratchet_wheel();
        click();
        click_spring();
        winding_sleeve();
    }
}

// ---------------------------------------------------------------------------
// STAGE 6 -- going train
// ---------------------------------------------------------------------------
module exploded_stage6() {
    translate([0, 0, ex(6)]) {
        translate([POS_GREAT_WHEEL[0], POS_GREAT_WHEEL[1], 0]) {
            great_wheel(); great_pinion();
        }
        centre_wheel(); centre_pinion();
        intermediate_wheel(); intermediate_pinion();
    }
}

// ---------------------------------------------------------------------------
// STAGE 7 -- motion works
// ---------------------------------------------------------------------------
module exploded_stage7() {
    translate([0, 0, ex(7)]) motion_works();
}

// ---------------------------------------------------------------------------
// STAGE 8 -- the carriage, exploded internally
// ---------------------------------------------------------------------------
module exploded_stage8() {
    translate([POS_CARRIAGE[0], POS_CARRIAGE[1], Z_CARRIAGE_Z0 + ex(8)]) {
        shaft_S04_carriage_axis();
        translate([0, 0, car_ex("carriage rim gear")])   carriage_rim_gear();
        translate([0, 0, car_ex("carriage floor")])      carriage_floor();
        translate([0, 0, car_ex("carriage floor")])      carriage_counter_mass();
        translate([0, 0, car_ex("carriage rim gear")])   carriage_rim_band();
        translate([0, 0, car_ex("carriage columns")])    carriage_columns();
        // --- the escapement, each member on its own ---
        translate([ESC_POS[0], ESC_POS[1], car_ex("escape pinion")])
            rotate(-ang_escape_rel()) escape_pinion();
        translate([ESC_POS[0], ESC_POS[1], car_ex("escape wheel")])
            rotate(-ang_escape_rel()) { escape_wheel(); escape_arbor_upper(); }
        translate([PAL_POS[0], PAL_POS[1], car_ex("pallet lever")])
            pallet_lever();
        translate([PAL_POS[0], PAL_POS[1], car_ex("pallet lever")])
            pallet_arbor();
        translate([BAL_POS[0], BAL_POS[1], car_ex("roller")])
            roller();
        translate([BAL_POS[0], BAL_POS[1], car_ex("balance wheel")]) {
            balance_wheel(); balance_staff();
        }
        translate([BAL_POS[0], BAL_POS[1], car_ex("hairspring")]) {
            hairspring(); hairspring_stud();
        }
        translate([0, 0, car_ex("carriage upper bridge")]) carriage_upper_bridge();
        translate([0, 0, car_ex("carriage upper bridge")]) carriage_jewels();
        translate([BAL_POS[0], BAL_POS[1], car_ex("balance endstone")])
            balance_endstone();
        translate([0, 0, car_ex("carriage top cap")])      carriage_top_cap();
        translate([0, 0, car_ex("seconds pointer")])       seconds_pointer();
    }
}

// ---------------------------------------------------------------------------
// STAGE 9 -- pillars and top bridge
// ---------------------------------------------------------------------------
module exploded_stage9() {
    translate([0, 0, ex(9)]) {
        pillars();
        carriage_bearings();
        top_bridge();
        bridge_jewels();
        bridge_jewels_set();
    }
}

// ---------------------------------------------------------------------------
// STAGE 10 -- dial, hands, case, crystal
// ---------------------------------------------------------------------------
module exploded_stage10() {
    translate([0, 0, ex(10)]) {
        dial_ring();
        hour_pipe();
        minute_pipe();
        hour_hand();
        minute_hand();
        case_ring();
        crystal();
    }
}

// ---------------------------------------------------------------------------
// THE WHOLE EXPLODED VIEW
// ---------------------------------------------------------------------------
module exploded_view() {
    exploded_stage1();
    exploded_stage2();
    exploded_stage3();
    exploded_stage4();
    exploded_stage5();
    exploded_stage6();
    exploded_stage7();
    exploded_stage8();
    exploded_stage9();
    exploded_stage10();
}

// ---------------------------------------------------------------------------
// Assembly-order labels, for a drawing.  These are text in the model space so a
// projection of the exploded view can be annotated without a separate step.
// ---------------------------------------------------------------------------
module exploded_labels() {
    LABELS = [
        [ 1, "1  back cover, wall mount"],
        [ 2, "2  MAIN PLATE (datum, z = 0)"],
        [ 3, "3  barrel bushes, fixed fourth wheel"],
        [ 4, "4  arbors"],
        [ 5, "5  mainspring, barrel drum, ratchet"],
        [ 6, "6  going train"],
        [ 7, "7  motion works"],
        [ 8, "8  TOURBILLON CARRIAGE (poise off the clock)"],
        [ 9, "9  pillars, top bridge"],
        [10, "10 dial, hands, case, crystal"]
    ];
    for (row = LABELS)
        translate([-PLATE_RADIUS - 18, 0, ex(row[0]) + MOVEMENT_Z_MIN])
            rotate([90, 0, 90])
                linear_extrude(height = 0.6)
                    text(row[1], size = 9, halign = "left", valign = "center");
}

module exploded_view_annotated() {
    exploded_view();
    exploded_labels();
}

if (EXPLODED_VIEW) exploded_view_annotated();
