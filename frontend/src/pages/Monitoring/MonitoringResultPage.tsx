import type { ReactNode } from "react";
import { useParams } from "react-router-dom";

import { BaselineComparison } from "@/components/baseline/BaselineComparison";
import { FindingsPanel } from "@/components/analysis/FindingsPanel";
import { ViolationsTable } from "@/components/analysis/ViolationsTable";
import { DistributionChart } from "@/components/charts/DistributionChart";
import { SPCControlChart } from "@/components/charts/SPCControlChart";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import { MetricCard } from "@/components/dashboard/MetricCard";
import { PageHeader } from "@/components/common/PageHeader";
import { StatusBadge } from "@/components/common/StatusBadge";
import { useManualCheckDetails } from "@/hooks/useMonitoring";
import { formatDateTime } from "@/utils/formatDate";
import { formatCapability, formatDelta, formatMeasurement, formatPercent } from "@/utils/formatNumber";

export function MonitoringResultPage() {
  const { manualCheckId } = useParams<{ manualCheckId: string }>();
  const { data: result, isLoading, error, refetch } = useManualCheckDetails(manualCheckId);

  if (isLoading) return <LoadingState message="Loading monitoring results..." />;
  if (error || !result) return <ErrorState error={error} title="Unable to load monitoring results" onRetry={refetch} />;

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Monitoring Analysis" subtitle="Current process behavior compared against the approved historical baseline." />

      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 rounded-lg border border-surface-200 bg-surface-0 px-4 py-3 text-sm">
        <InfoEntry label="Current Status" value={<StatusBadge status={result.final_status} />} />
        <InfoEntry label="Baseline Status" value={<StatusBadge status="ACTIVE" size="sm" />} />
        <InfoEntry label="Comparison Date" value={formatDateTime(result.created_at)} />
        <InfoEntry label="Chart Type" value={result.chart_type.replace("_", "-")} />
        <InfoEntry label="Unit" value={result.unit} />
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard label="Current Mean" value={formatMeasurement(result.current.mean, result.unit)} description={`Baseline: ${formatMeasurement(result.baseline.mean, result.unit)} · Shift: ${formatDelta(result.comparison.mean_shift, 4)} ${result.unit}`} />
        <MetricCard label="Current Cpk" value={formatCapability(result.current.cpk)} description={`Baseline: ${formatCapability(result.baseline.cpk)} · Change: ${formatDelta(result.comparison.cpk_change)}`} accent={capabilityAccent(result.current.cpk)} />
        <MetricCard label="Current Ppk" value={formatCapability(result.current.ppk)} description={`Baseline: ${formatCapability(result.baseline.ppk)} · Change: ${formatDelta(result.comparison.ppk_change)}`} accent={capabilityAccent(result.current.ppk)} />
        <MetricCard label="Current Sigma" value={formatMeasurement(result.current.within_sigma, result.unit)} description={`Baseline: ${formatMeasurement(result.baseline.within_sigma, result.unit)} · Change: ${formatPercent(result.comparison.within_variation_change_percentage)}`} />
      </div>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-ink-900">Current Data vs. Fixed Historical Baseline</h2>
        <p className="mb-3 text-xs text-ink-500">
          The UCL/CL/LCL lines below are the approved historical baseline's frozen limits -- they are never recalculated
          from the current dataset.
        </p>
        <SPCControlChart
          chartTitle="Current Measurements Against Baseline Limits"
          valueLabel="Current Value"
          points={result.current_chart.points}
          centerLine={result.baseline.center_line}
          ucl={result.baseline.ucl}
          lcl={result.baseline.lcl}
          specification={result.specification}
          unit={result.unit}
          violations={result.control_status.violations}
        />
      </section>

      {result.secondary_chart && result.baseline.secondary_center_line != null && (
        <section>
          <h2 className="mb-3 text-sm font-semibold text-ink-900">{secondaryChartTitle(result.chart_type)}</h2>
          <p className="mb-3 text-xs text-ink-500">
            Same rule as the chart above -- the UCL/CL/LCL lines are the baseline's frozen{" "}
            {secondaryChartTitle(result.chart_type).toLowerCase()} limits, not recalculated from this upload.
          </p>
          <SPCControlChart
            chartTitle={secondaryChartTitle(result.chart_type)}
            valueLabel={secondaryValueLabel(result.chart_type)}
            points={result.secondary_chart.points}
            centerLine={result.baseline.secondary_center_line}
            ucl={result.baseline.secondary_ucl ?? result.baseline.secondary_center_line}
            lcl={result.baseline.secondary_lcl ?? result.baseline.secondary_center_line}
            unit={result.unit}
            violations={[]}
          />
        </section>
      )}

      <section>
        <h2 className="mb-3 text-sm font-semibold text-ink-900">Distribution of Current Measurements</h2>
        <DistributionChart
          values={result.current_chart.points.map((p) => p.value)}
          mean={result.current.mean}
          specification={result.specification}
          unit={result.unit}
        />
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-ink-900">Baseline vs. Current Comparison</h2>
        <BaselineComparison baseline={result.baseline} current={result.current} comparison={result.comparison} unit={result.unit} />
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-ink-900">Findings</h2>
        <FindingsPanel findings={result.findings} />
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-ink-900">Baseline Limit Violations</h2>
        <ViolationsTable violations={result.control_status.violations} />
      </section>
    </div>
  );
}

function InfoEntry({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div>
      <span className="text-ink-500">{label}: </span>
      <span className="font-medium text-ink-900">{value}</span>
    </div>
  );
}

function secondaryChartTitle(chartType: string): string {
  if (chartType === "XBAR_R") return "Range Chart (R)";
  if (chartType === "XBAR_S") return "S Chart (Standard Deviation)";
  return "Moving Range Chart";
}

function secondaryValueLabel(chartType: string): string {
  if (chartType === "XBAR_R") return "Subgroup Range";
  if (chartType === "XBAR_S") return "Subgroup Std Dev";
  return "Moving Range";
}

function capabilityAccent(value: number | null): "normal" | "warning" | "critical" {
  if (value == null) return "warning";
  if (value >= 1.33) return "normal";
  if (value >= 1.0) return "warning";
  return "critical";
}
