/**
 * Pure display-logic helpers for chart data. These correlate and downsample
 * data the backend already computed -- they never derive a new SPC value.
 * Rule 42 is absolute: no mean/sigma/UCL/Cpk math lives here.
 */

import type { ChartPoint, ChartPointStatus, EnrichedChartPoint, RuleViolation } from "@/types";

/**
 * Cross-references each chart point's index against the violations list's
 * `affected_points` (both are backend-provided) to attach a display status
 * and the violation message(s) for that point. This is index-matching, not
 * rule evaluation -- the rule evaluation already happened on the backend.
 */
export function enrichChartPoints(points: ChartPoint[], violations: RuleViolation[]): EnrichedChartPoint[] {
  const byIndex = new Map<number, { status: ChartPointStatus; messages: string[] }>();

  for (const violation of violations) {
    const status: ChartPointStatus = violation.rule_name === "POINT_OUTSIDE_LIMITS" ? "OUT_OF_CONTROL" : "WARNING";
    for (const affectedIndex of violation.affected_points) {
      const existing = byIndex.get(affectedIndex);
      if (!existing || rank(status) > rank(existing.status)) {
        byIndex.set(affectedIndex, { status, messages: [violation.message] });
      } else {
        existing.messages.push(violation.message);
      }
    }
  }

  return points.map((point) => {
    const entry = byIndex.get(point.index);
    return {
      ...point,
      status: entry?.status ?? "NORMAL",
      violationMessages: entry?.messages ?? [],
    };
  });
}

function rank(status: ChartPointStatus): number {
  if (status === "OUT_OF_CONTROL") return 2;
  if (status === "WARNING") return 1;
  return 0;
}

const DEFAULT_MAX_DISPLAY_POINTS = 500;

/**
 * Downsamples a large point series for rendering performance while
 * guaranteeing every non-NORMAL point (warning/out-of-control) is kept
 * visible -- large datasets must never silently hide a violation to make
 * the chart lighter.
 */
export function downsampleForDisplay(
  points: EnrichedChartPoint[],
  maxPoints: number = DEFAULT_MAX_DISPLAY_POINTS,
): { displayed: EnrichedChartPoint[]; wasDownsampled: boolean } {
  if (points.length <= maxPoints) {
    return { displayed: points, wasDownsampled: false };
  }

  const mustKeep = new Set(points.filter((p) => p.status !== "NORMAL").map((p) => p.index));
  const budget = Math.max(maxPoints - mustKeep.size, 0);
  const stride = budget > 0 ? Math.ceil(points.length / budget) : points.length + 1;

  const keptIndices = new Set<number>(mustKeep);
  for (let i = 0; i < points.length; i += stride) {
    keptIndices.add(points[i].index);
  }
  // Always anchor the series endpoints so the trend line's start/end are
  // never accidentally clipped by the stride.
  keptIndices.add(points[0].index);
  keptIndices.add(points[points.length - 1].index);

  const displayed = points.filter((p) => keptIndices.has(p.index)).sort((a, b) => a.index - b.index);
  return { displayed, wasDownsampled: true };
}

/** X-axis label: prefer the backend timestamp when present (subgroup-based
 * charts always carry one), fall back to the raw sequence index otherwise. */
export function pointLabel(point: ChartPoint): string {
  return point.timestamp ?? `#${point.index}`;
}

/** Combines every relevant Y value across primary series, control limits,
 * and specification limits so a chart's Y-axis domain never clips a
 * reference line -- purely a rendering concern, not a calculation. */
export function computeYDomain(
  values: Array<number | null | undefined>,
  paddingFraction = 0.08,
): [number, number] {
  const finite = values.filter((v): v is number => typeof v === "number" && Number.isFinite(v));
  if (finite.length === 0) return [0, 1];
  const min = Math.min(...finite);
  const max = Math.max(...finite);
  const span = max - min || Math.abs(max) || 1;
  const padding = span * paddingFraction;
  // Round away IEEE-754 noise (e.g. 19.999999999999996 from min - padding)
  // before handing the domain to Recharts -- its own "nice tick" generator
  // otherwise inherits that noise and renders it verbatim.
  return [roundToSignificantDigits(min - padding, 8), roundToSignificantDigits(max + padding, 8)];
}

function roundToSignificantDigits(value: number, digits: number): number {
  if (value === 0) return 0;
  return Number(value.toPrecision(digits));
}
