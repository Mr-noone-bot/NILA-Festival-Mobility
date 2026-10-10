# NILA Shared API Contracts

This document formalizes the planned HTTP API contracts for NILA. It enables frontend and backend developers to work concurrently with well-defined mock and production schemas.

Base URL: `http://localhost:8000/api`

---

## 1. System Health

### `GET /api/health`
Checks whether the backend server and its submodules are healthy.

- **Request**: No parameters.
- **Response** (`200 OK`):
```json
{
  "status": "healthy",
  "service": "nila-backend",
  "version": "0.1.0",
  "environment": "foundation"
}
```

---

## 2. Festival Data Endpoints

### `GET /api/festivals`
Retrieves the list of supported Tamil Nadu temple festivals.

- **Response** (`200 OK`):
```json
[
  {
    "id": "madurai-chithirai-2026",
    "name": "Chithirai Thiruvizha",
    "city": "Madurai",
    "temple_id": "meenakshi-amman",
    "start_date": "2026-04-20",
    "end_date": "2026-05-01",
    "expected_peak_day": "2026-04-28",
    "peak_events": [
      {
        "name": "Chariot Procession (Ther)",
        "timestamp": "2026-04-28T08:00:00+05:30",
        "estimated_turnout": 500000
      }
    ]
  }
]
```

### `GET /api/festivals/{festival_id}`
Retrieves detailed metadata, zones, nearby bus stops, and routes for a specific festival.

- **Parameters**: `festival_id` (string, path parameter).
- **Response** (`200 OK`):
```json
{
  "id": "madurai-chithirai-2026",
  "name": "Chithirai Thiruvizha",
  "city": "Madurai",
  "temple": {
    "id": "meenakshi-amman",
    "name": "Meenakshi Sundareswarar Temple",
    "coordinates": { "latitude": 9.9195, "longitude": 78.1193 },
    "gates": ["East Tower", "West Tower", "North Tower", "South Tower"]
  },
  "stops": [
    { "id": "stop-periyar", "name": "Periyar Bus Stand", "capacity": 1500, "coordinates": { "lat": 9.9167, "lng": 78.1132 } },
    { "id": "stop-aarapalayam", "name": "Aarapalayam Bus Stand", "capacity": 1200, "coordinates": { "lat": 9.9326, "lng": 78.1064 } },
    { "id": "stop-mattuthavani", "name": "Mattuthavani (MIBT)", "capacity": 3000, "coordinates": { "lat": 9.9482, "lng": 78.1561 } }
  ],
  "default_fleet_size": 25
}
```

---

## 3. Crowd Prediction Engine

### `POST /api/predict`
Generates temporal crowd surge estimates based on festival schedule, event timeline, and weather.

- **Request Body**:
```json
{
  "festival_id": "madurai-chithirai-2026",
  "time_window_start": "2026-04-28T06:00:00+05:30",
  "time_window_end": "2026-04-28T18:00:00+05:30",
  "weather_condition": "extreme_heat",
  "surge_multiplier": 1.15
}
```

- **Response** (`200 OK`):
```json
{
  "festival_id": "madurai-chithirai-2026",
  "timeline": [
    {
      "timestamp": "2026-04-28T08:00:00+05:30",
      "total_crowd_estimate": 450000,
      "discharge_rate_per_hour": 15000,
      "surge_alert_level": "CRITICAL"
    }
  ],
  "peak_surge_time": "2026-04-28T10:30:00+05:30",
  "highest_demand_stops": ["stop-periyar", "stop-aarapalayam"]
}
```

---

## 4. Scenario Simulation Engine

### `POST /api/simulate`
Simulates spatial crowd distribution across gates, walking corridors, and bus stop accumulation over time.

- **Request Body**:
```json
{
  "festival_id": "madurai-chithirai-2026",
  "prediction_timeline_id": "pred-428",
  "simulation_step_minutes": 15,
  "crowd_exit_speed_kmh": 2.5
}
```

- **Response** (`200 OK`):
```json
{
  "simulation_id": "sim-2026-0428-01",
  "steps": [
    {
      "step_time": "2026-04-28T09:00:00+05:30",
      "stop_queues": {
        "stop-periyar": { "waiting_passengers": 3200, "queue_risk": "HIGH" },
        "stop-aarapalayam": { "waiting_passengers": 1400, "queue_risk": "MEDIUM" },
        "stop-mattuthavani": { "waiting_passengers": 400, "queue_risk": "LOW" }
      },
      "density_grid": [
        { "latitude": 9.919, "longitude": 78.118, "weight": 0.88 }
      ]
    }
  ]
}
```

---

## 5. Fixed-Fleet Optimization Engine

### `POST /api/optimize`
Computes optimal bus repositioning schedules under the **Fixed Fleet Invariant**. Fleet cannot expand; vehicles must be transferred between stops.

- **Request Body**:
```json
{
  "festival_id": "madurai-chithirai-2026",
  "total_fleet_size": 20,
  "current_allocation": {
    "stop-periyar": 5,
    "stop-aarapalayam": 5,
    "stop-mattuthavani": 10
  },
  "predicted_demand_profile": {
    "stop-periyar": 4200,
    "stop-aarapalayam": 1800,
    "stop-mattuthavani": 600
  },
  "time_horizon_minutes": 120
}
```

- **Response** (`200 OK`):
```json
{
  "plan_id": "opt-plan-901",
  "total_fleet_size": 20,
  "fleet_conserved": true,
  "repositioning_moves": [
    {
      "source_stop": "stop-mattuthavani",
      "destination_stop": "stop-periyar",
      "buses_to_transfer": 4,
      "departure_time": "2026-04-28T09:15:00+05:30",
      "arrival_time": "2026-04-28T09:40:00+05:30",
      "travel_time_minutes": 25,
      "source_service_loss": "Minor wait time increase at Mattuthavani (+4 min)",
      "expected_benefit": "Eliminates critical queue hazard at Periyar (-62% wait)",
      "network_effect": "+3,200 passengers cleared before 10:30 peak"
    }
  ],
  "final_allocation": {
    "stop-periyar": 9,
    "stop-aarapalayam": 5,
    "stop-mattuthavani": 6
  },
  "overall_queue_reduction_percentage": 58.4
}
```

---

## 6. Routing API Proxy

### `POST /api/routes`
Calculates live travel duration and road geometry between stops via OSRM without exposing routing secrets to the client.

- **Request Body**:
```json
{
  "origin": { "lat": 9.9482, "lng": 78.1561 },
  "destination": { "lat": 9.9167, "lng": 78.1132 },
  "congestion_factor": 1.4
}
```

- **Response** (`200 OK`):
```json
{
  "distance_meters": 6800,
  "duration_seconds": 1500,
  "duration_formatted": "25 mins",
  "geometry": {
    "type": "LineString",
    "coordinates": [
      [78.1561, 9.9482],
      [78.1350, 9.9320],
      [78.1132, 9.9167]
    ]
  }
}
```

---

## 7. Gemini AI Copilot Endpoint

### `POST /api/ai/ask`
Submits natural language operator questions regarding optimization plans, simulated scenarios, or trade-offs.

- **Request Body**:
```json
{
  "plan_id": "opt-plan-901",
  "question": "Why did we take 4 buses from Mattuthavani instead of Aarapalayam?"
}
```

- **Response** (`200 OK`):
```json
{
  "answer": "Mattuthavani currently holds 10 buses with an estimated demand of only 600 passengers, leaving excess idle buffer. Moving 4 buses from Mattuthavani incurs only a minor 4-minute wait time increase there, whereas taking buses from Aarapalayam would have triggered an acute bottleneck near the railway approach.",
  "confidence": "high",
  "trade_off_summary": {
    "source_stop": "stop-mattuthavani",
    "destination_stop": "stop-periyar",
    "service_loss": "Low risk",
    "benefit": "Immediate relief for 3,200 stranded pilgrims"
  }
}
```
