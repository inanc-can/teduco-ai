/**
 * Centralized API client for backend communication
 * Provides type-safe methods for all backend endpoints
 */

import { OnboardingFormValues } from "./schemas/onboarding";

// API Configuration
const API_CONFIG = {
  baseUrl: process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000",
  timeout: 10000,
} as const;

// Custom API Error class
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public details?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

// Generic fetch wrapper with error handling
async function apiRequest<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_CONFIG.baseUrl}${endpoint}`;

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.timeout);

    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.error || errorData.detail || "Request failed",
        response.status,
        errorData
      );
    }

    // Handle no-content responses
    if (response.status === 204) {
      return undefined as T;
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof Error && error.name === "AbortError") {
      throw new ApiError("Request timeout", 408);
    }
    throw new ApiError("Network error", 0, error);
  }
}

// Type definitions for API requests/responses
export interface UserIn {
  fname: string;
  lname: string;
  email: string;
  password: string;
  birth_date?: string;
}

export interface UserResponse {
  user_id: number;
}

export interface UniversityIn {
  name: string;
  country: string;
}

export interface UniversityResponse {
  university_id: number;
}

export interface OnboardingResponse {
  message: string;
  user_id?: number;
}

// Typed API methods organized by resource
export const api = {
  users: {
    create: (data: UserIn) =>
      apiRequest<UserResponse>("/users", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    delete: (userId: number) =>
      apiRequest<void>(`/users/${userId}`, {
        method: "DELETE",
      }),
  },

  universities: {
    create: (data: UniversityIn) =>
      apiRequest<UniversityResponse>("/universities", {
        method: "POST",
        body: JSON.stringify(data),
      }),
    linkToUser: (userId: number, uniId: number) =>
      apiRequest<void>(`/users/${userId}/universities/${uniId}`, {
        method: "POST",
      }),
  },

  onboarding: {
    submit: (data: OnboardingFormValues) =>
      apiRequest<OnboardingResponse>("/onboarding", {
        method: "POST",
        body: JSON.stringify(data),
      }),
  },
};

// Helper to check if error is ApiError
export function isApiError(error: unknown): error is ApiError {
  return error instanceof ApiError;
}

// Helper to format error message for UI
export function getErrorMessage(error: unknown): string {
  if (isApiError(error)) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "An unexpected error occurred";
}
