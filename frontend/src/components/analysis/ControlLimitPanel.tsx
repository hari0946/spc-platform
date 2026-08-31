import type { ChartSeries, SpecificationLimits } from "@/types";
import { formatMeasurement } from "@/utils/formatNumber";

interface ControlLimitPanelProps {
  chart: ChartSeries;
  specification: SpecificationLimits | null;
  unit: string;
}

/** Deliberately two visually separate blocks -- statistical control limits
 * (computed from process variation) are conceptually and often numerically
 * very different from engineering specification limits (customer/design
 * requirements), and users should never confuse the two. */
export function ControlLimitPanel({ chart, specification, unit }: ControlLimitPanelProps) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
      <div className="rounded-lg border border-surface-200 bg-surface-0 p-4">
        <h3 className="mb-3 text-sm font-semibold text-ink-900">Statistical Control Limits</h3>
        <p className="mb-3 text-xs text-ink-500">Computed from observed process variation.</p>
        <LimitRow label="UCL" value={chart.ucl} unit={unit} tone="critical" />
        <LimitRow label="Center Line" value={chart.center_line} unit={unit} />
        <LimitRow label="LCL" value={chart.lcl} unit={unit} tone="critical" />
      </div>

      <div className="rounded-lg border border-surface-200 bg-surface-0 p-4">
        <h3 className="mb-3 text-sm font-semibold text-ink-900">Engineering Specification Limits</h3>
        <p className="mb-3 text-xs text-ink-500">Defined by engineering/customer requirements.</p>
        {specification ? (
          <>
            <LimitRow label="USL" value={specification.usl} unit={unit} tone="warning" />
            <LimitRow label="Target" value={specification.target} unit={unit} />
            <LimitRow label="LSL" value={specification.lsl} unit={unit} tone="warning" />
          </>
        ) : (
          <p className="text-sm text-ink-500">No specification configured for this context.</p>
        )}
      </div>
    </div>
  );
}

function LimitRow({
  label,
  value,
  unit,
  tone = "neutral",
}: {
  label: string;
  value: number | null | undefined;
  unit: string;
  tone?: "neutral" | "warning" | "critical";
}) {
  const valueClass = tone === "critical" ? "text-status-critical" : tone === "warning" ? "text-status-warning" : "text-ink-900";
  return (
    <div className="flex items-center justify-between border-b border-surface-100 py-2 text-sm last:border-b-0">
      <span className="text-ink-500">{label}</span>
      <span className={`font-medium tabular-nums ${valueClass}`}>{value != null ? formatMeasurement(value, unit) : "Not set"}</span>
    </div>
  );
}
