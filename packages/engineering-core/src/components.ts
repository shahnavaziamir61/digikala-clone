/**
 * Parametric component model + component library.
 * Every component carries the full engineering record required by the spec:
 * ID, name, category, parametric dimensions, material, density, mass,
 * centre of mass, inertia, finish, tolerances, interfaces, CAD ref, revision.
 */
import { assertPositive } from './units.js';
import { getMaterial } from './materials.js';

export type ComponentCategory =
  | 'gear-wheel' | 'pinion' | 'spring' | 'barrel' | 'balance-wheel' | 'hairspring'
  | 'escapement' | 'tourbillon-cage' | 'shaft' | 'jewel' | 'bearing' | 'screw'
  | 'bridge' | 'plate' | 'material' | 'custom';

export interface ParametricComponent {
  id: string;
  name: string;
  nameFa?: string;
  category: ComponentCategory;
  /** Parametric dimensions [m] — keyed by engineering name. */
  dimensions: Record<string, number>;
  materialId: string;
  densityKgM3: number;
  massKg: number;
  centerOfMassM: [number, number, number];
  momentOfInertiaKgM2: number;
  surfaceFinishRaUm: number;
  tolerances: Record<string, { plusM: number; minusM: number }>;
  assemblyInterfaces: string[];
  bearingInterfaces: string[];
  fasteningInterfaces: string[];
  cadReference?: string; // file / SolidCraft feature id
  revision: number;
  manufacturingNotes: string;
  /** Sketch/feature history (parametric operations). */
  features: { type: string; params: Record<string, number | string> }[];
  source: string;
  license: string;
  createdAt: string;
  updatedAt: string;
}

let counter = 0;
export function newComponentId(prefix = 'cmp'): string {
  counter++;
  return `${prefix}-${Date.now().toString(36)}-${counter.toString(36)}`;
}

export function createComponent(input: Partial<ParametricComponent> & { name: string; category: ComponentCategory; materialId: string }): ParametricComponent {
  const mat = getMaterial(input.materialId);
  const now = new Date().toISOString();
  return {
    id: input.id ?? newComponentId(),
    name: input.name,
    nameFa: input.nameFa,
    category: input.category,
    dimensions: input.dimensions ?? {},
    materialId: input.materialId,
    densityKgM3: input.densityKgM3 ?? mat.densityKgM3,
    massKg: input.massKg ?? 0,
    centerOfMassM: input.centerOfMassM ?? [0, 0, 0],
    momentOfInertiaKgM2: input.momentOfInertiaKgM2 ?? 0,
    surfaceFinishRaUm: input.surfaceFinishRaUm ?? 0.4,
    tolerances: input.tolerances ?? {},
    assemblyInterfaces: input.assemblyInterfaces ?? [],
    bearingInterfaces: input.bearingInterfaces ?? [],
    fasteningInterfaces: input.fasteningInterfaces ?? [],
    cadReference: input.cadReference,
    revision: input.revision ?? 1,
    manufacturingNotes: input.manufacturingNotes ?? '',
    features: input.features ?? [],
    source: input.source ?? 'Horology Engineering library',
    license: input.license ?? 'MIT',
    createdAt: input.createdAt ?? now,
    updatedAt: input.updatedAt ?? now
  };
}

/** Recompute mass/inertia from dimensions for simple primitives (cylinder/ring). */
export function recomputeMass(c: ParametricComponent): ParametricComponent {
  const mat = getMaterial(c.materialId);
  const d = c.dimensions;
  let mass = c.massKg;
  let inertia = c.momentOfInertiaKgM2;
  if (d.diameterM && d.thicknessM) {
    const r = d.diameterM / 2;
    const vol = Math.PI * r * r * d.thicknessM;
    mass = vol * mat.densityKgM3;
    inertia = 0.5 * mass * r * r;
  } else if (d.outerDiameterM && d.innerDiameterM && d.thicknessM) {
    const ro = d.outerDiameterM / 2;
    const ri = d.innerDiameterM / 2;
    const vol = Math.PI * (ro * ro - ri * ri) * d.thicknessM;
    mass = vol * mat.densityKgM3;
    inertia = 0.5 * mass * (ro * ro + ri * ri);
  }
  return { ...c, massKg: mass, momentOfInertiaKgM2: inertia, densityKgM3: mat.densityKgM3, updatedAt: new Date().toISOString() };
}

export class ComponentLibrary {
  private items = new Map<string, ParametricComponent>();

  add(c: ParametricComponent): ParametricComponent {
    this.items.set(c.id, c);
    return c;
  }
  get(id: string): ParametricComponent | undefined {
    return this.items.get(id);
  }
  list(): ParametricComponent[] {
    return [...this.items.values()];
  }
  update(id: string, patch: Partial<ParametricComponent>): ParametricComponent {
    const cur = this.items.get(id);
    if (!cur) throw new Error(`Component not found: ${id}`);
    const next = { ...cur, ...patch, id: cur.id, revision: cur.revision + 1, updatedAt: new Date().toISOString() };
    this.items.set(id, next);
    return next;
  }
  remove(id: string): boolean {
    return this.items.delete(id);
  }
  duplicate(id: string, newName?: string): ParametricComponent {
    const cur = this.items.get(id);
    if (!cur) throw new Error(`Component not found: ${id}`);
    const copy: ParametricComponent = {
      ...JSON.parse(JSON.stringify(cur)),
      id: newComponentId(),
      name: newName ?? `${cur.name} (copy)`,
      revision: 1,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    this.items.set(copy.id, copy);
    return copy;
  }
  search(query: string, category?: ComponentCategory): ParametricComponent[] {
    const q = query.toLowerCase();
    return this.list().filter(
      (c) =>
        (!category || c.category === category) &&
        (c.name.toLowerCase().includes(q) || c.id.toLowerCase().includes(q) || c.category.includes(q))
    );
  }
  exportJSON(): string {
    return JSON.stringify(this.list(), null, 2);
  }
  importJSON(json: string): ParametricComponent[] {
    const arr = JSON.parse(json) as ParametricComponent[];
    if (!Array.isArray(arr)) throw new Error('Import expects a JSON array of components');
    return arr.map((c) => this.add(c));
  }
}

/** Seed library with initial engineering components. */
export function seedLibrary(): ComponentLibrary {
  const lib = new ComponentLibrary();
  const now = new Date().toISOString();
  const seed = (c: ParametricComponent) => lib.add(c);
  seed(createComponent({ id: 'gear-m1-z24', name: 'Gear wheel m1 z24', category: 'gear-wheel', materialId: 'brass', dimensions: { moduleM: 0.001, teeth: 24, faceWidthM: 0.002 }, features: [{ type: 'involute-extrude', params: { moduleM: 0.001, teeth: 24 } }], manufacturingNotes: 'Hob or shape cut; deburr; check backlash.' }));
  seed(createComponent({ id: 'pinion-m1-z8', name: 'Pinion m1 z8', category: 'pinion', materialId: 'steel-hardened', dimensions: { moduleM: 0.001, teeth: 8, faceWidthM: 0.002 }, features: [{ type: 'involute-extrude', params: { moduleM: 0.001, teeth: 8 } }], manufacturingNotes: 'Undercut risk at z=8, 20° — use profile shift.' }));
  seed(createComponent({ id: 'barrel-300clock', name: 'Mainspring barrel Ø120', category: 'barrel', materialId: 'brass', dimensions: { diameterM: 0.12, thicknessM: 0.008 }, features: [{ type: 'revolve', params: { diameterM: 0.12 } }], manufacturingNotes: 'Deep-drawn or machined; polish bore.' }));
  seed(createComponent({ id: 'balance-20mm', name: 'Balance wheel Ø20', category: 'balance-wheel', materialId: 'gilt-brass', dimensions: { diameterM: 0.02, thicknessM: 0.001 }, features: [{ type: 'revolve', params: { diameterM: 0.02 } }] }));
  seed(createComponent({ id: 'hairspring-blued', name: 'Blued steel hairspring', category: 'hairspring', materialId: 'blued-steel', dimensions: { lengthM: 0.05, thicknessM: 0.00002, widthM: 0.00015 }, features: [{ type: 'sweep-spiral', params: { turns: 6 } }] }));
  seed(createComponent({ id: 'escape-wheel-15', name: 'Escape wheel z15', category: 'escapement', materialId: 'steel-hardened', dimensions: { teeth: 15, diameterM: 0.012 }, features: [{ type: 'involute-extrude', params: { teeth: 15 } }] }));
  seed(createComponent({ id: 'cage-70mm', name: 'Tourbillon cage Ø70', category: 'tourbillon-cage', materialId: 'titanium', dimensions: { diameterM: 0.07, heightM: 0.012 }, features: [{ type: 'loft', params: { diameterM: 0.07 } }], manufacturingNotes: 'Skeletonised; balance dynamically.' }));
  seed(createComponent({ id: 'jewel-ruby-0.5', name: 'Ruby hole jewel Ø0.5', category: 'jewel', materialId: 'ruby', dimensions: { innerDiameterM: 0.0005, outerDiameterM: 0.0015, thicknessM: 0.0003 }, manufacturingNotes: 'Press fit; oil sink.' }));
  seed(createComponent({ id: 'shaft-0.3', name: 'Arbor shaft Ø0.3', category: 'shaft', materialId: 'steel-hardened', dimensions: { diameterM: 0.0003, lengthM: 0.005 }, features: [{ type: 'revolve', params: { diameterM: 0.0003 } }] }));
  seed(createComponent({ id: 'screw-m0.8', name: 'Blued screw M0.8', category: 'screw', materialId: 'blued-steel', dimensions: { diameterM: 0.0008, lengthM: 0.002 }, features: [{ type: 'thread', params: { pitchM: 0.0002 } }] }));
  seed(createComponent({ id: 'bridge-main', name: 'Main bridge', category: 'bridge', materialId: 'gilt-brass', dimensions: { thicknessM: 0.002 }, features: [{ type: 'extrude', params: { thicknessM: 0.002 } }] }));
  seed(createComponent({ id: 'plate-main', name: 'Main plate', category: 'plate', materialId: 'gilt-brass', dimensions: { thicknessM: 0.003 }, features: [{ type: 'extrude', params: { thicknessM: 0.003 } }] }));
  void now;
  void assertPositive;
  return lib;
}
