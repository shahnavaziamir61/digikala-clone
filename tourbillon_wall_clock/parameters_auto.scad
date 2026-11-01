// ===========================================================================
// parameters_auto.scad   --   MACHINE GENERATED, DO NOT EDIT BY HAND
// Source of truth: tools/design.py  +  tools/calc.py
// Regenerate with:   python3 tools/calc.py
// Every value below is derived and validated; see design.json and
// docs/CALCULATIONS.md for the derivation of each number.
// ===========================================================================

// ---- derived user parameters (the knobs the brief names by hand live in parameters.scad) --
// Anything declared in parameters.scad is deliberately NOT repeated here:
// that file includes this one, so its own declaration would win anyway,
// and duplicating a name across two files is how a value goes stale.
DIAL_APERTURE = 296;
BEAT_HZ = 1;
TARGET_RUN_DAYS = 3;

// ---- tooth counts ------------------------------------------------------
Z_BARREL_GEAR = 14;
Z_GREAT_WHEEL = 56;
Z_GREAT_PINION = 8;
Z_CENTRE_WHEEL = 48;
Z_CENTRE_PINION = 10;
Z_INTER_WHEEL = 75;
Z_INTER_PINION = 12;
Z_CARRIAGE_RIM = 96;
Z_FIXED_FOURTH = 40;
Z_ESCAPE_PINION = 10;
Z_ESCAPE_WHEEL = 15;
Z_CANON_PINION = 16;
Z_MINUTE_WHEEL = 64;
Z_MINUTE_PINION = 16;
Z_HOUR_WHEEL = 48;
Z_RATCHET = 24;

// ---- modules (mm) ------------------------------------------------------
M_BARREL_GEAR = 1.4;
M_GREAT_WHEEL = 1.4;
M_GREAT_PINION = 0.75;
M_CENTRE_WHEEL = 0.75;
M_CENTRE_PINION = 0.6;
M_INTER_WHEEL = 0.6;
M_INTER_PINION = 0.7;
M_CARRIAGE_RIM = 0.7;
M_FIXED_FOURTH = 0.45;
M_ESCAPE_PINION = 0.45;
M_ESCAPE_WHEEL = 1.3333;
M_CANON_PINION = 0.72;
M_MINUTE_WHEEL = 0.72;
M_MINUTE_PINION = 0.9;
M_HOUR_WHEEL = 0.9;
M_RATCHET = 1.5;

// ---- gear mesh data (pitch / tip / root diameters and centre distances) --
// Barrel gear -> Great wheel   i=4.0   a=49.0 mm   eps=2.228 (computed numerically from the generated cycloidal profiles (shared describing circle rr = 4.9000 mm))
Barrel_gear__Great_wheel_d1 = 19.6;
Barrel_gear__Great_wheel_d2 = 78.4;
Barrel_gear__Great_wheel_db1 = 18.418;
Barrel_gear__Great_wheel_db2 = 73.6719;
Barrel_gear__Great_wheel_da1 = 22.4;
Barrel_gear__Great_wheel_da2 = 81.2;
Barrel_gear__Great_wheel_df1 = 16.1;
Barrel_gear__Great_wheel_df2 = 74.9;
Barrel_gear__Great_wheel_a = 49;
Barrel_gear__Great_wheel_i = 4;
// Great pinion -> Centre wheel   i=6.0   a=21.0 mm   eps=1.874 (computed numerically from the generated cycloidal profiles (shared describing circle rr = 1.5000 mm))
Great_pinion__Centre_wheel_d1 = 6;
Great_pinion__Centre_wheel_d2 = 36;
Great_pinion__Centre_wheel_db1 = 5.6382;
Great_pinion__Centre_wheel_db2 = 33.8289;
Great_pinion__Centre_wheel_da1 = 7.5;
Great_pinion__Centre_wheel_da2 = 37.5;
Great_pinion__Centre_wheel_df1 = 4.125;
Great_pinion__Centre_wheel_df2 = 34.125;
Great_pinion__Centre_wheel_a = 21;
Great_pinion__Centre_wheel_i = 6;
// Centre pinion -> Intermediate wheel   i=7.5   a=25.5 mm   eps=2.048 (computed numerically from the generated cycloidal profiles (shared describing circle rr = 1.5000 mm))
Centre_pinion__Intermediate_wheel_d1 = 6;
Centre_pinion__Intermediate_wheel_d2 = 45;
Centre_pinion__Intermediate_wheel_db1 = 5.6382;
Centre_pinion__Intermediate_wheel_db2 = 42.2862;
Centre_pinion__Intermediate_wheel_da1 = 7.2;
Centre_pinion__Intermediate_wheel_da2 = 46.2;
Centre_pinion__Intermediate_wheel_df1 = 4.5;
Centre_pinion__Intermediate_wheel_df2 = 43.5;
Centre_pinion__Intermediate_wheel_a = 25.5;
Centre_pinion__Intermediate_wheel_i = 7.5;
// Intermediate pinion -> Carriage rim gear   i=8.0   a=37.8 mm   eps=2.183 (computed numerically from the generated cycloidal profiles (shared describing circle rr = 2.1000 mm))
Intermediate_pinion__Carriage_rim_gear_d1 = 8.4;
Intermediate_pinion__Carriage_rim_gear_d2 = 67.2;
Intermediate_pinion__Carriage_rim_gear_db1 = 7.8934;
Intermediate_pinion__Carriage_rim_gear_db2 = 63.1473;
Intermediate_pinion__Carriage_rim_gear_da1 = 9.8;
Intermediate_pinion__Carriage_rim_gear_da2 = 68.6;
Intermediate_pinion__Carriage_rim_gear_df1 = 6.65;
Intermediate_pinion__Carriage_rim_gear_df2 = 65.45;
Intermediate_pinion__Carriage_rim_gear_a = 37.8;
Intermediate_pinion__Carriage_rim_gear_i = 8;
// Fixed fourth wheel -> Escape pinion   i=0.25   a=11.25 mm   eps=1.213 (computed numerically from the generated cycloidal profiles (shared describing circle rr = 1.1250 mm))
Fixed_fourth_wheel__Escape_pinion_d1 = 18;
Fixed_fourth_wheel__Escape_pinion_d2 = 4.5;
Fixed_fourth_wheel__Escape_pinion_db1 = 16.9145;
Fixed_fourth_wheel__Escape_pinion_db2 = 4.2286;
Fixed_fourth_wheel__Escape_pinion_da1 = 18.9;
Fixed_fourth_wheel__Escape_pinion_da2 = 5.4;
Fixed_fourth_wheel__Escape_pinion_df1 = 16.875;
Fixed_fourth_wheel__Escape_pinion_df2 = 3.375;
Fixed_fourth_wheel__Escape_pinion_a = 11.25;
Fixed_fourth_wheel__Escape_pinion_i = 0.25;
// Canon pinion -> Minute wheel   i=4.0   a=28.8 mm   eps=2.381 (computed numerically from the generated cycloidal profiles (shared describing circle rr = 2.8800 mm))
Canon_pinion__Minute_wheel_d1 = 11.52;
Canon_pinion__Minute_wheel_d2 = 46.08;
Canon_pinion__Minute_wheel_db1 = 10.8253;
Canon_pinion__Minute_wheel_db2 = 43.301;
Canon_pinion__Minute_wheel_da1 = 12.96;
Canon_pinion__Minute_wheel_da2 = 47.52;
Canon_pinion__Minute_wheel_df1 = 9.72;
Canon_pinion__Minute_wheel_df2 = 44.28;
Canon_pinion__Minute_wheel_a = 28.8;
Canon_pinion__Minute_wheel_i = 4;
// Minute pinion -> Hour wheel   i=3.0   a=28.8 mm   eps=2.334 (computed numerically from the generated cycloidal profiles (shared describing circle rr = 3.6000 mm))
Minute_pinion__Hour_wheel_d1 = 14.4;
Minute_pinion__Hour_wheel_d2 = 43.2;
Minute_pinion__Hour_wheel_db1 = 13.5316;
Minute_pinion__Hour_wheel_db2 = 40.5947;
Minute_pinion__Hour_wheel_da1 = 16.2;
Minute_pinion__Hour_wheel_da2 = 45;
Minute_pinion__Hour_wheel_df1 = 12.15;
Minute_pinion__Hour_wheel_df2 = 40.95;
Minute_pinion__Hour_wheel_a = 28.8;
Minute_pinion__Hour_wheel_i = 3;

// ---- tooth system per MESH ---------------------------------------------
// A cycloidal pinion is conjugate ONLY with a cycloidal wheel generated
// by the SAME describing circle, so the system and the describing circle
// are properties of the mesh, never of one wheel alone.  Both members of
// a mesh are drawn from the same rr; gear_3d()/pinion_3d() require it.
Barrel_gear__Great_wheel_SYSTEM = "cycloidal";
Barrel_gear__Great_wheel_RR = 4.9;
Great_pinion__Centre_wheel_SYSTEM = "cycloidal";
Great_pinion__Centre_wheel_RR = 1.5;
Centre_pinion__Intermediate_wheel_SYSTEM = "cycloidal";
Centre_pinion__Intermediate_wheel_RR = 1.5;
Intermediate_pinion__Carriage_rim_gear_SYSTEM = "cycloidal";
Intermediate_pinion__Carriage_rim_gear_RR = 2.1;
Fixed_fourth_wheel__Escape_pinion_SYSTEM = "cycloidal";
Fixed_fourth_wheel__Escape_pinion_RR = 1.125;
Canon_pinion__Minute_wheel_SYSTEM = "cycloidal";
Canon_pinion__Minute_wheel_RR = 2.88;
Minute_pinion__Hour_wheel_SYSTEM = "cycloidal";
Minute_pinion__Hour_wheel_RR = 3.6;
// short names used by gear_generator.scad
CYCLO_RR_BARREL_GREAT = 4.9;   // Barrel gear <-> Great wheel
CYCLO_RR_GREAT_CENTRE = 1.5;   // Great pinion <-> Centre wheel
CYCLO_RR_CENTRE_INTER = 1.5;   // Centre pinion <-> Intermediate wheel
CYCLO_RR_INTER_CARRIAGE = 2.1;   // Intermediate pinion <-> Carriage rim gear
CYCLO_RR_EPICYCLIC = 1.125;   // Fixed fourth wheel <-> Escape pinion
CYCLO_RR_CANON_MINUTE = 2.88;   // Canon pinion <-> Minute wheel
CYCLO_RR_MINUTE_HOUR = 3.6;   // Minute pinion <-> Hour wheel

// ---- part geometry (all mm) -- the SCAD modules read these, never their own --
BARREL_DRUM_OD = 152;
BARREL_WALL_THK = 2.5;
BARREL_WALL_HEIGHT = 20;
BARREL_ARBOR_D = 60;
SPRING_THICK = 0.42;
SPRING_WIDTH = 18;
SPRING_E = 200000;
SPRING_FILL = 0.55;
SPRING_SAFE_STRESS = 1400;
WIND_SQUARE = 10;
CARRIAGE_BORE_R = 32.225;
CARRIAGE_FLOOR_OD = 62;
CARRIAGE_FLOOR_THK = 1.6;
CARRIAGE_FLOOR_HOLE_D = 30;
CARRIAGE_PINION_HOLE_D = 30;
CARRIAGE_RIM_BAND_H = 5.5;
CARRIAGE_UPPER_BRIDGE_L = 40;
CARRIAGE_UPPER_BRIDGE_W = 5;
CARRIAGE_UPPER_BRIDGE_T = 1.6;
CARRIAGE_COLUMN_D = 4;
CARRIAGE_COLUMN_N = 3;
CARRIAGE_COLUMN_R = 23;
CARRIAGE_ARBOR_D = 8;
FIXED_4TH_BOSS_D = 5;
CARRIAGE_MASS_CEILING_G = 20;
Y_ESCAPE = -11.25;
Y_PALLET = -1;
Y_BALANCE = 14;
ESCAPE_WHEEL_OD = 19.9995;
ESCAPE_WHEEL_THK = 1.2;
ESCAPE_PINION_H = 2.5;
BALANCE_OD = 28;
BALANCE_RIM_W = 3;
BALANCE_RIM_T = 2;
BALANCE_ARM_N = 2;
BALANCE_ARM_W = 4;
BALANCE_ARM_T = 1.6;
BALANCE_ARM_ANGLE = 90;
ROLLER_D = 8;
IMPULSE_PIN_R = 3.5;
IMPULSE_PIN_D = 1.6;
PALLET_LEVER_LEN = 11.5;
PALLET_LEVER_W = 5;
LOCK_ANGLE_DEG = 1.5;
DROP_ANGLE_DEG = 1;
IMPULSE_FRACTION = 0.42;
PALLET_STONE_L = 2.6;
PALLET_STONE_W = 1.6;
LEVER_BANKING_DEG = 6;
HAIRSPRING_OD = 26;
HAIRSPRING_ID = 16;
HAIRSPRING_T = 0.06;
HAIRSPRING_B = 1.8;
BALANCE_AMPLITUDE_DEG = 180;
BALANCE_Q = 250;
CARRIAGE_TARGET_H_MIN = 12;
CARRIAGE_TARGET_H_MAX = 20;
MOTION_RATIO_TARGET = 12;
CD_BARREL_CENTRE = 70;
CARRIAGE_COLUMN_ANGLES = [150, 240, 330];
// HUB_OD: [name, hub outer dia] -- looked up by name in the SCAD modules
HUB_OD = [
    ["barrel cover", 60],
    ["barrel drum", 60],
    ["barrel gear", 16],
    ["canon pinion", 4],
    ["carriage rim gear", 56.1],
    ["centre pinion", 4],
    ["centre wheel", 6],
    ["crystal / bezel", 285],
    ["dial ring", 230],
    ["fixed fourth wheel", 5],
    ["great pinion", 3],
    ["great wheel", 12],
    ["hands", 0],
    ["hour wheel", 20],
    ["intermediate pinion", 4],
    ["intermediate wheel", 12],
    ["main plate", 0],
    ["minute pinion", 4],
    ["minute wheel", 14],
    ["ratchet + click", 10],
    ["top bridge (skeleton)", 0]
];
function hub_od(name) = let(h = [for (e = HUB_OD) if (e[0] == name) e[1]]) h[0];
// Z_MOVEMENT: [z_bottom, z_top, footprint_od] per member; z=0 is the FRONT face of the main plate, +Z towards the dial
Z_MOVEMENT = [
    [-19.5, -18, 148],
    [-18, 1.5, 152],
    [-5, 0, 296],
    [1.5, 3.5, 18.9],
    [2, 4, 22.4],
    [2, 4, 80.9],
    [6.4, 8, 68.6],
    [2, 8.6, 7.5],
    [4, 8, 9.8],
    [4, 6, 46.2],
    [4, 9.5, 7.2],
    [6.6, 8.6, 37.5],
    [9, 12, 39],
    [10, 12, 12.96],
    [10, 12, 47.52],
    [12, 14, 16.2],
    [12, 14, 45],
    [14, 29, 9],
    [12, 30, 6],
    [20, 25, 296],
    [26, 28, 300],
    [28.5, 31.5, 300],
    [32, 36, 300]
];
// names, index-aligned with Z_MOVEMENT
Z_MOVEMENT_NAMES = ["barrel cover", "barrel drum", "main plate", "fixed fourth wheel", "barrel gear", "great wheel", "carriage rim gear", "great pinion", "intermediate pinion", "intermediate wheel", "centre pinion", "centre wheel", "ratchet + click", "canon pinion", "minute wheel", "minute pinion", "hour wheel", "hour pipe", "minute pipe", "top bridge (skeleton)", "dial ring", "hands", "crystal / bezel"];
// Z_CARRIAGE: same, but LOCAL to the carriage floor (add Z_CARRIAGE_Z0)
Z_CARRIAGE = [
    [-5, -2.6, 5.4],
    [-5, 3.2, 1.5],
    [0, 1.6, 62],
    [2, 3.2, 20],
    [2.2, 4.2, 24],
    [2.8, 4.4, 8],
    [4.8, 6.8, 28],
    [7.1, 8, 26],
    [8.4, 10, 40],
    [10, 10.8, 6],
    [10.8, 12.2, 20],
    [12.2, 13, 62]
];
// names, index-aligned with Z_CARRIAGE
Z_CARRIAGE_NAMES = ["escape pinion teeth", "escape arbor", "carriage lower plate", "escape wheel", "pallet lever + stones", "roller + impulse pin", "balance wheel", "hairspring", "carriage upper bridge", "balance endstone", "carriage top cap", "seconds pointer"];
// PLATE_WINDOWS: [x, y, dia, purpose] -- holes cut through the main plate
PLATE_WINDOWS = [
    [0, 70, 154, "barrel drum passage"],
    [0, -63.3, 74, "carriage window"],
    [0, 70, 42, "winding / ratchet"],
    [0, -25.5, 12, "intermediate arbor"]
];
// BRIDGE_WINDOWS: [x, y, dia, purpose, [members that must pass through]].
// The member list is what makes the windows checkable: calc.py C-18b
// sizes each window against exactly these parts and nothing else.
BRIDGE_WINDOWS = [
    [0, -63.3, 74, "carriage window", ["seconds pointer", "carriage upper bridge"]],
    [0, 70, 44, "barrel / winding", ["ratchet + click", "barrel gear"]],
    [28.8, 0, 64, "motion works", ["motion works"]],
    [0, 0, 13, "centre pipes", ["hour pipe", "minute pipe"]]
];

// ---- axis layout (origin = centre-wheel axis, +Y = 12 o'clock) ---------
POS_CENTRE_WHEEL = [0, 0];
POS_GREAT_WHEEL = [0, 21];
POS_BARREL = [0, 70];
POS_INTERMEDIATE = [0, -25.5];
POS_CARRIAGE = [0, -63.3];
POS_FIXED_FOURTH = [0, -63.3];
POS_MOTION_WORKS = [28.8, 0];
CD_BARREL_TO_GREAT = 49;
CD_GREAT_TO_CENTRE = 21;
CD_BARREL_TO_CENTRE_LAYOUT = 70;
CD_CENTRE_TO_INTERMEDIATE = 25.5;
CD_INTERMEDIATE_TO_CARRIAGE = 37.8;
CD_EPICYCLIC_ORBITAL = 11.25;
CD_MOTION_WORKS = 28.8;
PLATE_RADIUS = 148;

// ---- kinematic solution (derived, validated) ---------------------------
ratio_barrel_to_centre = 24;
ratio_centre_to_inter = 7.5;
ratio_inter_to_carriage = 8;
ratio_centre_to_carriage = 60;
centre_wheel_rpm = 0.0166667;
barrel_rpm = 0.000694444;
great_rpm = 0.00277778;
intermediate_rpm = 0.125;
carriage_rpm = 1;
hour_wheel_rpm = 0.00138889;
epicyclic_z4_over_zEP = 4;
escape_rel_carriage_rpm = 4;
escape_absolute_rpm = 5;
escape_teeth_per_second = 1;
balance_frequency_hz = 1;
beats_per_second = 2;
vph = 7200;
balance_period_s = 1;
carriage_rpm_required_by_balance = 1;
barrel_minutes_per_turn = 1440;
barrel_hours_per_turn = 24;
barrel_turns_per_day = 1;
// direction_barrel                           CW (viewed from the front)
// direction_centre_wheel                     CCW
// direction_intermediate                     CW
// direction_carriage                         CCW
// direction_escape_rel_carriage              CW (opposite to carriage)

// ---- mainspring (derived) ----------------------------------------------
MS_BARREL_INTERNAL_RADIUS_MM = 73.5;
MS_ARBOR_RADIUS_MM = 30;
MS_ARBOR_TO_THICKNESS_RATIO = 71.43;
MS_ANNULAR_AREA_MM2 = 14144.2;
MS_PACKING_FACTOR = 0.55;
MS_STRIP_THICKNESS_MM = 0.42;
MS_STRIP_WIDTH_MM = 18;
MS_STRIP_SECTION_MM2 = 7.56;
MS_ACTIVE_LENGTH_MM = 1029;
MS_MEAN_COIL_DIAMETER_MM = 103.5;
MS_COILS_IN_DRUM = 3.165;
MS_COILS_AROUND_ARBOR_WHEN_FULL = 5.459;
MS_COILS_AROUND_BARREL_WHEN_FLAT = 2.228;
MS_BARREL_TURNS_FULL_DISCHARGE = 3.231;
MS_BARREL_TURNS_PER_DAY = 1;
MS_BARREL_HOURS_PER_TURN = 24;
MS_SECOND_MOMENT_I_MM4 = 0.111132;
MS_TORQUE_FULL_WIND_NMM = 740.88;
MS_TORQUE_FLAT_NMM = 302.4;
MS_TORQUE_MEAN_NMM = 521.64;
MS_STRESS_FULL_WIND_MPA = 1400;
MS_STRESS_FLAT_MPA = 571.4;
MS_ENERGY_STORED_NMM = 10589.4;
MS_ENERGY_STORED_J = 10.589;
MS_RUN_TIME_DAYS = 3.23;
MS_RUN_TIME_HOURS = 77.5;
MS_TARGET_RUN_DAYS = 3;
MS_TARGET_MET = true;

// ---- oscillator (derived) ----------------------------------------------
OSC_FREQUENCY_HZ = 1;
OSC_PERIOD_S = 1;
OSC_AMPLITUDE_DEG = 180;
OSC_BALANCE_OD_MM = 28;
// rim_section_mm                           [3.0, 2.0]
OSC_MASS_RIM_G = 4.006;
OSC_MASS_TOTAL_G = 6.8;
OSC_J_RIM_G_MM2 = 625.9;
OSC_J_ARMS_G_MM2 = 26.4;
OSC_J_COLLET_G_MM2 = 9.47;
OSC_J_ROLLER_G_MM2 = 5.05;
OSC_J_TOTAL_G_MM2 = 666.8;
OSC_J_TOTAL_KG_M2 = 6.66823254e-07;
OSC_K_REQUIRED_NM_RAD = 2.632512689e-05;
OSC_K_REQUIRED_NMM_RAD = 0.0263251;
// hairspring_section_mm                    [1.8, 0.06]
OSC_HAIRSPRING_I_MM4 = 3.24e-05;
OSC_HAIRSPRING_ACTIVE_LENGTH_MM = 246.2;
OSC_HAIRSPRING_TURNS_AT_MEAN_RADIUS = 3.73;
OSC_HAIRSPRING_OD_MM = 26;
OSC_HAIRSPRING_ID_MM = 16;
OSC_HAIRSPRING_INNER_STRESS_MPA = 750;
OSC_OMEGA_MAX_RAD_S = 19.739;
OSC_ENERGY_IN_BALANCE_UJ = 129.91;
OSC_ASSUMED_Q = 250;
OSC_OSCILLATOR_POWER_UW = 3.265;
OSC_IMPULSE_ANGLE_RAD = 0.17593;
OSC_ESCAPE_TORQUE_REQUIRED_NMM = 0.73842;

// ---- carriage mass / inertia / poise (derived) -------------------------
// material: Ti-6Al-4V carriage, hardened steel arbors, brass balance
CAR_MASS_FLOOR_G = 6.992;
CAR_MASS_RIM_BAND_G = 8.412;
CAR_MASS_UPPER_BRIDGE_G = 2.016;
CAR_MASS_COLUMNS_G = 1.934;
CAR_MASS_ARBOR_G = 4.735;
CAR_MASS_CARRIAGE_ALONE_G = 24.089;
CAR_MASS_BALANCE_G = 6.8;
CAR_MASS_ESCAPE_WHEEL_G = 1.746;
CAR_MASS_ESCAPE_PINION_G = 0.312;
CAR_MASS_LEVER_G = 0.632;
CAR_MASS_HAIRSPRING_G = 0.0979;
CAR_MASS_ROTATING_TOTAL_G = 33.677;
CAR_J_CARRIAGE_G_MM2 = 14381.6;
CAR_J_CARRIAGE_KG_M2 = 1.438161671e-05;
CAR_J_BALANCE_KG_M2 = 6.66823254e-07;
CAR_J_TOTAL_ROTATING_KG_M2 = 1.504843996e-05;
CAR_STATIC_MOMENT_G_MM = 72.785;
CAR_CENTRE_OF_MASS_OFFSET_MM = 2.16125;
CAR_GRAVITY_TORQUE_AT_OFFSET_NM = 0.000714021;
CAR_ESCAPE_TORQUE_AVAILABLE_NM = 0.00121256;
CAR_GRAVITY_TO_ESCAPE_RATIO = 0.6;
CAR_COUNTER_MASS_AT_R30_G = 2.426;
CAR_POISE_SPEC_MG_MM = 12360.5;
CAR_POISE_SPEC_COM = 0.367027;
// poise_note: POISING IS THE SINGLE MOST CRITICAL ASSEMBLY OPERATION. The un-poised first moment computed above (72.78 g-mm) produces a gravity torque 1x larger tha

// ---- escapement geometry (derived) -------------------------------------
// type: Swiss lever, club-tooth escape wheel, 15 teeth
// reason_for_choice: The Swiss lever is the only escapement with (a) self-locked detent action that does not need a detent spring, (b) a documented geometry that can be la
ESC_ESCAPE_WHEEL_TEETH = 15;
ESC_ESCAPE_WHEEL_OD_MM = 19.9995;
ESC_ESCAPE_WHEEL_PITCH_R_MM = 9.99975;
ESC_TOOTH_PITCH_ANGLE_DEG = 24;
ESC_IMPULSE_ANGLE_DEG = 10.08;
ESC_LOCK_ANGLE_DEG_TOTAL = 3;
ESC_DROP_ANGLE_DEG = 1;
ESC_DRAW_ANGLE_DEG = 12;
ESC_ENTRY_STONE_ANGLE_DEG = 12;
ESC_EXIT_STONE_ANGLE_DEG = 10;
ESC_ESCAPE_TO_PALLET_DISTANCE_MM = 10.25;
ESC_PALLET_TO_BALANCE_DISTANCE_MM = 11.5;
ESC_LEVER_RATIO = 1.8365;
ESC_LOCKING_CIRCLE_RADIUS_MM = 6.262;
ESC_LEVER_BANKING_DEG_TOTAL = 6;
ESC_FORK_SLOT_WIDTH_MM = 0.367;
ESC_LEVER_SWING_DEG = 1.8261;
// pallet_stone_material: synthetic ruby, cemented and lapped
// escape_wheel_material: hardened 1.4034 steel, wire-EDM then lapped impulse faces
// manufacturability: The escape wheel and the pallet stones CANNOT be reliably 3-D printed: the impulse faces need a surface finish better than Ra 0.2 um and a hardness ab

// ---- Z stack (thickness budget) ----------------------------------------
CARRIAGE_HEIGHT_MM = 18;
MOVEMENT_THICKNESS_MM = 55.5;
