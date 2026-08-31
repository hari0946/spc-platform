import type { AnalysisResult } from "@/types";
import { formatInteger, formatMeasurement } from "@/utils/formatNumber";

interface StatisticsPanelProps {
  analysis: AnalysisResult;
}

export function StatisticsPanel({ analysis }: StatisticsPanelProps) {
  const { data_summary, statistics, unit } = analysis;
  const range = statistics.maximum - statistics.minimum;

  const rows: [string, string][] = [
    ["Count", formatInteger(data_summary.total_observations)],
    ["Valid Count", formatInteger(data_summary.valid_observations)],
    ["Invalid Count", formatInteger(data_summary.invalid_observations)],
    ["Mean", formatMeasurement(statistics.mean, unit)],
    ["Minimum", formatMeasurement(statistics.minimum, unit)],
    ["Maximum", formatMeasurement(statistics.maximum, unit)],
    ["Range", formatMeasurement(range, unit)],
    ["Within Sigma", formatMeasurement(statistics.within_sigma, unit)],
    ["Overall Sigma", formatMeasurement(statistics.overall_sigma, unit)],
  ];

  return (
    <div className="rounded-lg border border-surface-200 bg-surface-0 p-4">
      <h3 className="mb-3 text-sm font-semibold text-ink-900">Statistics</h3>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-2.5 text-sm sm:grid-cols-3">
        {rows.map(([label, value]) => (
          <div key={label}>
            <dt className="text-xs text-ink-500">{label}</dt>
            <dd className="font-medium tabular-nums text-ink-900">{value}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
