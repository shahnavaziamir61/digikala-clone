/**
 * Tourbillon engineering module.
 *
 * Kinematics (documented):
 *   Cage angular velocity  omega_cage = 2π / T_cage
 *   Fixed wheel (stationary) drives cage pinion:
 *     omega_escape (rel. cage) = omega_cage * (z_fixed / z_pinion)
 *   Balance beats at f_balance; escape wheel advances one pitch per beat.
 *   Required pinion/fixed ratio from beat rate:
 *     omega_escape = 2 * f_balance * (2π / N_escape)  [rad/s]
 *     => z_fixed / z_pinion = omega_escape / omega_cage
 *
 * Bearing load: cage weight + balance/escape assembly weight on lower pivot.
 * Dynamic balance: unbalance moment = m_unbal * r * omega^2.
 */
import { assertPositive, assertNonNegative } from './units.js';
import { planetaryRatio } from './gears.js';

export interface TourbillonParams {
  cageDiameterM: number;
  cageHeightM: number;
  cageMassKg: number;
  cageInertiaKgM2: number;
  cagePeriodS: number; // e.g. 60 for one-minute
  balanceDiameterM: number;
  balanceFrequencyHz: number;
  escapeTeeth: number;
  fixedWheelTeeth: number;
  pinionTeeth: number;
  shaftDiameterM: number;
  bearingInnerDiameterM: number;
  radialClearanceM: number;
  axialClearanceM: number;
  escapeWheelTorqueNm: number;
  unbalanceMassKg?: number;
  unbalanceRadiusM?: number;
  cageBridgeThicknessM?: number;
}

export interface TourbillonResult {
  cageAngularVelocityRadps: number;
  cageRpm: number;
  escapeWheelSpeedRadps: number; // relative to cage
  requiredRatio: number; // z_fixed/z_pinion needed for beat rate
  actualRatio: number;
  ratioErrorPct: number;
  beatRateVph: number;
  bearingLoadN: number;
  bearingContactPressurePa: number;
  radialClearanceOk: boolean;
  axialClearanceOk: boolean;
  unbalanceMomentNm: number;
  cageKineticEnergyJ: number;
  avgPowerW: number; // cage drive power (Estimated)
  warnings: string[];
  resultType: 'Calculated';
}

export function calculateTourbillon(p: TourbillonParams): TourbillonResult {
  assertPositive('cageDiameter', p.cageDiameterM);
  assertPositive('cageMass', p.cageMassKg);
  assertPositive('cagePeriod', p.cagePeriodS);
  assertPositive('balanceFrequency', p.balanceFrequencyHz);
  assertPositive('escapeTeeth', p.escapeTeeth);
  assertPositive('fixedWheelTeeth', p.fixedWheelTeeth);
  assertPositive('pinionTeeth', p.pinionTeeth);
  assertPositive('shaftDiameter', p.shaftDiameterM);
  assertNonNegative('radialClearance', p.radialClearanceM);
  assertNonNegative('axialClearance', p.axialClearanceM);

  const omegaCage = (2 * Math.PI) / p.cagePeriodS;
  const cageRpm = omegaCage * 60 / (2 * Math.PI);
  // Escape wheel: one pitch per beat, 2 beats per balance period
  const omegaEscape = 2 * p.balanceFrequencyHz * ((2 * Math.PI) / p.escapeTeeth);
  const requiredRatio = omegaEscape / omegaCage;
  const actualRatio = p.fixedWheelTeeth / p.pinionTeeth;
  const ratioErr = ((actualRatio - requiredRatio) / requiredRatio) * 100;
  const vph = 2 * p.balanceFrequencyHz * 3600;

  const W = p.cageMassKg * 9.81;
  const bearingArea = Math.PI * p.bearingInnerDiameterM * 0.001; // approx contact band 1mm
  const pressure = W / bearingArea;

  const mUnbal = p.unbalanceMassKg ?? 0;
  const rUnbal = p.unbalanceRadiusM ?? 0;
  const unbalMoment = mUnbal * rUnbal * omegaCage ** 2;

  const ke = 0.5 * p.cageInertiaKgM2 * omegaCage ** 2;
  // Avg power: escape impulse power + cage bearing friction (Estimated)
  const impulsePower = p.escapeWheelTorqueNm * omegaEscape;
  const frictionPower = 0.05 * W * (p.shaftDiameterM / 2) * omegaCage;
  const avgPower = impulsePower + frictionPower;

  const warnings: string[] = [];
  if (Math.abs(ratioErr) > 2)
    warnings.push(`Gear ratio error ${ratioErr.toFixed(1)}% — beat rate will differ from design. Adjust fixed wheel / pinion teeth.`);
  if (p.radialClearanceM < 0.000005) warnings.push('Radial clearance < 5 µm — risk of binding. Typical jewel clearance 5–15 µm.');
  if (p.radialClearanceM > 0.00005) warnings.push('Radial clearance > 50 µm — excessive play, rate instability.');
  if (p.axialClearanceM < 0.00002) warnings.push('Axial clearance < 20 µm — risk of endshake binding.');
  if (p.axialClearanceM > 0.0002) warnings.push('Axial clearance > 200 µm — excessive endshake.');
  if (pressure > 50e6) warnings.push(`Bearing contact pressure ${(pressure / 1e6).toFixed(1)} MPa — check jewel load rating.`);
  if (unbalMoment > 1e-6) warnings.push(`Unbalance moment ${unbalMoment.toExponential(2)} N·m — add counterpoise / balance screws.`);
  if (p.cagePeriodS !== 60) warnings.push(`Cage period ${p.cagePeriodS}s (not one-minute).`);

  return {
    cageAngularVelocityRadps: omegaCage,
    cageRpm,
    escapeWheelSpeedRadps: omegaEscape,
    requiredRatio,
    actualRatio,
    ratioErrorPct: ratioErr,
    beatRateVph: vph,
    bearingLoadN: W,
    bearingContactPressurePa: pressure,
    radialClearanceOk: p.radialClearanceM >= 0.000005 && p.radialClearanceM <= 0.00005,
    axialClearanceOk: p.axialClearanceM >= 0.00002 && p.axialClearanceM <= 0.0002,
    unbalanceMomentNm: unbalMoment,
    cageKineticEnergyJ: ke,
    avgPowerW: avgPower,
    warnings,
    resultType: 'Calculated'
  };
}

/** Suggest fixed/pinion teeth near a required ratio (search small integers). */
export function suggestTourbillonTeeth(requiredRatio: number, maxTeeth = 120): { fixed: number; pinion: number; ratio: number; errorPct: number } {
  assertPositive('ratio', requiredRatio);
  let best = { fixed: 1, pinion: 1, ratio: 1, errorPct: Infinity };
  for (let pinion = 6; pinion <= 30; pinion++) {
    const fixed = Math.round(requiredRatio * pinion);
    if (fixed < 10 || fixed > maxTeeth) continue;
    const ratio = fixed / pinion;
    const err = Math.abs(((ratio - requiredRatio) / requiredRatio) * 100);
    if (err < best.errorPct) best = { fixed, pinion, ratio, errorPct: err };
  }
  return best;
}

export { planetaryRatio };
