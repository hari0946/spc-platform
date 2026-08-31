import { AlertCircle, AlertTriangle, Info } from "lucide-react";

import { EmptyState } from "@/components/common/EmptyState";
import type { Finding, Severity } from "@/types";
import { formatDateTime } from "@/utils/formatDate";

interface FindingsPanelProps {
  findings: Finding[];
}

const SEVERITY_VISUAL: Record<Severity, { icon: typeof Info; className: string }> = {
  INFO: { icon: Info, className: "border-brand-50 bg-brand-50 text-brand-700" },
  WARNING: { icon: AlertTriangle, className: "border-status-warning-bg bg-status-warning-bg text-status-warning" },
  CRITICAL: { icon: AlertCircle, className: "border-status-critical-bg bg-status-critical-bg text-status-critical" },
};

/**
 * Displays findings exactly as the backend produced them. This component
 * never generates its own explanation, never infers root cause, and never
 * rewrites the backend's message -- it only formats severity/type/message
 * for display.
 */
export function FindingsPanel({ findings }: FindingsPanelProps) {
  if (findings.length === 0) {
    return <EmptyState title="No findings available." description="No notable process findings were generated for this analysis." />;
  }

  return (
    <ul className="flex flex-col gap-2.5">
      {findings.map((finding, index) => {
        const visual = SEVERITY_VISUAL[finding.severity];
        const Icon = visual.icon;
        return (
          <li key={finding.finding_id ?? index} className={`flex items-start gap-3 rounded-lg border px-4 py-3 ${visual.className}`}>
            <Icon className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
            <div className="flex-1">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide">
                <span>{finding.severity}</span>
                <span className="opacity-60">·</span>
                <span className="opacity-80">{finding.finding_type.replace(/_/g, " ")}</span>
              </div>
              <p className="mt-0.5 text-sm text-ink-900">{finding.message}</p>
              {finding.created_at && <p className="mt-0.5 text-xs text-ink-500">{formatDateTime(finding.created_at)}</p>}
            </div>
          </li>
        );
      })}
    </ul>
  );
}
