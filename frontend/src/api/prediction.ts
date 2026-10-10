import { apiClient } from './client';
import type { PredictionRequest, PredictionResponse } from './types';

/**
 * Generates temporal crowd surge estimates via POST /api/predict
 */
export async function predictCrowd(request: PredictionRequest): Promise<PredictionResponse> {
  if (!request.festival_id) {
    throw new Error('festival_id is required for prediction request');
  }

  return apiClient<PredictionResponse>('/api/predict', {
    method: 'POST',
    body: request,
  });
}
