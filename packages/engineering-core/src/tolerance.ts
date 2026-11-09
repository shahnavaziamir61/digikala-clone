/**
 * Tolerance analysis: worst-case, RSS (root-sum-square), Monte Carlo.
 * Seeded RNG for reproducibility.
 */
import { assertPositive } from './units.js';

export interface ToleranceItem {
  name: string;
  nominalM: number;
  plusTolM: number; // + tolerance
  minusTolM: number; // - tolerance (positive magnitude)
  sensitivity?: number; // d(result)/d(dimension), default 1
}

export interface ToleranceResult {
  nominalM: number;
  worstCasePlusM: number;
  worstCaseMinusM: number;
  rssToleranceM: number; // ± RSS
  monteCarloMeanM: number;
  monteCarloStdM: number;
  monteCarloP99LowM: number;
  monteCarloP99HighM: number;
  samples: number;
  warnings: string[];
  resultType: 'Calculated';
}

/** Mulberry32 seeded RNG. */
export function seededRng(seed: number): () => number {
  let a = seed >>> 0;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** Box-Muller normal sample using provided uniform RNG. */
function normal(rng: () => number): number {
  let u = 0;
  let v = 0;
  while (u === 0) u = rng();
  while (v === 0) v = rng();
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

export function analyzeTolerance(items: ToleranceItem[], opts?: { samples?: number; seed?: number }): ToleranceResult {
  if (items.length === 0) throw new Error('Need at least one tolerance item');
  const N = opts?.samples ?? 10000;
  const rng = seededRng(opts?.seed ?? 42);

  let nominal = 0;
  let wcPlus = 0;
  let wcMinus = 0;
  let rssSq = 0;
  for (const it of items) {
    const s = it.sensitivity ?? 1;
    nominal += it.nominalM * s;
    wcPlus += it.plusTolM * Math.abs(s);
    wcMinus += it.minusTolM * Math.abs(s);
    // RSS assumes tolerance = 3 sigma (normal)
    const sigma = ((it.plusTolM + it.minusTolM) / 2 / 3) * Math.abs(s);
    rssSq += sigma * sigma;
  }
  const rss = Math.sqrt(rssSq) * 3; // back to ±3sigma band

  // Monte Carlo: each dimension normal, sigma = tol/3
  const mc: number[] = new Array(N);
  for (let i = 0; i < N; i++) {
    let v = 0;
    for (const it of items) {
      const s = it.sensitivity ?? 1;
      const sigma = ((it.plusTolM + it.minusTolM) / 2 / 3);
      v += (it.nominalM + normal(rng) * sigma) * s;
    }
    mc[i] = v;
  }
  mc.sort((a, b) => a - b);
  const mean = mc.reduce((a, b) => a + b, 0) / N;
  const variance = mc.reduce((a, b) => a + (b - mean) ** 2, 0) / N;
  const std = Math.sqrt(variance);

  const warnings: string[] = [];
  if (wcPlus > Math.abs(nominal) * 0.1) warnings.push('Worst-case stack exceeds 10% of nominal — consider tighter tolerances.');
  if (rss > wcPlus * 0.8) warnings.push('RSS close to worst-case — few dominant tolerances; review distribution assumptions.');

  return {
    nominalM: nominal,
    worstCasePlusM: wcPlus,
    worstCaseMinusM: wcMinus,
    rssToleranceM: rss,
    monteCarloMeanM: mean,
    monteCarloStdM: std,
    monteCarloP99LowM: mc[Math.floor(0.005 * N)],
    monteCarloP99HighM: mc[Math.floor(0.995 * N)],
    samples: N,
    warnings,
    resultType: 'Calculated'
  };
}

/** Fit check: shaft/hole with tolerances -> min/max clearance. */
export function fitCheck(shaft: { nominalM: number; plusTolM: number; minusTolM: number }, hole: { nominalM: number; plusTolM: number; minusTolM: number }): {
  minClearanceM: number;
  maxClearanceM: number;
  interference: boolean;
  warnings: string[];
} {
  const minClearance = hole.nominalM - hole.minusTolM - (shaft.nominalM + shaft.plusTolM);
  const maxClearance = hole.nominalM + hole.plusTolM - (shaft.nominalM - shaft.minusTolM);
  const warnings: string[] = [];
  if (minClearance < 0) warnings.push('Interference possible at worst case — check assembly.');
  return { minClearanceM: minClearance, maxClearanceM: maxClearance, interference: minClearance < 0, warnings };
}
