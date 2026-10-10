/**
 * NILA Typed API Contracts
 * Directly mirrors backend FastAPI schemas from docs/api/contracts.md
 */

// ==========================================
// 1. Health
// ==========================================
export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
}

// ==========================================
// 2. Festivals
// ==========================================
export interface FestivalPeakEvent {
  name: string;
  timestamp: string;
  estimated_turnout: number;
}

export interface Festival {
  id: string;
  name: string;
  city: string;
  temple_id: string;
  start_date: string;
  end_date: string;
  expected_peak_day: string;
  peak_events: FestivalPeakEvent[];
}

export interface TempleCoordinates {
  latitude: number;
  longitude: number;
}

export interface TempleDetails {
  id: string;
  name: string;
  coordinates: TempleCoordinates;
  gates: string[];
}

export interface BackendStopCoordinates {
  lat: number;
  lng: number;
}

export interface BackendStop {
  id: string;
  name: string;
  capacity: number;
  coordinates: BackendStopCoordinates;
}

export interface FestivalDetails {
  id: string;
  name: string;
  city: string;
  temple: TempleDetails;
  stops: BackendStop[];
  default_fleet_size: number;
}

// ==========================================
// 3. Crowd Prediction
// ==========================================
export interface PredictionRequest {
  festival_id: string;
  time_window_start: string;
  time_window_end: string;
  weather_condition: string;
  surge_multiplier: number;
}

export interface TimelineStep {
  timestamp: string;
  total_crowd_estimate: number;
  discharge_rate_per_hour: number;
  surge_alert_level: 'LOW' | 'MEDIUM' | 'MODERATE' | 'HIGH' | 'CRITICAL';
}

export interface StopForecast {
  stop_id: string;
  predicted_demand: number;
  waiting_minutes: number;
  risk_level: string;
}

export interface PredictionResponse {
  festival_id: string;
  timeline: TimelineStep[];
  peak_surge_time: string;
  highest_demand_stops: string[];
  stop_forecasts?: StopForecast[];
}

// ==========================================
// 4. Fixed-Fleet Optimization
// ==========================================
export interface OptimizationRequest {
  festival_id: string;
  total_fleet_size: number;
  current_allocation: Record<string, number>;
  predicted_demand_profile: Record<string, number>;
  time_horizon_minutes: number;
}

export interface RepositioningMove {
  source_stop: string;
  destination_stop: string;
  buses_to_transfer: number;
  departure_time: string;
  arrival_time: string;
  travel_time_minutes: number;
  source_service_loss: string;
  expected_benefit: string;
  network_effect: string;
}

export interface Tradeoff {
  source_stop: string;
  destination_stop: string;
  service_loss: string;
  benefit: string;
}

export interface OptimizationResponse {
  plan_id: string;
  total_fleet_size: number;
  fleet_conserved: boolean;
  repositioning_moves: RepositioningMove[];
  final_allocation: Record<string, number>;
  overall_queue_reduction_percentage: number;
}

// ==========================================
// 5. Scenario Simulation
// ==========================================
export interface SimulationRequest {
  festival_id: string;
  prediction_timeline_id?: string;
  simulation_step_minutes?: number;
  crowd_exit_speed_kmh?: number;
  attendance_multiplier?: number;
  rain_probability?: number;
  event_delay_minutes?: number;
  bus_failures?: number;
}

export interface StopQueueStatus {
  waiting_passengers: number;
  queue_risk: 'LOW' | 'MEDIUM' | 'MODERATE' | 'HIGH' | 'CRITICAL';
}

export interface SimulationDensityPoint {
  latitude: number;
  longitude: number;
  weight: number;
}

export interface SimulationStep {
  step_time: string;
  stop_queues: Record<string, StopQueueStatus>;
  density_grid: SimulationDensityPoint[];
}

export interface SimulationResponse {
  simulation_id: string;
  steps: SimulationStep[];
}

// ==========================================
// 6. Routing API Proxy
// ==========================================
export interface RouteRequest {
  origin: { lat: number; lng: number };
  destination: { lat: number; lng: number };
  congestion_factor?: number;
}

export interface RouteGeometry {
  type: 'LineString';
  coordinates: [number, number][]; // [lng, lat]
}

export interface RouteResponse {
  distance_meters: number;
  duration_seconds: number;
  duration_formatted: string;
  geometry: RouteGeometry;
}

// ==========================================
// 7. AI Copilot
// ==========================================
export interface AIAskRequest {
  question: string;
  plan_id?: string;
  festival_id?: string;
  scenario?: Record<string, unknown>;
}

export interface TradeOffSummary {
  source_stop: string;
  destination_stop: string;
  service_loss: string;
  benefit: string;
}

export interface AIAskResponse {
  answer: string;
  confidence?: string;
  trade_off_summary?: TradeOffSummary;
}

// ==========================================
// 8. Unified API Error & State Types
// ==========================================
export type RequestStatus = 'idle' | 'loading' | 'success' | 'empty' | 'error';

export interface ApiErrorDetail {
  loc?: (string | number)[];
  msg: string;
  type?: string;
}

export interface ApiErrorPayload {
  message: string;
  status: number;
  statusText?: string;
  details?: ApiErrorDetail[] | unknown;
  url?: string;
}
