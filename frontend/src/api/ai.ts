import { apiClient } from './client';
import type { AIAskRequest, AIAskResponse } from './types';

/**
 * Submits natural language operator questions regarding optimization plans via POST /api/ai/ask
 */
export async function askCopilot(request: AIAskRequest): Promise<AIAskResponse> {
  if (!request.question || !request.question.trim()) {
    throw new Error('Question is required for AI copilot request');
  }

  return apiClient<AIAskResponse>('/api/ai/ask', {
    method: 'POST',
    body: {
      question: request.question.trim(),
      plan_id: request.plan_id || 'opt-plan-default',
      festival_id: request.festival_id,
      scenario: request.scenario || {},
    },
  });
}
