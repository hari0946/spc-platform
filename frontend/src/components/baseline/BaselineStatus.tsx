import { ShieldCheck } from "lucide-react";

import { StatusBadge } from "@/components/common/StatusBadge";
import type { BaselineStatus as BaselineStatusType } from "@/types";

interface BaselineStatusProps {
  status: BaselineStatusType;
}

/** ACTIVE gets a distinctly prominent treatment -- it's the one baseline
 * that is actually in force for Phase 2 monitoring comparisons, and users
 * should never mistake a DRAFT/SUPERSEDED baseline for it. */
export function BaselineStatus({ status }: BaselineStatusProps) {
  if (status === "ACTIVE") {
    return (
      <div className="flex items-center gap-2 rounded-md bg-status-normal-bg px-3 py-1.5 text-status-normal">
        <ShieldCheck className="h-4 w-4" aria-hidden="true" />
        <span className="text-sm font-semibold">Active Baseline</span>
      </div>
    );
  }
  return <StatusBadge status={status} />;
}
