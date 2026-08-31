import { Link } from "react-router-dom";

import { BaselineStatus } from "./BaselineStatus";
import { useContextLabels } from "@/hooks/useContextLabels";
import type { Baseline } from "@/types";
import { formatDateOnly } from "@/utils/formatDate";
import { formatCapability, formatMeasurement } from "@/utils/formatNumber";

interface BaselineCardProps {
  baseline: Baseline;
}

export function BaselineCard({ baseline }: BaselineCardProps) {
  const labels = useContextLabels({
    organization_id: baseline.organization_id,
    plant_id: baseline.plant_id,
    machine_id: baseline.machine_id,
    product_id: baseline.product_id,
    process_id: baseline.process_id,
    operation_id: baseline.operation_id,
    parameter_id: baseline.parameter_id,
  });

  return (
    <Link
      to={`/baselines/${baseline.baseline_id}`}
      className="flex flex-col gap-3 rounded-lg border border-surface-200 bg-surface-0 p-4 transition-shadow hover:shadow-sm"
    >
      <div className="flex items-start justify-between gap-2">
        <div>
          <p className="text-sm font-semibold text-ink-900">{labels.parameterName}</p>
          <p className="text-xs text-ink-500">{labels.machineName} · {labels.productName}</p>
        </div>
        <BaselineStatus status={baseline.status} />
      </div>

      <div className="grid grid-cols-3 gap-2 text-center text-sm">
        <div>
          <p className="text-xs text-ink-500">Center Line</p>
          <p className="font-medium text-ink-900">{formatMeasurement(baseline.center_line, baseline.unit)}</p>
        </div>
        <div>
          <p className="text-xs text-ink-500">Cpk</p>
          <p className="font-medium text-ink-900">{formatCapability(baseline.cpk)}</p>
        </div>
        <div>
          <p className="text-xs text-ink-500">Ppk</p>
          <p className="font-medium text-ink-900">{formatCapability(baseline.ppk)}</p>
        </div>
      </div>

      <div className="flex items-center justify-between text-xs text-ink-500">
        <span>{baseline.chart_type.replace("_", "-")}</span>
        <span>Created {formatDateOnly(baseline.created_at)}</span>
      </div>
    </Link>
  );
}
