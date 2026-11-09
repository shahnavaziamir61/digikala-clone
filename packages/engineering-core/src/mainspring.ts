/**
 * Mainspring & barrel engineering.
 *
 * Flat spiral spring model (documented approximation):
 *   Second moment of area   I = b * t^3 / 12
 *   Torsional stiffness     k = E * I / L_eff
 *   Torque                  T(theta) = k * (theta_wound - theta_preload_offset)
 *   Stored energy           E = integral T d(theta)  (numeric, supports nonlinear curves)
 *   Max bending stress      sigma = 6*T / (b * t^2) * Kt   (Kt stress concentration ~1.1)
 *   Safety factor           SF = yield / sigma_max
 *
 * Nonlinear torque curves: caller may supply measured T(theta) samples;
 * energy is then integrated from data (labelled "Measured" if flagged).
 */
import { assertPositive, assertNonNegative } from './units.js';
import { getMaterial } from './materials.js';

export interface MainspringParams {
  thicknessM: number; // t
  widthM: number; // b (radial height of spring strip)
  lengthM: number; // L developed length
  innerRadiusM: number; // arbor-side radius
  outerRadiusM: number; // barrel-side radius
  barrelDiameterM: number;
  arborDiameterM: number;
  activeTurns: number; // working turns available
  materialId: string;
  preloadTurns?: number; // turns pre-wound at full wind reference
  stressConcentration?: number; // Kt, default 1.1
  /** Optional measured torque curve: [thetaRad, torqueNm] pairs, ascending theta. */
  measuredCurve?: [number, number][];
  measured?: boolean;
}

export interface MainspringResult {
  stiffnessNmPerRad: number; // k
  maxTorqueNm: number;
  minTorqueNm: number;
  storedEnergyJ: number;
  maxStressPa: number;
  safetyFactor: number;
  fatigueSafetyFactor: number;
  workingTurns: number;
  /** Spring volume [m^3] approx: L * b * t */
  springVolumeM3: number;
  /** Torque curve samples for plotting: [thetaRad, torqueNm] */
  torqueCurve: [number, number][];
  energyCurve: [number, number][]; // [thetaRad, remainingEnergyJ]
  warnings: string[];
  resultType: 'Calculated' | 'Measured';
}

export function calculateMainspring(p: MainspringParams): MainspringResult {
  assertPositive('thickness', p.thicknessM);
  assertPositive('width', p.widthM);
  assertPositive('length', p.lengthM);
  assertPositive('innerRadius', p.innerRadiusM);
  assertPositive('outerRadius', p.outerRadiusM);
  assertPositive('barrelDiameter', p.barrelDiameterM);
  assertPositive('arborDiameter', p.arborDiameterM);
  assertPositive('activeTurns', p.activeTurns);
  const mat = getMaterial(p.materialId);
  const Kt = p.stressConcentration ?? 1.1;
  const preload = p.preloadTurns ?? 0;

  const I = (p.widthM * p.thicknessM ** 3) / 12;
  const k = (mat.elasticModulusPa * I) / p.lengthM;

  const thetaMax = p.activeTurns * 2 * Math.PI;
  const thetaPre = preload * 2 * Math.PI;

  const torqueAt = (theta: number): number => {
    if (p.measuredCurve && p.measuredCurve.length >= 2) {
      // Linear interpolation of measured data
      const c = p.measuredCurve;
      if (theta <= c[0][0]) return c[0][1];
      if (theta >= c[c.length - 1][0]) return c[c.length - 1][1];
      for (let i = 0; i < c.length - 1; i++) {
        if (theta >= c[i][0] && theta <= c[i + 1][0]) {
          const t = (theta - c[i][0]) / (c[i + 1][0] - c[i][0]);
          return c[i][1] + t * (c[i + 1][1] - c[i][1]);
        }
      }
      return c[c.length - 1][1];
    }
    return k * Math.max(0, theta - thetaPre);
  };

  // Sample curve + numeric energy integration (trapezoidal)
  const N = 200;
  const torqueCurve: [number, number][] = [];
  const energyCurve: [number, number][] = [];
  let energy = 0;
  let prevT = torqueAt(0);
  torqueCurve.push([0, prevT]);
  energyCurve.push([0, 0]);
  for (let i = 1; i <= N; i++) {
    const th = (thetaMax * i) / N;
    const T = torqueAt(th);
    const dTh = th - (thetaMax * (i - 1)) / N;
    energy += ((prevT + T) / 2) * dTh;
    torqueCurve.push([th, T]);
    energyCurve.push([th, energy]);
    prevT = T;
  }

  const maxTorque = Math.max(...torqueCurve.map((c) => c[1]));
  const minTorque = Math.min(...torqueCurve.map((c) => c[1]));
  const sigmaMax = ((6 * maxTorque) / (p.widthM * p.thicknessM ** 2)) * Kt;
  const sf = mat.yieldStrengthPa / sigmaMax;
  const fatigueSF = mat.fatigueLimitPa ? mat.fatigueLimitPa / sigmaMax : Infinity;

  const warnings: string[] = [];
  if (sf < 1.5) warnings.push(`Safety factor ${sf.toFixed(2)} < 1.5 — spring may take permanent set.`);
  if (p.outerRadiusM * 2 > p.barrelDiameterM) warnings.push('Spring outer radius exceeds barrel diameter — geometry conflict.');
  if (p.innerRadiusM * 2 < p.arborDiameterM) warnings.push('Spring inner radius smaller than arbor — interference.');
  if (minTorque <= 0) warnings.push('Torque reaches zero within working turns — power reserve ends early.');
  const torqueVariation = maxTorque > 0 ? (maxTorque - minTorque) / maxTorque : 0;
  if (torqueVariation > 0.5) warnings.push(`Torque variation ${(torqueVariation * 100).toFixed(0)}% across working turns — rate stability will suffer.`);

  return {
    stiffnessNmPerRad: k,
    maxTorqueNm: maxTorque,
    minTorqueNm: minTorque,
    storedEnergyJ: energy,
    maxStressPa: sigmaMax,
    safetyFactor: sf,
    fatigueSafetyFactor: fatigueSF,
    workingTurns: p.activeTurns,
    springVolumeM3: p.lengthM * p.widthM * p.thicknessM,
    torqueCurve,
    energyCurve,
    warnings,
    resultType: p.measured && p.measuredCurve ? 'Measured' : 'Calculated'
  };
}

/**
 * Power-reserve feasibility check.
 * Required energy = avgPower * time. Verdict is honest: INFEASIBLE if
 * stored usable energy < required (with efficiency chain applied).
 */
export function powerReserveCheck(opts: {
  storedEnergyJ: number;
  avgPowerConsumptionW: number; // at escapement / output
  transmissionEfficiency: number; // barrel -> escapement
  targetHours: number;
}): {
  requiredEnergyJ: number;
  usableEnergyJ: number;
  achievableHours: number;
  feasible: boolean;
  margin: number; // usable/required - 1
  warnings: string[];
} {
  assertNonNegative('storedEnergy', opts.storedEnergyJ);
  assertPositive('avgPower', opts.avgPowerConsumptionW);
  assertPositive('targetHours', opts.targetHours);
  const required = opts.avgPowerConsumptionW * opts.targetHours * 3600;
  const usable = opts.storedEnergyJ * opts.transmissionEfficiency;
  const achievable = usable / opts.avgPowerConsumptionW / 3600;
  const feasible = usable >= required;
  const warnings: string[] = [];
  if (!feasible)
    warnings.push(
      `INFEASIBLE for ${opts.targetHours} h: need ${(required / 1000).toFixed(2)} kJ usable, spring provides ${(usable / 1000).toFixed(2)} kJ. Increase spring volume / reduce consumption.`
    );
  return {
    requiredEnergyJ: required,
    usableEnergyJ: usable,
    achievableHours: achievable,
    feasible,
    margin: usable / required - 1,
    warnings
  };
}
