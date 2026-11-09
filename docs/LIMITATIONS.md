# Known limitations & next steps

This is a working engineering foundation, not a finished production tool.
Honest limitations:

1. **Rust** — the spec recommends Rust; this build is TypeScript/Node.js
   (no Rust toolchain in the sandbox). The core API is stable for a Rust/WASM port.
2. **Storage** — JSON file store. SQLite/PostgreSQL adapters are interface-ready
   but not implemented. No multi-user auth yet.
3. **CAD** — built-in STEP is faceted, not native B-rep. Full SolidCraft
   feature-tree editing, exploded views, assembly sequences and section-view
   drawings are roadmap items. 3MF needs zipping the manifest + STL.
4. **Drawings** — DXF 2D profiles only; dimensioned/section/assembly drawings
   and inspection plans are not yet generated.
5. **Escapement** — Swiss lever is fully event-simulated; English/detent/
   deadbeat/anchor use parameterised geometry (Estimated). Pallet contact
   is modelled via energy/impulse, not full 2D collision geometry.
6. **Mainspring** — linear spiral model unless a measured curve is supplied.
   No FEA, no fatigue-life prediction beyond safety factors.
7. **Gear stresses** — Lewis/Hertz approximations; verify with FEA for production.
8. **Materials** — typical values; verify against supplier datasheets.
9. **Tourbillon** — kinematics + bearing loads calculated; structural deflection
   and dynamic balance are simplified (unbalance moment only).
10. **Reference project** — 816 h reserve is a *Calculated* result at the stated
    1.86 µW consumption and 80% transmission efficiency. Real friction,
    temperature and manufacturing variation will change it. Prototype and measure.

## Next development steps (priority order)
1. SQLite store + auth (multi-user).
2. SolidCraft native parametric export (B-rep STEP) once CLI/MCP is available.
3. 2D pallet/escape-wheel collision geometry for full escapement validation.
4. Drawing generator (dimensioned views, BOM on drawing).
5. FEA hooks (stress/deflection) for cage, bridges and springs.
6. Rust/WASM port of the engineering core.
