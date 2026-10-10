import { apiClient } from './client';
import type { OptimizationRequest, OptimizationResponse } from './types';

/**
 * Computes optimal bus repositioning schedules under the Fixed Fleet Invariant via POST /api/optimize
 */
export async function optimizeFleet(request: OptimizationRequest): Promise<OptimizationResponse> {
  if (!request.festival_id) {
    throw new Error('festival_id is required for optimization request');
  }

  return apiClient<OptimizationResponse>('/api/optimize', {
    method: 'POST',
    body: request,
  });
}
