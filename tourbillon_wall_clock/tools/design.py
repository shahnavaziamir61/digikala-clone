#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
design.py -- THE FROZEN ARCHITECTURE of the tourbillon wall clock.

Tooth counts, modules, axis positions and the Z stack are decided HERE and
nowhere else.  tools/calc.py DERIVES and VALIDATES everything else (speeds,
torques, energy, run time, masses, tolerances, geometry).

===============================================================================
SELECTED ARCHITECTURE  (frozen -- no elements of other architectures are mixed)
===============================================================================
"Going-barrel wall-clock movement with a great-wheel barrel reduction, a
 rim-driven single-axis tourbillon carriage, a fixed concentric fourth wheel,
 and a Swiss lever escapement carried inside the rotating carriage."

POWER PATH -- GOING TRAIN
    mainspring in the BARREL DRUM
      -> BARREL GEAR       z=14   toothed ring on the drum's front face
      -> GREAT WHEEL       z=56   first reduction stage (4.0 : 1)
      -> GREAT PINION      z=8    rigid with the great wheel
      -> CENTRE WHEEL      z=48   second stage (6.0 : 1).  barrel:centre = 24.0
         the centre arbor makes 1 rev / HOUR and carries the minute hand
      -> CENTRE PINION     z=10   rigid with the centre wheel
      -> INTERMEDIATE WHEEL z=75
      -> INTERMEDIATE PINION z=12 rigid with the intermediate wheel
      -> CARRIAGE RIM GEAR z=96   external teeth on the carriage's lower rim
      -> CARRIAGE          1 rev / MINUTE

POWER PATH -- ESCAPEMENT (inside the carriage)
    FIXED FOURTH WHEEL  z=40  on a stub arbor bolted to the main plate,
                              concentric with the carriage axis, omega = 0,
                              standing INSIDE the carriage through the hole in
                              the carriage floor.  The escape pinion is
                              elongated and reaches down to it -- the Helwig
                              "flying tourbillon" arrangement.
      <- ESCAPE PINION  z=10  planet pinion, rigid with the escape wheel,
                              carried by the carriage, rolls on the fixed wheel
      -> ESCAPE WHEEL   15-tooth Swiss club-tooth
      -> PALLET LEVER   Swiss lever, two ruby pallet stones
      -> BALANCE + HAIRSPRING   1.000 Hz (2 beats/s, 7200 vph), 180 deg

MOTION WORKS (hands)
    CENTRE ARBOR (minute hand, 1 rev/h)
      -> CANON PINION z=16 -> MINUTE WHEEL z=64 -> MINUTE PINION z=16
      -> HOUR WHEEL z=48 (hour pipe, coaxial with the centre arbor)
    ratio = (64/16) x (48/16) = 4 x 3 = 12 EXACTLY

WINDING
    Key wound from the FRONT through the dial aperture.  A 10 mm square winding
    sleeve runs INSIDE the barrel arbor (the key does not fit the 60 mm arbor);
    ratchet z=24 + click on the barrel gear.  No maintaining power in the base
    version -- the movement stops while it is being wound (L-06).

===============================================================================
WHY THE ARCHITECTURE IS SHAPED THE WAY IT IS  (five hard constraints)
===============================================================================
(a) THE BARREL MUST TURN 24x SLOWER THAN THE CENTRE ARBOR.
        run time = barrel turns over a full spring discharge / barrel turns per day
    The spring delivers 3.23 barrel turns, and the target run is 3 days, so the
    barrel may make at most ~1 turn per day while the centre arbor makes 24.
    A SINGLE stage of 24:1 would need either a 336-tooth centre wheel or a
    2-leaf pinion, so the reduction is split 4.0 (barrel gear -> great wheel)
    x 6.0 (great pinion -> centre wheel) = 24.0, exactly as an English or
    French going barrel train does.  The torque cost is paid for explicitly:
        T_centre = T_barrel / 24 / eta^2.                                    -> L-03

(b) THE EXTRA INTERMEDIATE STAGE BETWEEN CENTRE AND CARRIAGE IS MANDATORY.
    centre wheel -> carriage must be exactly 60:1 (1 hour -> 1 minute).
    The carriage rim gear is limited by the 70 mm envelope:
        z_rim <= (70 - 2m)/m   ->   z_rim = 96 at m = 0.70 (tip OD 68.6 mm).
    A single stage would then need a driving pinion of 96/60 = 1.6 teeth.
    Two stages split 60 into 7.5 x 8.0, both realisable.                    -> L-01

(c) z_FIXED_4TH / z_ESCAPE_PINION = 4 IS SOLVED, NOT CHOSEN.
    The carriage is the planet carrier of an epicyclic whose sun (the fixed
    fourth wheel) has omega = 0.  Willis:
        omega_E_rel_carriage = -(z4 / zEP) * omega_carriage
    The pallet lever releases one escape tooth per balance oscillation:
        omega_E_rel_carriage [rev/s] = f_balance / z_E
    =>  omega_carriage = f_balance * zEP / (z_E * z4)
        = 1.0 * 10 / (15 * 40) = 1/60 rev/s = 1.000 rev/min      EXACTLY
    The 1 rpm carriage is a CONSEQUENCE of a 1 Hz balance, a 15-tooth escape
    wheel and a 4:1 epicyclic ratio -- it is not assumed anywhere.

(d) THE CARRIAGE IS THE REGULATED MEMBER.
    The escapement sits inside the carriage and the carriage is the epicyclic
    carrier, so the balance locks the rotation of the whole going train through
    the escape-pinion / fixed-fourth-wheel mesh.  The train cannot run faster
    than the balance allows; the carriage rim gear only supplies torque.  This
    is the same kinematic closure as a classical Breguet tourbillon.

(e) WHY A RIM-DRIVEN CARRIAGE INSTEAD OF THE CLASSICAL UNDER-CARRIAGE PINION.
    In the Breguet layout the carriage-drive pinion rolls on the fixed fourth
    wheel and is driven from OUTSIDE the carriage by the third wheel.  At a
    34 mm carriage radius that requires the driving wheel to reach inside the
    carriage envelope, which is geometrically impossible at 70 mm.  Driving the
    carriage by its own toothed rim (IWC Portugieser Tourbillon, Arnold & Son,
    most large-format tourbillons) removes the conflict and leaves the fixed
    fourth wheel concentric with the carriage axis, so (c) is unchanged.      -> L-01

===============================================================================
THE TORQUE / RUN-TIME TRADE-OFF  (why the run is 3 days and not 7)
===============================================================================
For a spiral spring of thickness t, width b, arbor radius r_arb and drum radius
r_out, with the stress held at its limit (t = 2 sigma_lim r_arb / E):

    turns over a full discharge  ~  (r_out^2 - r_arb^2)^2 / r_out^2
    mean torque                  ~  b t^3 (1/r_arb + 1/r_out)

Both improve with a bigger r_out, but torque improves with t^3 while turn count
improves with 1/t -- so they trade against each other directly.  Substituting
the stress limit and the maximum drum that fits the 296 mm plate gives

    turns x torque  =  0.55/634 * [(r_out^2 - r_arb^2)/r_out]^2 * (const)

which caps the product at about 3.2 turns x 0.52 N-m for this balance.  The
180 deg amplitude is therefore a DESIGN CONSEQUENCE, not a preference: 220 deg
would need 15 % more escape torque and would cut the run to 1.8 days.  A
guaranteed 7-8 day run needs a fusee (which decouples turns from torque) or a
materially lighter balance.  See docs/LIMITATIONS.md L-03.
===============================================================================
"""

import math

# =============================================================================
# 1.  TOP-LEVEL USER PARAMETERS  (mirrored 1:1 into parameters.scad)
# =============================================================================

CLOCK_DIAMETER        = 300.0   # mm  overall case OD
DIAL_APERTURE         = 296.0   # mm  movement plate OD
TOURBILLON_DIAMETER   = 70.0    # mm  carriage envelope OD (hard target)
GEAR_PRESSURE_ANGLE   = 20.0    # deg
GEAR_BACKLASH         = 0.08    # mm  circumferential backlash, machined metal
PLATE_THICKNESS       = 5.0     # mm  main plate thickness
SHAFT_DIAMETER        = 4.0     # mm  default arbor diameter
AXIAL_CLEARANCE       = 0.10    # mm  end float per pivot
RADIAL_CLEARANCE      = 0.02    # mm  pivot-to-jewel radial clearance
BEARING_SEAT_DIAMETER = 6.0     # mm  jewel / bush seat
PRINT_TOLERANCE       = 0.20    # mm  FDM hole compensation
TARGET_RUN_DAYS       = 3.0     # d   power-reserve target (3-day movement).
                                #     7-8 days is NOT reachable with one going
                                #     barrel at this balance -- see L-03.
BEAT_HZ               = 1.0     # Hz  balance oscillation frequency

MANUFACTURING = "metal"         # 'fdm' | 'resin' | 'metal'

MANUFACTURING_PRESETS = {
    "fdm":   dict(clearance=0.40, axial=0.40, radial=0.20, backlash=0.45,
                  hole_grow=0.40, min_wall=2.00, min_hole=1.60,
                  note="PLA/PETG, 0.4 mm nozzle, 0.2 mm layer"),
    "resin": dict(clearance=0.15, axial=0.15, radial=0.05, backlash=0.18,
                  hole_grow=0.10, min_wall=1.20, min_hole=0.80,
                  note="SLA/DLP, 50 um layer"),
    "metal": dict(clearance=0.03, axial=0.10, radial=0.02, backlash=0.08,
                  hole_grow=0.00, min_wall=0.80, min_hole=0.30,
                  note="brass / hardened steel, watchmaker fit"),
}

# =============================================================================
# 2.  TOOTH COUNTS AND MODULES   (the only free variables)
# =============================================================================

# --- going train: barrel reduction -------------------------------------------
Z_BARREL_GEAR   = 14      # toothed ring on the barrel drum front face
M_BARREL_GEAR   = 1.40    # d = 19.6
Z_GREAT_WHEEL   = 56      # great wheel -- first reduction stage
M_GREAT_WHEEL   = 1.40    # d = 78.4
Z_GREAT_PINION  = 8       # great pinion, rigid with the great wheel (cycloidal)
M_GREAT_PINION  = 0.75    # d = 6.0
Z_CENTRE_WHEEL  = 48      # 1 rev/hour -- minute-hand arbor
M_CENTRE_WHEEL  = 0.75    # d = 36.0

# --- going train: centre -> carriage (must be exactly 60) --------------------
Z_CENTRE_PINION = 10      # cycloidal pinion, rigid with the centre wheel
M_CENTRE_PINION = 0.60    # d = 6.0
Z_INTER_WHEEL   = 75      # intermediate wheel.  m = 0.60 is chosen so the wheel
                          # is only dia 45: because the carriage ROTATES, the
                          # intermediate wheel must clear the whole 69.6 mm swept
                          # cylinder of the carriage, and in particular the
                          # elongated escape pinion, which orbits at r = 11.25
                          # with a 2.7 mm tip radius and therefore sweeps
                          # r <= 13.95.  The wheel's teeth stop at
                          # 37.8 - 23.1 = 14.7 mm from the carriage axis and run
                          # at Z 4.0..6.0, below the pinion teeth (Z 1.4..3.8)
                          # and below the carriage floor (Z 6.4..8.0).
                          # A dia 75 wheel at m = 1.00 cannot do this -- C-18c.
M_INTER_WHEEL   = 0.60    # d = 45.0, tip dia 46.2
Z_INTER_PINION  = 12      # cycloidal pinion, rigid with the intermediate wheel
M_INTER_PINION  = 0.70    # d = 8.4
Z_CARRIAGE_RIM  = 96      # external teeth on the carriage lower rim
M_CARRIAGE_RIM  = 0.70    # d = 67.2, tip OD 68.6 (<= 70 mm target)
                          # NOTE M_INTER_PINION = M_CARRIAGE_RIM because the
                          # intermediate pinion drives the carriage rim.

# --- tourbillon epicyclic (SOLVED -- see header note (c)) ---------------------
Z_FIXED_FOURTH  = 40      # fixed fourth wheel, plate-mounted, omega = 0
M_FIXED_FOURTH  = 0.45    # d = 18.0, tip dia 18.9.  m is reduced from 0.50 so
                          # the fixed fourth wheel (r_tip 9.45) stays clear of
                          # the intermediate wheel, whose teeth reach to within
                          # 12.45 mm of the carriage axis.
Z_ESCAPE_PINION = 10      # planet pinion, rigid with the escape wheel
M_ESCAPE_PINION = 0.45    # d = 4.5, tip dia 5.4
Z_ESCAPE_WHEEL  = 15      # Swiss club-tooth escape wheel
M_ESCAPE_WHEEL  = 1.3333  # tip-sizing module: OD = 15 x 1.3333 = 20.0 mm

# --- motion works (must be exactly 12) ---------------------------------------
Z_CANON_PINION  = 16
# The motion works needs BOTH of its meshes to span the SAME distance from the
# centre arbor, because the hour wheel is concentric with the centre arbor and
# the minute wheel and minute pinion share one stud:
#       m1 (z_canon + z_minute_wheel) / 2  ==  m2 (z_minute_pinion + z_hour_wheel) / 2
# With the tooth counts fixed at (64/16) x (48/16) = 12 exactly, that forces
#       m1 * 80 == m2 * 64      ->      m1 = 0.8 * m2
# so the two meshes run at DIFFERENT modules.  Using one module for the whole
# motion works (the obvious choice) makes the geometry impossible: it would put
# the hour wheel 7.2 mm away from the axis it has to turn on.
M_CANON_PINION  = 0.72    # d = 11.52
Z_MINUTE_WHEEL  = 64
M_MINUTE_WHEEL  = 0.72    # d = 46.08
Z_MINUTE_PINION = 16
M_MINUTE_PINION = 0.90    # d = 14.4  (second motion-works module)
Z_HOUR_WHEEL    = 48
M_HOUR_WHEEL    = 0.90    # d = 43.2
MOTION_RATIO_TARGET = 12.0

# --- winding -----------------------------------------------------------------
Z_RATCHET       = 24
M_RATCHET       = 1.50    # d = 36.0
WIND_SQUARE     = 10.0    # mm  key square on the winding sleeve

# =============================================================================
# 3.  MAINSPRING / BARREL
# =============================================================================

BARREL_DRUM_OD      = 152.0    # mm  drum outside diameter
BARREL_WALL_THK     = 2.5      # mm  drum wall thickness -> internal r = 73.5
BARREL_WALL_HEIGHT  = 20.0     # mm  drum wall height (strip is 18 mm wide)
BARREL_ARBOR_D      = 60.0     # mm  spring barrel / arbor diameter.
                               #     r_arb/t = 71.4 -> sigma_max = E t/(2 r_arb)
                               #     = 1400 MPa exactly at the carbon-spring-
                               #     steel limit, comfortable for Nivaflex.
                               #     The 10 mm square winding sleeve runs
                               #     INSIDE it -- the key does not fit the arbor.
SPRING_THICK        = 0.42     # mm  strip thickness t
SPRING_WIDTH        = 18.0     # mm  strip width b
SPRING_E            = 200000.0 # N/mm^2  carbon spring steel / Nivaflex
SPRING_FILL         = 0.55     # -   annulus packing factor (0.50-0.60 typical)
SPRING_SAFE_STRESS  = 1400.0   # N/mm^2  max working bending stress
BALANCE_AMPLITUDE_DEG = 180.0  # deg design amplitude (half-cycle peak).
                               #     Set by the torque margin at the escape
                               #     wheel: 180 deg needs 0.930 N-mm and 1.213
                               #     N-mm is available (margin 1.30).  220 deg
                               #     would need 1.388 N-mm (margin 0.87 -> the
                               #     clock would not start) and would also cut
                               #     the run to 1.8 days.  See L-03.
BALANCE_Q           = 250.0    # -   assumed quality factor of the oscillator
                               #     (a real balance+hairspring is 200-400).
                               #     Used ONLY for the power-budget estimate.

# =============================================================================
# 4.  AXIS POSITIONS ON THE MAIN PLATE  (origin = centre-wheel axis)
#     +Y = 12 o'clock, +Z = towards the dial / viewer.
#     Every position equals the exact theoretical centre distance of its mesh;
#     calc.py verifies this (check C-17).
#     NOTE the barrel drum is recessed THROUGH the main plate (Z -18 .. +1.5)
#     so that its 152 mm footprint never collides with the going train, which
#     all lives at Z +2 .. +9 in front of the plate.
# =============================================================================

CD_BARREL_GREAT   = M_BARREL_GEAR * (Z_BARREL_GEAR + Z_GREAT_WHEEL) / 2.0      # 49.0
CD_GREAT_CENTRE   = M_GREAT_PINION * (Z_GREAT_PINION + Z_CENTRE_WHEEL) / 2.0   # 21.0
CD_CENTRE_INTER   = M_CENTRE_PINION * (Z_CENTRE_PINION + Z_INTER_WHEEL) / 2.0   # 42.5
CD_INTER_CARRIAGE = M_CARRIAGE_RIM * (Z_INTER_PINION + Z_CARRIAGE_RIM) / 2.0    # 37.8
# stud distance from the centre arbor; identical for both motion-works meshes
CD_MOTION         = M_CANON_PINION * (Z_CANON_PINION + Z_MINUTE_WHEEL) / 2.0    # 28.8
CD_MOTION_2       = M_MINUTE_PINION * (Z_MINUTE_PINION + Z_HOUR_WHEEL) / 2.0    # 28.8
assert abs(CD_MOTION - CD_MOTION_2) < 1e-9, \
    "motion works: the two meshes must span the same stud distance"
CD_EPICYCLIC      = M_FIXED_FOURTH * (Z_FIXED_FOURTH + Z_ESCAPE_PINION) / 2.0   # 12.5

POS_CENTRE_WHEEL  = (0.0, 0.0)
POS_GREAT_WHEEL   = (0.0, CD_GREAT_CENTRE)                          # (0, +21.0)
POS_BARREL        = (0.0, CD_GREAT_CENTRE + CD_BARREL_GREAT)        # (0, +70.0)
POS_INTERMEDIATE  = (0.0, -CD_CENTRE_INTER)                         # (0, -42.5)
POS_CARRIAGE      = (0.0, -(CD_CENTRE_INTER + CD_INTER_CARRIAGE))   # (0, -80.3)
POS_FIXED_FOURTH  = POS_CARRIAGE                                    # concentric
POS_MOTION_WORKS  = (CD_MOTION, 0.0)                                # (28.8, 0)

# The barrel axis -> centre axis LAYOUT distance.  This is NOT a mesh centre
# distance (the barrel does not mesh with the centre wheel directly); it is
# CD_GREAT_CENTRE + CD_BARREL_GREAT and both meshes lie on the same line.
CD_BARREL_CENTRE  = CD_GREAT_CENTRE + CD_BARREL_GREAT               # 70.0

# =============================================================================
# 5.  TOURBILLON CARRIAGE INTERNAL LAYOUT  (carriage-local coordinates)
#     Origin = carriage axis.  +Y = towards the seconds pointer at zero.
# =============================================================================

CARRIAGE_BORE_R         = (M_CARRIAGE_RIM * Z_CARRIAGE_RIM - 2.5 * M_CARRIAGE_RIM) / 2 - 0.5
CARRIAGE_FLOOR_OD       = 62.0
CARRIAGE_FLOOR_THK      = 1.6
CARRIAGE_FLOOR_HOLE_D   = 30.0   # central opening.  It is large on purpose:
                                 #     the fixed fourth wheel (dia 22.5), its
                                 #     stub arbor AND the elongated escape
                                 #     pinion (which orbits at r = 12.5 with a
                                 #     7.5 mm tip circle, so it sweeps
                                 #     r = 8.75..16.25) all pass through it, and
                                 #     it is what lets the 48.75 mm
                                 #     intermediate wheel -- whose teeth reach to
                                 #     within 12.45 mm of the carriage axis --
                                 #     pass UNDER the carriage floor at
                                 #     Z 4.2..6.2.  The floor is therefore an
                                 #     annulus 15..31 mm.
CARRIAGE_PINION_HOLE_D  = 30.0   # same opening; no separate pinion hole needed
CARRIAGE_RIM_BAND_H     = 5.5    # 3.5 mm solid + 2.0 mm pocketed
CARRIAGE_UPPER_BRIDGE_L = 40.0
CARRIAGE_UPPER_BRIDGE_W = 5.0
CARRIAGE_UPPER_BRIDGE_T = 1.6
CARRIAGE_COLUMN_D       = 4.0
CARRIAGE_COLUMN_N       = 3
CARRIAGE_COLUMN_R       = 23.0
# Column angular positions, degrees from +X counter-clockwise in carriage-local
# coordinates.  SOLVED, not chosen: a column at radius 23 must clear the balance
# (r 15 at y +14 -> sin(theta) <= 0.677) and the escape wheel (r 10 at y -12.5
# -> sin(theta) >= -0.941), which leaves the arcs [137.4, 250.2] and
# [289.8, 402.6] degrees.  150 / 240 / 330 is the even three-column set that
# fits, and it also keeps the columns clear of the two balance arms at +/-90 deg
# to the lever axis.
CARRIAGE_COLUMN_ANGLES  = (150.0, 240.0, 330.0)
CARRIAGE_ARBOR_D        = 8.0    # carriage sleeve OD (rotates on the plate)
FIXED_4TH_BOSS_D        = 5.0    # stub arbor carrying the fixed fourth wheel
CARRIAGE_MASS_CEILING_G = 20.0   # g   rotating assembly mass ceiling.  The
                                 #     carriage bearing loss dominates the whole
                                 #     power budget, so this is a hard target.

# escapement sub-assembly (all on the carriage Y axis, stacked in Z)
Y_ESCAPE         = -11.25    # escape arbor centre = -CD_EPICYCLIC EXACTLY.
                            # The escape pinion and the escape wheel are coaxial
                            # on this arbor (as in every real tourbillon) and are
                            # separated from the fixed fourth wheel in Z, not in
                            # radius: the pinion hangs BELOW the carriage floor
                            # (local -2.5 .. 1.9) to reach the fixed fourth wheel
                            # at movement Z 1.5 .. 3.5, while the escape wheel
                            # sits ABOVE the floor (local 2.0 .. 3.2).
Y_PALLET         = -1.0     # pallet-lever arbor centre.  Inline Swiss lever:
                            #     pivot -> escape centre 11.5 mm (= 1.15 x r_esc)
                            #     pivot -> impulse pin   11.5 mm
Y_BALANCE        = 14.0     # balance staff centre
ESCAPE_WHEEL_OD  = M_ESCAPE_WHEEL * Z_ESCAPE_WHEEL      # 20.0
ESCAPE_WHEEL_THK = 1.2
ESCAPE_PINION_H  = 2.5
BALANCE_OD       = 28.0
BALANCE_RIM_W    = 3.0
BALANCE_RIM_T    = 2.0
BALANCE_ARM_N    = 2
BALANCE_ARM_W    = 4.0
BALANCE_ARM_T    = 1.6
BALANCE_ARM_ANGLE = 90.0    # arms at +/-90 deg to the lever axis so the lever
                            # fork passes through the gap between them
ROLLER_D         = 8.0
IMPULSE_PIN_R    = 3.5      # impulse-pin circle radius on the roller
IMPULSE_PIN_D    = 1.6
PALLET_LEVER_LEN = 11.5     # pivot -> fork-horn tip; must reach the impulse
                            # pin circle at Y_BALANCE - IMPULSE_PIN_R = 9.5
PALLET_LEVER_W   = 5.0
LOCK_ANGLE_DEG   = 1.5
DROP_ANGLE_DEG   = 1.0
IMPULSE_FRACTION = 0.42
PALLET_STONE_L   = 2.6
PALLET_STONE_W   = 1.6
LEVER_BANKING_DEG = 6.0

HAIRSPRING_OD    = 26.0
HAIRSPRING_ID    = 16.0
HAIRSPRING_T     = 0.06
HAIRSPRING_B     = 1.80
REGULATOR_RANGE_S_PER_DAY = 60.0

# =============================================================================
# 6.  Z STACK (thickness budget).  z = 0 at the FRONT face of the main plate,
#     +Z towards the dial / viewer, -Z towards the wall.
#     Row: (name, z_bot, z_top, footprint_OD).  footprint_OD is the ANNULAR
#     outer diameter and HUB_OD the inner diameter, so calc.py can treat wheels
#     as rings rather than solid discs.
# =============================================================================

HUB_OD = {
    "main plate": 0.0,
    "fixed fourth wheel": 5.0,
    "great wheel": 12.0,
    "great pinion": 3.0,
    "centre wheel": 6.0,
    "carriage rim gear": 56.1,
    "intermediate pinion": 4.0,
    "centre pinion": 4.0,
    "barrel gear": 16.0,
    "barrel drum": 60.0,
    "intermediate wheel": 12.0,
    "barrel cover": 60.0,
    "hour wheel": 20.0,
    "minute pinion": 4.0,
    "ratchet + click": 10.0,
    "minute wheel": 14.0,
    "canon pinion": 4.0,
    "top bridge (skeleton)": 0.0,
    "dial ring": 230.0,
    "hands": 0.0,
    "crystal / bezel": 285.0,
}

# The barrel drum is recessed through the plate so that its 152 mm footprint
# (centre at y = +70) never meets the going train, which lives at Z +2 .. +9.
# Sorted by z_bottom.  Total movement thickness = last z_top - first z_bottom.
Z_MOVEMENT = [
    ("barrel cover",           -19.5, -18.0, 148.0),
    ("barrel drum",            -18.0,   1.5, 152.0),
    ("main plate",              -5.0,   0.0, 296.0),
    ("fixed fourth wheel",       1.5,   3.5,  18.9),
    ("barrel gear",              2.0,   4.0,  22.4),
    ("great wheel",              2.0,   4.0,  80.9),
    ("carriage rim gear",        6.4,   8.0,  68.6),
    ("great pinion",             2.0,   8.6,   7.5),
    ("intermediate pinion",      4.0,   8.0,   9.8),
    ("intermediate wheel",       4.0,   6.0,  46.2),
    ("centre pinion",            4.0,   9.5,   7.2),
    ("centre wheel",             6.6,   8.6,  37.5),
    ("ratchet + click",          9.0,  12.0,  39.0),
    ("canon pinion",            10.0,  12.0,  12.96),
    ("minute wheel",            10.0,  12.0,  47.52),
    ("minute pinion",           12.0,  14.0,  16.2),
    ("hour wheel",              12.0,  14.0,  45.0),
    ("hour pipe",               14.0,  29.0,   9.0),
    ("minute pipe",             12.0,  30.0,   6.0),
    ("top bridge (skeleton)",   20.0,  25.0, 296.0),
    ("dial ring",               26.0,  28.0, 300.0),
    ("hands",                   28.5,  31.5, 300.0),
    ("crystal / bezel",         32.0,  36.0, 300.0),
]

# Windows that MUST be cut in the top bridge and the main plate.  The skeleton
# bridge is not an annulus, it is a set of arms, so the interference checker
# models it as a full disc and these windows are verified separately (C-18b).
PLATE_WINDOWS = [
    # The barrel drum passage used to be BARREL_DRUM_OD + 4.0 = 156.0, which at
    # POS_BARREL = (0, 70) reaches 70 + 78 = 148.0 -- EXACTLY the plate radius.
    # A window tangent to the rim leaves no material at all at 12 o'clock, and
    # it also makes every 2-D boolean that touches it degenerate.  +2.0 leaves
    # 0.5 mm of radial clearance on the drum each side and 1.0 mm of rim; C-18d
    # now checks that margin against the selected process instead of assuming it.
    ("barrel drum passage",   POS_BARREL,        BARREL_DRUM_OD + 2.0),
    ("carriage window",       POS_CARRIAGE,      74.0),
    ("winding / ratchet",     POS_BARREL,        42.0),
    ("intermediate arbor",    POS_INTERMEDIATE,  12.0),
]
# (name, centre, window diameter, members that must pass through / be seen
#  through it).  C-18b checks the diameter against the members actually listed,
#  which is the only way to size a window honestly.
BRIDGE_WINDOWS = [
    ("carriage window",     POS_CARRIAGE,     74.0,
     ("seconds pointer", "carriage upper bridge")),
    ("barrel / winding",    POS_BARREL,       44.0,
     ("ratchet + click", "barrel gear")),
    ("motion works",        POS_MOTION_WORKS, 64.0, ("motion works",)),
    ("centre pipes",        POS_CENTRE_WHEEL, 13.0, ("hour pipe", "minute pipe")),
]

Z_CARRIAGE = [
    ("escape pinion teeth",     -5.0, -2.6,   5.4),
    ("escape arbor",            -5.0,  3.2,   1.5),
    ("carriage lower plate",       0.0,  1.6,  62.0),
    ("escape wheel",               2.0,  3.2,  20.0),
    ("pallet lever + stones",      2.2,  4.2,  24.0),
    ("roller + impulse pin",       2.8,  4.4,   8.0),
    ("balance wheel",              4.8,  6.8,  28.0),
    ("hairspring",                 7.1,  8.0,  26.0),
    ("carriage upper bridge",      8.4, 10.0,  40.0),
    ("balance endstone",          10.0, 10.8,   6.0),
    ("carriage top cap",          10.8, 12.2,  20.0),
    ("seconds pointer",           12.2, 13.0,  62.0),
]

# The carriage base sits at Z_CARRIAGE_Z0 on the movement stack, so that the
# elongated escape pinion (carriage-local -2.0) reaches the fixed fourth wheel
# (movement Z 1.5 .. 3.5) through the hole in the carriage floor.
Z_CARRIAGE_Z0 = 6.4

CARRIAGE_TARGET_H_MIN = 12.0
CARRIAGE_TARGET_H_MAX = 20.0

# =============================================================================
# 7.  DERIVED CONSTANTS AND HELPERS
# =============================================================================

def carriage_ratio_total():
    """centre wheel -> carriage = (zIW/zCP) x (zRG/zIP)."""
    return (Z_INTER_WHEEL / Z_CENTRE_PINION) * (Z_CARRIAGE_RIM / Z_INTER_PINION)


def barrel_to_centre():
    """Speed reduction barrel -> centre arbor = (zGW/zBG) x (zCW/zGP)."""
    return (Z_GREAT_WHEEL / Z_BARREL_GEAR) * (Z_CENTRE_WHEEL / Z_GREAT_PINION)


def motion_ratio():
    return (Z_MINUTE_WHEEL / Z_CANON_PINION) * (Z_HOUR_WHEEL / Z_MINUTE_PINION)


def epicyclic_ratio():
    return Z_FIXED_FOURTH / Z_ESCAPE_PINION


def carriage_rpm_from_beat(f_hz=BEAT_HZ):
    """omega_carriage [rpm] = f * zEP / (z_E * z4) * 60"""
    return f_hz * Z_ESCAPE_PINION / (Z_ESCAPE_WHEEL * Z_FIXED_FOURTH) * 60.0


def beat_from_carriage(carriage_rpm):
    return carriage_rpm / 60.0 * Z_ESCAPE_WHEEL * epicyclic_ratio()


def rim_tip_od():
    return M_CARRIAGE_RIM * Z_CARRIAGE_RIM + 2 * M_CARRIAGE_RIM


def rim_root_od():
    return M_CARRIAGE_RIM * Z_CARRIAGE_RIM - 2.5 * M_CARRIAGE_RIM


if __name__ == "__main__":
    print("barrel->centre ratio    :", barrel_to_centre(), "(4.0 x 6.0)")
    print("centre->carriage ratio  :", carriage_ratio_total(), "(must be 60)")
    print("motion works ratio      :", motion_ratio(), "(must be 12)")
    print("epicyclic z4/zEP        :", epicyclic_ratio())
    print("carriage rpm for 1 Hz   :", carriage_rpm_from_beat(1.0))
    print("beat Hz for 1 rpm cage  :", beat_from_carriage(1.0))
    print("cd barrel-great  %.3f  great at %s  barrel at %s"
          % (CD_BARREL_GREAT, POS_GREAT_WHEEL, POS_BARREL))
    print("cd great-centre  %.3f" % CD_GREAT_CENTRE)
    print("cd centre-inter  %.3f  inter at %s" % (CD_CENTRE_INTER, POS_INTERMEDIATE))
    print("cd inter-carriage %.3f  carriage at %s" % (CD_INTER_CARRIAGE, POS_CARRIAGE))
    print("cd epicyclic     %.3f  Y_ESCAPE %.1f" % (CD_EPICYCLIC, Y_ESCAPE))
    print("carriage rim tip OD %.2f  root OD %.2f  bore r %.2f"
          % (rim_tip_od(), rim_root_od(), CARRIAGE_BORE_R))
    print("drum reach          %.2f  plate radius %.1f"
          % (POS_BARREL[1] + BARREL_DRUM_OD / 2, DIAL_APERTURE / 2))
    print("carriage reach      %.2f" % (abs(POS_CARRIAGE[1]) + rim_tip_od() / 2))
    print("escape wheel OD     %.2f" % ESCAPE_WHEEL_OD)
