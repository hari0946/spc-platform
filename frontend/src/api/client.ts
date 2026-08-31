/**
 * Centralized Axios client. Every API module (analysis.api.ts,
 * uploads.api.ts, ...) imports this instance rather than constructing its
 * own -- baseURL, timeout, and error normalization live here exactly once.
 */

import axios, { AxiosError } from "axios";

import type { ApiErrorBody } from "@/types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60_000, // SPC analysis over a large historical CSV can legitimately take a while
});

/** Normalized, UI-safe error shape. Never carries a raw stack trace, SQL
 * error, or Snowflake error string -- those stay in the backend log; only
 * the backend's already-sanitized error_code/message reach here. */
export class ApiError extends Error {
  readonly errorCode: string;
  readonly details: Record<string, unknown>;
  readonly status: number | null;

  constructor(message: string, errorCode: string, status: number | null, details: Record<string, unknown> = {}) {
    super(message);
    this.name = "ApiError";
    this.errorCode = errorCode;
    this.status = status;
    this.details = details;
  }
}

const FALLBACK_MESSAGES: Record<number, string> = {
  400: "The request could not be processed.",
  404: "The requested resource was not found.",
  409: "This action conflicts with the current state of the data.",
  422: "The provided data is invalid.",
  503: "The service is temporarily unavailable. Please try again shortly.",
};

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorBody>) => {
    if (error.response) {
      const body = error.response.data;
      const status = error.response.status;
      const message = body?.message ?? FALLBACK_MESSAGES[status] ?? "Something went wrong. Please try again.";
      const errorCode = body?.error_code ?? "UNKNOWN_ERROR";
      return Promise.reject(new ApiError(message, errorCode, status, body?.details ?? {}));
    }
    if (error.request) {
      return Promise.reject(
        new ApiError("Unable to reach the server. Check your connection and try again.", "NETWORK_ERROR", null),
      );
    }
    return Promise.reject(new ApiError(error.message || "An unexpected error occurred.", "CLIENT_ERROR", null));
  },
);
