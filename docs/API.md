# REST API

Base: `http://localhost:3001` (frontend dev server proxies `/api` → `:3001`).
All bodies/responses are JSON unless noted. Errors: `400 {error}` / `404`.

## Health & materials
- `GET /api/health` → `{ok, service, version}`
- `GET /api/materials`, `GET /api/materials/:id`

## Projects (schema v1, validated on import)
- `GET /api/projects` · `POST /api/projects {name, watch}`
- `GET /api/projects/:id` · `PUT /api/projects/:id` (bumps version)
- `POST /api/projects/import` (validates schemaVersion=1)
- `POST /api/projects/:id/duplicate` · `DELETE /api/projects/:id`
- `GET /api/projects/:id/report` → engineering report (checks, assumptions, equations)
- `GET /api/projects/:id/bom` → bill of materials + total mass

## Components
- `GET /api/components?q=&category=` · `POST /api/components`
- `GET /api/components/:id` · `PUT /api/components/:id` (recomputes mass, bumps revision)
- `POST /api/components/:id/duplicate` · `DELETE /api/components/:id`

## Calculations (`POST`, JSON in → JSON out)
- `/api/calc/gear` — involute gear diameters, undercut, warnings
- `/api/calc/gear-mesh {g1,g2,opts}` — ratio, contact ratio, Lewis/Hertz stresses, SF
- `/api/calc/geartrain {stages,inputSpeedRadps,inputTorqueNm}`
- `/api/calc/mainspring` — torque curve, energy, stress, SF (supports `measuredCurve`)
- `/api/calc/power-reserve` — feasibility verdict for target hours
- `/api/calc/balance` — frequency, vph, screw sensitivity, temp/air/friction
- `/api/calc/escapement` — geometry; `/api/simulate/escapement {params,durationS}` — event log
- `/api/calc/tourbillon` — cage kinematics, ratio error, bearing load
- `/api/calc/tourbillon-suggest {requiredRatio}` — teeth suggestion
- `/api/calc/bearing` — clearances, pressure, friction torque, deflection
- `/api/calc/energy {budget,avgPowerConsumptionW,targetHours}` · `/api/calc/energy-series`
- `/api/calc/tolerance {items,opts}` — worst-case / RSS / Monte Carlo
- `/api/simulate/dynamics {bodies,opts}` — RK4/Dopri, energy drift
- `GET /api/validation/suite` — automated validation checks

## CAD
- `GET /api/cad/solidcraft/status` — backend probe (CLI/MCP/built-in)
- `POST /api/cad/export-gear {gear,format,name}` — STL/OBJ/STEP/DXF download
  (`X-Cad-Backend` header records which backend produced it)
- `POST /api/cad/mesh {gear,format,name}`

## WebSocket `ws://localhost:3001/ws/simulate`
Send `{type:'escapement', payload:{params,durationS}}` → `{type:'escapement-result', result}`.
Send `{type:'dynamics', payload:{bodies,opts}}` → streamed `{type:'dynamics-frame', samples}` chunks then `{type:'dynamics-done', summary}`.
