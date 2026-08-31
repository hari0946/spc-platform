import { useSearchParams } from "react-router-dom";

import { BaselineCard } from "@/components/baseline/BaselineCard";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import { PageHeader } from "@/components/common/PageHeader";
import { useBaselines } from "@/hooks/useBaseline";
import type { BaselineStatus } from "@/types";

const STATUS_FILTERS: Array<BaselineStatus | "ALL"> = ["ALL", "ACTIVE", "DRAFT", "SUPERSEDED", "ARCHIVED"];

export function BaselinesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const statusParam = searchParams.get("status") as BaselineStatus | null;

  const { data: baselines, isLoading, error, refetch } = useBaselines(statusParam ? { status: statusParam } : undefined);

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={statusParam === "ACTIVE" ? "Active Baselines" : "Baseline History"}
        subtitle="Manage historical SPC baselines used for Phase 2 monitoring comparisons."
      />

      <div className="flex items-center gap-1.5">
        {STATUS_FILTERS.map((status) => (
          <button
            key={status}
            type="button"
            onClick={() => setSearchParams(status === "ALL" ? {} : { status })}
            className={`rounded-md px-2.5 py-1 text-xs font-medium ${
              (statusParam ?? "ALL") === status ? "bg-brand-600 text-white" : "bg-surface-100 text-ink-700 hover:bg-surface-200"
            }`}
          >
            {status === "ALL" ? "All" : status.charAt(0) + status.slice(1).toLowerCase()}
          </button>
        ))}
      </div>

      {isLoading && <LoadingState message="Loading baselines..." />}
      {error && <ErrorState error={error} title="Unable to load baselines" onRetry={refetch} />}

      {baselines && baselines.length === 0 && (
        <EmptyState title="No active baseline available." description="Run and approve a historical analysis to create a baseline." />
      )}

      {baselines && baselines.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {baselines.map((baseline) => (
            <BaselineCard key={baseline.baseline_id} baseline={baseline} />
          ))}
        </div>
      )}
    </div>
  );
}
