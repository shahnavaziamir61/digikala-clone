# Engineering reference — equations, units, assumptions

All internal calculations use **SI** (m, kg, s, Pa, N, J, W, rad). Display
converts to metric/imperial (`engineering-core/units.ts`).

## Gears (`gears.ts`)

- Pitch diameter `d = m·z`; base `db = d·cos α`; addendum `ha = ha*·m` (1.0);
  dedendum `hf = hf*·m` (1.25); outside `da = d+2ha`; root `df = d−2hf`;
  centre distance `a = m(z1+z2)/2`.
- Transverse contact ratio:
  `ε = [√(ra1²−rb1²)+√(ra2²−rb2²)−a·sinα] / (π·m·cosα)`.
- Lewis bending: `σF = Ft/(b·m·Y)`, `Y(z)` fitted to standard values.
- Hertz contact: `σH = √[Ft/(b·2ρ′)·((1−ν1²)/E1+(1−ν2²)/E2)]`.
- Undercut: `z_min = 2/sin²α`. Involute flanks are generated analytically
  (`involuteFlankPoints`) — CAD geometry is true involute, not decorative.
- Bevel/worm/planetary: Willis `i = 1+z_ring/z_sun` (planetary, Calculated);
  bevel/worm are **Estimated** approximations.

## Mainspring (`mainspring.ts`)

- `I = b·t³/12`; `k = E·I/L`; `T(θ)=k·θ`; `E = ∫T dθ` (trapezoidal, supports
  measured curves); `σ = 6T/(b·t²)·Kt` (Kt=1.1); `SF = yield/σ`.
- Power-reserve check: `required = P_avg·t`; `usable = E·η`; verdict is honest
  (INFEASIBLE when usable < required).

## Balance (`balance.ts`)

- `f = (1/2π)·√(κ/I)`; `T=1/f`; `vph = 2·f·3600`.
- Screws: `I_screw = m·r²`; sensitivity `dT/dm = T·r²/(2I)`.
- Temperature (Estimated): `β≈2e-4/K`; isochronism `0.05 s/day/°` from 270°;
  air drag `T=c·ω|ω|`; pivot friction `T=μ·F·r`.

## Escapement (`escapement.ts`)

Swiss lever geometry + **hybrid event-driven simulation**: RK4 balance between
discrete LOCK → UNLOCK → IMPULSE → DROP events. Impulse energy
`E = T_wheel·Δθ_impulse`; balance velocity updated physically
`ω′ = sign·√(ω²+2E/I)`. Other types (English/detent/deadbeat/anchor) use
parameterised geometry, labelled Estimated.

## Tourbillon (`tourbillon.ts`)

- `ω_cage = 2π/T_cage`; `ω_escape = 2·f·(2π/N)`; required ratio
  `z_fixed/z_pinion = ω_escape/ω_cage`; bearing load `W=m·g`; unbalance
  `M = m·r·ω²`.

## Bearings (`bearings.ts`)

- `c_r = (D−d)/2`; `p = F/(d·L)`; `T_f = μ·F·r`; deflection `FL³/(3EI)`.

## Energy (`energy.ts`)

- `E = ∫T dθ`; `P = T·ω`; loss budget (gear/bearing/escapement/balance/cage);
  31-day target checked against stored energy, efficiency and consumption.

## Tolerance (`tolerance.ts`)

Worst-case (linear stack), RSS (`σ=√Σσi²`, `σi=tol/3`), Monte Carlo
(seeded Mulberry32 + Box-Muller, reproducible).

## Dynamics (`dynamics.ts`)

RK4 fixed-step and adaptive Dormand-Prince 5(4) with energy-drift reporting.
Gear joints enforce `ω_driven = −ratio·ω_driver`. Kinematic mode is never
presented as validated physics.

## Materials (`materials.ts`)

10 materials with typical published values (E, ν, ρ, yield, fatigue, friction).
**Verify against supplier datasheets before production.** Sources are noted
per material.

## Result labels

`Calculated` (closed-form), `Estimated` (approximation), `Simulated`
(numerical), `Measured` (user data), `Validated` (passed independent check
in `validation.ts`). See `validation.ts` for the automated suite.
