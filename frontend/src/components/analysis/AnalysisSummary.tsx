import { AlertCircle, AlertTriangle, CheckCircle2 } from "lucide-react";

import { MetricCard } from "@/components/dashboard/MetricCard";
import type { AnalysisResult } from "@/types";
import { formatCapability, formatMeasurement } from "@/utils/formatNumber";

interface AnalysisSummaryProps {
  analysis: AnalysisResult;
}

const STATUS_COPY: Record<
  AnalysisResult["stability"]["status"],
  { icon: typeof CheckCircle2; label: string; description: string; accent: "normal" | "warning" | "critical" }
> = {
  IN_CONTROL: {
    icon: CheckCircle2,
    label: "Normal",
    description: "Process is statistically stable. No special-cause variation detected.",
    accent: "normal",
  },
  WARNING: {
    icon: AlertTriangle,
    label: "Warning",
    description: "A trend or sustained shift pattern was detected. Review the highlighted points.",
    accent: "warning",
  },
  OUT_OF_CONTROL: {
    icon: AlertCircle,
    label: "Out of Control",
    description: "Special-cause variation detected. Review the highlighted points.",
    accent: "critical",
  },
};

export function AnalysisSummary({ analysis }: AnalysisSummaryProps) {
  const statusInfo = STATUS_COPY[analysis.stability.status];
  const Icon = statusInfo.icon;

  return (
    <div className="flex flex-col gap-4">
      <div
        className={`flex items-center gap-3 rounded-lg border px-5 py-4 ${
          statusInfo.accent === "normal"
            ? "border-status-normal-bg bg-status-normal-bg"
            : statusInfo.accent === "warning"
              ? "border-status-warning-bg bg-status-warning-bg"
              : "border-status-critical-bg bg-status-critical-bg"
        }`}
      >
        <Icon
          className={`h-7 w-7 shrink-0 ${
            statusInfo.accent === "normal" ? "text-status-normal" : statusInfo.accent === "warning" ? "text-status-warning" : "text-status-critical"
          }`}
          aria-hidden="true"
        />
        <div>
          <p
            className={`text-lg font-semibold ${
              statusInfo.accent === "normal" ? "text-status-normal" : statusInfo.accent === "warning" ? "text-status-warning" : "text-status-critical"
            }`}
          >
            {statusInfo.label}
          </p>
          <p className="text-sm text-ink-700">{statusInfo.description}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard label="Process Mean" value={formatMeasurement(analysis.statistics.mean, analysis.unit)} description="Center of the measured process data" />
        <MetricCard label="Within Sigma" value={formatMeasurement(analysis.statistics.within_sigma, analysis.unit)} description="Short-term (common-cause) variation" />
        <MetricCard label="Cpk" value={formatCapability(analysis.capability.cpk)} description="Short-term capability considering process centering" accent={capabilityAccent(analysis.capability.cpk)} />
        <MetricCard label="Ppk" value={formatCapability(analysis.capability.ppk)} description="Long-term capability considering process centering" accent={capabilityAccent(analysis.capability.ppk)} />
      </div>
    </div>
  );
}

function capabilityAccent(value: number | null): "normal" | "warning" | "critical" {
  if (value == null) return "warning";
  if (value >= 1.33) return "normal";
  if (value >= 1.0) return "warning";
  return "critical";
}
