# ASSEMBLY PROCEDURE, ADJUSTMENT AND FIRST TEST

The stages below are the **reverse of the exploded view** in
`exploded_view.scad`, whose `EXPLODE_STEP` table and `exploded_labels()` name
the same ten groups in the same order. Rendering
`openscad -D 'EXPLODED_VIEW=true' main.scad` shows the whole sequence pulled
apart along Z with the labels attached.

> **Before starting:** read `docs/LIMITATIONS.md`. In particular the escapement
> must not be printed (L-08, L-11), the hairspring must be ordered against the
> *measured* balance inertia (L-07), and no tolerance value in this document is
> qualified until calibration coupons have been measured on your own equipment
> (L-14). The carriage must be poised **off the clock** before stage 8.

**Datum convention:** the main plate's upper face is Z = 0. +Z points toward the
dial. +Y is 12 o'clock. Every position below is in that frame and comes from
`POS_*` in `parameters_auto.scad`.

---

## 1. Preparation

1. Confirm the process preset. `MANUFACTURING = "metal"` is the default and the
   only preset in which the escapement is permitted (check C-32, L-11).
2. Print or mill the **calibration coupons** described in `docs/TOLERANCES.md`
   and measure: hole/pin fit clearance, tooth backlash, and shrink. Enter the
   measured values into the preset you are using. Do not proceed with the
   default numbers for a final build.
3. Check every arbor against `docs/SHAFTS.md` (S-01 … S-09): diameter, pivot
   diameter, seat diameter, span, axial play, radial clearance. Measure, do not
   assume — the finest tolerance in the movement is the carriage axis at
   ≤ 0.015 mm radial.
4. Fit the jewels, endstones, bushes and the ball race into their seats and
   verify each one turns freely with its arbor before anything is assembled on
   top of it. A jewel fitted after the train is in place cannot be checked.

---

## 2. Assembly, in order

### Stage 2 — main plate (the datum)
The skeletonised main plate, Ø296 × 5.0, Z −5.0 … 0.0. It is the reference for
every other position; clamp it flat and do not machine anything after this
point. Its four windows (`PLATE_WINDOWS`) are:

| window | centre | diameter | rim margin |
|---|---|---|---|
| barrel drum passage | (0, 70) | **154.0** | 1.000 mm |
| carriage window | (0, −63.3) | 74.0 | 47.700 mm |
| winding / ratchet | (0, 70) | 42.0 | 57.000 mm |
| intermediate arbor | (0, −25.5) | 12.0 | 116.500 mm |

Check C-18d verifies those rim margins against the selected process's minimum
wall. The barrel passage margin is only 1.000 mm — **this plate must be
machined, not printed** (L-06).

### Stage 3 — barrel bushes, fixed fourth wheel
- Press the barrel bearing (MR85ZZ or a bronze bush, S-01) into the plate at
  (0, 70).
- Bolt the **fixed fourth wheel stub** to the plate at (0, −63.3), concentric
  with the carriage axis. Its boss is Ø5.0 (`FIXED_4TH_BOSS_D`) and the wheel
  itself sits at Z +1.5 … +3.5. This wheel **must not turn** — the whole
  escapement depends on it being stationary. Verify it after tightening.

### Stage 4 — arbors
Insert S-02 (centre, Ø4 × 42), S-03 (great wheel, Ø3 × 12), S-04 (intermediate,
Ø3 × 20) and the motion-works stud S-09 (Ø3 × 9, brass, pressed and peened) at
their `POS_*` positions. Check each one for free rotation and for the axial play
in `docs/SHAFTS.md` before continuing.

### Stage 5 — mainspring, barrel, ratchet
1. Fit the mainspring into the drum. The spring is BOM **B-01**: b = 18.0,
   t = 0.42, active length ≈ 1029 mm, ≈ 3.2 turns. Its hook engages the slot in
   the drum wall; the inner end engages the barrel arbor.
2. Fit the barrel drum (Ø154 window, drum Ø152 × 20, Z −18.0 … +1.5) onto
   S-01 and drop it through the plate passage.
3. Fit the barrel cover (Z −19.5 … −18.0) and its three screws.
4. Fit the ratchet wheel (z = 24, m = 1.5, Z +9.0 … +12.0) onto the winding
   sleeve, then the **click** and click spring. The click must hold the ratchet
   in *let-down* — check it by hand before winding.
5. Wind a quarter turn and confirm the click drops into the next tooth with an
   audible and tactile detent, and that the train cannot drive the key backwards.

> **Let-down control:** there is **no maintaining power** (L-04). The clock
> stops while you wind. Let the spring down through the train only with the
> click lifted and a finger on the key; never let it run free.

### Stage 6 — going train
In mesh order, each at its own Z band and each verified by turning the previous
one:

| # | member | teeth | module | centre distance | Z band |
|---|---|---|---|---|---|
| 1 | barrel gear → great wheel | 14 → 56 | 1.40 | 49.000 | +2.0 … +4.0 |
| 2 | great pinion → centre wheel | 8 → 48 | 0.75 | 21.000 | +2.0 … +8.6 |
| 3 | centre pinion → intermediate wheel | 10 → 75 | 0.60 | 25.500 | +4.0 … +6.0 |
| 4 | intermediate pinion → carriage rim gear | 12 → 96 | 0.70 | 37.800 | +4.0 … +8.0 |

Cumulative ratio barrel → carriage: 4.0 × 6.0 × … = **60.000** from the centre
wheel to the carriage, and **24.000** from the barrel to the centre wheel.
After this stage, turning the barrel by hand should rotate the intermediate
pinion freely with no binding at any angular position — turn it through at least
one full revolution of each wheel to be sure, since a single position can hide a
tight mesh.

### Stage 7 — motion works
At the stud (28.800, 0), S-09:
- canon pinion z = 16, **m = 0.72**, Z +10.0 … +12.0 (friction grip — see the
  adjustment note below)
- minute wheel z = 64, **m = 0.72**, Z +10.0 … +12.0
- minute pinion z = 16, m = 0.90, Z +12.0 … +14.0
- hour wheel z = 48, m = 0.90, Z +12.0 … +14.0
- hour pipe Ø9, Z +14.0 … +29.0; minute pipe Ø6, Z +12.0 … +30.0

Both meshes span exactly **28.800 mm** (check C-07b). The two modules are not a
mistake — a single module cannot close both meshes on one stud distance (L-05).

### Stage 8 — the tourbillon carriage (poised OFF the clock)
Build and poise the carriage as a sub-assembly, in carriage-local coordinates
(`escapement.scad` and `tourbillon_cage.scad` use these), then fit it whole.

1. **Carriage floor** Ø62 × 1.6 with a Ø30 central opening, local Z 0 … 1.6
   (global +6.4 … +8.0). This is the thinnest functional wall in the movement at
   1.20 mm — machined or resin only, never FDM (C-32).
2. **Escape pinion** (z = 10, m = 0.45) hanging *below* the floor, local
   Z −5.0 … −2.6, on the escape arbor at local y = −11.25. It must reach the
   fixed fourth wheel through the floor opening.
3. **Escape wheel** (15 teeth, OD 20.0) on the same arbor, local Z +2.0 … +3.2 —
   coaxial with the pinion at exactly r = 11.25 from the carriage axis,
   separated in Z only. Wire-EDM and lapped; **not printable** (L-08).
4. **Pallet lever** at local y = −1.0, Z +2.2 … +4.2, with the two ruby stones
   set and shellacked. Entry stone 12°, exit 10°, draw 12°, lock 1.5° per stone.
5. **Roller** Ø8 with the impulse pin at r = 3.5, local Z +2.8 … +4.4, on the
   balance staff at local y = +14.0.
6. **Balance wheel** Ø28, local Z +4.8 … +6.8, then the **hairspring**
   (OD 26 / ID 16) at +7.1 … +8.0 with its stud. The spring is B-02 and must be
   matched to the *measured* inertia of the balance you just made (L-07).
7. **Three columns** Ø4 at r = 23 and angles **(150°, 240°, 330°)** — not 120°
   spacing, because the escape wheel and pallet stones occupy the other sectors.
8. **Upper bridge** 40 × 5 × 1.6, local Z +8.4 … +10.0, with the three jewels
   and the balance endstone (+10.0 … +10.8).
9. **Sleeve arbor** Ø8 through the centre, **top cap**, and the **seconds
   pointer** at local +12.2 … +13.0.
10. **Counter-mass** 2.426 g at r = 30 on the floor's underside.
11. **Poise the carriage before fitting it.** Target ≤ 12 360.50 mg·mm, i.e.
    centre of mass within 0.367 mm of the axis (L-12). The as-modelled static
    moment is 72.785 g·mm and the CoM offset 2.161 mm, which would put
    0.60 × the available escape torque into the carriage bearing every time it
    rotates. Adjust with the poising screws until the carriage rests in any
    orientation with no preferred position.
12. Drop the poised carriage into the plate at (0, −63.3) onto the S-05 bearing
    (ball race below, ruby jewel above), and confirm the escape pinion has
    engaged the fixed fourth wheel. Turn the carriage by hand through a full
    revolution: it must run freely at every angle with no mesh tightness.

### Stage 9 — pillars and top bridge
Five pillars at r = 118 on a 72° pitch, then the skeleton top bridge
(Ø296 × 5.0, Z +20.0 … +25.0). Its windows (`BRIDGE_WINDOWS`) declare exactly
which members pass through each one; check C-18b verifies each window is at
least 1.0 mm larger in diameter than the members listed for it. Tighten in a
star pattern and re-check the carriage's freedom afterwards — a distorted bridge
is the most common way to bind a carriage jewel.

### Stage 10 — dial, hands, case, crystal
Dial ring Z +26.0 … +28.0 (ID 232, with the twelve applied markers cut 0.4 deep),
hands at +28.5 … +31.5, case ring and crystal/bezel +32.0 … +36.0. The winding
key enters from the **front** through the dial aperture (Ø296 aperture in a
Ø300 case). Set the hands with the movement running, not stopped.

### Stage 1 — back cover and wall mount
Last, because it closes the case: back cover 2.5 mm and the three-point wall
mount at (−100, 60), (100, 60), (0, −200) → modelled as (0, −20) offset keyhole
slots. The whole clock is 300 mm diameter × 55.5 mm of movement stack
(`MOVEMENT_THICKNESS`), Z −19.5 … +36.0.

---

## 3. Adjustment

Adjust in this order. Each step assumes the previous one has been measured, not
assumed.

1. **Mesh depth (going train).** With the bridge screws slightly slack, let each
   pair find its own depth, then tighten in a star pattern and re-check freedom.
   Backlash comes from the preset (`TOOTH_BACKLASH`: metal 0.08, resin 0.18,
   fdm 0.45) and must be measured with a tooth-pair gauge, not read from the
   model.
2. **End float.** Each arbor's axial play is in `docs/SHAFTS.md`. Adjust by
   shimming the jewel seat, never by bending a bridge.
3. **Canon pinion friction.** The canon pinion is labelled `Prototype` in
   `parts_export.scad` because its grip is **set by adjustment, not by
   calculation**: it must be tight enough to carry the minute hand and to be set
   by hand, and slack enough to slip when the hands are moved without straining
   the train. Set it on the bench with a spring gauge and record the value you
   actually achieve — it is not in the model.
4. **Pallet stones.** Lock 1.5° per stone, drop 1.0°, draw 12°, banking 6°.
   Adjust the stones in the lever, not the lever on its arbor. Verify with a
   microscope and a locking gauge.
5. **Hairspring.** Set the effective length by the regulator until the rate is
   right, then re-check the amplitude — changing the length changes both.
6. **Poise.** Re-check the carriage after the escapement has run in, because
   shellac and oil move mass.

---

## 4. First test

Do these in order and **record the numbers**; none of them can be predicted from
the CAD.

1. **Free run, no spring.** Turn the carriage by hand. It must make a full
   revolution with uniform resistance and no tight spot.
2. **Quarter wind.** Wind a quarter turn. The train should start and the balance
   should oscillate. Listen for a clean, even tick with no double-bank or
   galloping.
3. **Timegrapher.** Measure rate, amplitude and beat error in six positions.
   Expected: **1.000 Hz = 2 beats/s = 7200 vph**, amplitude target 180° (that is
   the assumption the whole power budget rests on — measure it and, if it
   differs, recompute with `python3 tools/calc.py` after editing
   `BALANCE_AMPLITUDE_DEG`).
4. **Carriage speed.** Tachometer on the carriage: **1.000 rpm**. This is a
   derived result, not an assumption — ω = f·z_EP/(z_E·z₄) = 1.000 × 10/(15 × 40)
   — so if the balance is at 1.000 Hz the carriage must be at exactly 1 rpm and
   the seconds pointer must keep correct seconds.
5. **Seconds indication.** Compare the carriage-mounted seconds pointer against
   a reference over ten minutes. It is driven directly by the carriage, so an
   error here is a rate error, not a gearing error.
6. **Hand train.** Over 12 hours, check that the minute hand advances 12× the
   seconds and the hour hand 1/12 of the minute hand. The motion-works ratio is
   (64/16) × (48/16) = **12 exactly**.
7. **Run time.** Wind fully and time the stop. Computed: **3.231 barrel turns =
   3.23 days (77.5 h)** nominal, 3.2 days at μ = 0.08, **2.3 days at
   μ = 0.15**. A measured run far below 2.3 days means the friction assumption
   is wrong, and the power budget in `docs/CALCULATIONS.md` should be recomputed
   with the measured μ before anything else is trusted.
8. **Winding.** Confirm the ratchet and click hold at every tooth, and that the
   key cannot back-drive. Remember there is no maintaining power: the clock
   stops while you wind (L-04).

**Only if all eight pass may this be called a working clock.** If any of them
fails, the failure is a physical result that the CAD could not have predicted,
and `docs/LIMITATIONS.md` section 1 explains why that is expected rather than
surprising.
