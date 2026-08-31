import type { ComponentType } from "react";

import { cn } from "@/utils/cn";

interface StatusCardProps {
  label: string;
  count: number;
  icon: ComponentType<{ className?: string }>;
  accent: "normal" | "warning" | "critical" | "brand";
}

const ACCENT_CLASSES: Record<StatusCardProps["accent"], string> = {
  normal: "border-status-normal-bg bg-status-normal-bg text-status-normal",
  warning: "border-status-warning-bg bg-status-warning-bg text-status-warning",
  critical: "border-status-critical-bg bg-status-critical-bg text-status-critical",
  brand: "border-brand-50 bg-brand-50 text-brand-700",
};

/** Used for the "Process Status Overview" summary row -- a simple count
 * card per process status bucket. */
export function StatusCard({ label, count, icon: Icon, accent }: StatusCardProps) {
  return (
    <div className={cn("flex items-center gap-3 rounded-lg border px-4 py-3", ACCENT_CLASSES[accent])}>
      <Icon className="h-6 w-6 shrink-0" aria-hidden="true" />
      <div>
        <p className="text-xl font-semibold tabular-nums">{count}</p>
        <p className="text-xs font-medium">{label}</p>
      </div>
    </div>
  );
}
