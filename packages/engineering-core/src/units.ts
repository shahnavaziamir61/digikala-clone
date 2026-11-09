/**
 * Engineering unit system — SI base with metric/imperial display conversions.
 * All internal calculations use SI: metres, kilograms, seconds, pascals,
 * newtons, joules, watts, radians.
 */

export type UnitSystem = 'metric' | 'imperial';

export interface Quantity {
  value: number;
  unit: string;
}

export const MM = 0.001; // 1 mm in metres
export const CM = 0.01;
export const DEG2RAD = Math.PI / 180;
export const RAD2DEG = 180 / Math.PI;

export function assertFinite(name: string, v: number): void {
  if (!Number.isFinite(v)) throw new Error(`Parameter "${name}" must be finite, got ${v}`);
}

export function assertPositive(name: string, v: number): void {
  assertFinite(name, v);
  if (v <= 0) throw new Error(`Parameter "${name}" must be > 0, got ${v}`);
}

export function assertNonNegative(name: string, v: number): void {
  assertFinite(name, v);
  if (v < 0) throw new Error(`Parameter "${name}" must be >= 0, got ${v}`);
}

/** Convert a length in metres to display units. */
export function formatLength(m: number, system: UnitSystem): string {
  if (system === 'imperial') {
    const inch = m / 0.0254;
    return `${inch.toFixed(4)} in`;
  }
  if (Math.abs(m) < 0.001) return `${(m * 1000).toFixed(4)} mm`;
  if (Math.abs(m) < 1) return `${(m * 1000).toFixed(3)} mm`;
  return `${m.toFixed(4)} m`;
}

export function formatMass(kg: number, system: UnitSystem): string {
  if (system === 'imperial') return `${(kg * 2.20462).toFixed(4)} lb`;
  if (kg < 0.001) return `${(kg * 1e6).toFixed(2)} mg`;
  if (kg < 1) return `${(kg * 1000).toFixed(3)} g`;
  return `${kg.toFixed(4)} kg`;
}

export function formatEnergy(j: number, system: UnitSystem): string {
  if (system === 'imperial') return `${(j * 0.737562).toFixed(4)} ft·lbf`;
  return `${j.toFixed(4)} J`;
}

export function formatTorque(nm: number, system: UnitSystem): string {
  if (system === 'imperial') return `${(nm * 8.85075).toFixed(4)} lbf·in`;
  if (Math.abs(nm) < 0.001) return `${(nm * 1e6).toFixed(2)} µN·m`;
  if (Math.abs(nm) < 1) return `${(nm * 1000).toFixed(3)} mN·m`;
  return `${nm.toFixed(4)} N·m`;
}

export function formatStress(pa: number, system: UnitSystem): string {
  if (system === 'imperial') return `${(pa / 6894.76).toFixed(2)} psi`;
  if (Math.abs(pa) >= 1e9) return `${(pa / 1e9).toFixed(3)} GPa`;
  if (Math.abs(pa) >= 1e6) return `${(pa / 1e6).toFixed(2)} MPa`;
  return `${pa.toFixed(1)} Pa`;
}

/** Parse a user-entered length in mm (metric) or inches (imperial) to metres. */
export function parseLength(input: number, system: UnitSystem): number {
  assertFinite('length', input);
  return system === 'imperial' ? input * 0.0254 : input * MM;
}
