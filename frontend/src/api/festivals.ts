import { apiClient } from './client';
import type { Festival, FestivalDetails, HealthResponse } from './types';

/**
 * Checks system health via GET /api/health
 */
export async function getHealth(): Promise<HealthResponse> {
  return apiClient<HealthResponse>('/api/health');
}

/**
 * Retrieves the catalog of supported Tamil Nadu temple festivals via GET /api/festivals
 */
export async function getFestivals(): Promise<Festival[]> {
  const result = await apiClient<Festival[]>('/api/festivals');
  if (!Array.isArray(result)) {
    throw new Error('Expected festival catalog array from GET /api/festivals');
  }
  return result;
}

/**
 * Retrieves detailed festival metadata, gates, nearby stops, and fleet size via GET /api/festivals/{festival_id}
 */
export async function getFestivalDetails(festivalId: string): Promise<FestivalDetails> {
  if (!festivalId) {
    throw new Error('festivalId is required to fetch festival details');
  }
  return apiClient<FestivalDetails>(`/api/festivals/${encodeURIComponent(festivalId)}`);
}
