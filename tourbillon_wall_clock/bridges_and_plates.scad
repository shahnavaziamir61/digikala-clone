// ===========================================================================
//  bridges_and_plates.scad  --  main plate, top bridge (skeleton), pillars and
//                               the jewel seats that hold the train.
//
//  The dial, the hands, the case, the crystal and the wall mounting live in
//  dial_and_case.scad.
//
//  The plate and the bridge are the parts that make every other dimension
//  real: the centre distances in parameters_auto.scad are only achievable if
//  the bearing holes are cut in the right places at the right size, and the
//  windows are only legal if the parts that pass through them actually fit.
//  calc.py checks both:
//     C-16  every member fits inside the 296 mm plate envelope
//     C-17  every placed axis equals its theoretical centre distance
//     C-18  no two members collide, in XY and in Z
//     C-18b every bridge window is at least 1 mm larger in diameter than the
//           union of the members explicitly declared to pass through it
//     C-18c nothing enters the volume the carriage sweeps as it turns
//
//  The top bridge is deliberately modelled as a FULL 296 mm disc with windows
//  cut in it, rather than as a skeleton of arms.  That is what makes C-18b
//  meaningful: a window can only be proven to exist if there is material around
//  it.  The hour and minute pipes pass through the declared "centre pipes"
//  window, which C-18b sizes at 13 mm against a 9 mm hour pipe.
// ===========================================================================

include <parameters.scad>

// ---------------------------------------------------------------------------
// 1.  MAIN PLATE  --  296 mm across, 5 mm thick, z = -5 .. 0.
//     z = 0 is its FRONT face; everything in the movement is dimensioned from
//     that datum, which is why the whole Z stack in parameters_auto.scad is
//     quoted relative to it.
// ---------------------------------------------------------------------------
module main_plate() {
    color(C_PLATE)
    translate([0, 0, dz(ZR_MAIN_PLATE)])
        difference() {
            union() {
                cylinder(d = 2 * PLATE_RADIUS, h = thk(ZR_MAIN_PLATE));
                // bearing pillars on the front face: the plate is 5 mm thick
                // but several arbors need a longer bearing span than that, so
                // the seats are raised.  Span values are in docs/SHAFTS.md.
                for (p = [POS_CENTRE_WHEEL, POS_GREAT_WHEEL, POS_INTERMEDIATE,
                          POS_MOTION_WORKS])
                    translate([p[0], p[1], thk(ZR_MAIN_PLATE)])
                        tube(od = BEARING_SEAT_DIAMETER + 3.0,
                             id = fit(SHAFT_DIAMETER), h = 1.6);
                // the fixed fourth wheel's stub boss, bolted here
                translate([POS_FIXED_FOURTH[0], POS_FIXED_FOURTH[1],
                           thk(ZR_MAIN_PLATE)])
                    cylinder(d = FIXED_4TH_BOSS_D + 4.0, h = 1.5);
            }
            // ---- windows / passages ----
            for (w = PLATE_WINDOWS)
                translate([w[0], w[1], -EPS])
                    cylinder(d = w[2], h = thk(ZR_MAIN_PLATE) + 2 * EPS);
            // ---- carriage bearing race: the carriage sleeve arbor runs here ----
            translate([POS_CARRIAGE[0], POS_CARRIAGE[1], -EPS])
                cylinder(d = fit(CARRIAGE_ARBOR_D) + 2 * RADIAL_CLEARANCE,
                         h = thk(ZR_MAIN_PLATE) + 2 * EPS);
            // ---- barrel arbor seat (the arbor is FIXED to the plate) ----
            translate([POS_BARREL[0], POS_BARREL[1], -EPS])
                cylinder(d = fit(BARREL_ARBOR_D * 0.5),
                         h = thk(ZR_MAIN_PLATE) + 2 * EPS);
            // ---- case / pillar screws, on a 132 mm bolt circle ----
            for (i = [0:5]) rotate(i * 60 + 30)
                translate([132, 0, -EPS])
                    cylinder(d = SCREW_CLEARANCE, h = thk(ZR_MAIN_PLATE) + 2 * EPS);
            // ---- bridge pillar screws ----
            for (a = [0, 72, 144, 216, 288]) rotate(a)
                translate([118, 0, -EPS])
                    cylinder(d = SCREW_CLEARANCE, h = thk(ZR_MAIN_PLATE) + 2 * EPS);
        }
}

// ---------------------------------------------------------------------------
// 2.  TOP BRIDGE (SKELETON)  --  z = 20 .. 25.
//     A full disc pierced with the four declared windows.  Every window carries
//     an explicit member list in design.py so the size can be checked rather
//     than eyeballed.
// ---------------------------------------------------------------------------
module top_bridge() {
    color(C_PLATE)
    translate([0, 0, dz(ZR_TOP_BRIDGE)])
        difference() {
            union() {
                cylinder(d = 2 * PLATE_RADIUS, h = thk(ZR_TOP_BRIDGE));
                // raised bearing seats for the upper pivots
                for (p = [POS_CENTRE_WHEEL, POS_GREAT_WHEEL, POS_INTERMEDIATE,
                          POS_MOTION_WORKS])
                    translate([p[0], p[1], -1.6])
                        tube(od = BEARING_SEAT_DIAMETER + 3.0,
                             id = fit(SHAFT_DIAMETER), h = 1.6);
                // the carriage's upper bearing: a jewel seat plus the race that
                // keeps the sleeve arbor coaxial over its whole 26 mm span
                translate([POS_CARRIAGE[0], POS_CARRIAGE[1], -1.6])
                    tube(od = CARRIAGE_ARBOR_D + 6.0,
                         id = fit(CARRIAGE_ARBOR_D) + 2 * RADIAL_CLEARANCE,
                         h = 1.6);
            }
            for (w = BRIDGE_WINDOWS)
                translate([w[0], w[1], -EPS])
                    cylinder(d = w[2], h = thk(ZR_TOP_BRIDGE) + 2 * EPS);
            // pillars
            for (a = [0, 72, 144, 216, 288]) rotate(a)
                translate([118, 0, -EPS])
                    cylinder(d = SCREW_CLEARANCE, h = thk(ZR_TOP_BRIDGE) + 2 * EPS);
            // lightening: the bridge spans 296 mm and does no structural work
            // between the windows, so most of it is removed.  What is left is a
            // ring at the pillars plus the bearing arms.
            for (i = [0:5]) rotate(i * 60 + 30)
                translate([86, 0, -EPS])
                    rotate(0) scale([1.5, 1.0, 1]) cylinder(d = 46, h = thk(ZR_TOP_BRIDGE) + 2 * EPS);
        }
}

module bridge_jewels() {
    // upper jewels for the centre, great-wheel, intermediate and motion-works
    // arbors.  Bought, not printed (B-05).
    color(C_RUBY)
    for (p = [POS_CENTRE_WHEEL, POS_GREAT_WHEEL, POS_INTERMEDIATE, POS_MOTION_WORKS])
        translate([p[0], p[1], ZR_TOP_BRIDGE[1] - 1.0])
            cylinder(d = 4.0, h = 1.0);
}

// ---------------------------------------------------------------------------
// 3.  PILLARS  --  hold the plate and the bridge apart at the validated spacing
// ---------------------------------------------------------------------------
module pillars() {
    color(C_SCREW)
    for (a = [0, 72, 144, 216, 288]) rotate(a)
        translate([118, 0, ZR_MAIN_PLATE[1]]) {
            tube(od = SCREW_PILLAR_D, id = PILLAR_SCREW_D,
                 h = ZR_TOP_BRIDGE[0] - ZR_MAIN_PLATE[1]);
        }
}
