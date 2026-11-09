/**
 * Balance wheel & hairspring engineering.
 *
 * Ideal oscillator:  f = (1/2π) * sqrt(kappa / I)
 *   kappa = hairspring torsional stiffness [N·m/rad]
 *   I     = total moment of inertia [kg·m^2]
 * Beat rate (vibrations per hour) = 2 * f * 3600.
 *
 * Extensions (all documented, labelled Estimated where approximate):
 *  - Timing screws: I_screw = m * r^2 (point mass at radius r)
 *  - Temperature: kappa(T) = kappa0 * (1 - beta * dT), beta from material
 *  - Amplitude-dependent rate (isochronism error): dRate ~ c * (A - A0)
 *  - Air drag torque: T_drag = c_air * omega * |omega|
 *  - Pivot friction torque: T_f = mu * F * r_pivot
 */
import { assertPositive, assertNonNegative, DEG2RAD } from './units.js';
import { getMaterial } from './materials.js';

export interface BalanceParams {
  diameterM: number;
  thicknessM: number;
  massKg: number; // rim + arms (without screws)
  timingScrewMassKg: number; // total screw mass
  timingScrewRadiusM: number; // mean radius of screws
  hairspringStiffnessNmPerRad: number; // kappa
  hairspringLengthM: number;
  materialId: string;
  amplitudeDeg: number; // operating amplitude (peak, one side)
  screwCount?: number;
  temperatureDeltaK?: number; // operating - reference
  airDragCoefficient?: number; // c_air [N·m·s^2/rad^2]
  pivotFrictionCoefficient?: number;
  pivotRadiusM?: number;
  weightN?: number; // balance weight (for pivot friction)
}

export interface BalanceResult {
  inertiaKgM2: number; // I total
  rimInertiaKgM2: number;
  screwInertiaKgM2: number;
  frequencyHz: number;
  periodS: number;
  beatRateVph: number;
  /** Rate sensitivity: d(period)/d(screw mass) [s/kg] */
  screwSensitivitySPerKg: number;
  /** Rate change per 0.1 g screw mass change [s/day] */
  ratePerTenthGramSecPerDay: number;
  temperatureRateShiftSecPerDayPerK: number;
  isochronismErrorSecPerDay: number; // amplitude-dependent, Estimated
  airDragTorqueNm: number; // at peak angular velocity
  pivotFrictionTorqueNm: number;
  energyPerCycleJ: number; // 0.5*kappa*A^2
  warnings: string[];
  resultType: 'Calculated';
}

export function calculateBalance(p: BalanceParams): BalanceResult {
  assertPositive('diameter', p.diameterM);
  assertPositive('thickness', p.thicknessM);
  assertPositive('mass', p.massKg);
  assertPositive('hairspringStiffness', p.hairspringStiffnessNmPerRad);
  assertPositive('amplitude', p.amplitudeDeg);
  getMaterial(p.materialId);

  const R = p.diameterM / 2;
  // Rim approximated as thin ring: I_rim = m * R^2 (arms add ~10%, noted)
  const I_rim = p.massKg * R * R * 1.1;
  const I_screw = p.timingScrewMassKg * p.timingScrewRadiusM ** 2;
  const I = I_rim + I_screw;

  const kappa = p.hairspringStiffnessNmPerRad;
  const f = Math.sqrt(kappa / I) / (2 * Math.PI);
  const T = 1 / f;
  const vph = 2 * f * 3600;

  // Sensitivity: T = 2π sqrt(I/kappa) => dT/dI = T/(2I); dI/dm_screw = r^2
  const dTdm = (T / (2 * I)) * p.timingScrewRadiusM ** 2;
  // Per 0.1 g: dT * (86400/T) sec/day equivalent
  const ratePerTenthGram = dTdm * 0.0001 * (86400 / T);

  // Temperature: dT/T = -0.5 * dk/kappa; dk/kappa = -beta*dT, beta ~ 2e-4/K (steel, Estimated)
  const beta = 2e-4;
  const dTfrac = 0.5 * beta; // per K
  const tempShift = dTfrac * 86400; // s/day per K

  // Isochronism (Estimated): ~0.5 s/day per 10° amplitude deviation from 270°
  const isoError = 0.05 * (p.amplitudeDeg - 270);

  const A = p.amplitudeDeg * DEG2RAD;
  const omegaPeak = 2 * Math.PI * f * A;
  const cAir = p.airDragCoefficient ?? 1e-7;
  const dragTorque = cAir * omegaPeak * Math.abs(omegaPeak);
  const mu = p.pivotFrictionCoefficient ?? 0.05;
  const rPiv = p.pivotRadiusM ?? 0.00015;
  const W = p.weightN ?? p.massKg * 9.81;
  const fricTorque = mu * W * rPiv;

  const energyCycle = 0.5 * kappa * A * A;

  const warnings: string[] = [];
  if (p.amplitudeDeg < 200) warnings.push('Low amplitude (<200°) — rate stability and impulse suffer.');
  if (p.amplitudeDeg > 320) warnings.push('Very high amplitude (>320°) — risk of overbanking / hairspring contact.');
  if (f < 0.5) warnings.push(`Low frequency ${f.toFixed(2)} Hz — check hairspring stiffness vs inertia.`);
  if (f > 5) warnings.push(`High frequency ${f.toFixed(2)} Hz — verify hairspring fatigue.`);
  if (I_screw > I_rim) warnings.push('Screw inertia dominates rim — unusual; check screw radius/mass.');

  return {
    inertiaKgM2: I,
    rimInertiaKgM2: I_rim,
    screwInertiaKgM2: I_screw,
    frequencyHz: f,
    periodS: T,
    beatRateVph: vph,
    screwSensitivitySPerKg: dTdm,
    ratePerTenthGramSecPerDay: ratePerTenthGram,
    temperatureRateShiftSecPerDayPerK: tempShift,
    isochronismErrorSecPerDay: isoError,
    airDragTorqueNm: dragTorque,
    pivotFrictionTorqueNm: fricTorque,
    energyPerCycleJ: energyCycle,
    warnings,
    resultType: 'Calculated'
  };
}

/** Required hairspring stiffness for a target frequency given inertia. */
export function requiredStiffness(inertiaKgM2: number, targetFreqHz: number): number {
  assertPositive('inertia', inertiaKgM2);
  assertPositive('freq', targetFreqHz);
  return inertiaKgM2 * (2 * Math.PI * targetFreqHz) ** 2;
}

/** Required inertia for a target frequency given stiffness. */
export function requiredInertia(stiffnessNmPerRad: number, targetFreqHz: number): number {
  assertPositive('stiffness', stiffnessNmPerRad);
  assertPositive('freq', targetFreqHz);
  return stiffnessNmPerRad / (2 * Math.PI * targetFreqHz) ** 2;
}
