# NILA Data Dictionary

This document describes the data files used by the NILA Festival Mobility and Crowd Management System.

## Dataset files

| File | Purpose | Current status |
|---|---|---|
| `data/festivals.json` | Festival schedules, ritual milestones, and attendance estimates | Populated with verified records for Madurai, Palani, and Tiruvannamalai |
| `data/temples.json` | Temple registry, spatial center coordinates, and cardinal gopuram gates | Populated with 3 official HR&CE temples and verified OSM coordinates/gates |
| `data/stops.json` | Bus stops, terminals, and pickup points | Populated with verified coordinates from OSM for 7 transit hubs |
| `data/routes.json` | Route corridors and ordered stop connections | Populated with 5 verified corridors and OSRM travel durations |
| `data/buses.json` | Fixed bus fleet inventory | Enforces Fixed Fleet Invariant ($F_{\text{total}} = 20$); 100% conserved |
| `data/crowd_profiles.json` | Crowd surge and event-end discharge profiles | 5 simulation profiles with time-of-day and decay multipliers |
| `data/weather_profiles.json` | Weather condition and physical impact factors | 4 simulation profiles with walking speed and delay multipliers |
| `data/scenarios.json` | Operational benchmark scenarios | 7 simulation input scenarios (normal, attendance surges, rain, delay, failure, combined) |

## Common fields and rules

- Each dataset uses JSON format and stores its records in a top-level `records` array.
- Stable, unique IDs are used throughout (`temple_id`, `festival_id`, `stop_id`, `route_id`, `bus_id`, `profile_id`, `scenario_id`).
- Dates follow ISO 8601 (`YYYY-MM-DD`). Unknown dates are explicitly stored as `null`.
- Latitude and longitude are verified numbers within the Tamil Nadu bounding box ($8.0^\circ\text{N} - 13.5^\circ\text{N}, 76.2^\circ\text{E} - 80.4^\circ\text{E}$).
- Distances are expressed in kilometres (`distance_km`) and meters (`distance_m`); durations in minutes (`nominal_duration_min`) and seconds (`duration_s`).
- Every record includes a `data_type` provenance label.

## Provenance labels

- `OFFICIAL`: Directly supported by an official government, temple, or district portal.
- `OPERATIONAL_ESTIMATE` / `DERIVED`: Calculated or transformed from cited source data (e.g., OpenStreetMap geometries, OSRM routing).
- `SIMULATION`: Synthetic data used for development, testing, or demonstration.

Never present simulation values as official records, real-time measurements, or verified predictions.
