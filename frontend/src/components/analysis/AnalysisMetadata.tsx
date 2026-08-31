import { StatusBadge } from "@/components/common/StatusBadge";
import { useContextLabels } from "@/hooks/useContextLabels";
import type { AnalysisResult } from "@/types";
import { formatDateTime } from "@/utils/formatDate";

interface AnalysisMetadataProps {
  analysis: AnalysisResult;
}

export function AnalysisMetadata({ analysis }: AnalysisMetadataProps) {
  const labels = useContextLabels(analysis.context);

  const entries: [string, string][] = [
    ["Machine", labels.machineName],
    ["Product", labels.productName],
    ["Process", labels.processName],
    ["Operation", labels.operationName],
    ["Parameter", labels.parameterName],
    ["Unit", analysis.unit || "—"],
    ["Chart Type", analysis.chart.type.replace("_", "-")],
    ["Analysis Date", formatDateTime(analysis.created_at)],
  ];

  return (
    <div className="flex flex-wrap items-center gap-x-6 gap-y-2 rounded-lg border border-surface-200 bg-surface-0 px-4 py-3 text-sm">
      {entries.map(([label, value]) => (
        <div key={label}>
          <span className="text-ink-500">{label}: </span>
          <span className="font-medium text-ink-900">{value}</span>
        </div>
      ))}
      <StatusBadge status={analysis.stability.status} />
    </div>
  );
}
