import { useMemo } from "react";
import { Bar, CartesianGrid, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { SpecificationLimits } from "@/types";
import { formatAxisTick, formatMeasurement } from "@/utils/formatNumber";

interface HistogramChartProps {
  /** Raw measurement values, exactly as returned by the backend (chart
   * point values) -- this component only bins them into frequency buckets
   * for display. Mean/sigma/limits below are never derived here; they are
   * passed in from the backend's own statistics/specification. */
  values: number[];
  mean?: number | null;
  /** Backend-computed overall (individual-value) sigma. Used only to plot
   * the standard normal-distribution reference curve (a fixed, well-known
   * formula, not a new statistic) -- never derived from `values` here. */
  sigma?: number | null;
  specification?: SpecificationLimits | null;
  unit: string;
  binCount?: number;
}

interface HistogramBucket {
  rangeStart: number;
  rangeEnd: number;
  center: number;
  label: string;
  count: number;
  normalCurve?: number;
}

/** Answers "how are measurement values distributed?" -- deliberately a
 * different visual language (bars, no time axis) from the control chart,
 * which answers "how does the process change over sequence/time?". */
export function HistogramChart({ values, mean, sigma, specification, unit, binCount = 16 }: HistogramChartProps) {
  const buckets = useMemo(() => buildHistogram(values, binCount, mean, sigma), [values, binCount, mean, sigma]);
  const hasCurve = mean != null && sigma != null && sigma > 0;

  if (values.length === 0) {
    return <p className="py-8 text-center text-sm text-ink-500">No chart data available.</p>;
  }

  return (
    <div>
      <p className="mb-2 text-xs text-ink-500">Frequency vs. measurement value ({unit})</p>
      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={buckets} margin={{ top: 8, right: hasCurve ? 16 : 16, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-surface-200)" vertical={false} />
          <XAxis dataKey="label" tick={{ fontSize: 10, fill: "var(--color-ink-500)" }} tickLine={false} interval="preserveStartEnd" />
          <YAxis
            yAxisId="frequency"
            tick={{ fontSize: 11, fill: "var(--color-ink-500)" }}
            tickLine={false}
            width={40}
            tickFormatter={(v) => formatAxisTick(v, 0)}
            allowDecimals={false}
            label={{ value: "Frequency", angle: -90, position: "insideLeft", fontSize: 10, fill: "var(--color-ink-500)" }}
          />
          {hasCurve && (
            <YAxis
              yAxisId="curve"
              orientation="right"
              tick={{ fontSize: 11, fill: "var(--color-brand-600)" }}
              tickLine={false}
              width={40}
              tickFormatter={(v) => formatAxisTick(v, 3)}
              label={{ value: "Normal fit", angle: 90, position: "insideRight", fontSize: 10, fill: "var(--color-brand-600)" }}
            />
          )}
          <Tooltip
            formatter={(value, name) => (name === "normalCurve" ? [formatAxisTick(Number(value), 4), "Normal fit"] : [value, "Frequency"])}
            labelFormatter={(label) => `Range: ${label} ${unit}`}
            contentStyle={{ fontSize: 12, borderRadius: 8 }}
          />
          <Bar yAxisId="frequency" dataKey="count" name="count" fill="var(--color-brand-600)" fillOpacity={0.55} radius={[2, 2, 0, 0]} isAnimationActive={false} />
          {hasCurve && (
            <Line
              yAxisId="curve"
              type="monotone"
              dataKey="normalCurve"
              name="normalCurve"
              stroke="var(--color-status-normal)"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          )}

          {mean != null && <ReferenceLine yAxisId="frequency" x={findBucketLabel(buckets, mean)} stroke="var(--color-ink-900)" strokeWidth={2} label={{ value: "Mean", position: "top", fontSize: 10 }} />}
          {specification?.lsl != null && <ReferenceLine yAxisId="frequency" x={findBucketLabel(buckets, specification.lsl)} stroke="var(--color-status-warning)" strokeDasharray="4 2" label={{ value: "LSL", position: "top", fontSize: 10, fill: "var(--color-status-warning)" }} />}
          {specification?.usl != null && <ReferenceLine yAxisId="frequency" x={findBucketLabel(buckets, specification.usl)} stroke="var(--color-status-warning)" strokeDasharray="4 2" label={{ value: "USL", position: "top", fontSize: 10, fill: "var(--color-status-warning)" }} />}
          {specification?.target != null && <ReferenceLine yAxisId="frequency" x={findBucketLabel(buckets, specification.target)} stroke="var(--color-status-normal)" strokeDasharray="4 2" label={{ value: "Target", position: "top", fontSize: 10, fill: "var(--color-status-normal)" }} />}
        </ComposedChart>
      </ResponsiveContainer>
      {mean != null && (
        <p className="mt-1 text-center text-xs text-ink-500">
          Mean: {formatMeasurement(mean, unit)} · n = {values.length.toLocaleString()}
          {hasCurve && " · Green line: normal distribution fitted from mean/sigma, not the actual data density"}
        </p>
      )}
    </div>
  );
}

/** Standard normal probability density function, scaled to bin width and
 * sample size so the curve's area matches the histogram's total bar area
 * (the usual way a "fitted normal curve" overlay is drawn on a frequency
 * histogram) -- this is a fixed, well-known formula evaluated at fixed
 * points, not a statistic computed from the data. */
function normalPdf(x: number, mean: number, sigma: number, n: number, binWidth: number): number {
  const exponent = -((x - mean) ** 2) / (2 * sigma * sigma);
  const density = (1 / (sigma * Math.sqrt(2 * Math.PI))) * Math.exp(exponent);
  return density * n * binWidth;
}

function buildHistogram(
  values: number[],
  binCount: number,
  mean?: number | null,
  sigma?: number | null,
): HistogramBucket[] {
  if (values.length === 0) return [];
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const width = span / binCount;
  const hasCurve = mean != null && sigma != null && sigma > 0;

  const buckets: HistogramBucket[] = Array.from({ length: binCount }, (_, i) => {
    const rangeStart = min + i * width;
    const rangeEnd = rangeStart + width;
    const center = rangeStart + width / 2;
    return {
      rangeStart,
      rangeEnd,
      center,
      label: rangeStart.toFixed(3),
      count: 0,
      normalCurve: hasCurve ? normalPdf(center, mean, sigma, values.length, width) : undefined,
    };
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
