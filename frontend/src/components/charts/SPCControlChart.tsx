import { Download, Maximize2, Minimize2 } from "lucide-react";
import { useMemo, useRef, useState } from "react";
import {
  Brush,
  CartesianGrid,
  ComposedChart,
  Line,
  ReferenceArea,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { DotItemDotProps } from "recharts";

import { ChartLegend, type LegendEntry } from "./ChartLegend";
import { ChartTooltip } from "./ChartTooltip";
import type { ChartPoint, EnrichedChartPoint, RuleViolation, SpecificationLimits } from "@/types";
import { computeYDomain, downsampleForDisplay, enrichChartPoints, pointLabel } from "@/utils/chartHelpers";
import { formatAxisTick } from "@/utils/formatNumber";

interface SPCControlChartProps {
  /** Backend-provided points, in backend order -- never re-sorted by value,
   * only ever plotted in the sequence the engine returned them. */
  points: ChartPoint[];
  violations: RuleViolation[];
  centerLine: number;
  ucl: number;
  lcl: number;
  specification?: SpecificationLimits | null;
  unit: string;
  chartTitle: string;
  /** Label for the plotted value series, e.g. "Individual Value", "Subgroup Mean", "Range". */
  valueLabel: string;
  height?: number;
}

/**
 * Generic SPC trend chart -- deliberately parameterized so the same
 * component renders an I-MR individuals chart, an XBAR-R mean chart, a
 * range/S/MR secondary chart, or a monitoring comparison chart. Nothing
 * about "diameter" or any specific parameter is hardcoded; the caller
 * supplies title/unit/valueLabel.
 *
 * The measurement series is always a single continuous <Line> -- violation
 * points are overlaid via a custom dot renderer, never by breaking the
 * line into disconnected segments.
 */
export function SPCControlChart({
  points,
  violations,
  centerLine,
  ucl,
  lcl,
  specification,
  unit,
  chartTitle,
  valueLabel,
  height = 320,
}: SPCControlChartProps) {
  const [showControlLimits, setShowControlLimits] = useState(true);
  const [showSpecLimits, setShowSpecLimits] = useState(true);
  const [showTarget, setShowTarget] = useState(true);
  const [showSigmaZones, setShowSigmaZones] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Zone A/B/C boundaries (Western Electric zone rules): the space between
  // the center line and each control limit is split into thirds -- this is
  // pure interpolation of two values the backend already computed (center
  // line and UCL/LCL), not a new sigma calculation. Handles an
  // asymmetric UCL/LCL (relative to center line) by scaling each side
  // independently rather than assuming symmetry.
  const zones = useMemo(() => {
    const upperThird = (ucl - centerLine) / 3;
    const lowerThird = (centerLine - lcl) / 3;
    return {
      oneSigmaUpper: centerLine + upperThird,
      twoSigmaUpper: centerLine + 2 * upperThird,
      oneSigmaLower: centerLine - lowerThird,
      twoSigmaLower: centerLine - 2 * lowerThird,
    };
  }, [centerLine, ucl, lcl]);

  const enriched = useMemo(() => enrichChartPoints(points, violations), [points, violations]);
  const { displayed, wasDownsampled } = useMemo(() => downsampleForDisplay(enriched), [enriched]);

  // Spec limits (USL/LSL/Target) usually sit much further from the center
  // line than the control limits do -- including them in the Y-domain
  // stretches the axis so wide that the sigma zone bands (which only span
  // UCL to LCL) get squeezed into a thin, cramped strip. When zones are
  // being shown, the zoomed-in control-limit view wins: the domain is
  // computed from the data and control limits only, same as the
  // (zone-friendly) secondary chart, and spec/target lines simply fall
  // outside the visible range rather than fighting zones for space.
  const yDomain = useMemo(
    () =>
      computeYDomain([
        ...enriched.map((p) => p.value),
        ucl,
        lcl,
        centerLine,
        showSpecLimits && !showSigmaZones ? specification?.usl : undefined,
        showSpecLimits && !showSigmaZones ? specification?.lsl : undefined,
        showTarget && !showSigmaZones ? specification?.target : undefined,
      ]),
    [enriched, ucl, lcl, centerLine, specification, showSpecLimits, showTarget, showSigmaZones],
  );

  function toggleFullscreen() {
    if (!containerRef.current) return;
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen?.();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen?.();
      setIsFullscreen(false);
    }
  }

  function downloadImage() {
    const svg = containerRef.current?.querySelector("svg");
    if (!svg) return;
    const serialized = new XMLSerializer().serializeToString(svg);
    const svgBlob = new Blob([serialized], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(svgBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${chartTitle.replace(/\s+/g, "_").toLowerCase()}.svg`;
    link.click();
    URL.revokeObjectURL(url);
  }

  const legendEntries: LegendEntry[] = [
    { label: valueLabel, colorClassName: "border-brand-600", lineStyle: "solid" },
    { label: "UCL / LCL", colorClassName: "border-status-critical", lineStyle: "dashed" },
    { label: "Center Line", colorClassName: "border-ink-500", lineStyle: "solid" },
    ...(specification?.usl != null || specification?.lsl != null
      ? [{ label: "USL / LSL", colorClassName: "border-status-warning", lineStyle: "dotted" as const }]
      : []),
    ...(specification?.target != null
      ? [{ label: "Target", colorClassName: "border-status-normal", lineStyle: "dotted" as const }]
      : []),
    ...(showSigmaZones
      ? [
          { label: "Zone C (±1σ)", colorClassName: "bg-surface-200", lineStyle: "marker" as const },
          { label: "Zone B (1σ–2σ)", colorClassName: "bg-status-warning-bg", lineStyle: "marker" as const },
          { label: "Zone A (2σ–3σ)", colorClassName: "bg-status-critical-bg", lineStyle: "marker" as const },
        ]
      : []),
    { label: "Warning point", colorClassName: "bg-status-warning", lineStyle: "marker" },
    { label: "Out of control", colorClassName: "bg-status-outofcontrol", lineStyle: "marker" },
  ];

  return (
    <div ref={containerRef} className="rounded-lg border border-surface-200 bg-surface-0 p-4">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <h3 className="text-sm font-semibold text-ink-900">{chartTitle}</h3>
        <div className="flex items-center gap-3">
          <ToggleChip label="Control Limits" checked={showControlLimits} onChange={setShowControlLimits} />
          <ToggleChip label="Sigma Zones" checked={showSigmaZones} onChange={setShowSigmaZones} />
          {specification?.usl != null || specification?.lsl != null ? (
            <ToggleChip label="Spec Limits" checked={showSpecLimits} onChange={setShowSpecLimits} />
          ) : null}
          {specification?.target != null ? (
            <ToggleChip label="Target" checked={showTarget} onChange={setShowTarget} />
          ) : null}
          <button type="button" onClick={downloadImage} className="rounded p-1.5 text-ink-500 hover:bg-surface-100" aria-label="Download chart image">
            <Download className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={toggleFullscreen}
            className="rounded p-1.5 text-ink-500 hover:bg-surface-100"
            aria-label={isFullscreen ? "Exit fullscreen" : "View fullscreen"}
          >
            {isFullscreen ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
          </button>
        </div>
      </div>

      <p className="mb-2 text-xs text-ink-500">
        {valueLabel}
        {unit ? ` (${unit})` : ""} vs. {points[0]?.timestamp != null ? "time" : "sequence"}
        {wasDownsampled &&
          ` · Showing a downsampled view (${displayed.length.toLocaleString()} of ${points.length.toLocaleString()} points) for rendering performance. All warning and out-of-control points remain visible.`}
      </p>

      <ResponsiveContainer
        width="100%"
        height={isFullscreen ? Math.round(window.innerHeight * 0.8) : showSigmaZones ? Math.max(height, 480) : height}
      >
        <ComposedChart data={displayed} margin={{ top: 8, right: 24, left: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--color-surface-200)" />
          <XAxis
            dataKey={pointLabel}
            tick={{ fontSize: 11, fill: "var(--color-ink-500)" }}
            tickLine={false}
            minTickGap={24}
          />
          <YAxis
            domain={yDomain}
            tick={{ fontSize: 11, fill: "var(--color-ink-500)" }}
            tickLine={false}
            tickFormatter={(value) => formatAxisTick(value)}
            width={72}
          />
          <Tooltip
            content={({ active, payload }) => (
              <ChartTooltip
                active={active}
                payload={payload as unknown as { payload: EnrichedChartPoint }[]}
                unit={unit}
                ucl={ucl}
                centerLine={centerLine}
                lcl={lcl}
                valueLabel={valueLabel}
              />
            )}
          />

          {showSigmaZones && showControlLimits && (
            <>
              {/* Zone A: 2σ-3σ each side -- strongest tint, red boundary
                  (its outer edge is the UCL/LCL line drawn below). Labels
                  are centered inside each band (not corner-anchored) so
                  they stay legible even when a band's pixel height is
                  small; the chart is also given extra height above
                  whenever zones are shown, specifically so each band has
                  room to breathe. */}
              <ReferenceArea
                y1={zones.twoSigmaUpper} y2={ucl} fill="var(--color-status-critical)" fillOpacity={0.16}
                stroke="var(--color-status-critical)" strokeOpacity={0.4} strokeDasharray="4 2"
                label={{ value: "A", position: "insideLeft", fontSize: 11, fontWeight: 700, fill: "var(--color-status-critical)" }}
              />
              <ReferenceArea
                y1={lcl} y2={zones.twoSigmaLower} fill="var(--color-status-critical)" fillOpacity={0.16}
                stroke="var(--color-status-critical)" strokeOpacity={0.4} strokeDasharray="4 2"
                label={{ value: "A", position: "insideLeft", fontSize: 11, fontWeight: 700, fill: "var(--color-status-critical)" }}
              />
              {/* Zone B: 1σ-2σ each side -- medium tint, amber boundary. */}
              <ReferenceArea
                y1={zones.oneSigmaUpper} y2={zones.twoSigmaUpper} fill="var(--color-status-warning)" fillOpacity={0.16}
                stroke="var(--color-status-warning)" strokeOpacity={0.4} strokeDasharray="4 2"
                label={{ value: "B", position: "insideLeft", fontSize: 11, fontWeight: 700, fill: "var(--color-status-warning)" }}
              />
              <ReferenceArea
                y1={zones.twoSigmaLower} y2={zones.oneSigmaLower} fill="var(--color-status-warning)" fillOpacity={0.16}
                stroke="var(--color-status-warning)" strokeOpacity={0.4} strokeDasharray="4 2"
                label={{ value: "B", position: "insideLeft", fontSize: 11, fontWeight: 700, fill: "var(--color-status-warning)" }}
              />
              {/* Zone C: within 1σ of center line -- lightest tint, neutral boundary. */}
              <ReferenceArea
                y1={zones.oneSigmaLower} y2={zones.oneSigmaUpper} fill="var(--color-ink-400)" fillOpacity={0.16}
                stroke="var(--color-ink-500)" strokeOpacity={0.4} strokeDasharray="4 2"
                label={{ value: "C", position: "insideLeft", fontSize: 11, fontWeight: 700, fill: "var(--color-ink-700)" }}
              />

              {/* Zone boundaries are mathematically contiguous (Zone C ends
                  exactly where Zone B starts) -- that's what a sigma zone
                  is, so the numeric limits must stay touching. What was
                  actually cramped was the *visual* rendering: draw a thin
                  background-colored seam on top of each boundary so every
                  band still reads as a clearly separate region on screen. */}
              <ReferenceLine y={zones.oneSigmaUpper} stroke="var(--color-surface-0)" strokeWidth={2} />
              <ReferenceLine y={zones.oneSigmaLower} stroke="var(--color-surface-0)" strokeWidth={2} />
              <ReferenceLine y={zones.twoSigmaUpper} stroke="var(--color-surface-0)" strokeWidth={2} />
              <ReferenceLine y={zones.twoSigmaLower} stroke="var(--color-surface-0)" strokeWidth={2} />
            </>
          )}

          {showControlLimits && (
            <>
              <ReferenceLine y={ucl} stroke="var(--color-status-critical)" strokeDasharray="6 3" label={{ value: "UCL", position: "right", fontSize: 10, fill: "var(--color-status-critical)" }} />
              <ReferenceLine y={centerLine} stroke="var(--color-ink-500)" label={{ value: "CL", position: "right", fontSize: 10, fill: "var(--color-ink-500)" }} />
              <ReferenceLine y={lcl} stroke="var(--color-status-critical)" strokeDasharray="6 3" label={{ value: "LCL", position: "right", fontSize: 10, fill: "var(--color-status-critical)" }} />
            </>
          )}
          {showSpecLimits && specification?.usl != null && (
            <ReferenceLine y={specification.usl} stroke="var(--color-status-warning)" strokeDasharray="2 2" label={{ value: "USL", position: "right", fontSize: 10, fill: "var(--color-status-warning)" }} />
          )}
          {showSpecLimits && specification?.lsl != null && (
            <ReferenceLine y={specification.lsl} stroke="var(--color-status-warning)" strokeDasharray="2 2" label={{ value: "LSL", position: "right", fontSize: 10, fill: "var(--color-status-warning)" }} />
          )}
          {showTarget && specification?.target != null && (
            <ReferenceLine y={specification.target} stroke="var(--color-status-normal)" strokeDasharray="2 2" label={{ value: "Target", position: "right", fontSize: 10, fill: "var(--color-status-normal)" }} />
          )}

          {/* The measurement series itself: one continuous solid line,
              connecting every point in backend-provided order. Violation
              points get a larger, colored dot overlaid via a custom dot
              renderer -- the line segment through them is never broken. */}
          <Line
            type="linear"
            dataKey="value"
            stroke="var(--color-brand-600)"
            strokeWidth={2}
            dot={ViolationDot}
            activeDot={{ r: 5 }}
            isAnimationActive={false}
            connectNulls
            name={valueLabel}
          />

          <Brush dataKey={pointLabel} height={22} stroke="var(--color-brand-600)" travellerWidth={8} />
        </ComposedChart>
      </ResponsiveContainer>

      <div className="mt-3 border-t border-surface-100 pt-3">
        <ChartLegend entries={legendEntries} />
      </div>
    </div>
  );
}

/** Custom dot: invisible for normal points (keeps the line visually clean
 * per the "no dotted/disconnected" requirement), a warning-colored marker
 * for WARNING points, and a larger critical marker for OUT_OF_CONTROL
 * points -- exactly the "overlay markers without breaking the line"
 * requirement. */
function ViolationDot(props: DotItemDotProps) {
  const { cx, cy } = props;
  const payload = props.payload as EnrichedChartPoint | undefined;
  if (cx == null || cy == null) return <g />;

  const status = payload?.status;
  if (status === "OUT_OF_CONTROL") {
    return <circle cx={cx} cy={cy} r={5} fill="var(--color-status-outofcontrol)" stroke="white" strokeWidth={1.5} />;
  }
  if (status === "WARNING") {
    return <circle cx={cx} cy={cy} r={4} fill="var(--color-status-warning)" stroke="white" strokeWidth={1.5} />;
  }
  return <g />;
}

function ToggleChip({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="flex cursor-pointer items-center gap-1.5 text-xs text-ink-700">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} className="h-3.5 w-3.5 accent-brand-600" />
      {label}
    </label>
  );
}
