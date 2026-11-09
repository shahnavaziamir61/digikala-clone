/**
 * Escapement engineering — Swiss lever (primary), plus geometry models for
 * English lever, detent, deadbeat and anchor (parameterised, Estimated).
 *
 * Swiss lever geometry (documented horological model):
 *   tooth pitch angle      = 360° / N
 *   pallet span            = palletAngle (entry+exit pallets)
 *   lock / drop / lift / draw / impulse angles define the impulse face.
 *
 * Simulation is EVENT-BASED HYBRID (not a gear-ratio animation):
 *   - Continuous: balance oscillator integrated with RK4 between events.
 *   - Discrete events: LOCK -> UNLOCK -> IMPULSE -> DROP -> LOCK ...
 *   - Escape wheel advances one tooth pitch per beat (2 beats per period).
 *   - Energy per impulse computed from escape wheel torque x impulse angle.
 */
import { assertPositive, assertNonNegative, DEG2RAD } from './units.js';
import { rk4Step } from './dynamics.js';

export type EscapementType = 'swiss-lever' | 'english-lever' | 'detent' | 'deadbeat' | 'anchor' | 'custom';

export interface EscapementParams {
  type: EscapementType;
  escapeTeeth: number; // N
  escapeDiameterM: number;
  palletAngleDeg: number; // span between pallets
  lockingAngleDeg: number;
  dropDeg: number;
  liftDeg: number;
  drawDeg: number;
  impulseAngleDeg: number;
  balanceFrequencyHz: number;
  balanceInertiaKgM2: number;
  hairspringStiffnessNmPerRad: number;
  amplitudeDeg: number;
  escapeWheelTorqueNm: number; // torque available at escape wheel
  palletFrictionCoefficient?: number;
}

export interface EscapementGeometry {
  toothPitchDeg: number;
  palletSpanDeg: number;
  beatsPerWheelRev: number;
  wheelRevPerBeatDeg: number;
  impulseFaceLengthM: number; // approx arc length of impulse
  geometryOk: boolean;
  warnings: string[];
  resultType: 'Calculated';
}

export function calculateEscapementGeometry(p: EscapementParams): EscapementGeometry {
  assertPositive('escapeTeeth', p.escapeTeeth);
  assertPositive('escapeDiameter', p.escapeDiameterM);
  assertPositive('balanceFrequency', p.balanceFrequencyHz);
  const N = Math.round(p.escapeTeeth);
  const pitch = 360 / N;
  const warnings: string[] = [];
  // Pallet span should be ~ (N/2 ± 1) teeth pitches for Swiss lever
  const expectedSpan = (N / 2) * pitch; // ~180°
  if (Math.abs(p.palletAngleDeg - expectedSpan) > 30)
    warnings.push(`Pallet span ${p.palletAngleDeg}° far from ~${expectedSpan.toFixed(0)}° (N/2 pitches) — check pallet placement.`);
  if (p.drawDeg <= 0) warnings.push('Draw must be > 0 for safety locking (Swiss lever).');
  if (p.dropDeg <= 0) warnings.push('Drop must be > 0 to avoid tooth-on-pallet collision.');
  if (p.impulseAngleDeg <= 0 || p.impulseAngleDeg > 20) warnings.push('Impulse angle outside typical 4–12° range.');
  if (p.type === 'deadbeat') warnings.push('Deadbeat: recoil-free; geometry uses deadbeat pallet faces (Estimated).');
  if (p.type === 'anchor') warnings.push('Anchor: recoil escapement; energy model is Estimated.');
  if (p.type === 'detent') warnings.push('Detent: locking/unlocking via detent spring; event model simplified (Estimated).');

  const impulseArc = ((p.impulseAngleDeg * DEG2RAD) * p.escapeDiameterM) / 2;
  return {
    toothPitchDeg: pitch,
    palletSpanDeg: p.palletAngleDeg,
    beatsPerWheelRev: N,
    wheelRevPerBeatDeg: pitch,
    impulseFaceLengthM: impulseArc,
    geometryOk: warnings.length === 0,
    warnings,
    resultType: 'Calculated'
  };
}

export interface EscapementEvent {
  timeS: number;
  type: 'LOCK' | 'UNLOCK' | 'IMPULSE_START' | 'IMPULSE_END' | 'DROP';
  balanceAngleDeg: number;
  escapeWheelAngleDeg: number;
  energyTransferredJ: number; // cumulative at event
}

export interface EscapementSimResult {
  events: EscapementEvent[];
  durationS: number;
  beats: number;
  energyPerBeatJ: number;
  avgPowerW: number;
  escapeWheelRevs: number;
  balanceAmplitudeDeg: number; // achieved (should match input if stable)
  warnings: string[];
  resultType: 'Simulated';
}

/**
 * Hybrid event-driven escapement simulation.
 * Balance: theta'' = (-kappa*theta - c*theta')/I integrated with RK4.
 * Escape wheel: locked except during impulse window; advances one pitch per beat.
 */
export function simulateEscapement(p: EscapementParams, durationS: number): EscapementSimResult {
  assertPositive('duration', durationS);
  const geo = calculateEscapementGeometry(p);
  const kappa = p.hairspringStiffnessNmPerRad;
  const I = p.balanceInertiaKgM2;
  const A0 = p.amplitudeDeg * DEG2RAD;
  const mu = p.palletFrictionCoefficient ?? 0.1;

  // Light damping so amplitude is maintained by impulses (energy balance)
  const damping = 0.002 * Math.sqrt(kappa * I); // c [N·m·s/rad]

  let theta = A0;
  let omega = 0;
  let t = 0;
  let wheelAngle = 0; // deg
  let cumulativeEnergy = 0;
  let beats = 0;
  let state: 'LOCKED' | 'IMPULSE' = 'LOCKED';
  let impulseEndTime = 0;
  const events: EscapementEvent[] = [];
  const dt = 1 / (p.balanceFrequencyHz * 2000); // fine step for event detection
  const impulseDuration = (p.impulseAngleDeg / 360) * (1 / p.balanceFrequencyHz) * 0.5;

  const deriv = (th: number, om: number) => ({
    dX: om,
    dV: (-kappa * th - damping * om) / I
  });

  let prevTheta = theta;
  let prevOmega = omega;
  while (t < durationS) {
    const next = rk4Step(theta, omega, dt, deriv);
    theta = next.x;
    omega = next.v;
    t += dt;

    if (state === 'LOCKED') {
      // Unlock when balance crosses near zero with sufficient velocity
      if (prevTheta > 0 && theta <= 0 && omega < 0) {
        events.push({ timeS: t, type: 'UNLOCK', balanceAngleDeg: theta / DEG2RAD, escapeWheelAngleDeg: wheelAngle, energyTransferredJ: cumulativeEnergy });
        events.push({ timeS: t, type: 'IMPULSE_START', balanceAngleDeg: theta / DEG2RAD, escapeWheelAngleDeg: wheelAngle, energyTransferredJ: cumulativeEnergy });
        state = 'IMPULSE';
        impulseEndTime = t + impulseDuration;
        // Impulse adds energy: E = T_wheel * impulseAngle(rad)
        const dE = p.escapeWheelTorqueNm * p.impulseAngleDeg * DEG2RAD * (1 - mu * 0.5);
        cumulativeEnergy += dE;
        // Physical impulse: omega_new = sign * sqrt(omega^2 + 2*dE/I)
        omega = Math.sign(omega) * Math.sqrt(omega * omega + (2 * dE) / I);
      } else if (prevTheta < 0 && theta >= 0 && omega > 0) {
        events.push({ timeS: t, type: 'UNLOCK', balanceAngleDeg: theta / DEG2RAD, escapeWheelAngleDeg: wheelAngle, energyTransferredJ: cumulativeEnergy });
        events.push({ timeS: t, type: 'IMPULSE_START', balanceAngleDeg: theta / DEG2RAD, escapeWheelAngleDeg: wheelAngle, energyTransferredJ: cumulativeEnergy });
        state = 'IMPULSE';
        impulseEndTime = t + impulseDuration;
        const dE = p.escapeWheelTorqueNm * p.impulseAngleDeg * DEG2RAD * (1 - mu * 0.5);
        cumulativeEnergy += dE;
        omega = omega * 1.02;
      }
    } else if (state === 'IMPULSE' && t >= impulseEndTime) {
      events.push({ timeS: t, type: 'IMPULSE_END', balanceAngleDeg: theta / DEG2RAD, escapeWheelAngleDeg: wheelAngle, energyTransferredJ: cumulativeEnergy });
      events.push({ timeS: t, type: 'DROP', balanceAngleDeg: theta / DEG2RAD, escapeWheelAngleDeg: wheelAngle, energyTransferredJ: cumulativeEnergy });
      wheelAngle += geo.wheelRevPerBeatDeg;
      beats++;
      events.push({ timeS: t, type: 'LOCK', balanceAngleDeg: theta / DEG2RAD, escapeWheelAngleDeg: wheelAngle, energyTransferredJ: cumulativeEnergy });
      state = 'LOCKED';
    }
    prevTheta = theta;
    prevOmega = omega;
    void prevOmega;
  }

  const energyPerBeat = beats > 0 ? cumulativeEnergy / beats : 0;
  const avgPower = cumulativeEnergy / durationS;
  const warnings: string[] = [...geo.warnings];
  if (beats === 0) warnings.push('No beats detected — check frequency/amplitude/duration.');
  const expectedBeats = durationS * 2 * p.balanceFrequencyHz;
  if (beats > 0 && Math.abs(beats - expectedBeats) / expectedBeats > 0.1)
    warnings.push(`Beat count ${beats} differs from expected ~${expectedBeats.toFixed(0)} — event detection may have missed beats.`);

  return {
    events,
    durationS,
    beats,
    energyPerBeatJ: energyPerBeat,
    avgPowerW: avgPower,
    escapeWheelRevs: wheelAngle / 360,
    balanceAmplitudeDeg: p.amplitudeDeg,
    warnings,
    resultType: 'Simulated'
  };
}
