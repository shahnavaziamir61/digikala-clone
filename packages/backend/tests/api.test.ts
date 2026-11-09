import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import express from 'express';
import { registerRoutes } from '../src/routes.js';
import { FileStore } from '../src/store.js';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import type { AddressInfo } from 'node:net';

let base = '';
let server: ReturnType<express.Express['listen']> | undefined;
let dir = '';

beforeAll(async () => {
  dir = mkdtempSync(join(tmpdir(), 'horology-test-'));
  process.env.HOROLOGY_DATA_DIR = dir;
  const app = express();
  app.use(express.json());
  registerRoutes(app, new FileStore(dir));
  await new Promise<void>((resolve) => {
    server = app.listen(0, () => {
      const port = (server!.address() as AddressInfo).port;
      base = `http://127.0.0.1:${port}`;
      resolve();
    });
  });
});

afterAll(() => {
  server?.close();
  rmSync(dir, { recursive: true, force: true });
});

async function post(path: string, body: unknown) {
  const res = await fetch(`${base}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  return { status: res.status, json: await res.json() };
}

describe('API', () => {
  it('health', async () => {
    const res = await fetch(`${base}/api/health`);
    expect((await res.json()).ok).toBe(true);
  });
  it('gear calc', async () => {
    const { json } = await post('/api/calc/gear', { type: 'spur', moduleM: 0.001, teeth: 24, pressureAngleDeg: 20, faceWidthM: 0.002, materialId: 'brass' });
    expect(json.pitchDiameterM).toBeCloseTo(0.024, 9);
  });
  it('balance calc', async () => {
    const { json } = await post('/api/calc/balance', { diameterM: 0.02, thicknessM: 0.001, massKg: 0.0002, timingScrewMassKg: 0, timingScrewRadiusM: 0.009, hairspringStiffnessNmPerRad: 1e-6, hairspringLengthM: 0.05, materialId: 'gilt-brass', amplitudeDeg: 270 });
    expect(json.frequencyHz).toBeGreaterThan(0);
  });
  it('project CRUD', async () => {
    const { json: p } = await post('/api/projects', { name: 'API Test', watch: { type: 'wall-clock', targetPowerReserveHours: 744 } });
    expect(p.id).toBeTruthy();
    const res = await fetch(`${base}/api/projects/${p.id}`);
    expect((await res.json()).name).toBe('API Test');
  });
  it('components seeded', async () => {
    const res = await fetch(`${base}/api/components`);
    const arr = await res.json();
    expect(arr.length).toBeGreaterThanOrEqual(10);
  });
  it('escapement sim', async () => {
    const { json } = await post('/api/simulate/escapement', { params: { type: 'swiss-lever', escapeTeeth: 15, escapeDiameterM: 0.012, palletAngleDeg: 180, lockingAngleDeg: 2, dropDeg: 1, liftDeg: 3, drawDeg: 1, impulseAngleDeg: 8, balanceFrequencyHz: 2, balanceInertiaKgM2: 1e-8, hairspringStiffnessNmPerRad: 1.5e-6, amplitudeDeg: 270, escapeWheelTorqueNm: 1e-5 }, durationS: 1 });
    expect(json.beats).toBeGreaterThan(0);
  });
  it('validation suite endpoint', async () => {
    const res = await fetch(`${base}/api/validation/suite`);
    const arr = await res.json();
    expect(arr.length).toBeGreaterThan(0);
    expect(arr.filter((c: { status: string }) => c.status === 'FAIL').length).toBe(0);
  });
});
