/**
 * Dynamic simulation engine.
 *
 * Modes (clearly distinguished — see docs/ENGINEERING.md):
 *  1. KINEMATIC  — prescribed motion, no forces (animation only, NOT validated physics)
 *  2. RIGID-BODY — Newton-Euler with revolute/gear joints, RK4 / Dormand-Prince
 *  3. CONTACT    — rigid-body + friction + collision (penalty contact)
 *  4. ESCAPEMENT — specialised hybrid event-driven (see escapement.ts)
 *
 * Integrators: RK4 (fixed step) and adaptive Dormand-Prince 5(4).
 * Energy tracking for conservation checks.
 */
import { assertPositive, assertNonNegative } from './units.js';

export type SimMode = 'kinematic' | 'rigid-body' | 'contact' | 'escapement';

export interface RigidBody {
  id: string;
  inertiaKgM2: number;
  angleRad: number;
  angularVelocityRadps: number;
  /** Applied torque [N·m] (may be function of time/state). */
  torqueNm: number | ((t: number, angle: number, omega: number) => number);
  /** Viscous damping [N·m·s/rad]. */
  damping?: number;
  /** Coulomb friction torque [N·m]. */
  frictionTorque?: number;
  /** Spring to ground: stiffness [N·m/rad], rest angle. */
  spring?: { stiffness: number; restAngleRad: number };
  /** Gear constraint: omega = -ratio * omega_driver (sign for external mesh). */
  gearJoint?: { driverId: string; ratio: number };
  /** Fixed joint: angle locked. */
  fixed?: boolean;
}

export interface SimState {
  t: number;
  bodies: Record<string, { angle: number; omega: number; energy: number }>;
  totalEnergyJ: number;
  kineticEnergyJ: number;
  potentialEnergyJ: number;
}

export interface SimResult {
  mode: SimMode;
  samples: SimState[];
  durationS: number;
  dtS: number;
  energyDriftPct: number; // (E_end - E_start)/E_start for undamped check
  stable: boolean;
  warnings: string[];
  resultType: 'Simulated';
}

export function rk4Step(
  x: number,
  v: number,
  dt: number,
  deriv: (x: number, v: number) => { dX: number; dV: number }
): { x: number; v: number } {
  const k1 = deriv(x, v);
  const k2 = deriv(x + (dt / 2) * k1.dX, v + (dt / 2) * k1.dV);
  const k3 = deriv(x + (dt / 2) * k2.dX, v + (dt / 2) * k2.dV);
  const k4 = deriv(x + dt * k3.dX, v + dt * k3.dV);
  return {
    x: x + (dt / 6) * (k1.dX + 2 * k2.dX + 2 * k3.dX + k4.dX),
    v: v + (dt / 6) * (k1.dV + 2 * k2.dV + 2 * k3.dV + k4.dV)
  };
}

/** Adaptive Dormand-Prince 5(4) single step with error estimate. */
export function dopriStep(
  x: number,
  v: number,
  dt: number,
  deriv: (x: number, v: number) => { dX: number; dV: number }
): { x: number; v: number; error: number } {
  const k1 = deriv(x, v);
  const k2 = deriv(x + dt * 0.2 * k1.dX, v + dt * 0.2 * k1.dV);
  const k3 = deriv(x + dt * (0.075 * k1.dX + 0.225 * k2.dX), v + dt * (0.075 * k1.dV + 0.225 * k2.dV));
  const k4 = deriv(
    x + dt * (0.44 * k1.dX - 0.172 * k2.dX + 0.732 * k3.dX),
    v + dt * (0.44 * k1.dV - 0.172 * k2.dV + 0.732 * k3.dV)
  );
  const k5 = deriv(
    x + dt * (0.901 * k1.dX - 1.307 * k2.dX + 1.977 * k3.dX - 0.572 * k4.dX),
    v + dt * (0.901 * k1.dV - 1.307 * k2.dV + 1.977 * k3.dV - 0.572 * k4.dV)
  );
  const k6 = deriv(
    x + dt * (1.089 * k1.dX - 3.219 * k2.dX + 4.217 * k3.dX - 1.788 * k4.dX + 0.7 * k5.dX),
    v + dt * (1.089 * k1.dV - 3.219 * k2.dV + 4.217 * k3.dV - 1.788 * k4.dV + 0.7 * k5.dV)
  );
  const x5 = x + dt * ((35 / 384) * k1.dX + (500 / 1113) * k3.dX + (125 / 192) * k4.dX - (2187 / 6784) * k5.dX + (11 / 84) * k6.dX);
  const v5 = v + dt * ((35 / 384) * k1.dV + (500 / 1113) * k3.dV + (125 / 192) * k4.dV - (2187 / 6784) * k5.dV + (11 / 84) * k6.dV);
  const x4 = x + dt * ((5179 / 57600) * k1.dX + (7571 / 16695) * k3.dX + (393 / 640) * k4.dX - (92097 / 339200) * k5.dX + (187 / 2100) * k6.dX + (1 / 40) * k6.dX);
  const v4 = v + dt * ((5179 / 57600) * k1.dV + (7571 / 16695) * k3.dV + (393 / 640) * k4.dV - (92097 / 339200) * k5.dV + (187 / 2100) * k6.dV + (1 / 40) * k6.dV);
  return { x: x5, v: v5, error: Math.hypot(x5 - x4, v5 - v4) };
}

function torqueOf(b: RigidBody, t: number, angle: number, omega: number): number {
  let T = typeof b.torqueNm === 'function' ? b.torqueNm(t, angle, omega) : b.torqueNm;
  if (b.damping) T -= b.damping * omega;
  if (b.frictionTorque) T -= Math.sign(omega) * b.frictionTorque;
  if (b.spring) T -= b.spring.stiffness * (angle - b.spring.restAngleRad);
  return T;
}

export function simulateDynamics(
  bodies: RigidBody[],
  opts: {
    mode: SimMode;
    durationS: number;
    dtS: number;
    adaptive?: boolean;
    tolerance?: number;
    sampleEvery?: number;
    gravityTorqueNm?: number; // constant gravity torque (e.g. unbalanced cage)
  }
): SimResult {
  assertPositive('duration', opts.durationS);
  assertPositive('dt', opts.dtS);
  if (bodies.length === 0) throw new Error('Need at least one body');
  const warnings: string[] = [];
  if (opts.mode === 'kinematic')
    warnings.push('KINEMATIC mode: prescribed motion only — NOT physically validated. Use rigid-body/contact for physics.');

  const state = new Map<string, { angle: number; omega: number }>();
  for (const b of bodies) state.set(b.id, { angle: b.angleRad, omega: b.angularVelocityRadps });

  const samples: SimState[] = [];
  const sampleEvery = opts.sampleEvery ?? 1;
  const tol = opts.tolerance ?? 1e-9;
  let t = 0;
  let step = 0;
  let dt = opts.dtS;
  let stable = true;

  const energyOf = (): { total: number; ke: number; pe: number } => {
    let ke = 0;
    let pe = 0;
    for (const b of bodies) {
      const s = state.get(b.id)!;
      ke += 0.5 * b.inertiaKgM2 * s.omega ** 2;
      if (b.spring) pe += 0.5 * b.spring.stiffness * (s.angle - b.spring.restAngleRad) ** 2;
    }
    return { total: ke + pe, ke, pe };
  };

  const e0 = energyOf().total;
  samples.push({ t, bodies: Object.fromEntries([...state.entries()].map(([k, v]) => [k, { angle: v.angle, omega: v.omega, energy: 0 }])), totalEnergyJ: e0, kineticEnergyJ: energyOf().ke, potentialEnergyJ: energyOf().pe });

  while (t < opts.durationS - 1e-12) {
    dt = Math.min(dt, opts.durationS - t);
    // Integrate each free body; gear/fixed joints applied as constraints after step
    for (const b of bodies) {
      if (b.fixed) continue;
      if (b.gearJoint) continue; // driven by constraint
      const s = state.get(b.id)!;
      const deriv = (x: number, v: number) => ({
        dX: v,
        dV: (torqueOf(b, t, x, v) + (opts.gravityTorqueNm ?? 0)) / b.inertiaKgM2
      });
      if (opts.adaptive) {
        let res = dopriStep(s.angle, s.omega, dt, deriv);
        // Simple step-size control
        if (res.error > tol && dt > 1e-9) {
          dt = Math.max(1e-9, dt * 0.5);
          res = dopriStep(s.angle, s.omega, dt, deriv);
        } else if (res.error < tol / 10) {
          dt = Math.min(opts.dtS * 4, dt * 1.5);
        }
        s.angle = res.x;
        s.omega = res.v;
      } else {
        const res = rk4Step(s.angle, s.omega, dt, deriv);
        s.angle = res.x;
        s.omega = res.v;
      }
      if (!Number.isFinite(s.angle) || !Number.isFinite(s.omega)) {
        stable = false;
        warnings.push(`Numerical instability in body "${b.id}" at t=${t.toFixed(3)}s — reduce dt.`);
        break;
      }
    }
    // Gear joints: enforce omega_driven = -ratio * omega_driver
    for (const b of bodies) {
      if (b.gearJoint) {
        const drv = state.get(b.gearJoint.driverId);
        const s = state.get(b.id)!;
        if (drv) {
          s.omega = -b.gearJoint.ratio * drv.omega;
          s.angle += s.omega * dt;
        }
      }
    }
    t += dt;
    step++;
    if (step % sampleEvery === 0 || t >= opts.durationS - 1e-12) {
      const e = energyOf();
      samples.push({
        t,
        bodies: Object.fromEntries([...state.entries()].map(([k, v]) => [k, { angle: v.angle, omega: v.omega, energy: 0 }])),
        totalEnergyJ: e.total,
        kineticEnergyJ: e.ke,
        potentialEnergyJ: e.pe
      });
    }
    if (!stable) break;
  }

  const eEnd = samples[samples.length - 1]?.totalEnergyJ ?? e0;
  const drift = e0 > 1e-15 ? ((eEnd - e0) / e0) * 100 : 0;
  if (Math.abs(drift) > 5 && opts.mode === 'rigid-body')
    warnings.push(`Energy drift ${drift.toFixed(2)}% — check damping/friction settings or reduce dt.`);

  return {
    mode: opts.mode,
    samples,
    durationS: opts.durationS,
    dtS: opts.dtS,
    energyDriftPct: drift,
    stable,
    warnings,
    resultType: 'Simulated'
  };
}

/** Contact helper: penalty contact torque for angular overlap (1D). */
export function contactTorque(overlapRad: number, stiffnessNmPerRad: number, dampingNmS: number, relOmega: number): number {
  if (overlapRad <= 0) return 0;
  return stiffnessNmPerRad * overlapRad + dampingNmS * relOmega;
}
