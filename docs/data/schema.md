# NILA Data Schemas & Ownership Guide

This document defines the data foundation schema for the NILA system.

**Data Owner**: Madhu (`data/`, `docs/data/`, `tests/data/`)

---

## 1. Directory Structure

```
data/
├── festivals.json          # Festival schedules, locations, peak dates
├── temples.json            # Temple grounds, gates, coordinates, zones
├── stops.json              # Bus stops, passenger capacity, GPS coords
├── routes.json             # Road connections between stops, base durations
├── buses.json              # Fixed fleet inventory and vehicle IDs
├── crowd_profiles.json     # Surge curve profiles, arrival/departure distributions
├── weather_profiles.json   # Weather multipliers (heat, rain, humidity)
└── scenarios.json          # Pre-packaged hackathon demo simulation scenarios
```

---

## 2. File Specifications

### `festivals.json`
Array of festival objects containing unique `id`, `name`, `city`, `temple_id`, `dates`, and key `peak_events` (chariot processions, temple car pulls, theerthavari).

### `temples.json`
Detailed spatial definitions of sacred grounds:
- `id`: unique slug
- `name`: formal name
- `center`: `[latitude, longitude]`
- `gates`: array of exit points, each with coordinates and maximum foot traffic throughput (people/minute).

### `stops.json`
Transit points surrounding the festival perimeter:
- `id`: string identifier
- `name`: terminal / stop name
- `coordinates`: `[latitude, longitude]`
- `staging_capacity`: maximum number of buses that can park simultaneously
- `passenger_capacity`: holding area safe capacity

### `routes.json`
Corridors between stops:
- `origin_id`, `destination_id`
- `distance_km`
- `nominal_duration_min`
- `congestion_sensitivity` (multiplier under heavy pedestrian spillover)

### `buses.json`
Fixed vehicle inventory:
- `fleet_id`, `vehicle_id`, `capacity` (seats + standing), `current_stop_id`.
- **Note**: Total count of active buses in this file defines the fixed fleet size constraint ($F_{\text{total}}$).

### `crowd_profiles.json`
Time-series distribution curves:
- Surge curves modeling buildup before ritual events and exponential decay/rush after event conclusion.

### `weather_profiles.json`
Weather adjustment parameters:
- Walking speed degradation factors, queue heat exhaustion risks, and weather multipliers.

### `scenarios.json`
Reproducible operational scenarios used for simulation, optimization benchmarks, and presentations.
