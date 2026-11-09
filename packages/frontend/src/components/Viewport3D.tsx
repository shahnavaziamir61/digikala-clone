import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { calculateGear, gearOutlinePoints } from '@horology/engineering-core';

export interface ViewportProps {
  playing: boolean;
  speed: number; // time scale
  balanceFreqHz: number;
  cagePeriodS: number;
  escapeTeeth: number;
  onStats?: (s: { cageAngleDeg: number; balanceAngleDeg: number; escapeAngleDeg: number }) => void;
}

function gearGeometry(moduleM: number, teeth: number, thicknessM: number): THREE.BufferGeometry {
  const g = calculateGear({ type: 'spur', moduleM, teeth, pressureAngleDeg: 20, faceWidthM: thicknessM, materialId: 'brass' });
  const outline = gearOutlinePoints(g, 5);
  const shape = new THREE.Shape();
  outline.forEach((p, i) => {
    const x = p.x * 1000; // mm for scene scale
    const y = p.y * 1000;
    if (i === 0) shape.moveTo(x, y);
    else shape.lineTo(x, y);
  });
  const geo = new THREE.ExtrudeGeometry(shape, { depth: thicknessM * 1000, bevelEnabled: false });
  geo.rotateX(-Math.PI / 2);
  return geo;
}

function ringGeometry(rOut: number, rIn: number, thickness: number): THREE.BufferGeometry {
  const shape = new THREE.Shape();
  shape.absarc(0, 0, rOut, 0, Math.PI * 2, false);
  const hole = new THREE.Path();
  hole.absarc(0, 0, rIn, 0, Math.PI * 2, true);
  shape.holes.push(hole);
  const geo = new THREE.ExtrudeGeometry(shape, { depth: thickness, bevelEnabled: false });
  geo.rotateX(-Math.PI / 2);
  return geo;
}

export default function Viewport3D({ playing, speed, balanceFreqHz, cagePeriodS, escapeTeeth, onStats }: ViewportProps) {
  const mountRef = useRef<HTMLDivElement>(null);
  const stateRef = useRef({ playing, speed, balanceFreqHz, cagePeriodS, escapeTeeth });
  stateRef.current = { playing, speed, balanceFreqHz, cagePeriodS, escapeTeeth };
  const statsRef = useRef(onStats);
  statsRef.current = onStats;

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0b1220);
    const camera = new THREE.PerspectiveCamera(45, mount.clientWidth / mount.clientHeight, 0.1, 2000);
    camera.position.set(90, 110, 90);
    camera.lookAt(0, 0, 0);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(mount.clientWidth, mount.clientHeight);
    mount.appendChild(renderer.domElement);

    scene.add(new THREE.AmbientLight(0xffffff, 0.7));
    const dir = new THREE.DirectionalLight(0xffffff, 1.2);
    dir.position.set(60, 120, 40);
    scene.add(dir);
    const grid = new THREE.GridHelper(300, 30, 0x334155, 0x1e293b);
    scene.add(grid);

    // Main plate (Ø300 mm scaled scene: use 150 radius units)
    const plate = new THREE.Mesh(new THREE.CylinderGeometry(150, 150, 4, 64), new THREE.MeshStandardMaterial({ color: 0x8a6d3b, metalness: 0.6, roughness: 0.4 }));
    plate.position.y = -4;
    scene.add(plate);

    // Barrel (Ø120)
    const barrel = new THREE.Mesh(new THREE.CylinderGeometry(60, 60, 10, 48), new THREE.MeshStandardMaterial({ color: 0xb08d57, metalness: 0.7, roughness: 0.35 }));
    barrel.position.set(-70, 6, -40);
    scene.add(barrel);

    // Gear train: barrel gear -> pinion -> wheel (true involute extrusions)
    const g1 = new THREE.Mesh(gearGeometry(0.004, 48, 0.004), new THREE.MeshStandardMaterial({ color: 0xd4af37, metalness: 0.7, roughness: 0.3 }));
    g1.position.set(-70, 12, -40);
    scene.add(g1);
    const g2 = new THREE.Mesh(gearGeometry(0.004, 12, 0.004), new THREE.MeshStandardMaterial({ color: 0x9fb3c8, metalness: 0.8, roughness: 0.25 }));
    g2.position.set(-20, 12, -40);
    scene.add(g2);
    const g3 = new THREE.Mesh(gearGeometry(0.004, 36, 0.004), new THREE.MeshStandardMaterial({ color: 0xd4af37, metalness: 0.7, roughness: 0.3 }));
    g3.position.set(30, 12, -40);
    scene.add(g3);

    // Tourbillon cage (Ø70) at centre
    const cageGroup = new THREE.Group();
    const cageRing = new THREE.Mesh(ringGeometry(35, 30, 3), new THREE.MeshStandardMaterial({ color: 0x7dd3fc, metalness: 0.8, roughness: 0.2 }));
    cageGroup.add(cageRing);
    const bridge = new THREE.Mesh(new THREE.BoxGeometry(66, 2, 8), new THREE.MeshStandardMaterial({ color: 0x7dd3fc, metalness: 0.8, roughness: 0.2 }));
    bridge.position.y = 6;
    cageGroup.add(bridge);
    const bridge2 = new THREE.Mesh(new THREE.BoxGeometry(8, 2, 66), new THREE.MeshStandardMaterial({ color: 0x7dd3fc, metalness: 0.8, roughness: 0.2 }));
    bridge2.position.y = 6;
    cageGroup.add(bridge2);
    // Balance wheel inside cage
    const balance = new THREE.Group();
    const rim = new THREE.Mesh(ringGeometry(11, 9.5, 1.5), new THREE.MeshStandardMaterial({ color: 0xfbbf24, metalness: 0.8, roughness: 0.25 }));
    balance.add(rim);
    for (let i = 0; i < 4; i++) {
      const screw = new THREE.Mesh(new THREE.SphereGeometry(1.2, 12, 12), new THREE.MeshStandardMaterial({ color: 0xef4444, metalness: 0.6 }));
      const a = (i / 4) * Math.PI * 2;
      screw.position.set(Math.cos(a) * 10.5, 1, Math.sin(a) * 10.5);
      balance.add(screw);
    }
    balance.position.y = 8;
    cageGroup.add(balance);
    // Escape wheel inside cage
    const escape = new THREE.Mesh(gearGeometry(0.0015, 15, 0.0015), new THREE.MeshStandardMaterial({ color: 0xe2e8f0, metalness: 0.9, roughness: 0.15 }));
    escape.position.set(18, 5, 0);
    cageGroup.add(escape);
    // Fixed wheel (stationary, under cage)
    const fixed = new THREE.Mesh(gearGeometry(0.002, 60, 0.002), new THREE.MeshStandardMaterial({ color: 0x64748b, metalness: 0.7, roughness: 0.4 }));
    fixed.position.y = 2;
    scene.add(fixed);
    scene.add(cageGroup);

    // Hairspring spiral above balance
    const spiralPts: THREE.Vector3[] = [];
    for (let i = 0; i <= 200; i++) {
      const t = i / 200;
      const r = 1 + t * 7;
      const a = t * Math.PI * 2 * 6;
      spiralPts.push(new THREE.Vector3(Math.cos(a) * r, 10.5, Math.sin(a) * r));
    }
    const spiral = new THREE.Line(new THREE.BufferGeometry().setFromPoints(spiralPts), new THREE.LineBasicMaterial({ color: 0x3b82f6 }));
    cageGroup.add(spiral);

    let raf = 0;
    let simT = 0;
    let last = performance.now();
    const animate = () => {
      raf = requestAnimationFrame(animate);
      const now = performance.now();
      const dtReal = (now - last) / 1000;
      last = now;
      const s = stateRef.current;
      if (s.playing) simT += dtReal * s.speed;
      const cageAngle = (simT / s.cagePeriodS) * Math.PI * 2;
      cageGroup.rotation.y = cageAngle;
      const balAngle = Math.sin(simT * 2 * Math.PI * s.balanceFreqHz) * (270 * Math.PI / 180);
      balance.rotation.y = balAngle;
      // Escape wheel: steps one pitch per beat (2 beats per period)
      const beats = Math.floor(simT * 2 * s.balanceFreqHz);
      escape.rotation.y = beats * ((2 * Math.PI) / s.escapeTeeth);
      g1.rotation.y = simT * 0.2;
      g2.rotation.y = -simT * 0.2 * (48 / 12);
      g3.rotation.y = simT * 0.2 * (48 / 12) * (12 / 36);
      statsRef.current?.({ cageAngleDeg: (cageAngle * 180) / Math.PI % 360, balanceAngleDeg: (balAngle * 180) / Math.PI, escapeAngleDeg: (escape.rotation.y * 180) / Math.PI % 360 });
      renderer.render(scene, camera);
    };
    animate();

    const onResize = () => {
      camera.aspect = mount.clientWidth / mount.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(mount.clientWidth, mount.clientHeight);
    };
    window.addEventListener('resize', onResize);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener('resize', onResize);
      renderer.dispose();
      mount.removeChild(renderer.domElement);
    };
  }, []);

  return <div ref={mountRef} className="viewport" aria-label="3D viewport" />;
}
