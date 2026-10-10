import { apiClient } from './client';
import type { SimulationRequest, SimulationResponse } from './types';

/**
 * Simulates spatial crowd distribution across gates and stops via POST /api/simulate
 */
export async function simulateCrowd(request: SimulationRequest): Promise<SimulationResponse> {
  if (!request.festival_id) {
    throw new Error('festival_id is required for simulation request');
  }

  return apiClient<SimulationResponse>('/api/simulate', {
    method: 'POST',
    body: request,
  });
}
