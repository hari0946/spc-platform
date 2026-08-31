/**
 * Chart-related types shared by both the historical analysis result and
 * the monitoring/manual-check result -- both backend responses use the
 * identical ChartSeries/ChartPoint/RuleViolation shapes (see
 * app/schemas/common.py on the backend).
 */

import type { ChartType, RuleName, Severity } from "./api.types";

/** One plotted point -- either an individual measurement (I-MR) or a
 * subgroup summary value (XBAR-R mean/range, XBAR-S mean/std-dev). The
 * frontend never computes `value`; it only ever displays what the backend
 * already calculated. */
export interface ChartPoint {
  index: number;
  subgroup_id: string | null;
  timestamp: string | null;
  value: number;
  n: number;
}

export interface ChartSeries {
  center_line: number;
  ucl: number;
  lcl: number;
  points: ChartPoint[];
}

export interface RuleViolation {
  rule_name: RuleName;
  chart_type: ChartType;
  severity: Severity;
  start_index: number;
  end_index: number;
  affected_points: number[];
  message: string;
  detected_at: string;
}

export interface SpecificationLimits {
  lsl: number | null;
  usl: number | null;
  target: number | null;
}

/** Derived, display-only status computed in the frontend by correlating a
 * point's index against the violations list (see utils/chartHelpers.ts).
 * This is pure data correlation, not SPC math -- the violation itself
 * always comes from the backend. */
export type ChartPointStatus = "NORMAL" | "WARNING" | "OUT_OF_CONTROL";

export interface EnrichedChartPoint extends ChartPoint {
  status: ChartPointStatus;
  violationMessages: string[];
}
