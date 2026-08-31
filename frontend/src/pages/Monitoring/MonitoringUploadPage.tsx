import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { StepProgress } from "@/components/common/LoadingState";
import { PageHeader } from "@/components/common/PageHeader";
import { BaselineStatus } from "@/components/baseline/BaselineStatus";
import { ContextSelector, EMPTY_SELECTION, type ContextSelection } from "@/components/upload/ContextSelector";
import { CsvUpload } from "@/components/upload/CsvUpload";
import { UploadProgress } from "@/components/upload/UploadProgress";
import { UploadValidation } from "@/components/upload/UploadValidation";
import { useActiveBaseline } from "@/hooks/useBaseline";
import { useRunMonitoringAnalysis } from "@/hooks/useMonitoring";
import { useUploadCurrent, useUploadStatus } from "@/hooks/useUpload";
import { DEFAULT_COLUMN_MAPPING } from "@/types";
import { formatDateOnly } from "@/utils/formatDate";
import { formatMeasurement } from "@/utils/formatNumber";

type Stage = "form" | "uploading" | "processing" | "analyzing" | "error";

export function MonitoringUploadPage() {
  const navigate = useNavigate();
  const [context, setContext] = useState<ContextSelection>(EMPTY_SELECTION);
  const [file, setFile] = useState<File | null>(null);
  const [stage, setStage] = useState<Stage>("form");
  const [uploadId, setUploadId] = useState<string | undefined>();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const isContextReady = Boolean(context.organizationId && context.plantId && context.parameterId);
  const activeBaseline = useActiveBaseline({
    parameterId: context.parameterId || undefined,
    machineId: context.machineId || undefined,
    productId: context.productId || undefined,
    operationId: context.operationId || undefined,
  });

  const uploadMutation = useUploadCurrent();
  const checkMutation = useRunMonitoringAnalysis();
  const uploadStatus = useUploadStatus(uploadId, stage === "processing");

  const canSubmit = isContextReady && Boolean(activeBaseline.data) && file != null && stage === "form";

  async function handleSubmit() {
    if (!file) return;
    setErrorMessage(null);
    try {
      setStage("uploading");
      const upload = await uploadMutation.mutateAsync({
        file,
        columnMapping: DEFAULT_COLUMN_MAPPING,
        organizationId: context.organizationId,
        plantId: context.plantId,
        machineId: context.machineId || undefined,
        productId: context.productId || undefined,
        processId: context.processId || undefined,
        operationId: context.operationId || undefined,
        parameterId: context.parameterId || undefined,
      });
      setUploadId(upload.upload_id);
      setStage(upload.status === "SILVER_COMPLETED" ? "analyzing" : "processing");
      if (upload.status === "SILVER_COMPLETED") await runCheck(upload.upload_id);
    } catch (err) {
      setStage("error");
      setErrorMessage(err instanceof Error ? err.message : "Unable to process this file.");
    }
  }

  async function runCheck(finalUploadId: string) {
    setStage("analyzing");
    try {
      const result = await checkMutation.mutateAsync({
        upload_id: finalUploadId,
        parameter_id: context.parameterId,
        machine_id: context.machineId || undefined,
        product_id: context.productId || undefined,
        operation_id: context.operationId || undefined,
      });
      navigate(`/monitoring/result/${result.manual_check_id}`);
    } catch (err) {
      setStage("error");
      setErrorMessage(err instanceof Error ? err.message : "Monitoring analysis failed.");
    }
  }

  useEffect(() => {
    if (stage !== "processing" || !uploadId || !uploadStatus.data) return;
    if (uploadStatus.data.status === "SILVER_COMPLETED") {
      void runCheck(uploadId);
    } else if (uploadStatus.data.status === "FAILED") {
      setStage("error");
      setErrorMessage(uploadStatus.data.error_message ?? "Unable to process this file.");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage, uploadId, uploadStatus.data?.status]);

  function handleCancel() {
    setStage("form");
    setFile(null);
    setUploadId(undefined);
    setErrorMessage(null);
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Current Data SPC Analysis"
        subtitle="Upload a new measurement CSV and compare current process behavior with the active historical baseline. This is not real-time monitoring."
      />

      {stage === "form" && (
        <div className="flex flex-col gap-6">
          <section className="rounded-lg border border-surface-200 bg-surface-0 p-5">
            <h2 className="mb-4 text-sm font-semibold text-ink-900">Manufacturing Context</h2>
            <ContextSelector value={context} onChange={setContext} />
          </section>

          {isContextReady && (
            <section className="rounded-lg border border-surface-200 bg-surface-0 p-5">
              <h2 className="mb-4 text-sm font-semibold text-ink-900">Active Baseline</h2>
              {activeBaseline.isLoading && <p className="text-sm text-ink-500">Looking up active baseline...</p>}
              {!activeBaseline.isLoading && !activeBaseline.data && (
                <EmptyState
                  title="No active baseline found."
                  description="Run and approve a historical analysis for this context before performing a manual check."
                />
              )}
              {activeBaseline.data && (
                <div className="flex flex-col gap-3">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs text-ink-500">Baseline ID: {activeBaseline.data.baseline_id.slice(0, 8)}</span>
                    <BaselineStatus status={activeBaseline.data.status} />
                  </div>
                  <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
                    <InfoTile label="Baseline Date" value={formatDateOnly(activeBaseline.data.created_at)} />
                    <InfoTile label="Chart Type" value={activeBaseline.data.chart_type.replace("_", "-")} />
                    <InfoTile label="UCL" value={formatMeasurement(activeBaseline.data.ucl, activeBaseline.data.unit)} />
                    <InfoTile label="LCL" value={formatMeasurement(activeBaseline.data.lcl, activeBaseline.data.unit)} />
                  </div>
                </div>
              )}
            </section>
          )}

          <section className="rounded-lg border border-surface-200 bg-surface-0 p-5">
            <h2 className="mb-4 text-sm font-semibold text-ink-900">Current Data Upload</h2>
            <CsvUpload file={file} onFileSelected={setFile} disabled={!activeBaseline.data} />
          </section>

          <div className="flex justify-end gap-3">
            <button type="button" onClick={handleCancel} className="btn btn-secondary">
              Cancel
            </button>
            <button type="button" onClick={handleSubmit} disabled={!canSubmit} className="btn btn-primary">
              Run Monitoring Analysis
            </button>
          </div>
        </div>
      )}

      {stage === "uploading" && <StepProgress steps={["Uploading CSV...", "Validating measurement data...", "Comparing with baseline..."]} currentStepIndex={0} />}

      {stage === "processing" && uploadStatus.data && (
        <div className="flex flex-col gap-4">
          <UploadProgress status={uploadStatus.data.status} errorMessage={uploadStatus.data.error_message} />
          {uploadStatus.data.total_rows != null && <UploadValidation upload={uploadStatus.data} />}
        </div>
      )}

      {stage === "analyzing" && <StepProgress steps={["Upload processed", "Running current SPC analysis...", "Comparing with baseline..."]} currentStepIndex={1} />}

      {stage === "error" && <ErrorState error={errorMessage ?? "Unable to process this file."} title="Monitoring analysis failed" onRetry={handleCancel} />}
    </div>
  );
}

function InfoTile({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-ink-500">{label}</p>
      <p className="font-medium text-ink-900">{value}</p>
    </div>
  );
}
