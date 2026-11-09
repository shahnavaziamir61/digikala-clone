/**
 * Energy & power-reserve analysis.
 *   E = ∫ T(θ) dθ   (numeric trapezoidal)
 *   P = T × ω
 * Loss budget: gear friction, bearing friction, escapement impulse,
 * balance losses, tourbillon cage losses.
 */
import { assertPositive, assertNonNegative } from './units.js';

export interface EnergyBudget {
  storedEnergyJ: number;
  gearFrictionPct: number; // of transmitted
  bearingFrictionPct: number;
  escapementLossPct: number;
  balanceLossPct: number;
  cageLossPct: number;
  transmissionEfficiency: number; // overall barrel->escapement
}

export interface EnergyResult {
  totalStoredJ: number;
  usableJ: number;
  requiredJ: number;
  remainingJ: number;
  efficiency: number;
  powerReserveHours: number;
  avgPowerW: number;
  lossBreakdown: { name: string; watts: number; pct: number }[];
  feasible: boolean;
  warnings: string[];
  resultType: 'Calculated';
}

export function integrateTorqueEnergy(curve: [number, number][]): number {
  if (curve.length < 2) throw new Error('Torque curve needs >= 2 points');
  let E = 0;
  for (let i = 1; i < curve.length; i++) {
    const [t0, T0] = curve[i - 1];
    const [t1, T1] = curve[i];
    E += ((T0 + T1) / 2) * (t1 - t0);
  }
  return E;
}

export function analyzeEnergy(
  budget: EnergyBudget,
  avgPowerConsumptionW: number,
  targetHours: number
): EnergyResult {
  assertNonNegative('stored', budget.storedEnergyJ);
  assertPositive('power', avgPowerConsumptionW);
  assertPositive('targetHours', targetHours);

  const usable = budget.storedEnergyJ * budget.transmissionEfficiency;
  const required = avgPowerConsumptionW * targetHours * 3600;
  const remaining = usable - required;
  const reserveHours = usable / avgPowerConsumptionW / 3600;

  const losses = [
    { name: 'Gear train friction', pct: budget.gearFrictionPct },
    { name: 'Bearing friction', pct: budget.bearingFrictionPct },
    { name: 'Escapement impulse', pct: budget.escapementLossPct },
    { name: 'Balance oscillator', pct: budget.balanceLossPct },
    { name: 'Tourbillon cage', pct: budget.cageLossPct }
  ].map((l) => ({ name: l.name, watts: avgPowerConsumptionW * (l.pct / 100), pct: l.pct }));

  const warnings: string[] = [];
  if (!budget.transmissionEfficiency || budget.transmissionEfficiency <= 0 || budget.transmissionEfficiency > 1)
    warnings.push('Transmission efficiency must be in (0,1].');
  if (remaining < 0)
    warnings.push(`Energy deficit: need ${(required / 1000).toFixed(2)} kJ, usable ${(usable / 1000).toFixed(2)} kJ. Target ${targetHours} h NOT feasible with current spring/consumption.`);
  else if (remaining / required < 0.2)
    warnings.push('Margin < 20% — fragile design; increase spring energy or reduce losses.');

  return {
    totalStoredJ: budget.storedEnergyJ,
    usableJ: usable,
    requiredJ: required,
    remainingJ: remaining,
    efficiency: budget.transmissionEfficiency,
    powerReserveHours: reserveHours,
    avgPowerW: avgPowerConsumptionW,
    lossBreakdown: losses,
    feasible: remaining >= 0,
    warnings,
    resultType: 'Calculated'
  };
}

/** Time series: torque, remaining energy, output torque over power reserve. */
export function energyTimeSeries(
  torqueCurve: [number, number][],
  avgPowerW: number,
  transmissionEfficiency: number,
  points = 100
): { timeH: number; torqueNm: number; remainingEnergyJ: number; outputTorqueNm: number }[] {
  if (torqueCurve.length < 2) throw new Error('Torque curve needs >= 2 points');
  const totalE = integrateTorqueEnergy(torqueCurve);
  const usable = totalE * transmissionEfficiency;
  const totalHours = usable / avgPowerW / 3600;
  const maxT = Math.max(...torqueCurve.map((c) => c[1]));
  const out: { timeH: number; torqueNm: number; remainingEnergyJ: number; outputTorqueNm: number }[] = [];
  for (let i = 0; i <= points; i++) {
    const frac = i / points;
    const th = frac * torqueCurve[torqueCurve.length - 1][0];
    // Interpolate torque at th
    let T = torqueCurve[0][1];
    for (let j = 0; j < torqueCurve.length - 1; j++) {
      if (th >= torqueCurve[j][0] && th <= torqueCurve[j + 1][0]) {
        const t = (th - torqueCurve[j][0]) / (torqueCurve[j + 1][0] - torqueCurve[j][0]);
        T = torqueCurve[j][1] + t * (torqueCurve[j + 1][1] - torqueCurve[j][1]);
        break;
      }
    }
    const remaining = usable * (1 - frac);
    out.push({
      timeH: frac * totalHours,
      torqueNm: T,
      remainingEnergyJ: remaining,
      outputTorqueNm: (T / maxT) * avgPowerW * 0.001 // scaled indicator
    });
  }
  return out;
}
