import { describe, it, expect } from 'vitest';
import {
  calculateGear, meshGears, planetaryRatio, gearOutlinePoints,
  calculateGearTrain, calculateMainspring, powerReserveCheck,
  calculateBalance, requiredStiffness, requiredInertia,
  calculateEscapementGeometry, simulateEscapement,
  calculateTourbillon, suggestTourbillonTeeth,
  calculateBearing, analyzeEnergy, integrateTorqueEnergy,
  analyzeTolerance, fitCheck, seededRng,
  simulateDynamics, rk4Step,
  seedLibrary, createComponent, recomputeMass,
  createProject, validateProject, parseProject, duplicateProject,
  runValidationSuite, generateReport,
  gearMesh, meshToSTL, meshToOBJ, meshToSTEP
} from '../src/index.js';

describe('gears', () => {
  it('computes standard diameters', () => {
    const g = calculateGear({ type: 'spur', moduleM: 0.001, teeth: 24, pressureAngleDeg: 20, faceWidthM: 0.002, materialId: 'brass' });
    expect(g.pitchDiameterM).toBeCloseTo(0.024, 9);
    expect(g.outsideDiameterM).toBeCloseTo(0.026, 9);
    expect(g.rootDiameterM).toBeCloseTo(0.0215, 9);
    expect(g.baseDiameterM).toBeCloseTo(0.024 * Math.cos(20 * Math.PI / 180), 9);
  });
  it('mesh ratio and stresses', () => {
    const m = meshGears(
      { type: 'pinion', moduleM: 0.001, teeth: 8, pressureAngleDeg: 20, faceWidthM: 0.002, materialId: 'steel-hardened' },
      { type: 'spur', moduleM: 0.001, teeth: 24, pressureAngleDeg: 20, faceWidthM: 0.002, materialId: 'brass' },
      { inputSpeedRadps: 10, inputTorqueNm: 0.001 }
    );
    expect(m.ratio).toBeCloseTo(3, 9);
    expect(m.outputSpeedRadps).toBeCloseTo(10 / 3, 9);
    expect(m.centerDistanceM).toBeCloseTo(0.016, 9);
    expect(m.bendingStressPa).toBeGreaterThan(0);
    expect(m.contactStressPa).toBeGreaterThan(0);
  });
  it('planetary ratio (Willis)', () => {
    expect(planetaryRatio(12, 48)).toBeCloseTo(5, 9);
  });
  it('gear outline has teeth', () => {
    const g = calculateGear({ type: 'spur', moduleM: 0.001, teeth: 12, pressureAngleDeg: 20, faceWidthM: 0.002, materialId: 'brass' });
    const pts = gearOutlinePoints(g, 4);
    expect(pts.length).toBeGreaterThan(12 * 10);
  });
  it('rejects mismatched modules', () => {
    expect(() =>
      meshGears(
        { type: 'spur', moduleM: 0.001, teeth: 12, pressureAngleDeg: 20, faceWidthM: 0.002, materialId: 'brass' },
        { type: 'spur', moduleM: 0.002, teeth: 12, pressureAngleDeg: 20, faceWidthM: 0.002, materialId: 'brass' },
        { inputSpeedRadps: 1, inputTorqueNm: 0.001 }
      )
    ).toThrow();
  });
});

describe('geartrain', () => {
  it('two-stage ratio multiplies', () => {
    const r = calculateGearTrain(
      [
        { driver: { type: 'pinion', moduleM: 0.001, teeth: 8, pressureAngleDeg: 20, faceWidthM: 0.002, materialId: 'steel-hardened' }, driven: { type: 'spur', moduleM: 0.001, teeth: 24, pressureAngleDeg: 20, faceWidthM: 0.002, materialId: 'brass' } },
        { driver: { type: 'pinion', moduleM: 0.001, teeth: 10, pressureAngleDeg: 20, faceWidthM: 0.002, materialId: 'steel-hardened' }, driven: { type: 'spur', moduleM: 0.001, teeth: 40, pressureAngleDeg: 20, faceWidthM: 0.002, materialId: 'brass' } }
      ],
      10, 0.001
    );
    expect(r.overallRatio).toBeCloseTo(12, 6);
    expect(r.outputTorqueNm).toBeGreaterThan(0.001);
  });
});

describe('mainspring', () => {
  it('energy positive and SF sane', () => {
    const ms = calculateMainspring({ thicknessM: 0.0002, widthM: 0.001, lengthM: 0.5, innerRadiusM: 0.01, outerRadiusM: 0.05, barrelDiameterM: 0.11, arborDiameterM: 0.015, activeTurns: 6, materialId: 'blued-steel' });
    expect(ms.storedEnergyJ).toBeGreaterThan(0);
    expect(ms.safetyFactor).toBeGreaterThan(0);
    expect(ms.torqueCurve.length).toBeGreaterThan(10);
  });
  it('power reserve verdict honest', () => {
    const chk = powerReserveCheck({ storedEnergyJ: 1, avgPowerConsumptionW: 1e-5, transmissionEfficiency: 0.8, targetHours: 744 });
    // 1 J * 0.8 / 1e-5 W = 80000 s = 22.2 h < 744 h → infeasible
    expect(chk.feasible).toBe(false);
    expect(chk.achievableHours).toBeCloseTo(22.2, 0);
  });
  it('measured curve integration', () => {
    // Constant 0.01 N·m over full working range (6 turns = 37.7 rad) → E = 0.377 J
    const ms = calculateMainspring({ thicknessM: 0.0002, widthM: 0.001, lengthM: 0.5, innerRadiusM: 0.01, outerRadiusM: 0.05, barrelDiameterM: 0.11, arborDiameterM: 0.015, activeTurns: 6, materialId: 'blued-steel', measuredCurve: [[0, 0.01], [37.7, 0.01]], measured: true });
    expect(ms.resultType).toBe('Measured');
    expect(ms.storedEnergyJ).toBeCloseTo(0.01 * 6 * 2 * Math.PI, 3);
  });
});

describe('balance', () => {
  it('oscillator formula round-trip', () => {
    const I = 1e-8;
    const f = 2;
    const kappa = requiredStiffness(I, f);
    expect(requiredInertia(kappa, f)).toBeCloseTo(I, 12);
    const b = calculateBalance({ diameterM: 0.02, thicknessM: 0.001, massKg: 0.0002, timingScrewMassKg: 0.00005, timingScrewRadiusM: 0.009, hairspringStiffnessNmPerRad: kappa, hairspringLengthM: 0.05, materialId: 'gilt-brass', amplitudeDeg: 270 });
    expect(b.frequencyHz).toBeGreaterThan(0);
    expect(b.beatRateVph).toBeCloseTo(2 * b.frequencyHz * 3600, 6);
    expect(b.periodS).toBeCloseTo(1 / b.frequencyHz, 9);
  });
});

describe('escapement', () => {
  it('geometry pitch', () => {
    const g = calculateEscapementGeometry({ type: 'swiss-lever', escapeTeeth: 15, escapeDiameterM: 0.012, palletAngleDeg: 180, lockingAngleDeg: 2, dropDeg: 1, liftDeg: 3, drawDeg: 1, impulseAngleDeg: 8, balanceFrequencyHz: 2, balanceInertiaKgM2: 1e-8, hairspringStiffnessNmPerRad: 1e-6, amplitudeDeg: 270, escapeWheelTorqueNm: 1e-5 });
    expect(g.toothPitchDeg).toBeCloseTo(24, 9);
  });
  it('event simulation produces beats', () => {
    const sim = simulateEscapement({ type: 'swiss-lever', escapeTeeth: 15, escapeDiameterM: 0.012, palletAngleDeg: 180, lockingAngleDeg: 2, dropDeg: 1, liftDeg: 3, drawDeg: 1, impulseAngleDeg: 8, balanceFrequencyHz: 2, balanceInertiaKgM2: 1e-8, hairspringStiffnessNmPerRad: 1.5e-6, amplitudeDeg: 270, escapeWheelTorqueNm: 1e-5 }, 2);
    expect(sim.beats).toBeGreaterThan(0);
    expect(sim.resultType).toBe('Simulated');
    expect(sim.events.some((e) => e.type === 'IMPULSE_START')).toBe(true);
  });
});

describe('tourbillon', () => {
  it('60s cage kinematics', () => {
    const t = calculateTourbillon({ cageDiameterM: 0.07, cageHeightM: 0.012, cageMassKg: 0.005, cageInertiaKgM2: 1e-6, cagePeriodS: 60, balanceDiameterM: 0.02, balanceFrequencyHz: 2, escapeTeeth: 15, fixedWheelTeeth: 80, pinionTeeth: 8, shaftDiameterM: 0.0005, bearingInnerDiameterM: 0.0005, radialClearanceM: 0.00001, axialClearanceM: 0.00005, escapeWheelTorqueNm: 1e-5 });
    expect(t.cageAngularVelocityRadps).toBeCloseTo((2 * Math.PI) / 60, 9);
    expect(t.beatRateVph).toBeCloseTo(14400, 6);
  });
  it('suggests teeth near ratio', () => {
    const s = suggestTourbillonTeeth(10.5);
    expect(s.errorPct).toBeLessThan(2);
  });
});

describe('bearings / energy / tolerance', () => {
  it('bearing clearance', () => {
    const b = calculateBearing({ type: 'hole-jewel', innerDiameterM: 0.0005, outerDiameterM: 0.0015, thicknessM: 0.0003, pivotDiameterM: 0.00048, holeDiameterM: 0.0005, radialLoadN: 0.01, axialLoadN: 0.001, shaftLengthM: 0.005, materialId: 'ruby' });
    expect(b.radialClearanceM).toBeCloseTo(0.00001, 9);
  });
  it('energy integral', () => {
    expect(integrateTorqueEnergy([[0, 2], [1, 2], [2, 2]])).toBeCloseTo(4, 9);
    const e = analyzeEnergy({ storedEnergyJ: 10, gearFrictionPct: 10, bearingFrictionPct: 5, escapementLossPct: 20, balanceLossPct: 5, cageLossPct: 5, transmissionEfficiency: 0.8 }, 1e-5, 100);
    expect(e.usableJ).toBeCloseTo(8, 9);
  });
  it('tolerance RSS < worst case', () => {
    const t = analyzeTolerance([
      { name: 'a', nominalM: 0.01, plusTolM: 0.0001, minusTolM: 0.0001 },
      { name: 'b', nominalM: 0.005, plusTolM: 0.0001, minusTolM: 0.0001 }
    ], { samples: 2000, seed: 7 });
    expect(t.rssToleranceM).toBeLessThan(t.worstCasePlusM);
    expect(t.monteCarloStdM).toBeGreaterThan(0);
  });
  it('fit check interference', () => {
    const f = fitCheck({ nominalM: 0.001, plusTolM: 0.00001, minusTolM: 0.00001 }, { nominalM: 0.001, plusTolM: 0.00001, minusTolM: 0.00001 });
    expect(f.interference).toBe(true);
  });
  it('seeded rng reproducible', () => {
    const a = seededRng(42)();
    const b = seededRng(42)();
    expect(a).toBe(b);
  });
});

describe('dynamics', () => {
  it('RK4 integrates constant acceleration', () => {
    const r = rk4Step(0, 0, 0.1, () => ({ dX: 0, dV: 1 }));
    expect(r.v).toBeCloseTo(0.1, 9);
  });
  it('spring oscillator conserves energy approx', () => {
    const sim = simulateDynamics(
      [{ id: 'b', inertiaKgM2: 1, angleRad: 1, angularVelocityRadps: 0, torqueNm: 0, spring: { stiffness: 1, restAngleRad: 0 } }],
      { mode: 'rigid-body', durationS: 6.28, dtS: 0.001 }
    );
    expect(sim.stable).toBe(true);
    expect(Math.abs(sim.energyDriftPct)).toBeLessThan(2);
  });
  it('kinematic mode warns', () => {
    const sim = simulateDynamics([{ id: 'b', inertiaKgM2: 1, angleRad: 0, angularVelocityRadps: 1, torqueNm: 0 }], { mode: 'kinematic', durationS: 1, dtS: 0.01 });
    expect(sim.warnings.join(' ')).toMatch(/KINEMATIC/);
  });
});

describe('components / project / validation / cad', () => {
  it('library CRUD + duplicate + search', () => {
    const lib = seedLibrary();
    expect(lib.list().length).toBeGreaterThanOrEqual(10);
    const found = lib.search('gear');
    expect(found.length).toBeGreaterThan(0);
    const dup = lib.duplicate(found[0].id);
    expect(dup.id).not.toBe(found[0].id);
    const upd = lib.update(dup.id, { manufacturingNotes: 'updated' });
    expect(upd.revision).toBe(2);
  });
  it('recompute mass for cylinder', () => {
    const c = recomputeMass(createComponent({ name: 'disc', category: 'plate', materialId: 'brass', dimensions: { diameterM: 0.01, thicknessM: 0.001 } }));
    expect(c.massKg).toBeGreaterThan(0);
  });
  it('project validation', () => {
    const p = createProject({ name: 'Test', watch: { type: 'wall-clock', targetPowerReserveHours: 744 } });
    expect(validateProject(p).ok).toBe(true);
    expect(validateProject({ ...p, schemaVersion: 99 }).ok).toBe(false);
    const parsed = parseProject(JSON.stringify(p));
    expect(parsed.name).toBe('Test');
    const dup = duplicateProject(p);
    expect(dup.id).not.toBe(p.id);
  });
  it('validation suite passes', () => {
    const checks = runValidationSuite();
    expect(checks.filter((c) => c.status === 'FAIL').length).toBe(0);
    const report = generateReport('test');
    expect(report.summary.pass).toBeGreaterThan(0);
    expect(report.equations.length).toBeGreaterThan(0);
  });
  it('cad exports', () => {
    const g = calculateGear({ type: 'spur', moduleM: 0.001, teeth: 12, pressureAngleDeg: 20, faceWidthM: 0.002, materialId: 'brass' });
    const mesh = gearMesh(g, 'test-gear');
    expect(mesh.faces.length).toBeGreaterThan(0);
    expect(meshToSTL(mesh).length).toBeGreaterThan(84);
    expect(meshToOBJ(mesh)).toContain('o test-gear');
    expect(meshToSTEP(mesh)).toContain('AP214IS');
  });
});
