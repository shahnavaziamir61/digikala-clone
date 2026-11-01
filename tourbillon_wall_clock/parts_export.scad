// ===========================================================================
//  parts_export.scad  --  one STL per printable / machinable part.
//
//  HOW TO EXPORT ONE PART
//      openscad -o stl_output/carriage_floor.stl \
//               -D 'PART_TO_EXPORT="carriage_floor"' parts_export.scad
//  The name must be one of the keys in PARTS below; `PARTS` itself is echoed on
//  a run with PART_TO_EXPORT="" so the list can be read off the console.
//
//  HOW TO EXPORT EVERYTHING (no OpenSCAD binary needed)
//      python3 tools/gen_stl.py            # pure-Python 2.5-D boolean + writer
//  gen_stl.py reads the same registry through tools/calc.py, so the two paths
//  cannot disagree about what a part is.
//
//  EVERY PART IS LABELLED.  The `status` field is one of
//      Functional            the geometry is load- or motion-bearing and every
//                            dimension behind it is computed and checked
//      Prototype             dimensioned and checked, but NOT validated by
//                            test -- it must be prototyped before it is trusted
//      Decorative-reference  drawn so the assembly is complete; the real part is
//                            bought or made by another process, and this model
//                            is NOT a manufacturing drawing for it
//  Parts marked Decorative-reference are excluded from every STL export, so no
//  cosmetic geometry can be mistaken for a manufacturable part.
//
//  PRINTABILITY.  `process` says which of the three tolerance presets the part
//  is allowed to be made under.  calc.py check C-32 measures the thinnest
//  functional wall in the movement at 1.20 mm (the carriage floor), which is
//  below the 2.00 mm FDM limit, so several parts are resin-or-metal only.  That
//  is a real constraint, not a preference, and it is stated per part.
// ===========================================================================

include <parameters.scad>
include <assembly.scad>
include <exploded_view.scad>

// ---------------------------------------------------------------------------
// THE PART REGISTRY
//   [name, status, process, material, print orientation, note]
// ---------------------------------------------------------------------------
PARTS = [
 // ---- plates and bridges -------------------------------------------------
 ["main_plate",          "Functional", "metal or resin", "brass 3 mm plate, milled",
  "flat", "The datum.  z = 0 is its front face; every other Z value is relative to it."],
 ["top_bridge",          "Functional", "metal or resin", "brass 3 mm plate, milled",
  "flat", "Skeleton bridge; the four windows are sized by check C-18b."],
 ["pillars",             "Functional", "metal", "brass rod, turned",
  "flat", "5 off.  Set the plate-to-bridge spacing that the whole Z stack assumes."],
 ["dial_ring",           "Functional", "metal or resin", "brass, silvered",
  "flat", "A RING: the 296 mm aperture is what makes the tourbillon visible."],
 ["case_ring",           "Functional", "fdm ok", "aluminium or printed",
  "flat", "Carries the crystal and the wall mount."],
 ["wall_mount",          "Functional", "fdm ok", "steel or printed",
  "flat", "Carries ~1.9 kg plus the winding load."],
 ["back_cover",          "Decorative", "fdm ok", "printed",
  "flat", "Dust cover.  Carries no load and no tolerance.  NOT exported."],

 // ---- barrel -------------------------------------------------------------
 ["barrel_drum",         "Functional", "metal", "brass, turned + teeth cut",
  "flat", "z=14 cycloidal rim gear integral with the drum.  19.5 mm deep."],
 ["barrel_cover",        "Functional", "metal or resin", "brass, turned",
  "flat", "Closes the drum; spigot-located, 3 screws."],
 ["barrel_arbor",        "Functional", "metal", "hardened steel, turned",
  "vertical", "FIXED to the plate.  Carries the spring's inner hook and the winding square."],
 ["ratchet_wheel",       "Functional", "metal", "hardened steel, milled",
  "flat", "z=24 m=1.5 saw tooth.  Winding and let-down control."],
 ["click",               "Prototype", "metal", "hardened steel, milled",
  "flat", "Spring force is NOT calculated; set by feel during adjustment."],
 ["winding_sleeve",      "Prototype", "metal", "brass, milled",
  "vertical", "10 mm square socket so the clock is wound from the FRONT."],
 ["mainspring",          "Decorative-reference", "bought", "carbon spring steel 0.42 x 18 x 1029",
  "n/a", "Bought, wound to the calculated length.  NOT exported, NOT printable."],

 // ---- going train --------------------------------------------------------
 ["great_wheel",         "Functional", "metal or resin", "brass, teeth cut",
  "flat", "z=56 m=1.40 cycloidal, 5 spokes.  Shares CYCLO_RR_BARREL_GREAT with the barrel gear."],
 ["great_pinion",        "Functional", "metal", "hardened steel, cut from the arbor",
  "vertical", "z=8 m=0.75, radial-flank leaves.  Rigid with the great wheel."],
 ["centre_wheel",        "Functional", "metal or resin", "brass, teeth cut",
  "flat", "z=48 m=0.75.  ONE REVOLUTION PER HOUR -- the reference member of the clock."],
 ["centre_pinion",       "Functional", "metal", "hardened steel",
  "vertical", "z=10 m=0.60.  Rigid with the centre wheel."],
 ["intermediate_wheel",  "Functional", "metal or resin", "brass, teeth cut",
  "flat", "z=75 m=0.60, tip dia 46.20.  Exists only because a single 60:1 stage cannot fit the 70 mm envelope (L-01).  Its teeth must stop 14.70 mm from the carriage axis -- proved by C-18c."],
 ["intermediate_pinion", "Functional", "metal", "hardened steel",
  "vertical", "z=12 m=0.70.  Drives the carriage rim gear."],
 ["fixed_fourth_wheel",  "Functional", "metal", "hardened steel, teeth cut",
  "flat", "z=40 m=0.45.  DOES NOT ROTATE.  Bolted to the plate, concentric with the carriage axis.  The sun of the epicyclic."],
 ["fixed_fourth_stub",   "Functional", "metal", "hardened steel",
  "vertical", "The reaction member for the whole escapement."],

 // ---- motion works -------------------------------------------------------
 ["canon_pinion",        "Prototype", "metal", "brass, burnished bore",
  "vertical", "z=16 m=0.72.  FRICTION fit on the centre arbor; the grip is set by adjustment, not calculated."],
 ["minute_wheel",        "Functional", "metal or resin", "brass, teeth cut",
  "flat", "z=64 m=0.72, tip dia 47.52."],
 ["minute_pinion",       "Functional", "metal", "hardened steel",
  "vertical", "z=16 m=0.90.  Rigid with the minute wheel."],
 ["hour_wheel",          "Functional", "metal or resin", "brass, teeth cut",
  "flat", "z=48 m=0.90.  Concentric with the centre arbor -- which is why the two motion-works meshes need different modules (C-07b)."],
 ["hour_pipe",           "Functional", "metal", "brass tube",
  "vertical", "dia 9, z = 14 .. 29.  Passes through the 13 mm bridge window."],
 ["minute_pipe",         "Functional", "metal", "brass tube",
  "vertical", "dia 6, z = 12 .. 30.  Passes THROUGH the hour pipe."],
 ["motion_works_stud",   "Functional", "metal", "brass, pressed and peened",
  "vertical", "Does not turn."],

 // ---- carriage -----------------------------------------------------------
 ["carriage_floor",      "Functional", "resin or metal", "Ti-6Al-4V, milled",
  "flat", "dia 62 x 1.6 with a 30 mm opening.  1.20 mm is the thinnest functional wall in the clock, which is why C-32 rules out FDM for it."],
 ["carriage_rim_gear",   "Functional", "metal", "Ti or brass, teeth cut",
  "flat", "z=96 m=0.70 cycloidal annulus.  Tip dia 68.60, inside the 70 mm target."],
 ["carriage_rim_band",   "Functional", "metal", "Ti-6Al-4V",
  "flat", "Ties floor to upper bridge; the outer running surface."],
 ["carriage_columns",    "Functional", "metal", "Ti-6Al-4V, turned",
  "vertical", "3 off at r = 23, angles 150/240/330 -- NOT 120 deg apart, because the balance and escape wheel leave only those arcs free (C-15h)."],
 ["carriage_upper_bridge","Functional","metal", "Ti-6Al-4V, milled",
  "flat", "40 x 5 x 1.6.  Upper bearing seat for the escape, pallet and balance arbors, so its hole positions ARE the coaxiality spec."],
 ["carriage_sleeve_arbor","Functional","metal", "hardened steel, lapped",
  "vertical", "THE most demanding bearing in the clock: 33.68 g at 1 rpm, radial play <= 0.015 mm.  Never printed."],
 ["carriage_top_cap",    "Functional", "metal", "Ti-6Al-4V",
  "flat", "Closes the carriage and carries the upper escape pivot."],
 ["carriage_counter_mass","Functional","metal", "brass",
  "flat", "2.43 g at r = 30, the CALCULATED starting point to bring the static moment from 72.79 g-mm inside the 12360 mg-mm poise spec (C-27).  Final mass is set on the poising tool."],
 ["seconds_pointer",     "Functional", "metal or resin", "blued steel",
  "flat", "The carriage turns once a minute, so this is a real seconds indicator."],

 // ---- escapement ---------------------------------------------------------
 ["escape_wheel",        "Functional", "metal ONLY", "hardened 1.4034, wire-EDM + lapped",
  "flat", "15 club teeth, dia 20.00.  NOT PRINTABLE: the impulse faces need Ra < 0.2 um and > 60 HRC or the lever will not unlock."],
 ["escape_pinion",       "Functional", "metal ONLY", "hardened steel",
  "vertical", "z=10 m=0.45, elongated: the toothed section hangs BELOW the carriage floor to reach the fixed fourth wheel (Helwig arrangement)."],
 ["pallet_lever",        "Functional", "metal ONLY", "hardened steel, milled",
  "flat", "Inline Swiss lever.  Stone arms 6.262 mm, fork arm 11.50 mm, ratio 1.8365, swing 1.83 deg."],
 ["pallet_stones",       "Functional", "bought", "synthetic ruby, cemented and lapped",
  "n/a", "2 off, 2.6 x 1.6.  Bought (B-11).  NOT exported."],
 ["roller",              "Functional", "metal", "hardened steel",
  "flat", "dia 8 with the impulse pin at r = 3.5."],
 ["impulse_pin",         "Functional", "bought", "ruby or hardened steel",
  "vertical", "dia 1.6.  Bought."],
 ["balance_wheel",       "Functional", "metal", "brass, 2 arms at 90 deg",
  "flat", "dia 28, 6.80 g, J = 6.668e-7 kg m^2.  1.000 Hz with the hairspring below."],
 ["balance_staff",       "Functional", "metal ONLY", "hardened, burnished, sapphire endstones",
  "vertical", "dia 1.6, pivots 0.35.  NOT printable."],
 ["hairspring",          "Decorative-reference", "bought", "blued spring steel 0.06 x 1.8 x 246.2",
  "n/a", "Bought or wound to the MEASURED inertia of the finished balance.  k is only 0.02633 N-mm/rad, so a spring 0.01 mm too thick is twice too stiff.  NOT exported."],

 // ---- dial, hands, case --------------------------------------------------
 ["hour_hand",           "Functional", "metal or resin", "blued steel",
  "flat", "Driven at exactly 1/12 of the minute hand (C-07)."],
 ["minute_hand",         "Functional", "metal or resin", "blued steel",
  "flat", "One revolution per hour."],
 ["crystal",             "Functional", "bought", "mineral glass or sapphire",
  "flat", "Bought (B-16).  Modelled for the seat only."],
 ["click_spring",        "Decorative-reference", "bought", "spring steel",
  "n/a", "Rate not calculated.  NOT exported."]
];

function part_status(name) = [for (p = PARTS) if (p[0] == name) p[1]][0];
function part_process(name) = [for (p = PARTS) if (p[0] == name) p[2]][0];
function part_material(name) = [for (p = PARTS) if (p[0] == name) p[3]][0];
function part_note(name)    = [for (p = PARTS) if (p[0] == name) p[5]][0];

// parts that may be exported at all
EXPORTABLE = [for (p = PARTS) if (p[1] != "Decorative-reference") p[0]];

// ---------------------------------------------------------------------------
// THE PART GEOMETRY, one module per registry entry.
// Each is drawn in ITS OWN LOCAL FRAME, flat on z = 0, ready to slice.
// ---------------------------------------------------------------------------
module part_geometry(name) {
    // ---- plates and bridges ----
    name == "main_plate"        ? translate([0, 0, -dz(ZR_MAIN_PLATE)]) main_plate() :
    name == "top_bridge"        ? translate([0, 0, -dz(ZR_TOP_BRIDGE)]) top_bridge() :
    name == "pillars"           ? pillars() :
    name == "dial_ring"         ? translate([0, 0, -dz(ZR_DIAL_RING)]) dial_ring() :
    name == "case_ring"         ? translate([0, 0, -dz(ZR_CRYSTAL) + 6]) case_ring() :
    name == "wall_mount"        ? translate([0, 0, -ZR_MAIN_PLATE[0] + 4]) wall_mount() :
    name == "back_cover"        ? translate([0, 0, -ZR_BARREL_COVER[0] + 2.5]) back_cover() :

    // ---- barrel ----
    name == "barrel_drum"       ? translate([0, 0, -dz(ZR_BARREL_DRUM)]) barrel_drum() :
    name == "barrel_cover"      ? translate([0, 0, -dz(ZR_BARREL_COVER)]) barrel_cover() :
    name == "barrel_arbor"      ? translate([0, 0, -dz(ZR_BARREL_COVER)]) barrel_arbor() :
    name == "ratchet_wheel"     ? translate([0, 0, -dz(ZR_RATCHET)]) ratchet_wheel() :
    name == "click"             ? translate([-Z_RATCHET * M_RATCHET / 2 - 5, 0, -dz(ZR_RATCHET)]) click() :
    name == "winding_sleeve"    ? translate([0, 0, -ZR_RATCHET[1]]) winding_sleeve() :

    // ---- going train ----
    name == "great_wheel"       ? translate([0, 0, -dz(ZR_GREAT_WHEEL)]) great_wheel() :
    name == "great_pinion"      ? translate([0, 0, -dz(ZR_GREAT_PINION)]) great_pinion() :
    name == "centre_wheel"      ? translate([0, 0, -dz(ZR_CENTRE_WHEEL)]) centre_wheel() :
    name == "centre_pinion"     ? translate([0, 0, -dz(ZR_CENTRE_PINION)]) centre_pinion() :
    name == "intermediate_wheel"? translate([-POS_INTERMEDIATE[0], -POS_INTERMEDIATE[1], -dz(ZR_INTER_WHEEL)]) intermediate_wheel() :
    name == "intermediate_pinion"? translate([-POS_INTERMEDIATE[0], -POS_INTERMEDIATE[1], -dz(ZR_INTER_PINION)]) intermediate_pinion() :
    name == "fixed_fourth_wheel"? translate([-POS_FIXED_FOURTH[0], -POS_FIXED_FOURTH[1], -dz(ZR_FIXED_FOURTH)]) fixed_fourth_wheel() :
    name == "fixed_fourth_stub" ? translate([-POS_FIXED_FOURTH[0], -POS_FIXED_FOURTH[1], 0]) fixed_fourth_stub() :

    // ---- motion works ----
    name == "canon_pinion"      ? translate([0, 0, -dz(ZR_CANON_PINION)]) canon_pinion() :
    name == "minute_wheel"      ? translate([-POS_MOTION_WORKS[0], -POS_MOTION_WORKS[1], -dz(ZR_MINUTE_WHEEL)]) minute_wheel() :
    name == "minute_pinion"     ? translate([-POS_MOTION_WORKS[0], -POS_MOTION_WORKS[1], -dz(ZR_MINUTE_PINION)]) minute_pinion() :
    name == "hour_wheel"        ? translate([0, 0, -dz(ZR_HOUR_WHEEL)]) hour_wheel() :
    name == "hour_pipe"         ? translate([0, 0, -dz(ZR_HOUR_PIPE)]) hour_pipe() :
    name == "minute_pipe"       ? translate([0, 0, -dz(ZR_MINUTE_PIPE)]) minute_pipe() :
    name == "motion_works_stud" ? translate([-POS_MOTION_WORKS[0], -POS_MOTION_WORKS[1], -ZR_TOP_BRIDGE[0]]) motion_works_stud() :

    // ---- carriage ----
    name == "carriage_floor"    ? carriage_floor() :
    name == "carriage_rim_gear" ? translate([0, 0, -(dz(ZR_RIM_GEAR) - Z_CARRIAGE_Z0)]) carriage_rim_gear() :
    name == "carriage_rim_band" ? carriage_rim_band() :
    name == "carriage_columns"  ? carriage_columns() :
    name == "carriage_upper_bridge" ? translate([0, 0, -Z_CARRIAGE[8][0]]) carriage_upper_bridge() :
    name == "carriage_sleeve_arbor" ? translate([0, 0, -Z_CARRIAGE[0][0]]) carriage_sleeve_arbor() :
    name == "carriage_top_cap"  ? translate([0, 0, -Z_CARRIAGE[10][0]]) carriage_top_cap() :
    name == "carriage_counter_mass" ? translate([0, 0, -(CARRIAGE_FLOOR_THK - 1.0)]) carriage_counter_mass() :
    name == "seconds_pointer"   ? translate([0, 0, -Z_CARRIAGE[11][0]]) seconds_pointer() :

    // ---- escapement ----
    name == "escape_wheel"      ? translate([-ESC_POS[0], -ESC_POS[1], -Z_CARRIAGE[3][0]]) escape_wheel() :
    name == "escape_pinion"     ? translate([-ESC_POS[0], -ESC_POS[1], -Z_CARRIAGE[0][0]]) escape_pinion() :
    name == "pallet_lever"      ? translate([-PAL_POS[0], -PAL_POS[1], -Z_CARRIAGE[4][0]]) pallet_lever() :
    name == "roller"            ? translate([-BAL_POS[0], -BAL_POS[1], -Z_CARRIAGE[5][0]]) roller() :
    name == "balance_wheel"     ? translate([-BAL_POS[0], -BAL_POS[1], -Z_CARRIAGE[6][0]]) balance_wheel() :
    name == "balance_staff"     ? translate([-BAL_POS[0], -BAL_POS[1], -(Z_CARRIAGE[6][0] - 1.0)]) balance_staff() :

    // ---- dial and hands ----
    name == "hour_hand"         ? translate([0, 0, -dz(ZR_HANDS)]) hour_hand() :
    name == "minute_hand"       ? translate([0, 0, -dz(ZR_HANDS) - 1.6]) minute_hand() :
    name == "crystal"           ? translate([0, 0, -dz(ZR_CRYSTAL)]) crystal() :
    echo("part_geometry: unknown part name '", name, "'.  Valid names: ", EXPORTABLE);
}

// ---------------------------------------------------------------------------
// ENTRY POINT.  With PART_TO_EXPORT set, render exactly that one part in its
// own local frame so the STL is directly printable.
// ---------------------------------------------------------------------------
if (PART_TO_EXPORT != "") {
    if (part_status(PART_TO_EXPORT) == "Decorative-reference")
        echo("REFUSING to export '", PART_TO_EXPORT, "': it is labelled ",
             part_status(PART_TO_EXPORT), ".  ", part_note(PART_TO_EXPORT));
    else {
        echo("exporting '", PART_TO_EXPORT, "'  status=", part_status(PART_TO_EXPORT),
             "  process=", part_process(PART_TO_EXPORT),
             "  material=", part_material(PART_TO_EXPORT));
        echo("note: ", part_note(PART_TO_EXPORT));
        // apply the print-shrink compensation of the selected process
        scale([PRINT_SHRINK_SCALE, PRINT_SHRINK_SCALE, PRINT_SHRINK_SCALE])
            part_geometry(PART_TO_EXPORT);
    }
} else {
    echo("PART_TO_EXPORT is empty.  Exportable parts:");
    for (n = EXPORTABLE) echo("   ", n, "   [", part_status(n), " / ", part_process(n), "]");
    echo("Refused (Decorative-reference, never exported):");
    for (p = PARTS) if (p[1] == "Decorative-reference") echo("   ", p[0]);
    // and show the whole clock so the file is useful on its own
    view_by_name(VIEW);
}
