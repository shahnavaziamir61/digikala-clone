# Architecture

## Modules (spec §3 → implementation)

| Spec module | Implementation |
|---|---|
| 1 Project Manager | `engineering-core/project.ts` + backend `/api/projects` |
| 2 Parametric CAD Workspace | frontend CAD page + Three.js viewport + cad-adapter |
| 3 Component Library | `engineering-core/components.ts` + `/api/components` |
| 4 Gear Generator | `engineering-core/gears.ts` (true involute) |
| 5 Gear Train Calculator | `engineering-core/geartrain.ts` |
| 6 Mainspring Engineering | `engineering-core/mainspring.ts` |
| 7 Barrel Engineering | mainspring module (barrel dims) + components |
| 8 Balance Wheel Engineering | `engineering-core/balance.ts` |
| 9 Hairspring Engineering | balance module (κ, length, material) |
| 10 Escapement Engineering | `engineering-core/escapement.ts` (hybrid event sim) |
| 11 Tourbillon Engineering | `engineering-core/tourbillon.ts` |
| 12 Jewels and Bearings | `engineering-core/bearings.ts` |
| 13 Kinematic Simulation | `dynamics.ts` mode `kinematic` (labelled, not validated) |
| 14 Dynamic Simulation | `dynamics.ts` RK4 / Dormand-Prince |
| 15 Energy Analysis | `engineering-core/energy.ts` |
| 16 Timing/Accuracy Analysis | balance module (rate, temp, isochronism) |
| 17 Contact/Friction Analysis | dynamics contact mode + bearings friction |
| 18 Tolerance Analysis | `engineering-core/tolerance.ts` (WC/RSS/MC) |
| 19 Material Database | `engineering-core/materials.ts` (10 materials) |
| 20 Manufacturing Preparation | backend BOM + CAD export endpoints |
| 21 Drawing Generator | DXF 2D profiles (roadmap: full drawings) |
| 22 BOM Generator | `GET /api/projects/:id/bom` |
| 23 Design Validation | `engineering-core/validation.ts` + `/api/validation/suite` |
| 24 Project Documentation | `docs/` + generated engineering reports |

## Data flow

```
React UI ──REST /api──▶ Express backend ──▶ engineering-core (pure TS)
         ◀──JSON───────   (FileStore)            ▲
Three.js viewport ◀── gearOutlinePoints (true involute) ──┘
WebSocket /ws/simulate ──▶ escapement/dynamics streaming
CAD export ──▶ cad-adapter ──▶ SolidCraft CLI/MCP (if present) else built-in mesh
```

## Storage

`FileStore` (JSON files, atomic writes) is the default. The `Store` interface
in `backend/src/store.ts` is storage-agnostic: implement SQLite
(`node:sqlite`, built into Node 22+) or PostgreSQL by replacing `FileStore`
— routes do not change. Multi-user deployment: run the backend behind auth
and swap the store; the REST API is stateless.

## Simulation modes (spec §10)

1. **Kinematic** — prescribed motion; explicitly labelled NOT validated.
2. **Rigid-body** — Newton-Euler, RK4 / adaptive Dormand-Prince 5(4), energy tracking.
3. **Contact & friction** — rigid-body + penalty contact + Coulomb friction.
4. **Escapement** — specialised hybrid event-driven (RK4 between LOCK/IMPULSE/DROP events).

## Rust roadmap

The core is pure TS with no runtime dependencies and a versioned JSON project
format. A Rust workspace can implement the same modules behind the same REST
schema; the frontend and project files remain compatible. No SolidCraft source
is modified; the adapter only probes supported CLI/MCP interfaces.
