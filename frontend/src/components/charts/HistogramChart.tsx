import { useMemo } from "react";
import { Bar, BarChart, CartesianGrid, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { SpecificationLimits } from "@/types";
import { formatAxisTick, formatMeasurement } from "@/utils/formatNumber";

interface HistogramChartProps {
  /** Raw measurement values, exactly as returned by the backend (chart
   * point values) -- this component only bins them into frequency buckets
   * for display. Mean/sigma/limits below are never derived here; they are
   * passed in from the backend's own statistics/specification. */
  values: number[];
  mean?: number | null;
  specification?: SpecificationLimits | null;
  unit: string;
  binCount?: number;
}

interface HistogramBucket {
  rangeStart: number;
  rangeEnd: number;
  label: string;
  count: number;
}

/** Answers "how are measurement values distributed?" -- deliberately a
 * different visual language (bars, no time axis) from the control chart,
 * which answers "how does the process change over sequence/time?". */
export function HistogramChart({ values, mean, specification, unit, binCount = 16 }: HistogramChartProps) {
  const buckets = useMemo(() => buildHistogram(values, binCount), [values, binCount]);

  if (values.length === 0) {
    return <p className="py-8 text-center text-sm text-ink-500">No chart data available.</p>;
  }

  return (
    <div>
      <p className="mb-2 text-xs text-ink-500">Frequency vs. measurement value ({unit})</p>
      <ResponsiveContainer width="100%" height={280}>
        <BarChart data={buckets} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-surface-200)" vertical={false} />
          <XAxis dataKey="label" tick={{ fontSize: 10, fill: "var(--color-ink-500)" }} tickLine={false} interval="preserveStartEnd" />
          <YAxis tick={{ fontSize: 11, fill: "var(--color-ink-500)" }} tickLine={false} width={40} tickFormatter={(v) => formatAxisTick(v, 0)} allowDecimals={false} />
          <Tooltip
            formatter={(value) => [value, "Frequency"]}
            labelFormatter={(label) => `Range: ${label} ${unit}`}
            contentStyle={{ fontSize: 12, borderRadius: 8 }}
          />
          <Bar dataKey="count" fill="var(--color-brand-600)" radius={[2, 2, 0, 0]} isAnimationActive={false} />

          {mean != null && <ReferenceLine x={findBucketLabel(buckets, mean)} stroke="var(--color-ink-900)" strokeWidth={2} label={{ value: "Mean", position: "top", fontSize: 10 }} />}
          {specification?.lsl != null && <ReferenceLine x={findBucketLabel(buckets, specification.lsl)} stroke="var(--color-status-warning)" strokeDasharray="4 2" label={{ value: "LSL", position: "top", fontSize: 10, fill: "var(--color-status-warning)" }} />}
          {specification?.usl != null && <ReferenceLine x={findBucketLabel(buckets, specification.usl)} stroke="var(--color-status-warning)" strokeDasharray="4 2" label={{ value: "USL", position: "top", fontSize: 10, fill: "var(--color-status-warning)" }} />}
          {specification?.target != null && <ReferenceLine x={findBucketLabel(buckets, specification.target)} stroke="var(--color-status-normal)" strokeDasharray="4 2" label={{ value: "Target", position: "top", fontSize: 10, fill: "var(--color-status-normal)" }} />}
        </BarChart>
      </ResponsiveContainer>
      {mean != null && (
        <p className="mt-1 text-center text-xs text-ink-500">
          Mean: {formatMeasurement(mean, unit)} · n = {values.length.toLocaleString()}
        </p>
      )}
    </div>
  );
}

function buildHistogram(values: number[], binCount: number): HistogramBucket[] {
  if (values.length === 0) return [];
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const width = span / binCount;

  const buckets: HistogramBucket[] = Array.from({ length: binCount }, (_, i) => {
    const rangeStart = min + i * width;
    const rangeEnd = rangeStart + width;
    return { rangeStart, rangeEnd, label: rangeStart.toFixed(3), count: 0 };
  });

  for (const value of values) {
    const index = Math.min(Math.floor((value - min) / width), binCount - 1);
    buckets[index].count += 1;
  }

  return buckets;
}

function findBucketLabel(buckets: HistogramBucket[], value: number): string {
  const bucket = buckets.find((b) => value >= b.rangeStart && value <= b.rangeEnd);
  return bucket?.label ?? buckets[buckets.length - 1]?.label ?? "";
}
