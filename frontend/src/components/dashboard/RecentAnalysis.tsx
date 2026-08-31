import { Eye } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { DataTable, type DataTableColumn } from "@/components/common/DataTable";
import { StatusBadge } from "@/components/common/StatusBadge";
import { useContextLabels } from "@/hooks/useContextLabels";
import type { ChartType } from "@/types";
import { formatDateTime } from "@/utils/formatDate";
import { formatCapability } from "@/utils/formatNumber";

/** Unified shape covering both a historical AnalysisSummary row and a
 * monitoring ManualCheckSummary row -- the two backend list endpoints
 * return different fields (chart_type/cpk vs current_cpk/final_status),
 * so the caller normalizes into this before handing rows here. */
export interface RecentAnalysisRow {
  id: string;
  type: "HISTORICAL" | "MONITORING";
  organizationId: string | null;
  plantId: string | null;
  machineId: string | null;
  productId: string | null;
  operationId: string | null;
  parameterId: string;
  chartType: ChartType | null;
  cpk: number | null;
  status: string;
  createdAt: string;
  viewPath: string;
}

interface RecentAnalysisProps {
  rows: RecentAnalysisRow[];
}

export function RecentAnalysis({ rows }: RecentAnalysisProps) {
  const navigate = useNavigate();

  const columns: DataTableColumn<RecentAnalysisRow>[] = [
    { key: "id", header: "Analysis ID", render: (r) => <span className="font-mono text-xs">{r.id.slice(0, 8)}</span> },
    { key: "type", header: "Type", render: (r) => (r.type === "HISTORICAL" ? "Historical" : "Monitoring") },
    { key: "machine", header: "Machine", render: (r) => <ContextCell row={r} field="machine" /> },
    { key: "product", header: "Product", render: (r) => <ContextCell row={r} field="product" /> },
    { key: "parameter", header: "Parameter", render: (r) => <ContextCell row={r} field="parameter" /> },
    { key: "chartType", header: "Chart Type", render: (r) => (r.chartType ? r.chartType.replace("_", "-") : "—") },
    { key: "cpk", header: "Cpk", render: (r) => formatCapability(r.cpk) },
    { key: "status", header: "Status", render: (r) => <StatusBadge status={r.status} size="sm" /> },
    { key: "date", header: "Date", render: (r) => formatDateTime(r.createdAt) },
    {
      key: "view",
      header: "",
      render: (r) => (
        <button
          type="button"
          onClick={() => navigate(r.viewPath)}
          className="flex items-center gap-1 text-brand-600 hover:text-brand-700"
          aria-label={`View analysis ${r.id}`}
        >
          <Eye className="h-4 w-4" />
        </button>
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={rows}
      keyExtractor={(r) => r.id}
      emptyTitle="No analyses found."
      emptyDescription="Upload a historical CSV to run your first SPC analysis."
    />
  );
}

function ContextCell({ row, field }: { row: RecentAnalysisRow; field: "machine" | "product" | "parameter" }) {
  const labels = useContextLabels({
    organization_id: row.organizationId,
    plant_id: row.plantId,
    machine_id: row.machineId,
    product_id: row.productId,
    operation_id: row.operationId,
    parameter_id: row.parameterId,
  });
  if (field === "machine") return <>{row.machineId ? labels.machineName : "—"}</>;
  if (field === "product") return <>{row.productId ? labels.productName : "—"}</>;
  return <>{labels.parameterName}</>;
}
