import { Express, Request, Response } from 'express';
import {
  MATERIALS, getMaterial,
  calculateGear, meshGears, calculateGearTrain,
  calculateMainspring, powerReserveCheck,
  calculateBalance,
  calculateEscapementGeometry, simulateEscapement,
  calculateTourbillon, suggestTourbillonTeeth,
  calculateBearing, analyzeEnergy, energyTimeSeries,
  analyzeTolerance, simulateDynamics,
  createProject, validateProject, parseProject, duplicateProject, bumpVersion,
  createComponent, recomputeMass,
  generateReport, runValidationSuite,
  gearMesh, meshToSTL, meshToOBJ, meshToSTEP
} from '@horology/engineering-core';
import { probeSolidCraft, exportGear } from '@horology/cad-adapter';
import { Store } from './store.js';

function err(res: Response, e: unknown) {
  res.status(400).json({ error: String(e instanceof Error ? e.message : e) });
}

export function registerRoutes(app: Express, store: Store) {
  app.get('/api/health', (_req, res) => res.json({ ok: true, service: 'horology-engineering', version: '0.1.0' }));

  // ---- Materials ----
  app.get('/api/materials', (_req, res) => res.json(MATERIALS));
  app.get('/api/materials/:id', (req, res) => {
    try { res.json(getMaterial(req.params.id)); } catch (e) { err(res, e); }
  });

  // ---- Projects ----
  app.get('/api/projects', (_req, res) => res.json(store.listProjects()));
  app.post('/api/projects', (req, res) => {
    try {
      const p = createProject({ name: req.body.name ?? 'Untitled', watch: req.body.watch ?? { type: 'custom', targetPowerReserveHours: 48 } });
      if (req.body.description) p.description = req.body.description;
      store.saveProject(p);
      res.status(201).json(p);
    } catch (e) { err(res, e); }
  });
  app.get('/api/projects/:id', (req, res) => {
    const p = store.getProject(req.params.id);
    if (!p) return res.status(404).json({ error: 'Project not found' });
    res.json(p);
  });
  app.put('/api/projects/:id', (req, res) => {
    try {
      const v = validateProject(req.body);
      if (!v.ok) return res.status(400).json({ error: 'Invalid project', errors: v.errors });
      const p = bumpVersion(req.body, req.body.note ?? 'Updated');
      store.saveProject(p);
      res.json(p);
    } catch (e) { err(res, e); }
  });
  app.post('/api/projects/import', (req, res) => {
    try {
      const p = parseProject(JSON.stringify(req.body));
      store.saveProject(p);
      res.status(201).json(p);
    } catch (e) { err(res, e); }
  });
  app.post('/api/projects/:id/duplicate', (req, res) => {
    const p = store.getProject(req.params.id);
    if (!p) return res.status(404).json({ error: 'Project not found' });
    const dup = duplicateProject(p, req.body?.name);
    store.saveProject(dup);
    res.status(201).json(dup);
  });
  app.delete('/api/projects/:id', (req, res) => {
    res.json({ deleted: store.deleteProject(req.params.id) });
  });
  app.get('/api/projects/:id/report', (req, res) => {
    const p = store.getProject(req.params.id);
    if (!p) return res.status(404).json({ error: 'Project not found' });
    res.json(generateReport(p.id));
  });
  app.get('/api/projects/:id/bom', (req, res) => {
    const p = store.getProject(req.params.id);
    if (!p) return res.status(404).json({ error: 'Project not found' });
    const bom = p.components.map((c) => ({
      id: c.id, name: c.name, category: c.category, material: c.materialId,
      massKg: c.massKg, revision: c.revision, cadReference: c.cadReference ?? null
    }));
    const totalMass = bom.reduce((a, b) => a + b.massKg, 0);
    res.json({ projectId: p.id, items: bom, totalMassKg: totalMass, count: bom.length });
  });
  app.get('/api/validation/suite', (_req, res) => res.json(runValidationSuite()));

  // ---- Components ----
  app.get('/api/components', (req, res) => {
    const q = String(req.query.q ?? '');
    const cat = req.query.category as never;
    const all = store.listComponents();
    const filtered = q ? all.filter((c) => c.name.toLowerCase().includes(q.toLowerCase()) || c.id.toLowerCase().includes(q.toLowerCase())) : all;
    res.json(cat ? filtered.filter((c) => c.category === cat) : filtered);
  });
  app.post('/api/components', (req, res) => {
    try {
      const c = recomputeMass(createComponent(req.body));
      store.saveComponent(c);
      res.status(201).json(c);
    } catch (e) { err(res, e); }
  });
  app.get('/api/components/:id', (req, res) => {
    const c = store.getComponent(req.params.id);
    if (!c) return res.status(404).json({ error: 'Component not found' });
    res.json(c);
  });
  app.put('/api/components/:id', (req, res) => {
    try {
      const cur = store.getComponent(req.params.id);
      if (!cur) return res.status(404).json({ error: 'Component not found' });
      const next = recomputeMass({ ...cur, ...req.body, id: cur.id, revision: cur.revision + 1, updatedAt: new Date().toISOString() });
      store.saveComponent(next);
      res.json(next);
    } catch (e) { err(res, e); }
  });
  app.post('/api/components/:id/duplicate', (req, res) => {
    const cur = store.getComponent(req.params.id);
    if (!cur) return res.status(404).json({ error: 'Component not found' });
    const copy = { ...JSON.parse(JSON.stringify(cur)), id: `cmp-${Date.now().toString(36)}`, name: req.body?.name ?? `${cur.name} (copy)`, revision: 1, createdAt: new Date().toISOString(), updatedAt: new Date().toISOString() };
    store.saveComponent(copy);
    res.status(201).json(copy);
  });
  app.delete('/api/components/:id', (req, res) => res.json({ deleted: store.deleteComponent(req.params.id) }));

  // ---- Calculations ----
  app.post('/api/calc/gear', (req, res) => { try { res.json(calculateGear(req.body)); } catch (e) { err(res, e); } });
  app.post('/api/calc/gear-mesh', (req, res) => { try { res.json(meshGears(req.body.g1, req.body.g2, req.body.opts)); } catch (e) { err(res, e); } });
  app.post('/api/calc/geartrain', (req, res) => { try { res.json(calculateGearTrain(req.body.stages, req.body.inputSpeedRadps, req.body.inputTorqueNm)); } catch (e) { err(res, e); } });
  app.post('/api/calc/mainspring', (req, res) => { try { res.json(calculateMainspring(req.body)); } catch (e) { err(res, e); } });
  app.post('/api/calc/power-reserve', (req, res) => { try { res.json(powerReserveCheck(req.body)); } catch (e) { err(res, e); } });
  app.post('/api/calc/balance', (req, res) => { try { res.json(calculateBalance(req.body)); } catch (e) { err(res, e); } });
  app.post('/api/calc/escapement', (req, res) => { try { res.json(calculateEscapementGeometry(req.body)); } catch (e) { err(res, e); } });
  app.post('/api/calc/tourbillon', (req, res) => { try { res.json(calculateTourbillon(req.body)); } catch (e) { err(res, e); } });
  app.post('/api/calc/tourbillon-suggest', (req, res) => { try { res.json(suggestTourbillonTeeth(req.body.requiredRatio)); } catch (e) { err(res, e); } });
  app.post('/api/calc/bearing', (req, res) => { try { res.json(calculateBearing(req.body)); } catch (e) { err(res, e); } });
  app.post('/api/calc/energy', (req, res) => { try { res.json(analyzeEnergy(req.body.budget, req.body.avgPowerConsumptionW, req.body.targetHours)); } catch (e) { err(res, e); } });
  app.post('/api/calc/energy-series', (req, res) => { try { res.json(energyTimeSeries(req.body.torqueCurve, req.body.avgPowerW, req.body.transmissionEfficiency)); } catch (e) { err(res, e); } });
  app.post('/api/calc/tolerance', (req, res) => { try { res.json(analyzeTolerance(req.body.items, req.body.opts)); } catch (e) { err(res, e); } });

  // ---- Simulation (REST) ----
  app.post('/api/simulate/escapement', (req, res) => { try { res.json(simulateEscapement(req.body.params, req.body.durationS ?? 5)); } catch (e) { err(res, e); } });
  app.post('/api/simulate/dynamics', (req, res) => { try { res.json(simulateDynamics(req.body.bodies, req.body.opts)); } catch (e) { err(res, e); } });

  // ---- CAD ----
  app.get('/api/cad/solidcraft/status', async (_req, res) => { res.json(await probeSolidCraft()); });
  app.post('/api/cad/export-gear', async (req, res) => {
    try {
      const gear = calculateGear(req.body.gear);
      const exp = await exportGear(gear, req.body.format ?? 'stl', req.body.name ?? 'gear');
      res.setHeader('Content-Type', exp.format === 'stl' ? 'application/octet-stream' : 'text/plain');
      res.setHeader('Content-Disposition', `attachment; filename="${exp.filename}"`);
      res.setHeader('X-Cad-Backend', exp.backend);
      res.send(exp.content);
    } catch (e) { err(res, e); }
  });
  app.post('/api/cad/mesh', (req, res) => {
    try {
      const gear = calculateGear(req.body.gear);
      const mesh = gearMesh(gear, req.body.name ?? 'gear');
      const fmt = req.body.format ?? 'obj';
      if (fmt === 'stl') { res.setHeader('Content-Type', 'application/octet-stream'); res.send(meshToSTL(mesh)); }
      else if (fmt === 'step') { res.setHeader('Content-Type', 'text/plain'); res.send(meshToSTEP(mesh)); }
      else { res.setHeader('Content-Type', 'text/plain'); res.send(meshToOBJ(mesh)); }
    } catch (e) { err(res, e); }
  });
}
