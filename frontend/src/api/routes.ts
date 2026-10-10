import { apiClient } from './client';
import type { RouteRequest, RouteResponse } from './types';

/**
 * Calculates live travel duration and road geometry between stops via POST /api/routes
 */
export async function fetchRoute(request: RouteRequest): Promise<RouteResponse> {
  if (!request.origin || !request.destination) {
    throw new Error('Both origin and destination coordinates are required for route request');
  }

  return apiClient<RouteResponse>('/api/routes', {
    method: 'POST',
    body: request,
  });
}
