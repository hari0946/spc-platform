import { useNavigate, useParams } from "react-router-dom";

import { BaselineStatus } from "@/components/baseline/BaselineStatus";
import { CapabilityChart } from "@/components/charts/CapabilityChart";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import { PageHeader } from "@/components/common/PageHeader";
import { useContextLabels } from "@/hooks/useContextLabels";
import { useApproveBaseline, useBaselineDetails } from "@/hooks/useBaseline";
import { formatDateTime } from "@/utils/formatDate";
import { formatCapability, formatInteger, formatMeasurement } from "@/utils/formatNumber";

export function BaselineDetailsPage() {
  const { baselineId } = useParams<{ baselineId: string }>();
  const navigate = useNavigate();
  const { data: baseline, isLoading, error, refetch } = useBaselineDetails(baselineId);
  const approveBaseline = useApproveBaseline();

  const labels = useContextLabels({
    organization_id: baseline?.organization_id ?? null,
    plant_id: baseline?.plant_id ?? null,
    machine_id: baseline?.machine_id ?? null,
    product_id: baseline?.product_id ?? null,
    process_id: baseline?.process_id ?? null,
    operation_id: baseline?.operation_id ?? null,
    parameter_id: baseline?.parameter_id ?? "",
  });

  if (isLoading) return <LoadingState message="Loading baseline..." />;
  if (error || !baseline) return <ErrorState error={error} title="Unable to load baseline" onRetry={refetch} />;

  async function handleApprove() {
    if (!baseline) return;
    const approved = await approveBaseline.mutateAsync({ baselineId: baseline.baseline_id, request: {} });
    navigate(`/baselines/${approved.baseline_id}`, { replace: true });
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Baseline Details"
        subtitle={`${labels.parameterName} · ${labels.machineName}`}
        actions={
          baseline.status === "DRAFT" ? (
            <button type="button" onClick={handleApprove} disabled={approveBaseline.isPending} className="btn btn-primary">
              Approve & Activate
            </button>
          ) : (
            <BaselineStatus status={baseline.status} />
          )
        }
      />

      {baseline.status === "DRAFT" && <BaselineStatus status={baseline.status} />}

      <div className="rounded-lg border border-surface-200 bg-surface-0 p-5">
        <h2 className="mb-3 text-sm font-semibold text-ink-900">Baseline Information</h2>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm sm:grid-cols-4">
          <Field label="Organization" value="—" />
          <Field label="Machine" value={labels.machineName} />
          <Field label="Product" value={labels.productName} />
          <Field label="Process" value={labels.processName} />
          <Field label="Operation" value={labels.operationName} />
          <Field label="Parameter" value={labels.parameterName} />
          <Field label="Unit" value={baseline.unit} />
          <Field label="Chart Type" value={baseline.chart_type.replace("_", "-")} />
          <Field label="Sample Count" value={formatInteger(baseline.sample_count)} />
          <Field label="Created" value={formatDateTime(baseline.created_at)} />
          <Field label="Approved" value={baseline.approved_at ? formatDateTime(baseline.approved_at) : "Not yet approved"} />
          <Field label="Approved By" value={baseline.approved_by ?? "—"} />
        </dl>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="rounded-lg border border-surface-200 bg-surface-0 p-4">
          <h3 className="mb-3 text-sm font-semibold text-ink-900">Statistical Control Limits</h3>
          <Field label="UCL" value={formatMeasurement(baseline.ucl, baseline.unit)} />
          <Field label="Center Line" value={formatMeasurement(baseline.center_line, baseline.unit)} />
          <Field label="LCL" value={formatMeasurement(baseline.lcl, baseline.unit)} />
          <Field label="Within Sigma" value={formatMeasurement(baseline.within_sigma, baseline.unit)} />
          <Field label="Overall Sigma" value={formatMeasurement(baseline.overall_sigma, baseline.unit)} />
        </div>
        <div className="rounded-lg border border-surface-200 bg-surface-0 p-4">
          <h3 className="mb-3 text-sm font-semibold text-ink-900">Engineering Specification</h3>
          <Field label="LSL" value={baseline.lsl != null ? formatMeasurement(baseline.lsl, baseline.unit) : "Not set"} />
          <Field label="Target" value={baseline.target != null ? formatMeasurement(baseline.target, baseline.unit) : "Not set"} />
          <Field label="USL" value={baseline.usl != null ? formatMeasurement(baseline.usl, baseline.unit) : "Not set"} />
        </div>
      </div>

      <div className="rounded-lg border border-surface-200 bg-surface-0 p-4">
        <h3 className="mb-3 text-sm font-semibold text-ink-900">Capability at Baseline</h3>
        <div className="mb-3 grid grid-cols-4 gap-3 text-center text-sm">
          <Field label="Cp" value={formatCapability(baseline.cp)} center />
          <Field label="Cpk" value={formatCapability(baseline.cpk)} center />
          <Field label="Pp" value={formatCapability(baseline.pp)} center />
          <Field label="Ppk" value={formatCapability(baseline.ppk)} center />
        </div>
        <CapabilityChart
          capability={{
            cp: baseline.cp, cpk: baseline.cpk, cpu: null, cpl: null, pp: baseline.pp, ppk: baseline.ppk, ppu: null, ppl: null,
            sigma_level_short_term: null, sigma_level_long_term: null,
          }}
        />
      </div>
    </div>
  );
}

function Field({ label, value, center }: { label: string; value: string; center?: boolean }) {
  return (
    <div className={center ? "text-center" : undefined}>
      <dt className="text-xs text-ink-500">{label}</dt>
      <dd className="font-medium text-ink-900">{value}</dd>
    </div>
  );
}
