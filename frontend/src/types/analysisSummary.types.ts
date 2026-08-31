import type { ChartType } from "./api.types";

/** Lightweight list-view row -- mirrors AnalysisSummaryResponse. */
export interface AnalysisSummary {
  analysis_id: string;
  analysis_type: "HISTORICAL" | "MANUAL_CHECK_CURRENT";
  upload_id: string;
  organization_id: string | null;
  plant_id: string | null;
  machine_id: string | null;
  product_id: string | null;
  operation_id: string | null;
  parameter_id: string;
  chart_type: ChartType;
  status: string;
  cpk: number | null;
  ppk: number | null;
  stability_status: string | null;
  created_at: string;
}

/** Lightweight list-view row -- mirrors ManualCheckSummaryResponse. */
export interface ManualCheckSummary {
  manual_check_id: string;
  upload_id: string;
  baseline_id: string;
  organization_id: string | null;
  plant_id: string | null;
  machine_id: string | null;
  product_id: string | null;
  operation_id: string | null;
  parameter_id: string;
  status: string;
  final_status: string | null;
  current_cpk: number | null;
  current_ppk: number | null;
  created_at: string;
}
