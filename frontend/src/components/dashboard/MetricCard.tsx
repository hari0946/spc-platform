import type { ComponentType, ReactNode } from "react";

import { cn } from "@/utils/cn";

interface MetricCardProps {
  label: string;
  value: ReactNode;
  description?: string;
  icon?: ComponentType<{ className?: string }>;
  accent?: "neutral" | "normal" | "warning" | "critical" | "brand";
  className?: string;
}

const ACCENT_CLASSES: Record<NonNullable<MetricCardProps["accent"]>, string> = {
  neutral: "text-ink-900",
  normal: "text-status-normal",
  warning: "text-status-warning",
  critical: "text-status-critical",
  brand: "text-brand-600",
};

/** The single reusable metric tile used across the dashboard and every
 * summary panel (statistics, capability, comparison cards). Deliberately
 * minimal -- one value, one short explanation, no decorative chrome. */
export function MetricCard({ label, value, description, icon: Icon, accent = "neutral", className }: MetricCardProps) {
  return (
    <div className={cn("rounded-lg border border-surface-200 bg-surface-0 p-4", className)}>
      <div className="flex items-center justify-between gap-2">
        <p className="text-xs font-medium uppercase tracking-wide text-ink-500">{label}</p>
        {Icon && <Icon className="h-4 w-4 text-ink-400" aria-hidden="true" />}
      </div>
      <p className={cn("mt-1.5 text-2xl font-semibold tabular-nums", ACCENT_CLASSES[accent])}>{value}</p>
      {description && <p className="mt-1 text-xs leading-snug text-ink-500">{description}</p>}
    </div>
  );
}
