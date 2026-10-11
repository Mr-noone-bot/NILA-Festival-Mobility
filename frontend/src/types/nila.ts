import type {
  Festival as BackendFestival,
  FestivalDetails,
  FestivalPeakEvent,
} from '../api/types';

export * from '../api/types';

export type RiskLevel = 'LOW' | 'MEDIUM' | 'MODERATE' | 'HIGH' | 'CRITICAL';

export interface Stop {
  id: string;
  name: string;
  shortName: string;
  coordinates: [number, number]; // [lng, lat]
  capacity: number;
  currentBuses: number;
  recommendedBuses: number;
  crowd: number;
  waitMinutes: number;
  risk: RiskLevel;
}

export interface CrowdPoint {
  coordinates: [number, number]; // [lng, lat]
  weight: number;
}

export interface FestivalEvent {
  name: string;
  timestamp: string;
  estimatedTurnout: number;
}

export interface UIFestival {
  id: string;
  name: string;
  city: string;
  temple: string;
  coordinates: [number, number]; // [lng, lat]
  dateLabel: string;
  expectedAttendance: number;
  peakTime: string;
  stops?: Stop[];
  events?: FestivalEvent[];
  temple_id?: string;
  start_date?: string;
  end_date?: string;
  expected_peak_day?: string;
  peak_events?: FestivalPeakEvent[];
}

// UI Festival presentation interface
export type Festival = UIFestival;

export function toUIFestival(
  backendFest: BackendFestival,
  details?: FestivalDetails | null
): UIFestival {
  const templeName = details?.temple?.name || 'Meenakshi Sundareswarar Temple';
  const coords: [number, number] = details?.temple?.coordinates
    ? [details.temple.coordinates.longitude, details.temple.coordinates.latitude]
    : [78.1193, 9.9195];

  const firstEvent = backendFest.peak_events?.[0];

  return {
    id: backendFest.id,
    name: backendFest.name,
    city: backendFest.city,
    temple: templeName,
    coordinates: coords,
    dateLabel: backendFest.expected_peak_day || `${backendFest.start_date} to ${backendFest.end_date}`,
    expectedAttendance: firstEvent?.estimated_turnout || 500000,
    peakTime: firstEvent?.timestamp || '10:30 AM',
    temple_id: backendFest.temple_id,
    start_date: backendFest.start_date,
    end_date: backendFest.end_date,
    expected_peak_day: backendFest.expected_peak_day,
    peak_events: backendFest.peak_events,
    events: (backendFest.peak_events || []).map((pe) => ({
      name: pe.name,
      timestamp: pe.timestamp,
      estimatedTurnout: pe.estimated_turnout,
    })),
  };
}

export interface ForecastMetrics {
  peakCrowd: number;
  peakTime: string;
  waitingMinutes: number;
  overloadedStops: number;
  risk: RiskLevel;
}

export interface ForecastResponse {
  source: 'api' | 'demo' | 'not_run';
  metrics: ForecastMetrics;
  points: CrowdPoint[];
  stops: Stop[];
  timeline?: Array<{
    timestamp: string;
    total_crowd_estimate: number;
    discharge_rate_per_hour: number;
    surge_alert_level: RiskLevel;
  }>;
}

export interface BusMove {
  sourceStop: string;
  destinationStop: string;
  buses: number;
  departure: string;
  arrival: string;
  travelMinutes: number;
  waitReduction: number;
  benefit: string;
  tradeoff: string;
  networkEffect: string;
}

export interface OptimizeResponse {
  source: 'api' | 'demo' | 'not_run';
  plan_id: string;
  total_fleet_size: number;
  fleet_conserved: boolean;
  move: BusMove | null;
  overall_queue_reduction_percentage: number;
  final_allocation?: Record<string, number>;
}

export interface ScenarioConfig {
  attendance: number;
  rain: number;
  delayMinutes: number;
  busFailures: number;
}

export interface ScenarioMetrics {
  peakCrowd: number;
  peakTime: string;
  waitingMinutes: number;
  queue: number;
  risk: RiskLevel;
}

export interface ScenarioResult {
  source: 'api' | 'demo' | 'not_run';
  baseline: ScenarioMetrics;
  scenario: ScenarioMetrics;
}

export interface CopilotResponse {
  source: 'api' | 'demo';
  answer: string;
  confidence?: string;
  trade_off_summary?: {
    source_stop: string;
    destination_stop: string;
    service_loss: string;
    benefit: string;
  };
}

export interface RouteGeometryResponse {
  distance_meters?: number;
  duration_seconds?: number;
  duration_formatted?: string;
  geometry?: {
    type: 'LineString';
    coordinates: [number, number][];
  };
}
