import { StatusBadge } from "@/components/common/StatusBadge";
import type { EnrichedChartPoint } from "@/types";
import { formatDateTime } from "@/utils/formatDate";
import { formatMeasurement } from "@/utils/formatNumber";

interface SPCTooltipPayloadEntry {
  payload: EnrichedChartPoint;
}

/** Deliberately not typed against recharts' own (generic, variance-fussy)
 * TooltipContentProps -- only `active`/`payload` are actually consumed,
 * loosely typed here and passed through from <Tooltip content={...}>. */
interface SPCChartTooltipProps {
  active?: boolean;
  payload?: ReadonlyArray<SPCTooltipPayloadEntry>;
  unit: string;
  ucl: number;
  centerLine: number;
  lcl: number;
  valueLabel: string;
}

/** Custom tooltip matching the spec's exact required fields: sequence,
 * timestamp, value, control limits, status, and violation rule if any. */
export function ChartTooltip({ active, payload, unit, ucl, centerLine, lcl, valueLabel }: SPCChartTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;

  const point = payload[0].payload;
  if (!point) return null;

  return (
    <div className="max-w-xs rounded-lg border border-surface-200 bg-surface-0 px-3 py-2.5 text-xs shadow-lg">
      <div className="mb-1.5 flex items-center justify-between gap-3">
        <span className="font-semibold text-ink-900">Point #{point.index}</span>
        <StatusBadge status={point.status} size="sm" />
      </div>
      <dl className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-0.5 text-ink-500">
        {point.timestamp && (
          <>
            <dt>Time</dt>
            <dd className="text-right text-ink-900">{formatDateTime(point.timestamp)}</dd>
          </>
        )}
        {point.subgroup_id && (
          <>
            <dt>Subgroup</dt>
            <dd className="text-right text-ink-900">{point.subgroup_id}</dd>
          </>
        )}
        <dt>{valueLabel}</dt>
        <dd className="text-right font-medium text-ink-900">{formatMeasurement(point.value, unit)}</dd>
        <dt>UCL</dt>
        <dd className="text-right text-ink-900">{formatMeasurement(ucl, unit)}</dd>
        <dt>Center Line</dt>
        <dd className="text-right text-ink-900">{formatMeasurement(centerLine, unit)}</dd>
        <dt>LCL</dt>
        <dd className="text-right text-ink-900">{formatMeasurement(lcl, unit)}</dd>
      </dl>
      {point.violationMessages.length > 0 && (
        <div className="mt-2 border-t border-surface-200 pt-1.5 text-status-critical">
          {point.violationMessages.map((msg, i) => (
            <p key={i}>{msg}</p>
          ))}
        </div>
      )}
    </div>
  );
}
