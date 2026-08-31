import type { RecentAnalysisRow } from "@/components/dashboard/RecentAnalysis";
import type { AnalysisSummary, ManualCheckSummary } from "@/types";

export function historicalToRow(analysis: AnalysisSummary): RecentAnalysisRow {
  return {
    id: analysis.analysis_id,
    type: "HISTORICAL",
    organizationId: analysis.organization_id,
    plantId: analysis.plant_id,
    machineId: analysis.machine_id,
    productId: analysis.product_id,
    operationId: analysis.operation_id,
    parameterId: analysis.parameter_id,
    chartType: analysis.chart_type,
    cpk: analysis.cpk,
    status: analysis.stability_status ?? analysis.status,
    createdAt: analysis.created_at,
    viewPath: `/historical/analysis/${analysis.analysis_id}`,
  };
}

export function monitoringToRow(check: ManualCheckSummary): RecentAnalysisRow {
  return {
    id: check.manual_check_id,
    type: "MONITORING",
    organizationId: check.organization_id,
    plantId: check.plant_id,
    machineId: check.machine_id,
    productId: check.product_id,
    operationId: check.operation_id,
    parameterId: check.parameter_id,
    chartType: null,
    cpk: check.current_cpk,
    status: check.final_status ?? check.status,
    createdAt: check.created_at,
    viewPath: `/monitoring/result/${check.manual_check_id}`,
  };
}

export function mergeAndSortRows(historical: AnalysisSummary[], monitoring: ManualCheckSummary[]): RecentAnalysisRow[] {
  const rows = [...historical.map(historicalToRow), ...monitoring.map(monitoringToRow)];
  return rows.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
}
