import { useState } from "react";

import { DataTable, type DataTableColumn } from "@/components/common/DataTable";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import { PageHeader } from "@/components/common/PageHeader";
import { useContextLabels } from "@/hooks/useContextLabels";
import { useConfigurations, useUpdateConfiguration } from "@/hooks/useConfigurations";
import type { SpcConfiguration } from "@/types";
import { formatDateTime } from "@/utils/formatDate";

export function SettingsPage() {
  const { data: configurations, isLoading, error, refetch } = useConfigurations();
  const updateConfig = useUpdateConfiguration();
  const [togglingId, setTogglingId] = useState<string | null>(null);

  async function handleToggleActive(config: SpcConfiguration) {
    setTogglingId(config.spc_configuration_id);
    try {
      await updateConfig.mutateAsync({ id: config.spc_configuration_id, request: { is_active: !config.is_active } });
    } finally {
      setTogglingId(null);
    }
  }

  const columns: DataTableColumn<SpcConfiguration>[] = [
    { key: "parameter", header: "Parameter", render: (c) => <ContextCell config={c} /> },
    { key: "chartType", header: "Chart Type", render: (c) => c.chart_type },
    { key: "subgroupSize", header: "Subgroup Size", render: (c) => c.subgroup_size },
    { key: "subgroupMethod", header: "Subgroup Method", render: (c) => c.subgroup_method.replace(/_/g, " ") },
    { key: "minSample", header: "Min. Sample Size", render: (c) => c.minimum_sample_size },
    { key: "rules", header: "Rules", render: (c) => `${c.ruleset.filter((r) => r.enabled).length} of ${c.ruleset.length} enabled` },
    { key: "updated", header: "Updated", render: (c) => formatDateTime(c.updated_at) },
    {
      key: "active",
      header: "Active",
      render: (c) => (
        <button
          type="button"
          onClick={() => handleToggleActive(c)}
          disabled={togglingId === c.spc_configuration_id}
          className={`rounded-full px-2.5 py-1 text-xs font-medium ${c.is_active ? "bg-status-normal-bg text-status-normal" : "bg-surface-100 text-ink-500"}`}
        >
          {c.is_active ? "Active" : "Inactive"}
        </button>
      ),
    },
  ];

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Settings" subtitle="Manage SPC chart, subgrouping, and rule configuration per manufacturing context." />

      {isLoading && <LoadingState message="Loading configurations..." />}
      {error && <ErrorState error={error} title="Unable to load SPC configurations" onRetry={refetch} />}
      {configurations && (
        <DataTable
          columns={columns}
          data={configurations}
          keyExtractor={(c) => c.spc_configuration_id}
          emptyTitle="No SPC configurations found."
          emptyDescription="Configurations are created automatically when you run your first historical upload, or via the API."
        />
      )}
    </div>
  );
}

function ContextCell({ config }: { config: SpcConfiguration }) {
  const labels = useContextLabels({
    organization_id: null,
    plant_id: null,
    machine_id: config.machine_id,
    product_id: config.product_id,
    operation_id: config.operation_id,
    parameter_id: config.parameter_id,
  });
  return <span>{labels.parameterName}</span>;
}
