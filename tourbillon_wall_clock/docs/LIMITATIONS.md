# LIMITATIONS, UNVALIDATED ITEMS, AND WHAT WOULD HAVE TO BE PROVEN BY TEST

**Read this before building anything.**

This document exists because a CAD model cannot prove that a mechanism works.
Everything in this repository that *is* proven is proven by a computation that
was actually run, and every computation that was run is listed with its result.
Everything that is *not* proven is listed here, with the reason and with the
test that would settle it.

Nothing in this project should be described as a working mechanical clock until
the items in section 1 have been closed on a built movement.

---

## 0. Status of the deliverables in one table

| Deliverable | Status | Where |
|---|---|---|
| OpenSCAD sources (15 files) | written, statically linted, **not compile-tested** (no OpenSCAD binary exists in this environment) | `*.scad`, `tools/scad_lint.py` |
| Assembly model | written; geometry verified by computation | `assembly.scad` |
| Exploded view | written; geometric animation only | `exploded_view.scad` |
| Gear / ratio table | **verified**, 46 checks pass | `docs/GEAR_TRAIN.md` |
| Tooth geometry | **verified**, 77 measurements pass | `tools/profile_check.py` |
| Tolerance table | written; **values are uncalibrated starting points** | `docs/TOLERANCES.md` |
| BOM, made vs bought | written | `BOM.csv`, `docs/BOM_MADE.csv`, `docs/BOM_BOUGHT.csv` |
| Arbor / shaft schedule | written; loads are **estimates**, not measurements | `docs/SHAFTS.md`, `shafts_and_bearings.scad` |
| STL per part | **25 of 46 verified and written; 21 refused** | `stl_output/`, section 6 |
| Dimensional + arbor drawings | generated from the same constants | `docs/DRAWING_LAYOUT.svg`, `docs/DRAWING_ARBORS.svg` |
| Assembly procedure | written | `docs/ASSEMBLY.md` |
| Adjustment / first test | written | `docs/ASSEMBLY.md` section 3 |
| This limitations register | this file | `docs/LIMITATIONS.md` |

Verification actually executed, with results:

| Suite | Command | Result |
|---|---|---|
| design + validation | `python3 tools/calc.py --report` | **46 checks, 0 failed** |
| tooth-profile geometry | `python3 tools/profile_check.py` | **77 measurements, 0 failed** |
| SCAD static lint | `python3 tools/scad_lint.py` | **15 files, 0 findings** |
| STL modeller self-test | `python3 tools/gen_stl.py --self-test` | **0 failures** |
| STL export | `python3 tools/gen_stl.py` | 25 written, 21 refused |

---

## 1. What CAD cannot prove — the timekeeping question

**The single most important limitation: nothing here demonstrates that this
clock keeps time.** The following are all *assumed or computed*, never measured,
and each one has to be settled on a physical movement with a timegrapher:

- **Amplitude.** The whole power budget is computed at a assumed balance
  amplitude of 180°. A real balance in a real escapement at this size might
  reach 120° or 240°, and the torque the escapement needs scales with it.
- **Isochronism.** The hairspring's rate versus amplitude is not modelled at
  all. No CAD system can predict it.
- **Friction.** Every pivot loss in the power budget uses a *chosen* coefficient
  (μ = 0.04 best / 0.08 nominal / 0.15 pessimistic). These are literature
  values for oiled steel-in-jewel, not measurements of these bearings. The
  pessimistic case already halves the run time (3.2 d → 2.3 d).
- **Lubrication regime.** Boundary, mixed or hydrodynamic — assumed, not
  analysed.
- **Positional error.** A tourbillon is supposed to average out positional
  error. Whether this one does depends on poising, on the balance's own
  imbalance and on the detent's behaviour, none of which is modelled.
- **Thermal drift.** Nothing here is temperature-compensated. The hairspring
  modulus and the balance inertia both drift, and the pendulum-sized balance
  makes that worse, not better.
- **The escapement's actual behaviour.** Lock, drop, impulse fraction and draw
  are set to conventional values (1.5° per stone, 1.0° drop, 0.42 impulse
  fraction, 12° draw) and the *geometry* is verified to be consistent. Whether
  the lever actually unlocks cleanly at 1 Hz with a 30 mm balance is a bench
  question.

**Required test:** build the movement, put the balance on a timegrapher, measure
rate, amplitude and beat error in six positions, and only then claim anything
about timekeeping.

---

## 2. Architecture limitations forced by geometry

### L-01 — the classical Breguet under-carriage pinion does not fit at 70 mm
The textbook tourbillon puts a pinion *under* the carriage, meshing with the
third wheel, and the escape pinion meshing with a fixed fourth wheel on the
carriage axis. At the required 70 mm carriage envelope with this train's centre
distances, that layout does not close: the under-pinion would have to sit at a
radius the carriage floor does not have. **Decision:** rim-driven carriage
(Helwig / IWC Mystère style) — an intermediate pinion drives teeth on the
carriage rim, and the fixed fourth wheel is concentric with the carriage axis,
reached through a Ø30 mm opening in the carriage floor. Consequence: the
carriage rim gear (z = 96, m = 0.70, tip Ø68.60) is a *loaded* gear and part of
the carriage's rotating mass, which is why the carriage is heavy (section 4).

### L-02 — the carriage envelope is 68.60 mm, not the 70 mm target
`TOURBILLON_DIAMETER = 70` is the target envelope. The rim gear's tip circle is
Ø68.60 mm, which is inside the target, and check C-34 verifies both it and the
300 mm clock diameter. The 1.40 mm difference is the tip-circle allowance; it
is deliberate, not an error.

### L-03 — one going barrel cannot give 7 days
The mainspring is computed from a closed-form stress limit, not chosen:
σ = 1400 MPa at full wind, strip 0.42 × 18 mm, active length 1029.0 mm, stored
energy 10.589 J, 3.231 barrel turns from full wind to flat. At 1.0000 barrel
turn per day that is **3.23 days (77.5 h)**, against a 3.0-day target. A 7-day
barrel would need roughly twice the drum diameter or a thinner, longer spring
past its stress limit. **Do not quote 7 days for this movement.**

### L-04 — there is no maintaining power
The winding interface is a key entering from the front through the dial
aperture, driving a 10 mm square on a sleeve inside the Ø60 mm barrel arbor,
with a ratchet (z = 24, m = 1.5) and a click. **During winding the train is
unpowered**, so the clock stops for the duration. A real going-barrel clock
would have a maintaining spring or a Harrison-style device. Adding one is a
design change, not a parameter.

### L-05 — the motion works needs two different modules
The hour wheel must be concentric with the centre arbor while the minute wheel
and minute pinion share one stud, so both meshes must span the same stud
distance. A single module cannot do it: `m(16+64)/2 = 36.0 ≠ m(16+48)/2 = 28.8`.
The design uses **m₁ = 0.8 · m₂** (canon pinion / minute wheel at m = 0.72,
minute pinion / hour wheel at m = 0.90), which closes both meshes on exactly
28.800 mm. Check C-07b verifies this and reports that a single-module
alternative would misplace the hour wheel by 7.200 mm. Consequence: the motion
works has two cutters, not one.

### L-06 — the barrel drum passage nearly breaches the plate rim
The drum is Ø152 at (0, 70) on a Ø296 plate, so it reaches 146 mm against a
148 mm plate radius: 2 mm of rim. The passage window was originally Ø156, which
reached **exactly** 148.000 mm — tangent to the rim, leaving zero material at
12 o'clock. It is now Ø154 (1.000 mm rim margin). Check **C-18d** now tests
every plate and bridge window against the selected process's minimum wall
instead of assuming the margin. Note that 1.000 mm still fails the resin
(1.2 mm) and FDM (2.0 mm) minimum walls: **the main plate must be machined.**

---

## 3. Parts that cannot be made as modelled

### L-07 — the hairspring must be bought, made to measured inertia
The computed hairspring (k = 0.02633 N·mm/rad for J = 666.8 g·mm² at 1.000 Hz)
needs an active length of 246.2 mm in 3.73 turns, with σ_inner = 750 MPa at
180° amplitude — inside the 1400 MPa limit, so the *design* is sound. But a
first attempt at t = 0.12 mm / ID 5 mm gave **4920 MPa** and failed check C-25.
A spring of this stiffness at this size is not a printable or a casually
wound part. **It must be ordered from a hairspring maker, or adapted from a
marine-chronometer / regulator spring, and matched to the MEASURED inertia of
the finished balance — not to the CAD value.** BOM item B-02.

### L-08 — the escape wheel and the pallet stones are not printable
The 15-tooth Swiss club escape wheel (OD 20.0, m = 1.3333) and the two ruby
pallet stones need locking faces at Ra < 0.2 µm and above 60 HRC. No additive
process delivers either. **Wire-EDM from 1.4034 mm stock, then lapped.** The
stones are bought, cut and polished (BOM B-01 group). In `parts_export.scad`
both are labelled `Decorative-reference` and the exporter **refuses** to write
an STL for them, so nobody can print a part that cannot work.

### L-09 — the balance is enormous for its rate
A Ø30 mm balance oscillating at 1.000 Hz has J = 666.8 g·mm², roughly four
thousand times a wristwatch balance. That is a deliberate consequence of
choosing 1 Hz (a wall-clock rate) with a visible 70 mm carriage, and it is why
the escapement needs the torque it needs. It also means the balance is very
sensitive to poising and to any residual unbalance. **Raising the beat rate to
reduce torque was tried and abandoned** — it does not help at this size.

### L-10 — no printed hole is a bearing, anywhere
Every pivot in `shafts_and_bearings.scad` is a hardened steel arbor in a jewel,
a bronze bush or a ball race. The printed or milled hole in a plate is a *seat*
for that bearing, never the bearing. `docs/SHAFTS.md` gives the seat diameter,
pivot diameter, span, axial play and radial clearance for each of S-01…S-09.
The finest is S-05, the carriage axis: Ø8 × 26, pivot Ø3.0, span 18, axial play
0.04 mm, radial clearance ≤ 0.015 mm, hardened and lapped, ball race below and
a ruby jewel above.

### L-11 — FDM cannot build the functional parts
The thinnest functional wall in the movement is **1.20 mm** (the carriage
floor). The metal preset allows 0.80 mm and resin 1.20 mm; **FDM needs 2.00 mm**
(check C-32). The smallest arbor is 1.2 mm (C-33) and the smallest printable
hole in the FDM preset is 1.6 mm. **An FDM build of this movement is a shape
mock-up only**; the escapement is refused outright in the FDM preset.

---

## 4. Mass, inertia and poising — computed, not measured

| Quantity | Value | Note |
|---|---|---|
| carriage mass alone | 24.089 g | floor 6.99, rim band 8.41, upper bridge 2.02, columns 1.93, sleeve arbor 4.74 |
| rotating mass | 33.677 g | carriage + escapement |
| J about the carriage axis | 1.438 × 10⁻⁵ kg·m² | 1.5048 × 10⁻⁵ incl. escapement |
| static moment | 72.785 g·mm | |
| centre-of-mass offset | 2.161 mm | from the rotation axis |
| gravity torque on the carriage | 7.14 × 10⁻⁴ N·m | **0.60 ×** the available escape torque |
| poise specification | ≤ 12 360.50 mg·mm | CoM ≤ 0.367 mm |
| counter-mass fitted | 2.426 g at r = 30 mm | modelled as `carriage_counter_mass` |

**L-12 — a 33.7 g rotating carriage is about a hundred times a real tourbillon
carriage** (~0.3 g). This follows directly from L-01: because the carriage is
rim-driven, the rim gear is part of the rotating mass. The gravity torque the
unpoised carriage applies to the train is 0.60 × the escape torque, which is
why poising is a specification and not an option. **These masses are computed
from the modelled volumes and nominal densities; they are not weighings.**
Poise must be checked on a poising tool and corrected with the poising screws
in the BOM.

**L-13 — the carriage rotation rate is derived, not assumed.**
ω_carriage = f · z_EP / (z_E · z₄) = 1.000 × 10 / (15 × 40) = **1.000 rpm**,
and the seconds hand is driven off the carriage, so the tourbillon *is* the
seconds display. This is tied to the escapement frequency by that equation; if
the balance is not at 1.000 Hz the carriage is not at 1 rpm and the seconds
indication is wrong. Check C-01…C-34 verify the chain end to end.

---

## 5. Tolerances are starting points, not a qualified scheme

`docs/TOLERANCES.md` and `parameters.scad` carry three presets, all of them
**uncalibrated**:

| preset | fit clearance | axial play | radial play | backlash | hole growth | min wall | min hole | Ra | escapement allowed |
|---|---|---|---|---|---|---|---|---|---|
| `fdm` | 0.40 | 0.40 | 0.20 | 0.45 | 0.40 | 2.00 | 1.60 | 12 | **NO** |
| `resin` | 0.15 | 0.15 | 0.05 | 0.18 | 0.10 | 1.20 | 0.80 | 3 | prototype only |
| `metal` | 0.03 | 0.10 | 0.02 | 0.08 | 0.00 | 0.80 | 0.30 | 0.4 | YES |

**L-14 — none of these numbers is qualified for any specific machine, material
or operator.** They must be replaced by values measured from **calibration
coupons** printed or milled on the actual equipment before a final build: a
hole/pin matrix for fit clearance, a tooth-pair gauge for backlash, and a
shrink coupon for `PRINT_SHRINK_SCALE`. Selecting a preset is
`MANUFACTURING = "fdm" | "resin" | "metal"`; the default is `metal`.

**L-15 — precision timekeeping parts must not be fully printed.** The
escapement, the balance, the hairspring and every arbor are metal parts in the
BOM. A printed version of any of them is a geometry check, not a component.

---

## 6. The STL export is partial, and says so

There is no OpenSCAD binary in this environment, so the `.scad` files could not
be compiled to STL. `tools/gen_stl.py` is an **independent second
implementation** of the same part geometry that reads the same constants out of
`parameters_auto.scad` (with `cross_check()` proving the two sources agree),
resolves each part's 2-D booleans exactly, and writes binary STL.

Every part is verified before it is written, by three measurements rather than
by trusting the construction:

1. the **signed volume** of the emitted triangles equals the analytic slab
   volume (positive only if every normal points outward);
2. every directed edge appears exactly as often as its reverse (**closed and
   consistently oriented**);
3. the bounding box is finite and non-degenerate.

**Result of the last run: 25 parts written and verified, 21 refused.**

The refusals are not silent. `python3 tools/gen_stl.py` prints each refused
part with its analytic volume, its mesh volume and the reason. The cause in
every case is the same: a part whose cross-section needs *two void loops that
share a boundary* (a slot cut through an annulus, a lightening pocket touching
a bore), which the pure-Python hole-bridging triangulator cannot represent as a
single watertight cap. The 25 parts that do export include every gear rim,
pinion body, pipe, pillar, jewel, cap, hand and the two large skeleton plates'
simpler members.

**To get the other 21 as manufacturing geometry, install OpenSCAD and use the
authoritative exporter:**

```sh
openscad -o stl_output/carriage_floor.stl -D 'PART_TO_EXPORT="carriage_floor"' main.scad
```

`parts_export.scad` holds the 50-row part registry with each part's
`Functional` / `Prototype` / `Decorative-reference` label, its process and its
material, and it refuses to export anything labelled `Decorative-reference`.
Until those 21 files exist, **the STL set is incomplete and must not be
described as "STL per printable part" without that qualifier.**

**L-16 — no STL here has been sliced, and none has been printed.**
Watertightness and correct outward normals are verified by computation
(section above); printability, orientation, support strategy and shrinkage are
not.

---

## 7. The OpenSCAD sources are linted, not compiled

**L-17 — the `.scad` files have never been through the OpenSCAD compiler**,
because none is installed and none is available to install in this environment.
What was actually done instead is `tools/scad_lint.py`, which reports only
checks it performs:

- **L-01** every file is pure ASCII
- **L-02** `()`, `[]`, `{}` balance, ignoring comments and strings
- **L-03** the whole file tokenises (no stray characters, no unterminated literal)
- **L-04** every module and function called is defined here or is an OpenSCAD builtin
- **L-05** every bare identifier read is assigned somewhere: a parameter, an
  argument, a `let`/comprehension binding, or a value exported into
  `parameters_auto.scad`
- **L-06** the include graph has no cycles and every include resolves
- **L-07** a file that reads exported constants includes `parameters.scad`
- **L-08** the numeric constants in `gear_generator.scad` agree, evaluated, with
  `tools/gearmath.py`
- **L-09/L-10** the part registry is complete, and nothing labelled
  `Decorative-reference` is reachable from an export path
- **L-11** no constant is declared twice — which caught a real bug: see below

Two genuine defects were found and fixed by this linter, and both would have
been silent in a compiler:

- **A name collision that would have destroyed every tooth count.**
  `parameters.scad` includes `parameters_auto.scad` and then declared 13
  Z-stack ranges with the *same names* as tooth counts (`Z_GREAT_WHEEL = 56`
  versus `Z_GREAT_WHEEL = [2.0, 4.0]`). In OpenSCAD the last assignment wins, so
  every gear would have been built from a list instead of an integer. The ranges
  are now `ZR_*` and L-11 fails the build if any name is ever declared twice.
- **A motion-works module that could not close.** Both meshes have to span the
  same stud distance and a single module gives 36.0 mm versus 28.8 mm. Fixed by
  m₁ = 0.8 · m₂ (L-05 above), now covered by check C-07b.

A linter is not a compiler. **Before trusting the model visually, install
OpenSCAD and render `main.scad`.**

---

## 8. Known modelling simplifications

- **L-18 — the mainspring coils are `Decorative-reference`.** The spring's
  *parameters* (length, thickness, width, stress, torque, energy, run time) are
  computed and validated; the drawn coils are a reference shape for the drum
  cavity, excluded from STL export, and they are not a model of how a real
  spring packs or unrolls.
- **L-19 — the hairspring drawn in `escapement.scad` is a reference spiral.**
  Its rate comes from the computed k, not from the drawn geometry. See L-07.
- **L-20 — the animation is geometric, not kinematic.** `parameters.scad`
  exposes `ang_centre()`, `ang_great()`, `ang_intermediate()`, `ang_carriage()`,
  `ang_escape_abs()`, `ang_escape_rel()` and `ang_hour()`, driven by
  `DRIVE_FROM_TRAIN`. These place the parts at the angles the *ratios* imply.
  There is no solver, no contact, no backlash behaviour and no dynamics: it is
  not a simulation and must not be described as one.
- **L-21 — the pallet stones, impulse pin and click spring have holder geometry
  and interfaces only.** They are bought or made to the dimensions in
  `docs/BOM_BOUGHT.csv`.
- **L-22 — the crystal is a bought part** with a modelled seat, not a designed
  component.

---

## 9. Items that need validation, in the order they should be done

1. **Install OpenSCAD and render `main.scad`** (closes L-17 for the whole model).
2. **Export the 21 refused STLs from OpenSCAD** (closes L-16's geometry half).
3. **Print or mill calibration coupons** and replace the tolerance presets with
   measured values (closes L-14).
4. **Make the arbors and jewels first**, and measure the actual pivot friction
   of one arbor before committing to the power budget (tests the μ assumption
   in section 1).
5. **Order the hairspring against the MEASURED balance inertia**, not the CAD
   value (L-07).
6. **Bench-test the escapement alone** — escape wheel, lever, balance — before
   assembling the carriage, and measure amplitude and lock (section 1).
7. **Poise the carriage on a poising tool** to ≤ 12 360.50 mg·mm (L-12).
8. **Assemble the full movement** and measure rate in six positions on a
   timegrapher, plus carriage speed with a tachometer to confirm 1.000 rpm and
   1.000 Hz (L-13).
9. **Measure the run time** against the computed 3.23 days (L-03).

Until steps 6–9 have passed, this repository contains a **verified geometric
and kinematic design**, not a working clock.
