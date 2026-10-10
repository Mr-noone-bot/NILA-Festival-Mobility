# NILA Map & Geospatial Architecture

## 1. Geospatial Stack Architecture

The NILA mapping subsystem is structured to decouple geospatial visualization from backend compute and secret management.

```
┌────────────────────────────────────────────────────────┐
│                   FRONTEND CLIENT                      │
│                                                        │
│   MapLibre GL JS (Vector Base Map Canvas)             │
│        ▲                                               │
│        │ Vector Tiles / Styles                         │
│   OpenFreeMap (https://tiles.openfreemap.org/...)      │
│                                                        │
│   deck.gl HeatmapLayer / ArcLayer (Crowd & Fleet Overlays)
└───────────────────────────┬────────────────────────────┘
                            │ /api/routes, /api/predict
                            ▼
┌────────────────────────────────────────────────────────┐
│                   BACKEND SERVICE                      │
│                                                        │
│   FastAPI Proxy & Route Cache Layer                    │
│   (Injects credentials, coordinates, avoids browser leaks)
└───────────────────────────┬────────────────────────────┘
                            │ Transit Matrix / Path Requests
                            ▼
┌────────────────────────────────────────────────────────┐
│                 ROUTING INFRASTRUCTURE                 │
│                                                        │
│   OSRM (Open Source Routing Machine)                   │
└────────────────────────────────────────────────────────┘
```

---

## 2. Component Specifications

### 2.1 Base Map Rendering: MapLibre GL JS
- **Library**: `maplibre-gl` (v4.x)
- **Role**: High-performance WebGL vector map rendering without vendor lock-in or billable map quotas.
- **Base Style**: **OpenFreeMap** (`https://tiles.openfreemap.org/styles/liberty` or configurable via `VITE_MAP_STYLE_URL`).

### 2.2 Crowd & Fleet Visualization: deck.gl
- **Library**: `@deck.gl/core`, `@deck.gl/layers`
- **Layers**:
  - `HeatmapLayer`: Continuous spatial density representation of simulated/predicted crowd concentrations around temples and transit hubs.
  - `ScatterplotLayer` / `IconLayer`: Live bus stop capacities and bus staging points.
  - `ArcLayer` / `PathLayer`: Dynamic bus repositioning corridors indicating source $\rightarrow$ destination vehicle transfers.

### 2.3 Routing Engine: OSRM via Backend
- **Engine**: Open Source Routing Machine (OSRM).
- **Architecture Rule**:
  - The frontend client **must NOT directly query external routing APIs** or expose routing credentials/tokens.
  - The frontend queries `POST /api/routes` on the NILA backend.
  - The backend communicates with OSRM (`OSRM_BACKEND_URL`), computes matrices, applies travel-time adjustments, and returns GeoJSON coordinates and travel durations to the client.

---

## 3. Configuration & Security Rules

1. **No Hardcoded Keys or URLs**:
   - `VITE_MAP_STYLE_URL` controls the map style.
   - `VITE_API_BASE_URL` controls backend communication.
   - `OSRM_BACKEND_URL` is kept on the backend.
2. **Deterministic Fallback**:
   - If external OSRM routing is unreachable, backend falls back to Euclidean or pre-calculated haversine travel time approximations with festival congestion multipliers.
