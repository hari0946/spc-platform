import { useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { RecentAnalysis } from "@/components/dashboard/RecentAnalysis";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import { PageHeader } from "@/components/common/PageHeader";
import { useAnalysisList } from "@/hooks/useAnalysis";
import { useManualCheckList } from "@/hooks/useMonitoring";
import { mergeAndSortRows } from "@/utils/analysisRows";

const PAGE_SIZE = 15;
type TypeFilter = "ALL" | "HISTORICAL" | "MONITORING";
type StatusFilter = "ALL" | "IN_CONTROL" | "WARNING" | "OUT_OF_CONTROL" | "CRITICAL" | "NORMAL";

export function AnalysisHistoryPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const typeParam = (searchParams.get("type") as TypeFilter | null) ?? "ALL";

  const [statusFilter, setStatusFilter] = useState<StatusFilter>("ALL");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);

  const historical = useAnalysisList({ analysisType: "HISTORICAL", limit: 200 });
  const monitoring = useManualCheckList({ limit: 200 });

  const isLoading = historical.isLoading || monitoring.isLoading;
  const error = historical.error ?? monitoring.error;

  const allRows = useMemo(() => mergeAndSortRows(historical.data ?? [], monitoring.data ?? []), [historical.data, monitoring.data]);

  const filteredRows = useMemo(() => {
    let rows = allRows;
    if (typeParam !== "ALL") rows = rows.filter((r) => r.type === typeParam);
    if (statusFilter !== "ALL") rows = rows.filter((r) => r.status === statusFilter);
    if (search.trim()) {
      const q = search.trim().toLowerCase();
      rows = rows.filter((r) => r.id.toLowerCase().includes(q));
    }
    return rows;
  }, [allRows, typeParam, statusFilter, search]);

  const totalPages = Math.max(1, Math.ceil(filteredRows.length / PAGE_SIZE));
  const pageRows = filteredRows.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  function setTypeFilter(value: TypeFilter) {
    setPage(1);
    setSearchParams(value === "ALL" ? {} : { type: value });
  }

  if (isLoading) return <LoadingState message="Loading analysis history..." />;
  if (error) return <ErrorState error={error} title="Unable to load analysis history" />;

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title={
          typeParam === "MONITORING"
            ? "Current Data SPC Analysis"
            : typeParam === "HISTORICAL"
              ? "Historical Data SPC Analysis"
              : "Analysis History"
        }
        subtitle="Browse and search every historical analysis and monitoring check."
      />

      <div className="flex flex-wrap items-center gap-3">
        <FilterGroup label="Type" value={typeParam} options={["ALL", "HISTORICAL", "MONITORING"]} onChange={(v) => setTypeFilter(v as TypeFilter)} />
        <FilterGroup
          label="Status"
          value={statusFilter}
          options={["ALL", "IN_CONTROL", "NORMAL", "WARNING", "OUT_OF_CONTROL", "CRITICAL"]}
          onChange={(v) => {
            setStatusFilter(v as StatusFilter);
            setPage(1);
          }}
        />
        <input
          type="search"
          placeholder="Search by ID..."
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
          className="input ml-auto w-56"
        />
      </div>

      <RecentAnalysis rows={pageRows} />

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-ink-500">
          <span>
            Page {page} of {totalPages} ({filteredRows.length} results)
          </span>
          <div className="flex gap-2">
            <button type="button" onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="btn btn-secondary">
              Previous
            </button>
            <button type="button" onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="btn btn-secondary">
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function FilterGroup<T extends string>({ label, value, options, onChange }: { label: string; value: T; options: T[]; onChange: (v: T) => void }) {
  return (
    <div className="flex items-center gap-1.5">
      <span className="text-xs font-medium text-ink-500">{label}:</span>
      {options.map((option) => (
        <button
          key={option}
          type="button"
          onClick={() => onChange(option)}
          className={`rounded-md px-2 py-1 text-xs font-medium ${value === option ? "bg-brand-600 text-white" : "bg-surface-100 text-ink-700 hover:bg-surface-200"}`}
        >
          {option === "ALL" ? "All" : option.replace(/_/g, " ")}
        </button>
      ))}
    </div>
  );
}
