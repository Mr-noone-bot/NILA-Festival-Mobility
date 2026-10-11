# NILA Data Source Register

Last Updated: 2026-10-11  
Data Owner: MADHU (Tamil Nadu Data & Validation)

---

## 1. Official Temple Sources

- **Meenakshi Sundaraswarar Temple, Madurai**  
  HR&CE Temple ID: `31962` / `031962`  
  Portal URL: https://maduraimeenakshi.hrce.tn.gov.in/hrcehome/index_temple.php?tid=031962  
  Coordinates Verification: OpenStreetMap Relation 3124508 ([OSM Link](https://www.openstreetmap.org/relation/3124508))

- **Dhandayuthapaniswamy Temple, Palani**  
  HR&CE Temple ID: `32203`  
  Portal URL: https://palanimurugan.hrce.tn.gov.in/hrcehome/index_temple.php?tid=32203  
  Coordinates Verification: OpenStreetMap Node 245648719 ([OSM Link](https://www.openstreetmap.org/node/245648719))

- **Arunachaleswarar Temple, Tiruvannamalai**  
  HR&CE Temple ID: `20343`  
  Portal URL: https://annamalaiyar.hrce.tn.gov.in/hrcehome/index_temple.php?action=contact_us&tid=20343  
  Coordinates Verification: OpenStreetMap Relation 3124509 ([OSM Link](https://www.openstreetmap.org/relation/3124509))

---

## 2. Official Festival Sources

- **Tamil Nadu HR&CE Festival Calendar**:  
  https://hrce.tn.gov.in/hrcehome/hrce-festival-calendar.php
- **Madurai District Administration (Festivals & Events)**:  
  https://madurai.nic.in/festivals-and-events/
- **Tiruvannamalai District Administration (Karthigai Festival)**:  
  https://tiruvannamalai.nic.in/karthigai-festival/

*Verification Rule*: Any festival date not explicitly verified against official portal publication is retained as `null` with a `PARTIALLY_VERIFIED` status tag. No unannounced dates are fabricated.

---

## 3. Transport Stops and Route Corridors

- **OpenStreetMap Export & Search API**:  
  https://www.openstreetmap.org/search  
  *Attribution*: "© OpenStreetMap contributors" (ODbL license: https://www.openstreetmap.org/copyright)
- **OSRM (Open Source Routing Machine)**:  
  https://router.project-osrm.org / https://map.project-osrm.org/  
  Used to determine road travel distances (`distance_km`) and baseline transit durations (`nominal_duration_min`).

---

## 4. Provenance Classification

- **OFFICIAL**: Government, district, or HR&CE temple published data.
- **OPERATIONAL_ESTIMATE / DERIVED**: Calculated spatial coordinates, OSRM distances, and transit operating capacities.
- **SIMULATION**: Synthetic modeling assumptions for crowd surges, weather factors, and fleet redistribution scenarios.
