# NILA System Architecture

## 1. Overview & Core Mission

**NILA** is an AI-powered festival mobility and crowd management system built for large-scale Tamil Nadu temple festivals.

During major festival events (e.g., Chithirai Thiruvizha in Madurai, Karthigai Deepam in Tiruvannamalai, Mahamaham in Kumbakonam), tens of thousands to millions of devotees congregate within a concentrated sacred perimeter. When religious events conclude (e.g., chariot procession, theerthavari, deepam lighting), massive crowd surges simultaneously discharge towards public transit pick-up points.

### The Core Problem Solved by NILA:
> *"When will festival crowd build, where will it concentrate, and how should the existing fixed bus fleet be repositioned at the right time to reduce overcrowding?"*

---

## 2. The Invariant Principle: Fixed Fleet Constraint

The system operates under a strict physical reality:
**No buses can magically appear.** The public transit authority possesses a finite, pre-assigned pool of vehicles.

$$\sum_{s \in \text{Stops}} \text{Buses}(s, t) = F_{\text{total}} \quad \forall t$$

If $F_{\text{total}} = 20$, then the sum of all allocated, in-transit, and staged buses must equal exactly $20$ before, during, and after optimization.

### Zero-Sum Service Trade-Off Model
Every bus dispatched to alleviate a surge at Stop $B$ must be drawn from another Stop $A$. Therefore, every single repositioning decision must explicitly calculate and expose:

1. **Source Stop**: Stop where service is reduced.
2. **Destination Stop**: Stop receiving reinforcement.
3. **Number of Buses**: Quantity of vehicles reassigned.
4. **Departure Time ($t_{\text{dep}}$)**: Exactly when buses depart origin.
5. **Arrival Time ($t_{\text{arr}}$)**: When buses reach destination given traffic/distance.
6. **Travel Time ($\Delta t$)**: Travel duration through the festival road network (computed via OSRM).
7. **Source Service Loss**: Increase in wait times / queue risk at origin stop.
8. **Expected Benefit**: Reduction in overcrowding / surge relief at destination stop.
9. **Network Effect**: Net impact on passenger throughput across the entire network.

---

## 3. End-to-End System Pipeline

```
Tamil Nadu Festival Data (Temples, Dates, Zones, Historical Turnout)
        ↓
Scenario / Input Engine (Active festival, time-of-day, weather conditions)
        ↓
Festival Schedule + Weather + Transport Capacity
        ↓
Crowd Prediction Engine (Temporal surge buildup & post-event discharge)
        ↓
Crowd Distribution Engine (Spatial allocation to gates, corridors & stops)
        ↓
Bus Demand Engine (Demand-vs-capacity gap analysis per stop)
        ↓
Fixed-Fleet Optimization Engine (Constrained fleet redistribution MILP/OR-Tools)
        ↓
Bus Plan + Routes + Risk (Time-aware dispatch schedules & trade-off metrics)
        ↓
Map Engine (MapLibre + deck.gl crowd heatmaps & transit corridors)
        ↓
NILA Command Center (Real-time operator interface & situational metrics)
        ↓
Gemini AI Copilot (Natural language plan explanation, risk audit & Q&A)
```

---

## 4. Role of Gemini AI Copilot vs. Deterministic Engines

### Strict Architectural Boundary:
- **Gemini is NOT the mathematical decision engine.**
- Gemini does **NOT** invent numbers, solve optimization matrices, or calculate bus schedules.
- **Gemini is an Explanation, Orchestration, and Operator Query Layer.**

```
┌────────────────────────────────────────────────────────┐
│               DETERMINISTIC CORE ENGINES               │
│  - Crowd Prediction Engine (Statistical / ML models)   │
│  - Fixed-Fleet Optimization Engine (OR-Tools / Scipy)  │
│  - Route Duration Engine (OSRM API)                    │
└───────────────────────────┬────────────────────────────┘
                            │ Structured Mathematical Plan
                            │ & Trade-off Vectors
                            ▼
┌────────────────────────────────────────────────────────┐
│                   GEMINI AI COPILOT                    │
│  - Explains WHY bus movements were recommended         │
│  - Highlights operational trade-offs and risks         │
│  - Responds to natural-language operator inquiries     │
│  - Translates technical metrics into situational briefs│
└────────────────────────────────────────────────────────┘
```

> **Reliability Guarantee**: If the Gemini API is unreachable, offline, or rate-limited, the entire deterministic prediction, optimization, and map routing pipeline **continues to function with 100% mathematical integrity**.
