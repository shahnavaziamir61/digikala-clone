const BASE = '';

async function post<T = any>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  if (!res.ok) throw new Error(`API ${path}: ${res.status} ${await res.text()}`);
  return res.json() as Promise<T>;
}
async function get<T = any>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`API ${path}: ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  health: () => get<{ ok: boolean }>('/api/health'),
  materials: () => get<unknown[]>('/api/materials'),
  projects: () => get<unknown[]>('/api/projects'),
  createProject: (body: unknown) => post<any>('/api/projects', body),
  getProject: (id: string) => get<any>(`/api/projects/${id}`),
  saveProject: (id: string, body: unknown) => fetch(`${BASE}/api/projects/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then((r) => r.json()),
  duplicateProject: (id: string) => post<any>(`/api/projects/${id}/duplicate`, {}),
  report: (id: string) => get<any>(`/api/projects/${id}/report`),
  bom: (id: string) => get<any>(`/api/projects/${id}/bom`),
  components: (q = '') => get<unknown[]>(`/api/components${q ? `?q=${encodeURIComponent(q)}` : ''}`),
  createComponent: (body: unknown) => post<any>('/api/components', body),
  updateComponent: (id: string, body: unknown) => fetch(`${BASE}/api/components/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then((r) => r.json()),
  duplicateComponent: (id: string) => post<any>(`/api/components/${id}/duplicate`, {}),
  deleteComponent: (id: string) => fetch(`${BASE}/api/components/${id}`, { method: 'DELETE' }).then((r) => r.json()),
  calcGear: (body: unknown) => post<any>('/api/calc/gear', body),
  calcMesh: (body: unknown) => post<any>('/api/calc/gear-mesh', body),
  calcTrain: (body: unknown) => post<any>('/api/calc/geartrain', body),
  calcMainspring: (body: unknown) => post<any>('/api/calc/mainspring', body),
  calcPowerReserve: (body: unknown) => post<any>('/api/calc/power-reserve', body),
  calcBalance: (body: unknown) => post<any>('/api/calc/balance', body),
  calcEscapement: (body: unknown) => post<any>('/api/calc/escapement', body),
  calcTourbillon: (body: unknown) => post<any>('/api/calc/tourbillon', body),
  calcBearing: (body: unknown) => post<any>('/api/calc/bearing', body),
  calcEnergy: (body: unknown) => post<any>('/api/calc/energy', body),
  calcEnergySeries: (body: unknown) => post<any>('/api/calc/energy-series', body),
  calcTolerance: (body: unknown) => post<any>('/api/calc/tolerance', body),
  simEscapement: (body: unknown) => post<any>('/api/simulate/escapement', body),
  simDynamics: (body: unknown) => post<any>('/api/simulate/dynamics', body),
  validationSuite: () => get<unknown[]>('/api/validation/suite'),
  cadStatus: () => get<any>('/api/cad/solidcraft/status'),
  exportGear: (body: unknown) => fetch(`${BASE}/api/cad/export-gear`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
};
