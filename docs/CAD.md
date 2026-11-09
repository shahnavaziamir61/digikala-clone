# CAD integration — SolidCraft adapter

SolidCraft: https://github.com/tangency-labs/solidcraft · Docs: https://docs.solidcraft.io/
(SolidCraft is a parametric 3D CAD application in Rust with desktop, web and MCP automation.)

## How the adapter works (`packages/cad-adapter`)

1. **Probe** — checks for a `solidcraft` CLI on PATH (`solidcraft --version`)
   and for an MCP endpoint (`SOLIDCRAFT_MCP_URL` + `/health`).
2. **Transport only** — the adapter never feeds back into horology calculations.
   Geometry (true involute outlines from `engineering-core`) is handed to the
   CAD engine; the parametric feature record is preserved in manifests.
3. **No undocumented APIs** — only the probed CLI/MCP interfaces are used.
   If neither is present, the built-in mesh exporter is used and the response
   header `X-Cad-Backend: builtin-mesh` records it.

## Enabling SolidCraft

```bash
# Install SolidCraft per https://docs.solidcraft.io/ and put it on PATH, then:
export SOLIDCRAFT_BIN=/path/to/solidcraft
# …or run its MCP server and set:
export SOLIDCRAFT_MCP_URL=http://localhost:PORT
curl http://localhost:3001/api/cad/solidcraft/status
```

## Formats

| Format | Built-in | Via SolidCraft |
|---|---|---|
| STL | ✅ true involute mesh | ✅ |
| OBJ | ✅ | ✅ |
| STEP | ⚠️ AP214 **faceted** B-rep (labelled) | native B-rep (use SolidCraft directly) |
| DXF | ✅ 2D profile | ✅ |
| 3MF | manifest + STL payload (zip to complete) | ✅ |

## Parametric operations (spec §4)

Component `features` record sketch/extrude/revolve/sweep/loft/fillet/chamfer/
thread/pattern/mirror/boolean operations as data. The built-in exporter
realises extrude/revolve/sweep/loft for gears, rings and spirals; full
feature-tree editing in SolidCraft is the roadmap (see LIMITATIONS.md).
