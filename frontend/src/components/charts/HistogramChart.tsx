import { useMemo } from "react";
import { Bar, CartesianGrid, ComposedChart, LabelList, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

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
  const buckets = useMemo(
    () => buildHistogram(values, binCount, mean, sigma, specification),
    [values, binCount, mean, sigma, specification],
  );
  const hasCurve = mean != null && sigma != null && sigma > 0;

  if (values.length === 0) {
    return <p className="py-8 text-center text-sm text-ink-500">No chart data available.</p>;
  }

  return (
    <div>
      <p className="mb-2 text-xs text-ink-500">Frequency vs. measurement value ({unit})</p>
      <ResponsiveContainer width="100%" height={340}>
        <ComposedChart data={buckets} margin={{ top: 36, right: 16, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-surface-200)" vertical={false} />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 10, fill: "var(--color-ink-500)" }}
            tickLine={false}
            interval="preserveStartEnd"
            label={{ value: `Measurement (${unit})`, position: "insideBottom", offset: -4, fontSize: 11, fill: "var(--color-ink-500)" }}
          />
          {/* Bars and curve share one axis -- the curve is scaled (density x
              n x bin width) to already be in "expected count" units, so it's
              directly comparable to the bar counts on the same scale, the
              way a fitted-normal-curve overlay is conventionally drawn. */}
          <YAxis
            tick={{ fontSize: 11, fill: "var(--color-ink-500)" }}
            tickLine={false}
            width={40}
            tickFormatter={(v) => formatAxisTick(v, 0)}
            allowDecimals={false}
            label={{ value: "Frequency", angle: -90, position: "insideLeft", fontSize: 10, fill: "var(--color-ink-500)" }}
          />
          <Tooltip
            formatter={(value, name) => (name === "Normal fit" ? [formatAxisTick(Number(value), 2), "Normal fit"] : [value, "Frequency"])}
            labelFormatter={(label) => `Range: ${label} ${unit}`}
            contentStyle={{ fontSize: 12, borderRadius: 8 }}
          />
          <Bar dataKey="count" name="Frequency" fill="#bbf7d0" stroke="var(--color-ink-900)" strokeWidth={1} isAnimationActive={false}>
            <LabelList dataKey="count" position="top" formatter={(v: unknown) => (typeof v === "number" && v > 0 ? v : "")} fontSize={11} fill="var(--color-ink-700)" />
          </Bar>
          {hasCurve && (
            <Line
              type="monotone"
              dataKey="normalCurve"
              name="Normal fit"
              stroke="var(--color-brand-700)"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          )}

          {/* "top" labels all render at the same height above the plot
              regardless of x-position -- when two lines land close together
              (e.g. Mean and Target are often only a hair apart), their
              labels would otherwise overlap. Distinct `offset` values stack
              them at different heights instead. */}
          {specification?.lsl != null && <ReferenceLine x={findBucketLabel(buckets, specification.lsl)} stroke="var(--color-status-critical)" strokeWidth={1.5} label={{ value: `LSL=${formatMeasurement(specification.lsl, "")}`, position: "top", offset: 8, fontSize: 11 }} />}
          {specification?.usl != null && <ReferenceLine x={findBucketLabel(buckets, specification.usl)} stroke="var(--color-status-critical)" strokeWidth={1.5} label={{ value: `USL=${formatMeasurement(specification.usl, "")}`, position: "top", offset: 8, fontSize: 11 }} />}
          {specification?.target != null && <ReferenceLine x={findBucketLabel(buckets, specification.target)} stroke="var(--color-status-normal)" strokeDasharray="4 2" label={{ value: "Target", position: "top", offset: 22, fontSize: 10, fill: "var(--color-status-normal)" }} />}
          {mean != null && <ReferenceLine x={findBucketLabel(buckets, mean)} stroke="var(--color-ink-900)" strokeDasharray="4 2" label={{ value: "Mean", position: "top", offset: 22, fontSize: 10 }} />}
        </ComposedChart>
      </ResponsiveContainer>
      {mean != null && (
        <p className="mt-3 text-center text-xs text-ink-500">
          Mean: {formatMeasurement(mean, unit)} · n = {values.length.toLocaleString()}
          {hasCurve && " · Blue curve: normal distribution fitted from mean/sigma, not the actual data density"}
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

// How many sigma out a normal curve needs to run before it visually reads
// as "tapered to the baseline" rather than abruptly cut off -- past ~3.5
// sigma the density is under 0.1% of the peak, indistinguishable from zero
// at chart resolution.
const CURVE_TAPER_SIGMA = 4;
// Pure safety net against a pathological input (e.g. a garbage sigma),
// not a limit that normal curve-taper or spec-limit padding should ever
// hit -- LSL/USL/Target must always fall inside the plotted range (see
// below), or their reference lines silently collapse onto the same edge
// bucket and their labels render stacked on top of each other.
const ABSOLUTE_MAX_PADDING_BINS_PER_SIDE = 40;

function buildHistogram(
  values: number[],
  binCount: number,
  mean?: number | null,
  sigma?: number | null,
  specification?: SpecificationLimits | null,
): HistogramBucket[] {
  if (values.length === 0) return [];
  const dataMin = Math.min(...values);
  const dataMax = Math.max(...values);
  const span = dataMax - dataMin || 1;
  const width = span / binCount;
  const hasCurve = mean != null && sigma != null && sigma > 0;

  // Extend the bucket range past the real data on both sides -- far enough
  // for the normal curve to actually decay toward the baseline instead of
  // being clipped flat, AND always far enough to include LSL/USL/Target if
  // they're set, however far from the data they happen to be. The extra
  // bins are real bins (same width as the data-driven ones), they just
  // never receive any actual values, so they stay count = 0.
  const lowerBounds = [dataMin];
  const upperBounds = [dataMax];
  if (hasCurve) {
    lowerBounds.push(mean - CURVE_TAPER_SIGMA * sigma);
    upperBounds.push(mean + CURVE_TAPER_SIGMA * sigma);
  }
  if (specification?.lsl != null) lowerBounds.push(specification.lsl);
  if (specification?.usl != null) upperBounds.push(specification.usl);
  if (specification?.target != null) {
    lowerBounds.push(specification.target);
    upperBounds.push(specification.target);
  }
  const lowerBound = Math.min(...lowerBounds);
  const upperBound = Math.max(...upperBounds);

  const paddingLeftBins = Math.min(ABSOLUTE_MAX_PADDING_BINS_PER_SIDE, Math.max(0, Math.ceil((dataMin - lowerBound) / width)));
  const paddingRightBins = Math.min(ABSOLUTE_MAX_PADDING_BINS_PER_SIDE, Math.max(0, Math.ceil((upperBound - dataMax) / width)));

  const min = dataMin - paddingLeftBins * width;
  const totalBins = binCount + paddingLeftBins + paddingRightBins;

  const buckets: HistogramBucket[] = Array.from({ length: totalBins }, (_, i) => {
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
    const index = Math.max(0, Math.min(Math.floor((value - min) / width), totalBins - 1));
    buckets[index].count += 1;
  }

  return buckets;
}

function findBucketLabel(buckets: HistogramBucket[], value: number): string {
  if (buckets.length === 0) return "";
  const bucket = buckets.find((b) => value >= b.rangeStart && value <= b.rangeEnd);
  if (bucket) return bucket.label;
  // The bucket range always covers LSL/USL/Target by construction (see
  // buildHistogram), so this only triggers for a value genuinely outside
  // that -- fall to whichever edge is actually nearer, rather than always
  // the last bucket, so two out-of-range values on opposite sides don't
  // collapse onto the same label.
  return value < buckets[0].rangeStart ? buckets[0].label : buckets[buckets.length - 1].label;
}
