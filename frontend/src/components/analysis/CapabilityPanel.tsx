import { CapabilityChart } from "@/components/charts/CapabilityChart";
import { MetricCard } from "@/components/dashboard/MetricCard";
import type { CapabilityMetrics, SpecificationLimits } from "@/types";
import { formatCapability, formatMeasurement } from "@/utils/formatNumber";

interface CapabilityPanelProps {
  capability: CapabilityMetrics;
  specification: SpecificationLimits | null;
  unit: string;
  warnings?: string[];
}

const METRIC_MEANING: Record<string, string> = {
  Cp: "Potential short-term capability",
  Cpk: "Actual short-term capability considering centering",
  Cpu: "Short-term capability against the upper limit",
  Cpl: "Short-term capability against the lower limit",
  Pp: "Overall process performance",
  Ppk: "Overall performance considering centering",
  Ppu: "Overall performance against the upper limit",
  Ppl: "Overall performance against the lower limit",
};

export function CapabilityPanel({ capability, specification, unit, warnings }: CapabilityPanelProps) {
  const entries: [string, number | null][] = [
    ["Cp", capability.cp],
    ["Cpk", capability.cpk],
    ["Cpu", capability.cpu],
    ["Cpl", capability.cpl],
    ["Pp", capability.pp],
    ["Ppk", capability.ppk],
    ["Ppu", capability.ppu],
    ["Ppl", capability.ppl],
  ];

  const hasAnyValue = entries.some(([, value]) => value != null);

  return (
    <div className="flex flex-col gap-4 rounded-lg border border-surface-200 bg-surface-0 p-4">
      <h3 className="text-sm font-semibold text-ink-900">Process Capability</h3>

      {!hasAnyValue ? (
        <p className="rounded-md bg-status-warning-bg px-3 py-2 text-sm text-status-warning">
          {warnings?.[0] ?? "Capability indices are not available for this analysis (no specification configured)."}
        </p>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {entries.map(([label, value]) => (
              <MetricCard key={label} label={label} value={formatCapability(value)} description={METRIC_MEANING[label]} />
            ))}
          </div>

          <div className="grid grid-cols-3 gap-3 rounded-md bg-surface-50 px-4 py-3 text-sm">
            <SpecTile label="LSL" value={specification?.lsl} unit={unit} />
            <SpecTile label="Target" value={specification?.target} unit={unit} />
            <SpecTile label="USL" value={specification?.usl} unit={unit} />
          </div>

          <div>
            <p className="mb-2 text-xs font-medium uppercase tracking-wide text-ink-500">Short-term vs Long-term Capability</p>
            <CapabilityChart capability={capability} />
          </div>

          {capability.sigma_level_short_term != null && (
            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wide text-ink-500">Sigma Level (Six Sigma Rating)</p>
              <div className="grid grid-cols-2 gap-3">
                <MetricCard
                  label="Short-term Sigma Level"
                  value={`${formatCapability(capability.sigma_level_short_term, 1)}σ`}
                  description="3 x Cpk -- distance from the mean to the nearest spec limit, in sigma units, before any long-term shift adjustment."
                  accent={sigmaLevelAccent(capability.sigma_level_short_term)}
                />
                <MetricCard
                  label="Long-term Sigma Level"
                  value={`${formatCapability(capability.sigma_level_long_term, 1)}σ`}
                  description="The number Six Sigma methodology actually reports -- short-term level minus the standard 1.5σ assumed long-term process shift."
                  accent={sigmaLevelAccent(capability.sigma_level_long_term)}
                />
              </div>
              <p className="mt-2 text-xs text-ink-500">
                A "Six Sigma" process is one with a short-term sigma level of 6σ (Cpk = 2.0), reported as 4.5σ
                long-term (≈3.4 defects per million) after the standard shift.
              </p>
            </div>
          )}
        </>
      )}

      {warnings && warnings.length > 0 && hasAnyValue && (
        <ul className="list-inside list-disc space-y-0.5 text-xs text-ink-500">
          {warnings.map((w, i) => (
            <li key={i}>{w}</li>
          ))}
        </ul>
      )}
    </div>
  );
}

function sigmaLevelAccent(value: number | null): "normal" | "warning" | "critical" {
  if (value == null) return "warning";
  if (value >= 6) return "normal";
  if (value >= 3) return "warning";
  return "critical";
}

function SpecTile({ label, value, unit }: { label: string; value: number | null | undefined; unit: string }) {
  return (
    <div className="text-center">
      <p className="text-xs text-ink-500">{label}</p>
      <p className="font-medium text-ink-900">{value != null ? formatMeasurement(value, unit) : "Not set"}</p>
    </div>
  );
}
