/**
 * Types for Phase 1 historical SPC analysis. Mirrors
 * app/schemas/analysis.py on the backend exactly -- field names and
 * nullability match the real, verified API response, not a hypothetical
 * shape.
 */

import type { ChartType, StabilityStatus } from "./api.types";
import type { ChartSeries, RuleViolation, SpecificationLimits } from "./chart.types";

export interface AnalysisContext {
  organization_id: string | null;
  plant_id: string | null;
  production_line_id: string | null;
  machine_id: string | null;
  product_id: string | null;
  process_id: string | null;
  operation_id: string | null;
  parameter_id: string;
}

export interface DataSummary {
  total_observations: number;
  valid_observations: number;
  invalid_observations: number;
  subgroups: number;
}

export interface AnalysisChart {
  type: ChartType;
  subgroup_size_used: number;
  primary_chart: ChartSeries;
  secondary_chart: ChartSeries | null;
  selection_reason: string;
}

export interface AnalysisStatistics {
  mean: number;
  minimum: number;
  maximum: number;
  within_sigma: number;
  overall_sigma: number;
}

export interface CapabilityMetrics {
  cp: number | null;
  cpk: number | null;
  cpu: number | null;
  cpl: number | null;
  pp: number | null;
  ppk: number | null;
  ppu: number | null;
  ppl: number | null;
  /** "Sigma level" / Six Sigma process rating, derived from Cpk
   * (sigma_level_short_term = 3 x Cpk; long_term subtracts the standard
   * 1.5-sigma Six Sigma shift convention). Backend-computed, never
   * re-derived on the frontend. */
  sigma_level_short_term: number | null;
  sigma_level_long_term: number | null;
}

export interface StabilityResult {
  status: StabilityStatus;
  violations: RuleViolation[];
}

/** The single source of truth for both a freshly-run analysis
 * (POST /analysis/historical) and a re-opened historical one
 * (GET /analysis/{id}) -- the backend guarantees both return this exact
 * shape, so the frontend never needs two rendering code paths. */
export interface AnalysisResult {
  analysis_id: string;
  context: AnalysisContext;
  unit: string;
  data_summary: DataSummary;
  chart: AnalysisChart;
  statistics: AnalysisStatistics;
  specification: SpecificationLimits | null;
  capability: CapabilityMetrics;
  stability: StabilityResult;
  warnings: string[];
  created_at: string;
}

export interface HistoricalAnalysisRequest {
  upload_id: string;
  parameter_id: string;
  machine_id?: string;
  product_id?: string;
  process_id?: string;
  operation_id?: string;
  spc_configuration_id?: string;
}
