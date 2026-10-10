# NILA — AI-Powered Festival Mobility & Crowd Management System

[![Hackathon](https://img.shields.io/badge/Hackathon-SAKTHI%20HACKFEST'26-orange.svg)](https://github.com/Mr-noone-bot/NILA-Festival-Mobility)
[![Status](https://img.shields.io/badge/Status-Foundation%20Phase-blue.svg)](https://github.com/Mr-noone-bot/NILA-Festival-Mobility)
[![Python](https://img.shields.io/badge/Backend-FastAPI%20%7C%20Python%203.11-green.svg)](https://fastapi.tiangolo.com)
[![Frontend](https://img.shields.io/badge/Frontend-React%20%7C%20Vite%20%7C%20TypeScript-cyan.svg)](https://vitejs.dev)

---

## Problem

During major temple festivals in Tamil Nadu (e.g., Chithirai Thiruvizha, Karthigai Deepam, Mahamaham), tens of thousands of devotees assemble in compact sacred zones. When sacred rituals conclude, intense crowd surges simultaneously pour toward surrounding bus stops.

Public transit authorities cannot simply summon additional buses out of thin air. Transit operators face acute overcrowding, dangerous choke points at specific bus stops, and excessive wait times while idle or underutilized buses remain stalled at other terminals.

---

## Solution

**NILA** predicts post-event crowd surges and calculates time-aware, zero-sum redistribution of an **existing fixed bus fleet**.

Instead of assuming infinite transport capacity, NILA enforces the **Fixed Fleet Invariant**:
$$\sum \text{Allocated Buses} = F_{\text{total}}$$
Every single vehicle repositioning recommendation explicitly balances source stop service reduction against destination stop queue relief, calculating travel times through the congested festival road network via OSRM.

---

## Core Innovations

- **Crowd Prediction**: Models temporal crowd buildup leading up to sacred rituals and sharp post-event discharge.
- **Event-End Awareness**: Accounts for key ritual milestones (e.g., temple car arrival, flag hoisting, theerthavari) that trigger simultaneous mass exits.
- **Weather-Aware Scenarios**: Modulates pedestrian walking speeds and passenger heat exhaustion risk based on weather profiles.
- **Fixed-Fleet Optimization**: Conserves total vehicle count while computing optimal mathematical reassignments via constrained optimization.
- **Time-Aware Bus Repositioning**: Factors in realistic road transit durations ($t_{\text{departure}} + \Delta t_{\text{travel}} = t_{\text{arrival}}$) so buses arrive before the surge peaks.
- **Explicit Service Trade-Offs**: For every transfer, transparently reports source service loss vs. destination relief.
- **Map & Geospatial Visualization**: MapLibre vector maps + OpenFreeMap tiles + deck.gl heatmap layers for real-time situational awareness.
- **Gemini AI Copilot**: Natural-language explanation and operator audit layer explaining the *why* behind optimization decisions without compromising deterministic safety.

---

## Architecture

```
Tamil Nadu Festival Data
        ↓
Scenario / Input Engine
        ↓
Festival Schedule + Weather + Transport Capacity
        ↓
Crowd Prediction Engine
        ↓
Crowd Distribution Engine
        ↓
Bus Demand Engine
        ↓
Fixed-Fleet Optimization Engine
        ↓
Bus Plan + Routes + Risk
        ↓
Map Engine
        ↓
NILA Command Center
        ↓
Gemini AI Copilot
```

Detailed architectural documentation:
- [System Architecture](file:///docs/architecture/system-architecture.md)
- [Map Architecture](file:///docs/architecture/map-architecture.md)
- [API Contracts](file:///docs/api/contracts.md)
- [Team Ownership Matrix](file:///docs/integration/team-ownership.md)
- [Integration Rules](file:///docs/integration/rules.md)

---

## Team

- **Gugaan** — Project Owner / Integration Lead / Prediction + Simulation + Gemini
- **Sanjay** — Backend + Optimization + Routing
- **Chandhana** — Frontend + UI/UX + Maps
- **Madhu** — Tamil Nadu Data + Validation

---

## Technology Stack

- **Frontend**: React, Vite, TypeScript, Tailwind CSS, MapLibre GL JS, deck.gl
- **Backend**: Python 3.11+, FastAPI, Pydantic, Uvicorn
- **Optimization**: Google OR-Tools / Constrained Mixed-Integer Programming
- **Routing**: OSRM (Open Source Routing Machine) proxied via backend
- **Maps**: OpenFreeMap vector tile server + MapLibre GL JS
- **AI / Copilot**: Google Gemini SDK (Natural-language audit & reasoning layer)

---

## Development Setup

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Git

### 1. Repository Setup
```bash
git clone https://github.com/Mr-noone-bot/NILA-Festival-Mobility.git
cd NILA-Festival-Mobility
cp .env.example .env
```

### 2. Backend Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows PowerShell)
.venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run backend development server
uvicorn backend.main:app --reload --port 8000
```
Backend API will be accessible at: `http://localhost:8000`  
Interactive API Docs (Swagger UI): `http://localhost:8000/docs`  
Health check endpoint: `http://localhost:8000/api/health`

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend development interface will be live at: `http://localhost:5173`

### 4. Running Backend Tests
```bash
pytest
```

---

## Project Status

> **Current Phase**: FOUNDATION PHASE  
> The repository foundation, directory partitions, API contracts, health checks, geospatial blueprints, and invariant constraints are established. Core prediction algorithms, optimization solvers, and UI components are in active development by designated module owners.
