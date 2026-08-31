import { AlertCircle, AlertTriangle, Archive, CheckCircle2, Circle, FileCheck, ShieldAlert } from "lucide-react";
import type { ComponentType } from "react";

import { cn } from "@/utils/cn";

export type BadgeStatus =
  | "NORMAL"
  | "IN_CONTROL"
  | "WARNING"
  | "OUT_OF_CONTROL"
  | "CRITICAL"
  | "DRAFT"
  | "APPROVED"
  | "ACTIVE"
  | "SUPERSEDED"
  | "ARCHIVED"
  | "OPEN"
  | "ACKNOWLEDGED"
  | "RESOLVED";

interface StatusVisual {
  label: string;
  icon: ComponentType<{ className?: string }>;
  className: string;
}

/** Status is always conveyed by text + icon together, never color alone
 * (see accessibility requirements) -- every entry here has a distinct
 * label and icon, even where the color happens to be similar. */
const STATUS_VISUALS: Record<BadgeStatus, StatusVisual> = {
  NORMAL: { label: "Normal", icon: CheckCircle2, className: "bg-status-normal-bg text-status-normal" },
  IN_CONTROL: { label: "In Control", icon: CheckCircle2, className: "bg-status-normal-bg text-status-normal" },
  WARNING: { label: "Warning", icon: AlertTriangle, className: "bg-status-warning-bg text-status-warning" },
  OUT_OF_CONTROL: { label: "Out of Control", icon: AlertCircle, className: "bg-status-outofcontrol-bg text-status-outofcontrol" },
  CRITICAL: { label: "Critical", icon: ShieldAlert, className: "bg-status-critical-bg text-status-critical" },
  DRAFT: { label: "Draft", icon: Circle, className: "bg-surface-100 text-ink-500" },
  APPROVED: { label: "Approved", icon: FileCheck, className: "bg-brand-50 text-brand-700" },
  ACTIVE: { label: "Active", icon: CheckCircle2, className: "bg-status-normal-bg text-status-normal" },
  SUPERSEDED: { label: "Superseded", icon: Archive, className: "bg-surface-100 text-ink-500" },
  ARCHIVED: { label: "Archived", icon: Archive, className: "bg-surface-100 text-ink-400" },
  OPEN: { label: "Open", icon: AlertCircle, className: "bg-status-warning-bg text-status-warning" },
  ACKNOWLEDGED: { label: "Acknowledged", icon: CheckCircle2, className: "bg-brand-50 text-brand-700" },
  RESOLVED: { label: "Resolved", icon: CheckCircle2, className: "bg-status-normal-bg text-status-normal" },
};

interface StatusBadgeProps {
  status: string;
  className?: string;
  size?: "sm" | "md";
}

export function StatusBadge({ status, className, size = "md" }: StatusBadgeProps) {
  const visual = STATUS_VISUALS[status as BadgeStatus] ?? {
    label: status,
    icon: Circle,
    className: "bg-surface-100 text-ink-500",
  };
  const Icon = visual.icon;

  return (
    <span
      role="status"
      aria-label={visual.label}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md font-medium",
        size === "sm" ? "px-2 py-0.5 text-xs" : "px-2.5 py-1 text-sm",
        visual.className,
        className,
      )}
    >
      <Icon className={size === "sm" ? "h-3 w-3" : "h-3.5 w-3.5"} aria-hidden="true" />
      {visual.label}
    </span>
  );
}
