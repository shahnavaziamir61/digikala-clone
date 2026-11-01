// ===========================================================================
//  dial_and_case.scad  --  dial ring, hands, case, crystal and wall mounting.
//
//  The dial is a RING, not a disc: the 296 mm aperture is what makes the
//  tourbillon visible from the front, which is the central requirement of the
//  brief.  The chapter ring carries the hour markers and the minute track;
//  seconds are read directly off the carriage, because the carriage turns once
//  per minute (derived, not assumed -- see tourbillon_cage.scad).
//
//  Functional / decorative split, as required:
//     dial ring        Functional (carries the hour markers that the hands
//                               read against; dimensioned from DIAL_APERTURE)
//     hour hand        Functional
//     minute hand      Functional
//     crystal          Functional (seals the movement; seats in the case ring)
//     case ring        Functional (carries the crystal and the wall mount)
//     wall mount       Functional (carries the whole clock plus winding load)
//     bezel finish     Decorative
//     back cover       Decorative (dust cover; carries no load, no tolerance)
// ===========================================================================

include <parameters.scad>

// ---------------------------------------------------------------------------
// 4.  DIAL RING  --  z = 26 .. 28.
//     A RING, not a disc: the 296 mm aperture is what makes the tourbillon
//     visible from the front, which is the central requirement of the brief.
//     The chapter ring carries the hour markers and the minute track; the
//     carriage is read directly, since it turns once a minute.
// ---------------------------------------------------------------------------
DIAL_RING_ID = 232;      // leaves a 32 mm wide chapter ring at the rim
module dial_ring() {
    if (!SHOW_DIAL) ;
    else color(C_DIAL)
        translate([0, 0, dz(ZR_DIAL_RING)])
            difference() {
                cylinder(d = DIAL_APERTURE, h = thk(ZR_DIAL_RING));
                translate([0, 0, -EPS])
                    cylinder(d = DIAL_RING_ID, h = thk(ZR_DIAL_RING) + 2 * EPS);
                // hour markers
                for (i = [0:11]) rotate(i * 30)
                    translate([DIAL_APERTURE / 2 - 14, 0, thk(ZR_DIAL_RING) - 0.4])
                        cube([8, i % 3 == 0 ? 3.6 : 2.0, 0.4 + EPS], center = true);
                // minute track
                for (i = [0:59]) rotate(i * 6)
                    translate([DIAL_APERTURE / 2 - 5.5, 0, thk(ZR_DIAL_RING) - 0.25])
                        cube([3, i % 5 == 0 ? 1.2 : 0.6, 0.25 + EPS], center = true);
            }
}

// ---------------------------------------------------------------------------
// 5.  HANDS  --  z = 28.5 .. 31.5, on the hour pipe (9 mm) and minute pipe
//     (6 mm).  The hour hand is driven at exactly 1/12 of the minute hand by
//     the motion works ((64/16) x (48/16) = 12.000, checked by C-07).
// ---------------------------------------------------------------------------
module hour_hand() {
    color(C_HANDS)
    translate([0, 0, dz(ZR_HANDS)])
        rotate(-ang_hour()) {
            hull() {
                cylinder(d = 9.0, h = 1.4);
                translate([0, 96, 0]) cylinder(d = 5.0, h = 1.4);
            }
            translate([0, -26, 0]) cylinder(d = 7.0, h = 1.4);   // counterpoise
        }
}

module minute_hand() {
    color(C_HANDS)
    translate([0, 0, dz(ZR_HANDS) + 1.6])
        rotate(-ang_centre()) {
            hull() {
                cylinder(d = 6.0, h = 1.4);
                translate([0, 132, 0]) cylinder(d = 3.4, h = 1.4);
            }
            translate([0, -34, 0]) cylinder(d = 5.0, h = 1.4);
        }
}

// ---------------------------------------------------------------------------
// 6.  CASE, CRYSTAL AND WALL MOUNTING
//     STATUS: Decorative for the bezel finish; functional for the crystal seat
//     and the wall mount, which do carry load.
// ---------------------------------------------------------------------------
module case_ring() {
    if (!SHOW_CASE) ;
    else color(C_CASE)
        translate([0, 0, dz(ZR_CRYSTAL) - 6])
            difference() {
                cylinder(d = CLOCK_DIAMETER, h = thk(ZR_CRYSTAL) + 6);
                translate([0, 0, -EPS])
                    cylinder(d = DIAL_APERTURE, h = thk(ZR_CRYSTAL) + 8 * EPS);
                // rear fixing points
                for (i = [0:5]) rotate(i * 60 + 30)
                    translate([132, 0, -EPS])
                        cylinder(d = SCREW_CLEARANCE, h = thk(ZR_CRYSTAL) + 2 * EPS);
            }
}

module crystal() {
    if (!SHOW_CRYSTAL) ;
    else color(C_CRYSTAL)
        translate([0, 0, dz(ZR_CRYSTAL)])
            difference() {
                cylinder(d = DIAL_APERTURE + 2, h = 3.0);
                translate([0, 0, 3.0]) scale([1, 1, 0.35])
                    sphere(d = DIAL_APERTURE + 2);   // a slight dome
            }
}

module wall_mount() {
    // STATUS: functional.  The clock is 55.5 mm thick and roughly 1.9 kg with a
    // brass plate; the mount has to take that plus the winding load.  Two
    // 5 mm keyhole slots on a 200 mm spacing, into a plate that bolts to the
    // rear of the case.
    color(C_CASE)
    translate([0, 0, ZR_MAIN_PLATE[0] - 4])
        difference() {
            hull() {
                translate([-100, 60, 0]) cylinder(d = 24, h = 4);
                translate([ 100, 60, 0]) cylinder(d = 24, h = 4);
                translate([   0, -20, 0]) cylinder(d = 24, h = 4);
            }
            for (p = [[-100, 60], [100, 60], [0, -20]])
                translate([p[0], p[1], -EPS]) {
                    cylinder(d = 5.0, h = 4 + 2 * EPS);
                    translate([0, 6, 0]) cylinder(d = 9.0, h = 4 + 2 * EPS);
                    translate([0, 3, 0]) cube([9.0, 6, 4 + 2 * EPS], center = true);
                }
        }
}

module back_cover() {
    // STATUS: Decorative.  A dust cover; it carries no load and no tolerance.
    color(C_CASE)
    translate([0, 0, ZR_BARREL_COVER[0] - 2.5])
        difference() {
            cylinder(d = CLOCK_DIAMETER, h = 2.5);
            for (i = [0:5]) rotate(i * 60 + 30)
                translate([132, 0, -EPS])
                    cylinder(d = SCREW_CLEARANCE, h = 2.5 + 2 * EPS);
        }
}
