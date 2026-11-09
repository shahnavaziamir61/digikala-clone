const BASE = '';
async function post(path, body) {
    const res = await fetch(`${BASE}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (!res.ok)
        throw new Error(`API ${path}: ${res.status} ${await res.text()}`);
    return res.json();
}
async function get(path) {
    const res = await fetch(`${BASE}${path}`);
    if (!res.ok)
        throw new Error(`API ${path}: ${res.status}`);
    return res.json();
}
export const api = {
    health: () => get('/api/health'),
    materials: () => get('/api/materials'),
    projects: () => get('/api/projects'),
    createProject: (body) => post('/api/projects', body),
    getProject: (id) => get(`/api/projects/${id}`),
    saveProject: (id, body) => fetch(`${BASE}/api/projects/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then((r) => r.json()),
    duplicateProject: (id) => post(`/api/projects/${id}/duplicate`, {}),
    report: (id) => get(`/api/projects/${id}/report`),
    bom: (id) => get(`/api/projects/${id}/bom`),
    components: (q = '') => get(`/api/components${q ? `?q=${encodeURIComponent(q)}` : ''}`),
    createComponent: (body) => post('/api/components', body),
    updateComponent: (id, body) => fetch(`${BASE}/api/components/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then((r) => r.json()),
    duplicateComponent: (id) => post(`/api/components/${id}/duplicate`, {}),
    deleteComponent: (id) => fetch(`${BASE}/api/components/${id}`, { method: 'DELETE' }).then((r) => r.json()),
    calcGear: (body) => post('/api/calc/gear', body),
    calcMesh: (body) => post('/api/calc/gear-mesh', body),
    calcTrain: (body) => post('/api/calc/geartrain', body),
    calcMainspring: (body) => post('/api/calc/mainspring', body),
    calcPowerReserve: (body) => post('/api/calc/power-reserve', body),
    calcBalance: (body) => post('/api/calc/balance', body),
    calcEscapement: (body) => post('/api/calc/escapement', body),
    calcTourbillon: (body) => post('/api/calc/tourbillon', body),
    calcBearing: (body) => post('/api/calc/bearing', body),
    calcEnergy: (body) => post('/api/calc/energy', body),
    calcEnergySeries: (body) => post('/api/calc/energy-series', body),
    calcTolerance: (body) => post('/api/calc/tolerance', body),
    simEscapement: (body) => post('/api/simulate/escapement', body),
    simDynamics: (body) => post('/api/simulate/dynamics', body),
    validationSuite: () => get('/api/validation/suite'),
    cadStatus: () => get('/api/cad/solidcraft/status'),
    exportGear: (body) => fetch(`${BASE}/api/cad/export-gear`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
};
