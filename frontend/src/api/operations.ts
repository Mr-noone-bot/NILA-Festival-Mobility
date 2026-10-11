import { apiClient } from './client';

export type OccupancyBand = 'EMPTY' | 'SEATS_FREE' | 'STANDING' | 'CROWDED';
export type BusStatus = 'AVAILABLE' | 'IN_SERVICE' | 'RETURNING' | 'UNAVAILABLE';
export type ConfidenceLevel = 'HIGH' | 'LOW' | 'VERIFY_REQUIRED';
export type DecisionPriority = 'CRITICAL' | 'HIGH' | 'MODERATE';
export type DecisionStatus = 'PENDING' | 'APPROVED' | 'REJECTED';
export type OrderStatus = 'DISPATCH_PENDING' | 'ACKNOWLEDGED' | 'EN_ROUTE' | 'COMPLETED' | 'CANNOT_COMPLY';

export interface BusTelemetryItem {
  bus_id: string;
  route: string;
  current_stop: string;
  capacity: number;
  current_load: number;
  occupancy_band: OccupancyBand;
  status: BusStatus;
  free_at: string;
  release_point: string;
  confidence: ConfidenceLevel;
  source: string;
  candidate_for_repositioning: boolean;
  last_update: string;
}

export interface FleetSummaryResponse {
  total_fleet: number;
  available: number;
  in_service: number;
  returning: number;
  unavailable: number;
  provenance: string;
  buses: BusTelemetryItem[];
}

export interface DecisionItem {
  id: string;
  priority: DecisionPriority;
  problem: string;
  action: string;
  bus_ids: string[];
  source_stop: string;
  destination_stop: string;
  departure_time: string;
  arrival_time: string;
  travel_time_minutes: number;
  benefit: string;
  tradeoff: string;
  network_effect: string;
  confidence: string;
  status: DecisionStatus;
  order_id?: string;
  created_at: string;
}

export interface OrderDispatchItem {
  id: string;
  decision_id: string;
  bus_id: string;
  source_stop: string;
  destination_stop: string;
  departure_time: string;
  arrival_time: string;
  priority: string;
  status: OrderStatus;
  cannot_comply_reason?: string;
  alternative_bus_id?: string;
  created_at: string;
}

export interface CrowdReportResponse {
  id: string;
  stop_id: string;
  level: string;
  notes?: string;
  timestamp: string;
  status: string;
}

export interface HandoverResponse {
  timestamp: string;
  network_risk: string;
  peak_window: string;
  overloaded_stops: string[];
  approved_moves_count: number;
  pending_decisions_count: number;
  active_fleet_summary: {
    total: number;
    available: number;
    in_service: number;
    returning: number;
    unavailable: number;
  };
  outstanding_issues: string[];
  next_review_time: string;
  provenance: string;
}

/**
 * Fetch live fleet telemetry ledger
 */
export async function getFleetLedger(): Promise<FleetSummaryResponse> {
  return apiClient<FleetSummaryResponse>('/api/operations/fleet');
}

/**
 * Fetch individual vehicle telemetry details
 */
export async function getBusDetails(busId: string): Promise<BusTelemetryItem> {
  return apiClient<BusTelemetryItem>(`/api/operations/fleet/${encodeURIComponent(busId)}`);
}

/**
 * Update bus occupancy band (Crew 1-tap reporter)
 */
export async function updateBusOccupancy(
  busId: string,
  occupancyBand: OccupancyBand,
  currentLoad?: number
): Promise<BusTelemetryItem> {
  return apiClient<BusTelemetryItem>(`/api/operations/fleet/${encodeURIComponent(busId)}/occupancy`, {
    method: 'POST',
    body: {
      occupancy_band: occupancyBand,
      current_load: currentLoad,
    },
  });
}

/**
 * Fetch prioritized Decision Queue
 */
export async function getDecisions(): Promise<DecisionItem[]> {
  return apiClient<DecisionItem[]>('/api/operations/decisions');
}

/**
 * Approve operational decision (transitions to APPROVED and generates Order)
 */
export async function approveDecision(decisionId: string): Promise<OrderDispatchItem> {
  return apiClient<OrderDispatchItem>(`/api/operations/decisions/${encodeURIComponent(decisionId)}/approve`, {
    method: 'POST',
  });
}

/**
 * Reject operational decision
 */
export async function rejectDecision(decisionId: string): Promise<DecisionItem> {
  return apiClient<DecisionItem>(`/api/operations/decisions/${encodeURIComponent(decisionId)}/reject`, {
    method: 'POST',
  });
}

/**
 * Fetch dispatch orders for Depot and Crew interfaces
 */
export async function getOrders(): Promise<OrderDispatchItem[]> {
  return apiClient<OrderDispatchItem[]>('/api/operations/orders');
}

/**
 * Acknowledge dispatch order (Depot or Crew)
 */
export async function acknowledgeOrder(orderId: string): Promise<OrderDispatchItem> {
  return apiClient<OrderDispatchItem>(`/api/operations/orders/${encodeURIComponent(orderId)}/acknowledge`, {
    method: 'POST',
  });
}

/**
 * Report Cannot Comply with alternative recomputation
 */
export async function cannotComplyOrder(orderId: string, reason: string): Promise<OrderDispatchItem> {
  return apiClient<OrderDispatchItem>(`/api/operations/orders/${encodeURIComponent(orderId)}/cannot-comply`, {
    method: 'POST',
    body: { reason },
  });
}

/**
 * Field Marshal 1-tap crowd report
 */
export async function reportStopCrowd(
  stopId: string,
  level: 'LIGHT' | 'MODERATE' | 'HEAVY' | 'UNSAFE',
  notes?: string
): Promise<CrowdReportResponse> {
  return apiClient<CrowdReportResponse>(`/api/operations/stops/${encodeURIComponent(stopId)}/crowd-report`, {
    method: 'POST',
    body: {
      stop_id: stopId,
      level,
      notes,
    },
  });
}

/**
 * Generate grounded shift handover brief
 */
export async function generateHandoverBrief(): Promise<HandoverResponse> {
  return apiClient<HandoverResponse>('/api/operations/ai/handover', {
    method: 'POST',
  });
}
