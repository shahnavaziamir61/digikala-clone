# Installation & development

## Prerequisites
- Node.js ≥ 20 (tested on 22), npm ≥ 10.
- No Rust toolchain required (see README technology note).

## Install & build
```bash
npm install
npm run build        # tsc (core, adapter, backend) + vite (frontend)
npm test             # 27 core + 7 backend tests
```

## Run
```bash
npm run dev            # backend :3001
npm run dev:frontend   # frontend :5173 (separate terminal)
# or production: npm run build && (cd packages/backend && npm start) + serve packages/frontend/dist
```

## Verify reference project
```bash
node scripts/verify-reference.mjs
# Recomputes the 300 mm / 70 mm / 60 s / 31-day design and compares with projects/*.json
```

## Data directory
Backend persists to `./data/` (override `HOROLOGY_DATA_DIR`). Delete it to reset.

## Troubleshooting
- Frontend shows "backend offline": start `npm run dev` first.
- Port busy: `PORT=3002 npm run dev` and update `packages/frontend/vite.config.ts` proxy.
