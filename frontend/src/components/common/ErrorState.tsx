import { AlertTriangle, RotateCcw } from "lucide-react";

import { ApiError } from "@/api/client";

interface ErrorStateProps {
  error: unknown;
  /** Overrides the derived message -- use for a context-specific fallback
   * like "Unable to validate CSV" instead of the raw API message. */
  title?: string;
  onRetry?: () => void;
  className?: string;
}

/** Renders any caught error as a calm, user-facing message. Never surfaces
 * a raw stack trace, SQL error, or Snowflake error -- ApiError already
 * carries only the backend's sanitized message; anything else (a thrown
 * JS error, a network failure) falls back to a generic message. */
export function ErrorState({ error, title, onRetry, className }: ErrorStateProps) {
  const message = deriveMessage(error);

  return (
    <div
      role="alert"
      className={`flex flex-col items-center justify-center gap-3 rounded-lg border border-status-critical-bg bg-status-critical-bg px-6 py-12 text-center ${className ?? ""}`}
    >
      <AlertTriangle className="h-8 w-8 text-status-critical" aria-hidden="true" />
      <div>
        <p className="font-semibold text-ink-900">{title ?? "Something went wrong"}</p>
        <p className="mt-1 text-sm text-ink-500">{message}</p>
      </div>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-2 inline-flex items-center gap-1.5 rounded-md border border-surface-300 bg-surface-0 px-3 py-1.5 text-sm font-medium text-ink-700 hover:bg-surface-100"
        >
          <RotateCcw className="h-3.5 w-3.5" aria-hidden="true" />
          Try again
        </button>
      )}
    </div>
  );
}

function deriveMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  if (typeof error === "string" && error.trim()) return error;
  return "An unexpected error occurred. Please try again.";
}
