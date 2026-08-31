import type { BaselineStatus, ChartType } from "./api.types";

/** Mirrors app/schemas/baseline.py BaselineResponse exactly. */
export interface Baseline {
  baseline_id: string;
  analysis_id: string;
  organization_id: string | null;
  plant_id: string | null;
  production_line_id: string | null;
  process_id: string | null;
  machine_id: string | null;
  product_id: string | null;
  operation_id: string | null;
  parameter_id: string;
  chart_type: ChartType;
  unit: string;
  baseline_start: string | null;
  baseline_end: string | null;
  sample_count: number;
  mean: number;
  within_sigma: number;
  overall_sigma: number;
  center_line: number;
  ucl: number;
  lcl: number;
  secondary_center_line: number | null;
  secondary_ucl: number | null;
  secondary_lcl: number | null;
  lsl: number | null;
  usl: number | null;
  target: number | null;
  cp: number | null;
  cpk: number | null;
  pp: number | null;
  ppk: number | null;
  status: BaselineStatus;
  created_at: string;
  created_by: string | null;
  approved_at: string | null;
  approved_by: string | null;
}

export interface BaselineCreateRequest {
  analysis_id: string;
  created_by?: string;
}

export interface BaselineApproveRequest {
  approved_by?: string;
}
