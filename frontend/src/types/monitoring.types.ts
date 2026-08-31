/**
 * Phase 2 manual monitoring types. Mirrors app/schemas/manual_check.py
 * exactly (both POST /manual-check/run and GET /manual-check/{id} return
 * this identical shape on the backend).
 */

import type { ChartType, FinalProcessStatus } from "./api.types";
import type { ChartSeries, RuleViolation, SpecificationLimits } from "./chart.types";
import type { Finding } from "./findings.types";

export interface BaselineSummary {
  baseline_id: string;
  mean: number;
  ucl: number;
  center_line: number;
  lcl: number;
  within_sigma: number;
  overall_sigma: number;
  /** Frozen limits for the secondary (range / moving-range) chart -- null
   * for baselines saved before this field existed. */
  secondary_center_line: number | null;
  secondary_ucl: number | null;
  secondary_lcl: number | null;
  cp: number | null;
  cpk: number | null;
  pp: number | null;
  ppk: number | null;
  lsl: number | null;
  usl: number | null;
  target: number | null;
}

export interface CurrentSummary {
  mean: number;
  within_sigma: number;
  overall_sigma: number;
  cp: number | null;
  cpk: number | null;
  pp: number | null;
  ppk: number | null;
}

export interface ComparisonMetrics {
  mean_shift: number;
  mean_shift_percentage: number | null;
  within_variation_change_percentage: number | null;
  overall_variation_change_percentage: number | null;
  cpk_change: number | null;
  ppk_change: number | null;
  /** Authoritative "is this a significant change" determination from
   * BaselineComparisonEngine on the backend -- never re-derive these from
   * the raw deltas above. */
  mean_shift_detected: boolean;
  variation_increase_detected: boolean;
  variation_reduction_detected: boolean;
  capability_improvement_detected: boolean;
  capability_degradation_detected: boolean;
}

export interface ControlStatus {
  status: string;
  violations: RuleViolation[];
}

export interface ManualCheckResult {
  manual_check_id: string;
  upload_id: string;
  unit: string;
  chart_type: ChartType;
  specification: SpecificationLimits | null;
  baseline: BaselineSummary;
  current: CurrentSummary;
  current_chart: ChartSeries;
  /** Range (XBAR-R/S) or Moving Range (I-MR) chart for the current
   * dataset -- null if a baseline was created before this field existed. */
  secondary_chart: ChartSeries | null;
  comparison: ComparisonMetrics;
  control_status: ControlStatus;
  findings: Finding[];
  final_status: FinalProcessStatus;
  warnings: string[];
  created_at: string;
}

export interface ManualCheckRequest {
  upload_id: string;
  parameter_id: string;
  machine_id?: string;
  product_id?: string;
  operation_id?: string;
  baseline_id?: string;
  triggered_by?: string;
}
