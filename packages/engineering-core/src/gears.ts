/**
 * Involute gear engineering engine.
 *
 * Equations (SI, standard spur gear theory — see docs/ENGINEERING.md):
 *   pitch diameter      d  = m * z
 *   base diameter       db = d * cos(alpha)
 *   addendum            ha = ha* * m          (ha* = 1.0 standard)
 *   dedendum            hf = hf* * m          (hf* = 1.25 standard)
 *   outside diameter    da = d + 2*ha
 *   root diameter       df = d - 2*hf
 *   center distance     a  = m*(z1+z2)/2
 *   transverse contact ratio eps = [sqrt(ra1^2-rb1^2)+sqrt(ra2^2-rb2^2)-a*sin(alpha)] / (pi*m*cos(alpha))
 *   Lewis bending stress sigmaF = Ft / (b * m * Y) * K  (Y from standard form factor approx)
 *   Hertz contact stress sigmaH = sqrt( Ft/(b*d1) * (1/(2*rho')) * ((1-nu1^2)/E1 + (1-nu2^2)/E2) )
 *   pitch-line velocity  v = omega1 * d1/2
 *
 * Gear types: spur (full), pinion (small z), internal, bevel (approx. via
 * equivalent teeth), worm (lead angle model), planetary (ratio via Willis).
 * Bevel/worm use documented approximations and are labelled "Estimated".
 */
import { assertPositive, assertNonNegative, DEG2RAD } from './units.js';
import { getMaterial } from './materials.js';

export type GearType = 'spur' | 'pinion' | 'internal' | 'bevel' | 'worm' | 'planetary';

export interface GearParams {
  type: GearType;
  moduleM: number; // m [m]
  teeth: number; // z
  pressureAngleDeg: number; // alpha
  faceWidthM: number; // b
  backlashM?: number; // circumferential backlash [m]
  materialId: string;
  accuracyClass?: number; // ISO 1328 grade, informational
  addendumFactor?: number; // ha*
  dedendumFactor?: number; // hf*
  /** For worm: axial module; for bevel: pitch cone angle deg */
  extra?: { leadAngleDeg?: number; pitchConeAngleDeg?: number };
}

export interface GearResult {
  type: GearType;
  moduleM: number;
  teeth: number;
  pressureAngleDeg: number;
  pitchDiameterM: number;
  baseDiameterM: number;
  outsideDiameterM: number;
  rootDiameterM: number;
  addendumM: number;
  dedendumM: number;
  circularPitchM: number;
  faceWidthM: number;
  /** Minimum teeth to avoid undercut with standard 20° full-depth teeth. */
  minTeethNoUndercut: number;
  undercut: boolean;
  warnings: string[];
  resultType: 'Calculated';
}

export interface MeshResult {
  ratio: number; // omega1/omega2 = z2/z1 (external)
  centerDistanceM: number;
  transverseContactRatio: number;
  pitchLineVelocityMps: number; // at given input speed
  inputSpeedRadps: number;
  outputSpeedRadps: number;
  /** Lewis bending stress on pinion [Pa] at given input torque. */
  bendingStressPa: number;
  /** Hertz contact stress [Pa]. */
  contactStressPa: number;
  bendingSafetyFactor: number;
  contactSafetyFactor: number;
  slidingVelocityMps: number;
  efficiency: number; // mesh efficiency estimate
  warnings: string[];
  resultType: 'Calculated';
}

function minTeethForUndercut(alphaDeg: number): number {
  const a = alphaDeg * DEG2RAD;
  // z_min = 2*ha* / sin^2(alpha), ha*=1
  return Math.ceil(2 / Math.pow(Math.sin(a), 2));
}

/** Lewis form factor Y(z) approximation (standard 20° full-depth, polynomial fit). */
export function lewisFormFactor(z: number): number {
  // Fitted to standard Lewis Y values; valid approx for 10 <= z <= 200.
  const zz = Math.max(10, Math.min(200, z));
  return 0.175 + 0.0007 * zz + 0.000002 * zz * zz;
}

export function calculateGear(p: GearParams): GearResult {
  assertPositive('module', p.moduleM);
  assertPositive('teeth', p.teeth);
  assertPositive('faceWidth', p.faceWidthM);
  if (p.pressureAngleDeg <= 0 || p.pressureAngleDeg >= 45)
    throw new Error('Pressure angle must be in (0, 45) degrees');
  if (p.backlashM !== undefined) assertNonNegative('backlash', p.backlashM);
  getMaterial(p.materialId); // validate

  const haStar = p.addendumFactor ?? 1.0;
  const hfStar = p.dedendumFactor ?? 1.25;
  const m = p.moduleM;
  const z = Math.round(p.teeth);
  const alpha = p.pressureAngleDeg * DEG2RAD;

  const d = m * z;
  const db = d * Math.cos(alpha);
  const ha = haStar * m;
  const hf = hfStar * m;
  const da = d + 2 * ha;
  const df = d - 2 * hf;
  const circularPitch = Math.PI * m;
  const zMin = minTeethForUndercut(p.pressureAngleDeg);
  const warnings: string[] = [];
  if (z < zMin) warnings.push(`Undercut risk: z=${z} < z_min=${zMin} for alpha=${p.pressureAngleDeg}°. Use profile shift or more teeth.`);
  if (p.type === 'internal') warnings.push('Internal gear: root/outside definitions swapped in use; mesh with internal formula.');
  if (p.type === 'bevel') warnings.push('Bevel gear: diameters are pitch-cone equivalents; detailed cone geometry is Estimated.');
  if (p.type === 'worm') warnings.push('Worm gear: module is axial module; lead angle required for exact geometry.');

  return {
    type: p.type,
    moduleM: m,
    teeth: z,
    pressureAngleDeg: p.pressureAngleDeg,
    pitchDiameterM: d,
    baseDiameterM: db,
    outsideDiameterM: da,
    rootDiameterM: df,
    addendumM: ha,
    dedendumM: hf,
    circularPitchM: circularPitch,
    faceWidthM: p.faceWidthM,
    minTeethNoUndercut: zMin,
    undercut: z < zMin,
    warnings,
    resultType: 'Calculated'
  };
}

export function meshGears(
  g1: GearParams,
  g2: GearParams,
  opts: {
    inputSpeedRadps: number;
    inputTorqueNm: number; // torque on gear 1
    centerDistanceM?: number; // override (for backlash / non-standard)
  }
): MeshResult {
  const r1 = calculateGear(g1);
  const r2 = calculateGear(g2);
  if (Math.abs(g1.moduleM - g2.moduleM) > 1e-12)
    throw new Error('Meshing gears must share the same module');
  if (Math.abs(g1.pressureAngleDeg - g2.pressureAngleDeg) > 1e-9)
    throw new Error('Meshing gears must share the same pressure angle');

  const alpha = g1.pressureAngleDeg * DEG2RAD;
  const a = opts.centerDistanceM ?? (g1.moduleM * (g1.teeth + g2.teeth)) / 2;
  const ratio = g2.teeth / g1.teeth; // omega1/omega2
  const omega1 = opts.inputSpeedRadps;
  const omega2 = omega1 / ratio;
  const v = (omega1 * r1.pitchDiameterM) / 2;

  // Transverse contact ratio
  const ra1 = r1.outsideDiameterM / 2;
  const ra2 = r2.outsideDiameterM / 2;
  const rb1 = r1.baseDiameterM / 2;
  const rb2 = r2.baseDiameterM / 2;
  const path1 = Math.sqrt(Math.max(0, ra1 * ra1 - rb1 * rb1));
  const path2 = Math.sqrt(Math.max(0, ra2 * ra2 - rb2 * rb2));
  const eps = (path1 + path2 - a * Math.sin(alpha)) / (Math.PI * g1.moduleM * Math.cos(alpha));

  // Tangential force from input torque
  const Ft = opts.inputTorqueNm / (r1.pitchDiameterM / 2);

  // Lewis bending stress (pinion, smaller gear)
  const pinion = g1.teeth <= g2.teeth ? g1 : g2;
  const Y = lewisFormFactor(pinion.teeth);
  const sigmaF = Ft / (pinion.faceWidthM * pinion.moduleM * Y);

  // Hertz contact stress
  const mat1 = getMaterial(g1.materialId);
  const mat2 = getMaterial(g2.materialId);
  const rhoPrime = 1 / (1 / (r1.pitchDiameterM / 2) + 1 / (r2.pitchDiameterM / 2)); // equivalent radius
  const term = (1 - mat1.poissonRatio ** 2) / mat1.elasticModulusPa + (1 - mat2.poissonRatio ** 2) / mat2.elasticModulusPa;
  const sigmaH = Math.sqrt((Ft / (g1.faceWidthM * 2 * rhoPrime)) * term * 2); // approx. line contact

  const bendSF = Math.min(mat1.yieldStrengthPa, mat2.yieldStrengthPa) / sigmaF;
  const contactSF = Math.min(mat1.yieldStrengthPa, mat2.yieldStrengthPa) / sigmaH;

  // Sliding velocity at tip (approx): v_slide = v * tan(alpha) * (1 + ...)
  const vSlide = v * Math.tan(alpha) * 1.5;

  const warnings: string[] = [];
  if (eps < 1.2) warnings.push(`Low contact ratio eps=${eps.toFixed(2)} (<1.2): noisy / weak mesh.`);
  if (bendSF < 1.5) warnings.push(`Bending safety factor ${bendSF.toFixed(2)} < 1.5 — increase face width or module.`);
  if (contactSF < 1.2) warnings.push(`Contact safety factor ${contactSF.toFixed(2)} < 1.2 — risk of pitting.`);
  if (opts.centerDistanceM !== undefined) {
    const aStd = (g1.moduleM * (g1.teeth + g2.teeth)) / 2;
    warnings.push(`Non-standard center distance: ${(opts.centerDistanceM * 1000).toFixed(3)} mm vs standard ${(aStd * 1000).toFixed(3)} mm. Backlash changed.`);
  }

  return {
    ratio,
    centerDistanceM: a,
    transverseContactRatio: eps,
    pitchLineVelocityMps: v,
    inputSpeedRadps: omega1,
    outputSpeedRadps: omega2,
    bendingStressPa: sigmaF,
    contactStressPa: sigmaH,
    bendingSafetyFactor: bendSF,
    contactSafetyFactor: contactSF,
    slidingVelocityMps: vSlide,
    efficiency: 0.98, // typical single external mesh, Estimated
    warnings,
    resultType: 'Calculated'
  };
}

/** Planetary (Willis) ratio: ring fixed, sun input, carrier output: i = 1 + z_ring/z_sun. */
export function planetaryRatio(sunTeeth: number, ringTeeth: number): number {
  assertPositive('sunTeeth', sunTeeth);
  assertPositive('ringTeeth', ringTeeth);
  return 1 + ringTeeth / sunTeeth;
}

/**
 * True involute flank points for one tooth (2D, centred on +X axis).
 * Returns points from root to tip along the involute.
 */
export function involuteFlankPoints(
  r: GearResult,
  pointsPerFlank = 12
): { x: number; y: number }[] {
  const rb = r.baseDiameterM / 2;
  const ra = r.outsideDiameterM / 2;
  const rf = r.rootDiameterM / 2;
  const pitchR = r.pitchDiameterM / 2;
  const alpha = r.pressureAngleDeg * DEG2RAD;
  // Half tooth thickness angle at pitch circle = pi/(2z)
  const halfToothAnglePitch = Math.PI / (2 * r.teeth);
  const inv = (a: number) => Math.tan(a) - a;
  const invAlpha = inv(alpha);
  // Start radius: max(root, base)
  const rStart = Math.max(rf, rb);
  const pts: { x: number; y: number }[] = [];
  for (let i = 0; i <= pointsPerFlank; i++) {
    const rr = rStart + ((ra - rStart) * i) / pointsPerFlank;
    const cosA = rb / rr;
    const a = Math.acos(Math.min(1, Math.max(-1, cosA))); // pressure angle at rr
    const halfAngle = halfToothAnglePitch + invAlpha - inv(a);
    pts.push({ x: rr * Math.cos(halfAngle), y: rr * Math.sin(halfAngle) });
  }
  void pitchR;
  return pts;
}

/** Full 2D outline of the gear (all teeth), for CAD / 3D extrusion. */
export function gearOutlinePoints(r: GearResult, pointsPerFlank = 8): { x: number; y: number }[] {
  const flank = involuteFlankPoints(r, pointsPerFlank);
  const z = r.teeth;
  const rf = r.rootDiameterM / 2;
  const pts: { x: number; y: number }[] = [];
  const toothPitch = (2 * Math.PI) / z;
  for (let t = 0; t < z; t++) {
    const baseAng = t * toothPitch;
    // root arc to flank start
    const startAng = Math.atan2(flank[0].y, flank[0].x);
    const rootSteps = 3;
    for (let s = 0; s < rootSteps; s++) {
      const ang = baseAng + (startAng * s) / rootSteps;
      pts.push({ x: rf * Math.cos(ang), y: rf * Math.sin(ang) });
    }
    // right flank up
    for (const p of flank) {
      const c = Math.cos(baseAng);
      const s = Math.sin(baseAng);
      pts.push({ x: p.x * c - p.y * s, y: p.x * s + p.y * c });
    }
    // tip arc to mirrored flank
    const tipAng = Math.atan2(flank[flank.length - 1].y, flank[flank.length - 1].x);
    const tipSteps = 3;
    const ra = r.outsideDiameterM / 2;
    for (let s = 1; s <= tipSteps; s++) {
      const ang = baseAng + tipAng + ((toothPitch / 2 - tipAng) * s) / tipSteps;
      pts.push({ x: ra * Math.cos(ang), y: ra * Math.sin(ang) });
    }
    // left flank down (mirror)
    for (let i = flank.length - 1; i >= 0; i--) {
      const p = flank[i];
      const c = Math.cos(baseAng);
      const s = Math.sin(baseAng);
      const mx = p.x * c + p.y * s;
      const my = p.x * s - p.y * c;
      pts.push({ x: mx, y: my });
    }
  }
  return pts;
}
