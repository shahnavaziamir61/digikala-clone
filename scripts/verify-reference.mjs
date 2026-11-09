/**
 * Recompute the reference project and compare with the stored JSON.
 * Usage: npm run build && node scripts/verify-reference.mjs
 */
import { readFileSync } from 'node:fs';
import {
  calculateMainspring, calculateBalance, calculateTourbillon,
  simulateEscapement, analyzeEnergy
} from '../packages/engineering-core/dist/index.js';

const stored = JSON.parse(readFileSync('projects/reference-wall-clock-300mm.json', 'utf8'));

const ms = calculateMainspring({ thicknessM: 0.0006, widthM: 0.006, lengthM: 4.0, innerRadiusM: 0.012, outerRadiusM: 0.07, barrelDiameterM: 0.15, arborDiameterM: 0.02, activeTurns: 8, materialId: 'blued-steel' });
const Iest = 0.002 * 0.02 * 0.02 * 1.1 + 0.0002 * 0.018 * 0.018;
const kappa = Iest * (2 * Math.PI * 1) ** 2;
const bal = calculateBalance({ diameterM: 0.04, thicknessM: 0.002, massKg: 0.002, timingScrewMassKg: 0.0002, timingScrewRadiusM: 0.018, hairspringStiffnessNmPerRad: kappa, hairspringLengthM: 0.08, materialId: 'blued-steel', amplitudeDeg: 270 });
const tb = calculateTourbillon({ cageDiameterM: 0.07, cageHeightM: 0.012, cageMassKg: 0.008, cageInertiaKgM2: 2e-6, cagePeriodS: 60, balanceDiameterM: 0.04, balanceFrequencyHz: bal.frequencyHz, escapeTeeth: 15, fixedWheelTeeth: 80, pinionTeeth: 10, shaftDiameterM: 0.0006, bearingInnerDiameterM: 0.0006, radialClearanceM: 0.00001, axialClearanceM: 0.00005, escapeWheelTorqueNm: 7e-6 });
const esc = simulateEscapement({ type: 'swiss-lever', escapeTeeth: 15, escapeDiameterM: 0.02, palletAngleDeg: 180, lockingAngleDeg: 2, dropDeg: 1, liftDeg: 3, drawDeg: 1, impulseAngleDeg: 8, balanceFrequencyHz: bal.frequencyHz, balanceInertiaKgM2: bal.inertiaKgM2, hairspringStiffnessNmPerRad: kappa, amplitudeDeg: 270, escapeWheelTorqueNm: 7e-6 }, 10);
const en = analyzeEnergy({ storedEnergyJ: ms.storedEnergyJ, gearFrictionPct: 10, bearingFrictionPct: 5, escapementLossPct: 20, balanceLossPct: 5, cageLossPct: 5, transmissionEfficiency: 0.8 }, esc.avgPowerW, 744);

const checks = [
  ['mainspring energy', ms.storedEnergyJ, stored.calculations.mainspring.storedEnergyJ],
  ['balance freq', bal.frequencyHz, stored.calculations.balance.frequencyHz],
  ['tourbillon ratio', tb.actualRatio, stored.calculations.tourbillon.actualRatio],
  ['escapement power', esc.avgPowerW, stored.calculations.escapement.avgPowerW],
  ['reserve hours', en.powerReserveHours, stored.calculations.energy.powerReserveHours]
];
let ok = true;
for (const [name, fresh, saved] of checks) {
  const match = Math.abs(fresh - saved) / Math.max(1e-12, Math.abs(saved)) < 0.01;
  console.log(`${match ? 'PASS' : 'FAIL'} ${name}: fresh=${fresh} stored=${saved}`);
  if (!match) ok = false;
}
console.log(ok ? 'Reference project verified ✓' : 'Reference project MISMATCH ✗');
process.exit(ok ? 0 : 1);
