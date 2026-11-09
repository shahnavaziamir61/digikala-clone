/**
 * Jewels, bearings and pivots.
 *   Radial clearance   c_r = (D_hole - d_pivot)/2
 *   Axial clearance    c_a = endshake
 *   Contact pressure   p = F / (d * L_contact)
 *   Friction torque    T_f = mu * F * r_pivot
 *   Shaft deflection   delta = F*L^3/(3*E*I), I = pi*d^4/64
 */
import { assertPositive, assertNonNegative } from './units.js';
import { getMaterial } from './materials.js';

export type BearingType = 'hole-jewel' | 'cap-jewel' | 'pivot' | 'ball' | 'thrust' | 'custom';

export interface BearingParams {
  type: BearingType;
  innerDiameterM: number; // pivot / bore
  outerDiameterM: number;
  thicknessM: number;
  pivotDiameterM: number;
  holeDiameterM: number;
  radialLoadN: number;
  axialLoadN: number;
  shaftLengthM: number; // for deflection
  materialId: string;
  frictionCoefficient?: number;
  surfaceFinishRaUm?: number;
}

export interface BearingResult {
  radialClearanceM: number;
  axialClearanceM: number; // estimated from thickness vs pivot length (caller may override)
  contactPressurePa: number;
  frictionTorqueNm: number;
  frictionPowerW: number;
  shaftDeflectionM: number;
  loadRatingN: number; // approx from material (Estimated)
  warnings: string[];
  resultType: 'Calculated';
}

export function calculateBearing(p: BearingParams): BearingResult {
  assertPositive('innerDiameter', p.innerDiameterM);
  assertPositive('outerDiameter', p.outerDiameterM);
  assertPositive('thickness', p.thicknessM);
  assertPositive('pivotDiameter', p.pivotDiameterM);
  assertPositive('holeDiameter', p.holeDiameterM);
  assertNonNegative('radialLoad', p.radialLoadN);
  assertNonNegative('axialLoad', p.axialLoadN);
  const mat = getMaterial(p.materialId);
  const mu = p.frictionCoefficient ?? mat.frictionCoefficient ?? 0.1;

  const radialClearance = (p.holeDiameterM - p.pivotDiameterM) / 2;
  const F = Math.hypot(p.radialLoadN, p.axialLoadN);
  const contactArea = p.pivotDiameterM * p.thicknessM;
  const pressure = F / contactArea;
  const frictionTorque = mu * F * (p.pivotDiameterM / 2);

  const E = mat.elasticModulusPa;
  const d = p.pivotDiameterM;
  const I = (Math.PI * d ** 4) / 64;
  const deflection = (F * p.shaftLengthM ** 3) / (3 * E * I);

  // Load rating: approx 0.1 * yield * contact area (Estimated, conservative)
  const loadRating = 0.1 * mat.yieldStrengthPa * contactArea;

  const warnings: string[] = [];
  if (radialClearance < 0) warnings.push('Interference fit (negative clearance) — check hole/pivot diameters.');
  if (radialClearance > 0.00005) warnings.push('Radial clearance > 50 µm — excessive play.');
  if (pressure > mat.yieldStrengthPa * 0.5) warnings.push('Contact pressure high — jewel may crack under shock.');
  if (deflection > radialClearance * 2) warnings.push('Shaft deflection exceeds clearance — pivot may rub.');
  if (p.type === 'ball') warnings.push('Ball bearing: point-contact model simplified (Estimated).');

  return {
    radialClearanceM: radialClearance,
    axialClearanceM: 0, // requires pivot length data; see tolerance module
    contactPressurePa: pressure,
    frictionTorqueNm: frictionTorque,
    frictionPowerW: 0, // needs speed; computed in dynamics
    shaftDeflectionM: deflection,
    loadRatingN: loadRating,
    warnings,
    resultType: 'Calculated'
  };
}
