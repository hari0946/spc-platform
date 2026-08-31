/**
 * Shared primitive types used across every API response. Kept separate
 * from domain types (analysis/baseline/chart) so those files only import
 * what they conceptually depend on.
 */

/** Structured error body returned by every failed backend request (see
 * app/core/exceptions.py AppException.to_dict() on the backend). */
export interface ApiErrorBody {
  error_code: string;
  message: string;
  details: Record<string, unknown>;
}

export type StabilityStatus = "IN_CONTROL" | "WARNING" | "OUT_OF_CONTROL";

export type FinalProcessStatus = "NORMAL" | "WARNING" | "OUT_OF_CONTROL" | "CRITICAL";

export type Severity = "INFO" | "WARNING" | "CRITICAL";

export type BaselineStatus = "DRAFT" | "ACTIVE" | "SUPERSEDED" | "ARCHIVED";

export type UploadType = "HISTORICAL" | "CURRENT";

export type UploadStatus =
  | "UPLOADED"
  | "BRONZE_LOADING"
  | "BRONZE_COMPLETED"
  | "VALIDATING"
  | "VALIDATION_COMPLETED"
  | "SILVER_LOADING"
  | "SILVER_COMPLETED"
  | "FAILED";

export type ChartType = "XBAR_R" | "XBAR_S" | "IMR";

export type SubgroupMethod = "EXISTING_ID" | "FIXED_SIZE" | "CONSECUTIVE" | "TIME_WINDOW";

export type RuleName = "POINT_OUTSIDE_LIMITS" | "TREND_INCREASING" | "TREND_DECREASING" | "RUN_SAME_SIDE";

export type FindingType =
  | "MEAN_SHIFT"
  | "VARIATION_INCREASE"
  | "VARIATION_REDUCTION"
  | "CAPABILITY_DEGRADATION"
  | "CAPABILITY_IMPROVEMENT"
  | "NEW_LIMIT_VIOLATION"
  | "TREND_DETECTED"
  | "SHIFT_DETECTED"
  | "PROCESS_STABLE"
  | "PROCESS_UNSTABLE";
