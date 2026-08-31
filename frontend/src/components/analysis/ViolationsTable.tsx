import { useMemo, useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/common/DataTable";
import { StatusBadge } from "@/components/common/StatusBadge";
import type { RuleViolation, Severity } from "@/types";
import { formatDateTime } from "@/utils/formatDate";

interface ViolationsTableProps {
  violations: RuleViolation[];
  onSelectViolation?: (violation: RuleViolation) => void;
}

const SEVERITY_FILTERS: Array<Severity | "ALL"> = ["ALL", "INFO", "WARNING", "CRITICAL"];

export function ViolationsTable({ violations, onSelectViolation }: ViolationsTableProps) {
  const [severityFilter, setSeverityFilter] = useState<Severity | "ALL">("ALL");

  const filtered = useMemo(
    () => (severityFilter === "ALL" ? violations : violations.filter((v) => v.severity === severityFilter)),
    [violations, severityFilter],
  );

  const columns: DataTableColumn<RuleViolation>[] = [
    { key: "sequence", header: "Sequence", render: (v) => `#${v.start_index}${v.end_index !== v.start_index ? `–${v.end_index}` : ""}` },
    { key: "timestamp", header: "Timestamp", render: (v) => formatDateTime(v.detected_at) },
    { key: "rule", header: "Rule", render: (v) => v.rule_name.replace(/_/g, " ") },
    { key: "severity", header: "Severity", render: (v) => <StatusBadge status={v.severity} size="sm" /> },
    { key: "message", header: "Message", render: (v) => v.message, className: "max-w-md whitespace-normal" },
  ];

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center gap-1.5">
        {SEVERITY_FILTERS.map((option) => (
          <button
            key={option}
            type="button"
            onClick={() => setSeverityFilter(option)}
            className={`rounded-md px-2.5 py-1 text-xs font-medium ${
              severityFilter === option ? "bg-brand-600 text-white" : "bg-surface-100 text-ink-700 hover:bg-surface-200"
            }`}
          >
            {option === "ALL" ? "All" : option.charAt(0) + option.slice(1).toLowerCase()}
          </button>
        ))}
      </div>

      <DataTable
        columns={columns}
        data={filtered}
        keyExtractor={(v) => `${v.rule_name}-${v.start_index}-${v.detected_at}`}
        onRowClick={onSelectViolation}
        emptyTitle="No violations detected."
        emptyDescription="No SPC rule violations were found in this dataset."
      />
    </div>
  );
}
