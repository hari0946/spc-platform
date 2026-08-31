import { Minus, TrendingDown, TrendingUp } from "lucide-react";

import type { BaselineSummary, ComparisonMetrics, CurrentSummary } from "@/types";
import { formatCapability, formatMeasurement } from "@/utils/formatNumber";

interface BaselineComparisonProps {
  baseline: BaselineSummary;
  current: CurrentSummary;
  comparison: ComparisonMetrics;
  unit: string;
}

/** "shifted" is deliberately neutral (not "improved"/"decreased") -- a
 * mean shift has no inherent good/bad direction without knowing which way
 * is desirable relative to target, unlike variation (lower is always
 * better) or capability (higher is always better). */
type Interpretation = "improved" | "decreased" | "shifted" | "none";

interface ComparisonRow {
  metric: string;
  baselineValue: number | null;
  currentValue: number | null;
  change: number | null;
  /** Backend-computed determination, where the backend actually computes
   * one for this metric -- undefined means "no backend interpretation
   * available", in which case only the raw numbers are shown. */
  interpretation?: Interpretation;
  formatter: (v: number | null) => string;
}

/**
 * Metric | Baseline | Current | Change table. Every "Improved / Decreased
 * / No Significant Change" label comes directly from the backend's own
 * detection flags (BaselineComparisonEngine) -- this component never
 * invents its own significance threshold from the raw deltas.
 */
export function BaselineComparison({ baseline, current, comparison, unit }: BaselineComparisonProps) {
  const rows: ComparisonRow[] = [
    {
      metric: "Mean",
      baselineValue: baseline.mean,
      currentValue: current.mean,
      change: comparison.mean_shift,
      interpretation: comparison.mean_shift_detected ? "shifted" : "none",
      formatter: (v) => formatMeasurement(v, unit),
    },
    {
      metric: "Within Sigma",
      baselineValue: baseline.within_sigma,
      currentValue: current.within_sigma,
      change: current.within_sigma - baseline.within_sigma,
      interpretation: comparison.variation_increase_detected ? "decreased" : comparison.variation_reduction_detected ? "improved" : "none",
      formatter: (v) => formatMeasurement(v, unit),
    },
    {
      metric: "Overall Sigma",
      baselineValue: baseline.overall_sigma,
      currentValue: current.overall_sigma,
      change: current.overall_sigma - baseline.overall_sigma,
      formatter: (v) => formatMeasurement(v, unit),
    },
    { metric: "Cp", baselineValue: baseline.cp, currentValue: current.cp, change: delta(current.cp, baseline.cp), formatter: formatCapability },
    {
      metric: "Cpk",
      baselineValue: baseline.cpk,
      currentValue: current.cpk,
      change: comparison.cpk_change,
      interpretation: comparison.capability_degradation_detected ? "decreased" : comparison.capability_improvement_detected ? "improved" : "none",
      formatter: formatCapability,
    },
    { metric: "Pp", baselineValue: baseline.pp, currentValue: current.pp, change: delta(current.pp, baseline.pp), formatter: formatCapability },
    {
      metric: "Ppk",
      baselineValue: baseline.ppk,
      currentValue: current.ppk,
      change: comparison.ppk_change,
      formatter: formatCapability,
    },
  ];

  return (
    <div className="overflow-x-auto rounded-lg border border-surface-200 bg-surface-0">
      <table className="w-full min-w-max text-left text-sm">
        <thead>
          <tr className="border-b border-surface-200 bg-surface-50 text-ink-500">
            <th className="px-4 py-2.5 font-medium">Metric</th>
            <th className="px-4 py-2.5 font-medium">Baseline</th>
            <th className="px-4 py-2.5 font-medium">Current</th>
            <th className="px-4 py-2.5 font-medium">Change</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <ComparisonRowView key={row.metric} row={row} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ComparisonRowView({ row }: { row: ComparisonRow }) {
  const { metric, baselineValue, currentValue, change, interpretation, formatter } = row;

  return (
    <tr className="border-b border-surface-100 last:border-b-0">
      <td className="px-4 py-2.5 font-medium text-ink-900">{metric}</td>
      <td className="px-4 py-2.5 tabular-nums text-ink-700">{formatter(baselineValue)}</td>
      <td className="px-4 py-2.5 tabular-nums text-ink-700">{formatter(currentValue)}</td>
      <td className="px-4 py-2.5">
        <div className="flex items-center gap-1.5">
          <span className="tabular-nums text-ink-900">
            {change != null ? (change > 0 ? "+" : "") + formatter(change) : "N/A"}
          </span>
          {interpretation && (
            <>
              <InterpretationIcon interpretation={interpretation} />
              <span className={`text-xs ${interpretationColor(interpretation)}`}>{interpretationLabel(interpretation)}</span>
            </>
          )}
        </div>
      </td>
    </tr>
  );
}

function interpretationLabel(interpretation: Interpretation): string {
  if (interpretation === "improved") return "Improved";
  if (interpretation === "decreased") return "Decreased";
  if (interpretation === "shifted") return "Shift detected";
  return "No significant change";
}

function interpretationColor(interpretation: Interpretation): string {
  if (interpretation === "improved") return "text-status-normal";
  if (interpretation === "decreased") return "text-status-critical";
  if (interpretation === "shifted") return "text-status-warning";
  return "text-ink-500";
}

function InterpretationIcon({ interpretation }: { interpretation: Interpretation }) {
  if (interpretation === "improved") return <TrendingUp className="h-3.5 w-3.5 text-status-normal" aria-hidden="true" />;
  if (interpretation === "decreased") return <TrendingDown className="h-3.5 w-3.5 text-status-critical" aria-hidden="true" />;
  if (interpretation === "shifted") return <TrendingUp className="h-3.5 w-3.5 text-status-warning" aria-hidden="true" />;
  return <Minus className="h-3.5 w-3.5 text-ink-400" aria-hidden="true" />;
}

function delta(current: number | null, baseline: number | null): number | null {
  if (current == null || baseline == null) return null;
  return current - baseline;
}
