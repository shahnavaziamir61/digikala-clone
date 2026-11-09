/**
 * CAD geometry generation & export (built-in mesh exporter).
 * Involute gear outlines are extruded to triangle meshes.
 * Formats: STL (binary), OBJ, STEP (AP214 faceted B-rep — labelled as such),
 * DXF (2D profile). 3MF is a ZIP container; we emit a manifest + STL payload
 * and label it accordingly (see cad-adapter for SolidCraft path).
 */
import { GearResult, gearOutlinePoints } from './gears.js';

export interface Mesh {
  vertices: [number, number, number][];
  faces: [number, number, number][];
  name: string;
}

/** Extrude a 2D outline (z=0..thickness) into a closed triangle mesh. */
export function extrudeOutline(outline: { x: number; y: number }[], thicknessM: number, name: string): Mesh {
  const n = outline.length;
  const vertices: [number, number, number][] = [];
  for (const p of outline) vertices.push([p.x, p.y, 0]);
  for (const p of outline) vertices.push([p.x, p.y, thicknessM]);
  const faces: [number, number, number][] = [];
  // Bottom fan (reverse winding)
  for (let i = 1; i < n - 1; i++) faces.push([0, i + 1, i]);
  // Top fan
  for (let i = 1; i < n - 1; i++) faces.push([n, n + i, n + i + 1]);
  // Sides
  for (let i = 0; i < n; i++) {
    const j = (i + 1) % n;
    faces.push([i, j, n + j]);
    faces.push([i, n + j, n + i]);
  }
  return { vertices, faces, name };
}

export function gearMesh(gear: GearResult, name: string): Mesh {
  const outline = gearOutlinePoints(gear, 6);
  return extrudeOutline(outline, gear.faceWidthM, name);
}

export function meshToSTL(mesh: Mesh): Buffer {
  const n = mesh.faces.length;
  const buf = Buffer.alloc(84 + n * 50);
  buf.write('Horology Engineering STL', 0, 'ascii');
  buf.writeUInt32LE(n, 80);
  let off = 84;
  const normal = (a: [number, number, number], b: [number, number, number], c: [number, number, number]): [number, number, number] => {
    const u = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
    const v = [c[0] - a[0], c[1] - a[1], c[2] - a[2]];
    const nx = u[1] * v[2] - u[2] * v[1];
    const ny = u[2] * v[0] - u[0] * v[2];
    const nz = u[0] * v[1] - u[1] * v[0];
    const len = Math.hypot(nx, ny, nz) || 1;
    return [nx / len, ny / len, nz / len];
  };
  for (const f of mesh.faces) {
    const a = mesh.vertices[f[0]];
    const b = mesh.vertices[f[1]];
    const c = mesh.vertices[f[2]];
    const nrm = normal(a, b, c);
    buf.writeFloatLE(nrm[0], off); buf.writeFloatLE(nrm[1], off + 4); buf.writeFloatLE(nrm[2], off + 8);
    buf.writeFloatLE(a[0], off + 12); buf.writeFloatLE(a[1], off + 16); buf.writeFloatLE(a[2], off + 20);
    buf.writeFloatLE(b[0], off + 24); buf.writeFloatLE(b[1], off + 28); buf.writeFloatLE(b[2], off + 32);
    buf.writeFloatLE(c[0], off + 36); buf.writeFloatLE(c[1], off + 40); buf.writeFloatLE(c[2], off + 44);
    buf.writeUInt16LE(0, off + 48);
    off += 50;
  }
  return buf;
}

export function meshToOBJ(mesh: Mesh): string {
  const lines = [`# ${mesh.name} — Horology Engineering`, `o ${mesh.name}`];
  for (const v of mesh.vertices) lines.push(`v ${v[0]} ${v[1]} ${v[2]}`);
  for (const f of mesh.faces) lines.push(`f ${f[0] + 1} ${f[1] + 1} ${f[2] + 1}`);
  return lines.join('\n') + '\n';
}

/**
 * STEP AP214 faceted B-rep export.
 * NOTE: This is a faceted representation, not a native B-rep solid.
 * For production STEP, use the SolidCraft adapter (cad-adapter package).
 */
export function meshToSTEP(mesh: Mesh): string {
  const lines: string[] = [];
  lines.push("ISO-10303-21;");
  lines.push("HEADER;");
  lines.push("FILE_DESCRIPTION(('Faceted B-rep exported by Horology Engineering'),'2;1');");
  lines.push("FILE_NAME('horology-export.step','2026-01-01T00:00:00',('Horology Engineering'),(''), '','','');");
  lines.push("FILE_SCHEMA(('AP214IS'));");
  lines.push("ENDSEC;");
  lines.push("DATA;");
  let id = 1;
  const cartIds: number[] = [];
  for (const v of mesh.vertices) {
    lines.push(`#${id}=CARTESIAN_POINT('',(${v[0].toExponential(6)},${v[1].toExponential(6)},${v[2].toExponential(6)}));`);
    cartIds.push(id);
    id++;
  }
  const faceIds: number[] = [];
  for (const f of mesh.faces) {
    lines.push(`#${id}=FACETED_BREP_FACE_SURFACE('',(#${cartIds[f[0]]},#${cartIds[f[1]]},#${cartIds[f[2]]}),$);`);
    faceIds.push(id);
    id++;
  }
  lines.push(`#${id}=CLOSED_SHELL('',(${faceIds.map((f) => `#${f}`).join(',')}));`);
  lines.push('ENDSEC;');
  lines.push('END-ISO-10303-21;');
  return lines.join('\n') + '\n';
}

/** 2D DXF profile of a gear outline. */
export function outlineToDXF(outline: { x: number; y: number }[], name: string): string {
  const lines = ['0', 'SECTION', '2', 'ENTITIES'];
  for (let i = 0; i < outline.length; i++) {
    const a = outline[i];
    const b = outline[(i + 1) % outline.length];
    lines.push('0', 'LINE', '8', name, '10', String(a.x), '20', String(a.y), '11', String(b.x), '21', String(b.y));
  }
  lines.push('0', 'ENDSEC', '0', 'EOF');
  return lines.join('\n') + '\n';
}
