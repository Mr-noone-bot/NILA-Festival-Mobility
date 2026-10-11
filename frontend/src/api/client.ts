import type { ApiErrorPayload } from './types';

/**
 * Custom API Error class with detailed status code and payload
 */
export class ApiError extends Error {
  public status: number;
  public statusText: string;
  public details?: unknown;
  public url?: string;

  constructor(payload: ApiErrorPayload) {
    super(payload.message);
    this.name = 'ApiError';
    this.status = payload.status;
    this.statusText = payload.statusText || 'Error';
    this.details = payload.details;
    this.url = payload.url;
  }
}

/**
 * Centralized Base URL resolution from VITE_API_BASE_URL
 */
const BASE_URL: string = (
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
).replace(/\/+$/, '');

export interface RequestOptions extends Omit<RequestInit, 'body'> {
  body?: unknown;
  timeoutMs?: number;
}

/**
 * Centralized HTTP request client with complete error handling:
 * - 2xx parsing with empty response detection
 * - 400 Bad Request
 * - 404 Not Found
 * - 422 Validation Error (FastAPI standard)
 * - 500 Internal Server Error
 * - Abort / Timeout handling
 * - Network failure
 */
export async function apiClient<T>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { body, timeoutMs = 12000, headers, ...restOptions } = options;

  const url = endpoint.startsWith('http')
    ? endpoint
    : `${BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const requestHeaders: Record<string, string> = {
    Accept: 'application/json',
    ...(headers as Record<string, string>),
  };

  if (body !== undefined && !(body instanceof FormData)) {
    requestHeaders['Content-Type'] = 'application/json';
  }

  try {
    const response = await fetch(url, {
      ...restOptions,
      headers: requestHeaders,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    // Handle non-2xx HTTP responses
    if (!response.ok) {
      let errorData: unknown;
      let errorMessage = `HTTP ${response.status} (${response.statusText})`;

      try {
        const text = await response.text();
        if (text) {
          try {
            errorData = JSON.parse(text);
            if (typeof errorData === 'object' && errorData !== null) {
              const obj = errorData as Record<string, unknown>;
              if (typeof obj.detail === 'string') {
                errorMessage = obj.detail;
              } else if (Array.isArray(obj.detail)) {
                // FastAPI 422 ValidationError array
                errorMessage = obj.detail
                  .map((d: { msg?: string; loc?: string[] }) => d.msg || JSON.stringify(d))
                  .join('; ');
              } else if (typeof obj.message === 'string') {
                errorMessage = obj.message;
              }
            }
          } catch {
            errorMessage = text;
          }
        }
      } catch {
        // Fall back to default status text
      }

      throw new ApiError({
        message: errorMessage,
        status: response.status,
        statusText: response.statusText,
        details: errorData,
        url,
      });
    }

    // HTTP 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    const rawText = await response.text();
    if (!rawText.trim()) {
      throw new ApiError({
        message: 'Empty response returned from server',
        status: response.status,
        statusText: 'Empty Response',
        url,
      });
    }

    try {
      return JSON.parse(rawText) as T;
    } catch {
      throw new ApiError({
        message: 'Invalid JSON response from server',
        status: response.status,
        statusText: 'JSON Parse Error',
        details: rawText,
        url,
      });
    }
  } catch (err: unknown) {
    clearTimeout(timeoutId);

    if (err instanceof ApiError) {
      throw err;
    }

    if (err instanceof Error) {
      if (err.name === 'AbortError') {
        throw new ApiError({
          message: `Request timed out after ${timeoutMs / 1000}s while connecting to ${url}`,
          status: 408,
          statusText: 'Request Timeout',
          url,
        });
      }

      // Network failures, CORS rejections, connection refused
      throw new ApiError({
        message: `Network failure connecting to backend (${url}): ${err.message}. Ensure backend is running.`,
        status: 0,
        statusText: 'Network Error',
        details: err,
        url,
      });
    }

    throw new ApiError({
      message: 'Unknown client error occurred during request',
      status: 0,
      statusText: 'Unknown Error',
      details: err,
      url,
    });
  }
}

export { BASE_URL };
