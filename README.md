# Horology Engineering

**Parametric Mechanical Watch Design & Simulation Environment**

A professional, modular, engineering-grade platform for designing, calculating,
modelling, assembling, simulating, validating and preparing mechanical watches
and clocks for manufacturing — wristwatches, wall clocks, tourbillons, gear
trains, mainsprings, balances, hairsprings, escapements, jewels and bearings.

> **Engineering honesty:** every result is labelled *Calculated*, *Estimated*,
> *Simulated*, *Measured* or *Validated*. Untested results are never labelled
> Validated. Design targets are never presented as verified results.

## Quick start

```bash
npm install
npm run build          # build all workspaces
npm test               # run all tests (34 tests)
npm run dev            # backend on :3001 (REST /api, WS /ws/simulate)
npm run dev:frontend   # frontend on :5173 (proxies /api → :3001)
```

Open the frontend URL in your browser. The backend must be running for
calculations; the 3D viewport and UI work standalone.

## Repository layout

```
packages/
  engineering-core/   Pure TypeScript calculation engine (zero runtime deps)
    src/ gears, geartrain, mainspring, balance, escapement, tourbillon,
         bearings, energy, tolerance, dynamics, components, project,
         validation, cad, materials, units
    tests/            27 vitest tests (physical assertions)
  backend/            Express REST API + WebSocket simulation streaming
    src/ server, routes, store (JSON file store; SQLite/Postgres-ready)
    tests/            7 API tests
  frontend/           React + Vite + Three.js dark engineering UI (EN/FA, RTL)
    src/ App, api, i18n, components (Viewport3D, Charts), pages
  cad-adapter/        SolidCraft CAD adapter (CLI/MCP probe + built-in mesh fallback)
projects/
  reference-wall-clock-300mm.json   300 mm wall clock, 1-min tourbillon (verified calcs)
docs/
  ARCHITECTURE.md  ENGINEERING.md  API.md  CAD.md  INSTALL.md
  LIMITATIONS.md   EXAMPLE-REPORT.md
```

## Technology note (Rust)

The master specification recommends a Rust backend. This sandbox has **no Rust
toolchain** (only npm/pypi/github are reachable), so the runnable implementation
is TypeScript/Node.js with the same modular architecture. The engineering core
is pure, dependency-free TypeScript with a stable API surface, so a Rust port
(or WASM bridge) can mirror it module-by-module without changing the frontend
or project format. See `docs/ARCHITECTURE.md`.

## Reference project

`projects/reference-wall-clock-300mm.json` — 300 mm wall clock, Ø70 mm cage,
60 s/rev, 1 Hz balance (7200 vph), 31-day (744 h) target. All numbers in the
file are outputs of the calculation engine (run `node scripts/verify-reference.mjs`
to reproduce). Current verified result: **816 h reserve, feasible** at the
stated consumption — see `docs/EXAMPLE-REPORT.md`.

## CAD

SolidCraft integration via `packages/cad-adapter` (CLI/MCP probe, no
undocumented APIs assumed). Without SolidCraft installed, the built-in exporter
produces true-involute STL/OBJ/STEP-faceted/DXF. See `docs/CAD.md`.

## Licence

MIT.
