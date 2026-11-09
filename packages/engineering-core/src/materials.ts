/**
 * Material database for horological engineering.
 * Values are typical published engineering values (see docs/ENGINEERING.md
 * for sources and uncertainty). All SI units.
 */

export interface Material {
  id: string;
  name: string;
  nameFa?: string;
  category: string;
  elasticModulusPa: number; // E
  poissonRatio: number; // nu
  densityKgM3: number; // rho
  yieldStrengthPa: number;
  ultimateStrengthPa: number;
  hardnessHv?: number;
  frictionCoefficient?: number; // dry, steel-on-steel reference
  thermalExpansionPerK?: number;
  fatigueLimitPa?: number; // rotating bending, approx
  notes: string;
  source: string;
}

export const MATERIALS: Material[] = [
  {
    id: 'blued-steel',
    name: 'Blued Steel (spring steel)',
    category: 'Steel',
    elasticModulusPa: 200e9,
    poissonRatio: 0.3,
    densityKgM3: 7850,
    yieldStrengthPa: 1600e6,
    ultimateStrengthPa: 2000e6,
    hardnessHv: 750,
    frictionCoefficient: 0.15,
    thermalExpansionPerK: 11.5e-6,
    fatigueLimitPa: 700e6,
    notes: 'Classic mainspring / hairspring steel. High yield, good fatigue.',
    source: 'Typical values per Machinery Handbook; verify against supplier datasheet.'
  },
  {
    id: 'silicon',
    name: 'Silicon (MEMS hairspring)',
    category: 'Semiconductor',
    elasticModulusPa: 170e9,
    poissonRatio: 0.28,
    densityKgM3: 2330,
    yieldStrengthPa: 7000e6,
    ultimateStrengthPa: 7000e6,
    hardnessHv: 1100,
    frictionCoefficient: 0.1,
    thermalExpansionPerK: 2.6e-6,
    fatigueLimitPa: 500e6,
    notes: 'Brittle, no plasticity. Excellent thermal stability, antimagnetic.',
    source: 'Typical MEMS silicon values.'
  },
  {
    id: 'brass',
    name: 'Brass CuZn39Pb3',
    category: 'Copper alloy',
    elasticModulusPa: 110e9,
    poissonRatio: 0.34,
    densityKgM3: 8500,
    yieldStrengthPa: 300e6,
    ultimateStrengthPa: 450e6,
    hardnessHv: 120,
    frictionCoefficient: 0.2,
    thermalExpansionPerK: 19e-6,
    fatigueLimitPa: 150e6,
    notes: 'Gear wheels, plates. Good machinability.',
    source: 'Typical CuZn39Pb3 datasheet values.'
  },
  {
    id: 'gilt-brass',
    name: 'Gilt Brass',
    category: 'Copper alloy',
    elasticModulusPa: 100e9,
    poissonRatio: 0.34,
    densityKgM3: 8400,
    yieldStrengthPa: 250e6,
    ultimateStrengthPa: 380e6,
    hardnessHv: 100,
    frictionCoefficient: 0.2,
    thermalExpansionPerK: 19e-6,
    fatigueLimitPa: 120e6,
    notes: 'Traditional movement plates / bridges.',
    source: 'Typical values.'
  },
  {
    id: 'steel-hardened',
    name: 'Hardened Steel (pinions, arbors)',
    category: 'Steel',
    elasticModulusPa: 210e9,
    poissonRatio: 0.3,
    densityKgM3: 7850,
    yieldStrengthPa: 1200e6,
    ultimateStrengthPa: 1500e6,
    hardnessHv: 700,
    frictionCoefficient: 0.15,
    thermalExpansionPerK: 11.5e-6,
    fatigueLimitPa: 600e6,
    notes: 'Pinions, pivots, escape wheels.',
    source: 'Typical values.'
  },
  {
    id: 'titanium',
    name: 'Titanium Grade 5 (Ti-6Al-4V)',
    category: 'Titanium',
    elasticModulusPa: 114e9,
    poissonRatio: 0.34,
    densityKgM3: 4430,
    yieldStrengthPa: 880e6,
    ultimateStrengthPa: 950e6,
    hardnessHv: 350,
    frictionCoefficient: 0.3,
    thermalExpansionPerK: 8.6e-6,
    fatigueLimitPa: 500e6,
    notes: 'Lightweight cage / bridges.',
    source: 'Typical Ti-6Al-4V datasheet.'
  },
  {
    id: 'ruby',
    name: 'Synthetic Ruby (Al2O3)',
    category: 'Jewel',
    elasticModulusPa: 400e9,
    poissonRatio: 0.22,
    densityKgM3: 3980,
    yieldStrengthPa: 3000e6,
    ultimateStrengthPa: 3000e6,
    hardnessHv: 2000,
    frictionCoefficient: 0.05,
    thermalExpansionPerK: 5e-6,
    notes: 'Pivot bearings. Brittle; avoid tensile shock.',
    source: 'Typical sapphire/ruby values.'
  },
  {
    id: 'sapphire',
    name: 'Synthetic Sapphire (Al2O3)',
    category: 'Jewel',
    elasticModulusPa: 400e9,
    poissonRatio: 0.22,
    densityKgM3: 3980,
    yieldStrengthPa: 3000e6,
    ultimateStrengthPa: 3000e6,
    hardnessHv: 2000,
    frictionCoefficient: 0.05,
    thermalExpansionPerK: 5e-6,
    notes: 'Crystal / jewels.',
    source: 'Typical values.'
  },
  {
    id: 'nivarox',
    name: 'Nivarox-type alloy (hairspring)',
    category: 'Nickel alloy',
    elasticModulusPa: 180e9,
    poissonRatio: 0.3,
    densityKgM3: 8100,
    yieldStrengthPa: 1400e6,
    ultimateStrengthPa: 1600e6,
    hardnessHv: 550,
    frictionCoefficient: 0.15,
    thermalExpansionPerK: 12e-6,
    fatigueLimitPa: 600e6,
    notes: 'Low thermal coefficient hairspring alloy (estimated typical).',
    source: 'Typical Nivarox published data; verify with supplier.'
  },
  {
    id: 'aluminium',
    name: 'Aluminium 7075-T6',
    category: 'Aluminium',
    elasticModulusPa: 71.7e9,
    poissonRatio: 0.33,
    densityKgM3: 2810,
    yieldStrengthPa: 503e6,
    ultimateStrengthPa: 572e6,
    hardnessHv: 175,
    frictionCoefficient: 0.25,
    thermalExpansionPerK: 23.6e-6,
    fatigueLimitPa: 160e6,
    notes: 'Lightweight plates / cage.',
    source: 'Typical 7075-T6 datasheet.'
  }
];

export function getMaterial(id: string): Material {
  const m = MATERIALS.find((x) => x.id === id);
  if (!m) throw new Error(`Unknown material id: ${id}`);
  return m;
}
