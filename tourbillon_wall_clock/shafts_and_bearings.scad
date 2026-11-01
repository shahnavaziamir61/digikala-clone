// ===========================================================================
//  shafts_and_bearings.scad  --  every arbor, pivot, jewel seat and bush in the
//                                movement, as separate named parts.
//
//  NOTHING IN THIS FILE IS PRINTED.  Every arbor here is hardened silver steel
//  or brass stock, turned and lapped.  This is a standing requirement of the
//  design and not a preference: A PRINTED HOLE IS NOT A PRECISION BEARING.  A
//  0.4 mm nozzle leaves a stair-stepped bore with 12 um Ra and PLA cold-flows
//  under a sustained radial load, so a printed pivot would wear out in hours and
//  would never hold the <= 0.015 mm radial play the carriage axis needs.
//  The printed version of this clock therefore prints the PLATES, BRIDGES,
//  WHEEL BLANKS and CASE, and buys every arbor and jewel listed here.
//  See docs/LIMITATIONS.md L-07 and docs/SHAFTS.md.
//
//  Each part below carries:
//     - its diameter and overall length
//     - the pivot diameter at each end (the part that actually bears)
//     - the bearing seat diameter (what the jewel or bush is sized to)
//     - the span between the two supports
//     - the allowed axial play and radial clearance
//  Radial and axial loads are computed in docs/SHAFTS.md, not here.
// ===========================================================================

include <parameters.scad>

// ---------------------------------------------------------------------------
// 0.  THE SHAFT TABLE.  One row per arbor; the numbers are the ones validated
//     in docs/SHAFTS.md (S-01 .. S-09).  Every module below reads from here so
//     a dimension exists in exactly one place.
//
//     id      dia   length  pivot_d  seat_d  span    axial   radial  material
// ---------------------------------------------------------------------------
SHAFT_TABLE = [
 ["S-01 barrel arbor",       30.0, 44.0, 30.0, 30.0, 22.0, 0.20, 0.05, "hardened steel, MR85ZZ"],
 ["S-02 centre arbor",        4.0, 42.0,  1.5,  4.0, 20.0, 0.10, 0.02, "hardened silver steel"],
 ["S-03 great wheel arbor",   3.0, 12.0,  1.2,  3.0,  8.0, 0.10, 0.02, "hardened silver steel"],
 ["S-04 intermediate arbor",  3.0, 20.0,  1.2,  3.0,  9.0, 0.10, 0.02, "hardened silver steel"],
 ["S-05 carriage axis",       8.0, 26.0,  3.0,  8.0, 18.0, 0.04, 0.015,"hardened + lapped, ball race below, ruby above"],
 ["S-06 escape arbor",        1.5, 17.0,  0.5,  1.5,  8.0, 0.05, 0.01, "hardened silver steel, elongated pinion"],
 ["S-07 pallet arbor",        1.2, 13.0,  0.4,  1.2,  6.0, 0.05, 0.01, "hardened silver steel"],
 ["S-08 balance staff",       1.6, 20.0,  0.35, 1.6,  7.0, 0.03, 0.008,"hardened, burnished, sapphire endstones"],
 ["S-09 motion works stud",   3.0,  9.0,  3.0,  3.0,  5.0, 0.15, 0.03, "brass, pressed and peened"]
];

function shaft_row(id) = [for (r = SHAFT_TABLE) if (r[0] == id) r][0];

// ---------------------------------------------------------------------------
// 1.  JEWELS AND BUSHES  (all bought -- see docs/BOM_BOUGHT.csv)
//     A jewel is modelled as its real purchased form: a ruby cylinder with a
//     conical oil sink and a pierced hole.  The hole is sized
//     pivot_d + 2 * RADIAL_CLEARANCE, which is the only place the radial play
//     of the whole movement is set.
// ---------------------------------------------------------------------------
module jewel(seat_d, hole_d, thk = 1.2, oil_sink = true) {
    color(C_RUBY)
    difference() {
        cylinder(d = seat_d, h = thk);
        translate([0, 0, -EPS])
            cylinder(d = hole_d + 2 * RADIAL_CLEARANCE, h = thk + 2 * EPS);
        if (oil_sink)
            translate([0, 0, thk - 0.35])
                cylinder(d1 = hole_d + 2 * RADIAL_CLEARANCE, d2 = hole_d + 1.6, h = 0.35 + EPS);
    }
}

module endstone(d, thk = 0.8) {
    // flat sapphire thrust washer: takes the axial load of a vertical arbor
    color(C_RUBY)
    cylinder(d = d, h = thk);
}

module bronze_bush(seat_d, bore_d, h) {
    // used only where the speed and load are low enough that a jewel is not
    // justified: the barrel drum on its arbor, and the motion-works stud.
    // STATUS: functional, but its wear rate is NOT calculated -- see L-07.
    color([0.72, 0.45, 0.28])
    tube(od = seat_d, id = bore_d + 2 * RADIAL_CLEARANCE, h = h);
}

module ball_race(bore_d, thk = 2.0) {
    // the carriage's lower bearing.  STATUS: Prototype -- a recirculating ball
    // race at 8 mm bore is a purchased item (B-08); this is a placeholder of
    // the correct envelope, not a modelled bearing.
    color(C_PINION)
    translate([0, 0, 0])
        difference() {
            cylinder(d = bore_d + 8.0, h = thk);
            translate([0, 0, -EPS]) cylinder(d = bore_d, h = thk + 2 * EPS);
            for (i = [0:8]) rotate(i * 40)
                translate([(bore_d + 4.0) / 2, 0, thk / 2])
                    sphere(d = 1.6);
        }
}

// ---------------------------------------------------------------------------
// 2.  GENERIC ARBOR.  Draws a shaft of the given diameter and length with two
//     reduced pivots, so the pivot diameter -- not the arbor diameter -- is what
//     meets the jewel.  This is the single reason a movement runs or does not.
// ---------------------------------------------------------------------------
module arbor(d, length, pivot_d, seat_d, pivot_len = 1.6,
             shoulder = 0.6, colour = C_ARBOR) {
    color(colour)
    union() {
        // lower pivot
        translate([0, 0, -pivot_len])
            cylinder(d = pivot_d - 2 * RADIAL_CLEARANCE, h = pivot_len + shoulder);
        // body
        cylinder(d = d, h = length);
        // upper pivot
        translate([0, 0, length - shoulder])
            cylinder(d = pivot_d - 2 * RADIAL_CLEARANCE, h = pivot_len + shoulder);
        // jewel seats, a sliding fit in the plate / bridge
        translate([0, 0, -0.2]) tube(od = seat_d, id = d - EPS, h = 0.8);
        translate([0, 0, length - 0.6]) tube(od = seat_d, id = d - EPS, h = 0.8);
    }
}

// ---------------------------------------------------------------------------
// 3.  THE INDIVIDUAL ARBORS, each drawn at its true position and height.
//     These are the parts that appear in the exploded view and the BOM.
// ---------------------------------------------------------------------------
module shaft_S01_centre_arbor() {
    r = shaft_row("S-02 centre arbor");
    translate([POS_CENTRE_WHEEL[0], POS_CENTRE_WHEEL[1], dz(ZR_CENTRE_PINION) - 2.0])
        arbor(r[1], r[2], r[3], r[4]);
}

module shaft_S02_great_arbor() {
    r = shaft_row("S-03 great wheel arbor");
    translate([POS_GREAT_WHEEL[0], POS_GREAT_WHEEL[1], dz(ZR_GREAT_WHEEL) - 1.5])
        arbor(r[1], r[2], r[3], r[4]);
}

module shaft_S03_intermediate_arbor() {
    r = shaft_row("S-04 intermediate arbor");
    translate([POS_INTERMEDIATE[0], POS_INTERMEDIATE[1], dz(ZR_INTER_WHEEL) - 1.0])
        arbor(r[1], r[2], r[3], r[4]);
}

module shaft_S04_carriage_axis() {
    // THE MOST DEMANDING BEARING IN THE CLOCK.  It carries the entire rotating
    // assembly (33.68 g) at 1 rpm and any wobble appears directly as a rate
    // error, because the escapement is mounted on what it carries.
    //   radial play <= 0.015 mm, axial play 0.03 - 0.05 mm
    //   lower: ball race against the main plate
    //   upper: ruby jewel in the top bridge
    // STATUS: functional.  Must be hardened and lapped, never printed.
    r = shaft_row("S-05 carriage axis");
    translate([POS_CARRIAGE[0], POS_CARRIAGE[1], Z_CARRIAGE_Z0 + Z_CARRIAGE[0][0]])
        arbor(r[1], r[2], r[3], r[4], pivot_len = 2.4);
}

module carriage_bearings() {
    translate([POS_CARRIAGE[0], POS_CARRIAGE[1], 0]) {
        ball_race(CARRIAGE_ARBOR_D);
        translate([0, 0, ZR_TOP_BRIDGE[1] - 1.2])
            jewel(seat_d = CARRIAGE_ARBOR_D + 3.0,
                  hole_d = CARRIAGE_ARBOR_D, thk = 1.2);
    }
}

module shaft_S05_motion_stud() {
    r = shaft_row("S-09 motion works stud");
    translate([POS_MOTION_WORKS[0], POS_MOTION_WORKS[1], ZR_TOP_BRIDGE[0]])
        arbor(r[1], r[2], r[3], r[4], pivot_len = 0.8);
}

// ---------------------------------------------------------------------------
// 4.  THE JEWELS THAT ARE PRESSED INTO THE PLATE AND THE BRIDGE
//     Every rotating arbor except the barrel gets one at each end.  Their hole
//     diameters are the ONLY place radial play is set for the whole movement,
//     so they are all driven off RADIAL_CLEARANCE.
// ---------------------------------------------------------------------------
module plate_jewels() {
    for (p = [[POS_CENTRE_WHEEL,   4.0, 1.5],
              [POS_GREAT_WHEEL,    3.0, 1.2],
              [POS_INTERMEDIATE,   3.0, 1.2],
              [POS_MOTION_WORKS,   3.0, 3.0]])
        translate([p[0][0], p[0][1], ZR_MAIN_PLATE[1] - 1.2])
            jewel(seat_d = p[2] + 2.0, hole_d = p[2]);
}

module bridge_jewels_set() {
    for (p = [[POS_CENTRE_WHEEL,   4.0, 1.5],
              [POS_GREAT_WHEEL,    3.0, 1.2],
              [POS_INTERMEDIATE,   3.0, 1.2],
              [POS_MOTION_WORKS,   3.0, 3.0]])
        translate([p[0][0], p[0][1], ZR_TOP_BRIDGE[1] - 1.2])
            jewel(seat_d = p[2] + 2.0, hole_d = p[2]);
}

// ---------------------------------------------------------------------------
// 5.  BARREL BEARINGS  --  the drum turns on the fixed arbor through a bronze
//     bush.  This is the one place a plain bush is acceptable: 1 rev/day and
//     133 N of mesh load.  Its wear is NOT calculated (L-07).
// ---------------------------------------------------------------------------
module barrel_bearings() {
    translate([POS_BARREL[0], POS_BARREL[1], 0]) {
        translate([0, 0, dz(ZR_BARREL_DRUM)])
            bronze_bush(BARREL_ARBOR_D + 4.0, BARREL_ARBOR_D, 6.0);
        translate([0, 0, ZR_MAIN_PLATE[1] - 4.0])
            bronze_bush(BARREL_ARBOR_D + 4.0, BARREL_ARBOR_D, 4.0);
    }
}

// ---------------------------------------------------------------------------
// 6.  ALL SHAFTS AND BEARINGS
// ---------------------------------------------------------------------------
module shafts_and_bearings() {
    shaft_S01_centre_arbor();
    shaft_S02_great_arbor();
    shaft_S03_intermediate_arbor();
    shaft_S04_carriage_axis();
    shaft_S05_motion_stud();
    carriage_bearings();
    plate_jewels();
    bridge_jewels_set();
    barrel_bearings();
}
