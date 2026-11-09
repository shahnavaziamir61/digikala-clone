/**
 * Versioned JSON project format (schema v1).
 * Validation is manual (zero-dependency) and strict about version.
 */
import { ParametricComponent } from './components.js';

export const PROJECT_SCHEMA_VERSION = 1;

export interface WatchConfig {
  type: 'wristwatch' | 'wall-clock' | 'tourbillon' | 'custom';
  caseDiameterM?: number;
  movementDiameterM?: number;
  tourbillon?: {
    cageDiameterM: number;
    cagePeriodS: number;
    balanceFrequencyHz: number;
  };
  targetPowerReserveHours: number;
}

export interface Project {
  schemaVersion: number;
  id: string;
  name: string;
  nameFa?: string;
  description: string;
  createdAt: string;
  updatedAt: string;
  watch: WatchConfig;
  components: ParametricComponent[];
  gearTrain: { stages: { driverTeeth: number; drivenTeeth: number; moduleM: number }[] };
  assembly: { id: string; name: string; componentIds: string[]; parentId?: string }[];
  materials: string[]; // material ids used
  simulation: { mode: string; durationS: number; dtS: number };
  calculations: Record<string, unknown>; // cached calc results
  validation: { checkedAt: string; results: { module: string; status: string; message: string }[] };
  manufacturing: { notes: string; units: 'metric' | 'imperial' };
  cadReferences: Record<string, string>;
  versionHistory: { version: number; at: string; note: string }[];
}

function newProjectId(): string {
  return `proj-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

export function createProject(input: { name: string; watch: WatchConfig }): Project {
  const now = new Date().toISOString();
  return {
    schemaVersion: PROJECT_SCHEMA_VERSION,
    id: newProjectId(),
    name: input.name,
    description: '',
    createdAt: now,
    updatedAt: now,
    watch: input.watch,
    components: [],
    gearTrain: { stages: [] },
    assembly: [],
    materials: [],
    simulation: { mode: 'rigid-body', durationS: 10, dtS: 0.001 },
    calculations: {},
    validation: { checkedAt: now, results: [] },
    manufacturing: { notes: '', units: 'metric' },
    cadReferences: {},
    versionHistory: [{ version: 1, at: now, note: 'Created' }]
  };
}

export function validateProject(data: unknown): { ok: boolean; errors: string[] } {
  const errors: string[] = [];
  if (typeof data !== 'object' || data === null) return { ok: false, errors: ['Project must be an object'] };
  const p = data as Record<string, unknown>;
  if (p.schemaVersion !== PROJECT_SCHEMA_VERSION)
    errors.push(`Unsupported schemaVersion ${String(p.schemaVersion)} (expected ${PROJECT_SCHEMA_VERSION})`);
  if (typeof p.id !== 'string' || !p.id) errors.push('Missing id');
  if (typeof p.name !== 'string' || !p.name) errors.push('Missing name');
  if (typeof p.watch !== 'object' || p.watch === null) errors.push('Missing watch config');
  else {
    const w = p.watch as Record<string, unknown>;
    if (typeof w.targetPowerReserveHours !== 'number' || (w.targetPowerReserveHours as number) <= 0)
      errors.push('watch.targetPowerReserveHours must be > 0');
  }
  if (!Array.isArray(p.components)) errors.push('components must be an array');
  if (!Array.isArray(p.assembly)) errors.push('assembly must be an array');
  return { ok: errors.length === 0, errors };
}

export function parseProject(json: string): Project {
  const data = JSON.parse(json);
  const v = validateProject(data);
  if (!v.ok) throw new Error(`Invalid project: ${v.errors.join('; ')}`);
  return data as Project;
}

export function duplicateProject(p: Project, newName?: string): Project {
  const copy = JSON.parse(JSON.stringify(p)) as Project;
  copy.id = `proj-${Date.now().toString(36)}`;
  copy.name = newName ?? `${p.name} (copy)`;
  copy.createdAt = new Date().toISOString();
  copy.updatedAt = copy.createdAt;
  copy.versionHistory = [...p.versionHistory, { version: p.versionHistory.length + 1, at: copy.createdAt, note: 'Duplicated' }];
  return copy;
}

export function bumpVersion(p: Project, note: string): Project {
  const next = { ...p, updatedAt: new Date().toISOString() };
  next.versionHistory = [...p.versionHistory, { version: p.versionHistory.length + 1, at: next.updatedAt, note }];
  return next;
}
