import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { ErrorState } from "@/components/common/ErrorState";
import { PageHeader } from "@/components/common/PageHeader";
import { StepProgress } from "@/components/common/LoadingState";
import { ContextSelector, EMPTY_SELECTION, type ContextSelection } from "@/components/upload/ContextSelector";
import { CsvUpload } from "@/components/upload/CsvUpload";
import { UploadProgress } from "@/components/upload/UploadProgress";
import { UploadValidation } from "@/components/upload/UploadValidation";
import { useRunHistoricalAnalysis } from "@/hooks/useAnalysis";
import { useEffectiveConfiguration, useCreateConfiguration } from "@/hooks/useConfigurations";
import { useEffectiveSpecification, useCreateSpecification } from "@/hooks/useReferenceData";
import { useUploadHistorical, useUploadStatus } from "@/hooks/useUpload";
import type { ConfiguredChartType, SubgroupMethod } from "@/types";
import { DEFAULT_COLUMN_MAPPING } from "@/types";

type Stage = "form" | "uploading" | "processing" | "analyzing" | "error";

const SUBGROUP_METHODS: { value: SubgroupMethod; label: string }[] = [
  { value: "CONSECUTIVE", label: "Consecutive (time-gap aware)" },
  { value: "FIXED_SIZE", label: "Fixed Size" },
  { value: "EXISTING_ID", label: "Existing Subgroup ID (from source data)" },
  { value: "TIME_WINDOW", label: "Time Window" },
];

export function HistoricalUploadPage() {
  const navigate = useNavigate();

  const [context, setContext] = useState<ContextSelection>(EMPTY_SELECTION);
  const [file, setFile] = useState<File | null>(null);
  const [lsl, setLsl] = useState("");
  const [usl, setUsl] = useState("");
  const [target, setTarget] = useState("");
  const [chartType, setChartType] = useState<ConfiguredChartType>("AUTO");
  const [subgroupSize, setSubgroupSize] = useState(5);
  const [subgroupMethod, setSubgroupMethod] = useState<SubgroupMethod>("CONSECUTIVE");
  const [stage, setStage] = useState<Stage>("form");
  const [uploadId, setUploadId] = useState<string | undefined>();
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const effectiveSpec = useEffectiveSpecification({
    parameterId: context.parameterId || undefined,
    machineId: context.machineId || undefined,
    productId: context.productId || undefined,
    operationId: context.operationId || undefined,
  });
  const effectiveConfig = useEffectiveConfiguration({
    parameterId: context.parameterId || undefined,
    machineId: context.machineId || undefined,
    productId: context.productId || undefined,
    operationId: context.operationId || undefined,
  });

  const uploadMutation = useUploadHistorical();
  const createSpecMutation = useCreateSpecification();
  const createConfigMutation = useCreateConfiguration();
  const analysisMutation = useRunHistoricalAnalysis();
  const uploadStatus = useUploadStatus(uploadId, stage === "processing");

  const isContextReady = Boolean(context.organizationId && context.plantId && context.parameterId);
  const canSubmit = isContextReady && file != null && stage === "form";

  async function handleSubmit() {
    if (!file) return;
    setErrorMessage(null);

    try {
      // Ensure a specification exists for this context if the user provided limits.
      if ((lsl || usl) && !effectiveSpec.data) {
        await createSpecMutation.mutateAsync({
          parameterId: context.parameterId,
          lsl: lsl ? Number(lsl) : undefined,
          usl: usl ? Number(usl) : undefined,
          target: target ? Number(target) : undefined,
          machineId: context.machineId || undefined,
          productId: context.productId || undefined,
          operationId: context.operationId || undefined,
        });
      }

      // Ensure an SPC configuration exists for this context.
      if (!effectiveConfig.data) {
        await createConfigMutation.mutateAsync({
          parameter_id: context.parameterId,
          machine_id: context.machineId || undefined,
          product_id: context.productId || undefined,
          operation_id: context.operationId || undefined,
          chart_type: chartType,
          subgroup_size: subgroupSize,
          subgroup_method: subgroupMethod,
        });
      }

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

      if (upload.status === "SILVER_COMPLETED") {
        await runAnalysis(upload.upload_id);
      }
    } catch (err) {
      setStage("error");
      setErrorMessage(err instanceof Error ? err.message : "Unable to process this file.");
    }
  }

  async function runAnalysis(finalUploadId: string) {
    setStage("analyzing");
    try {
      const analysis = await analysisMutation.mutateAsync({
        upload_id: finalUploadId,
        parameter_id: context.parameterId,
        machine_id: context.machineId || undefined,
        product_id: context.productId || undefined,
        operation_id: context.operationId || undefined,
      });
      navigate(`/historical/analysis/${analysis.analysis_id}`);
    } catch (err) {
      setStage("error");
      setErrorMessage(err instanceof Error ? err.message : "Analysis failed.");
    }
  }

  // Once upload processing reaches a terminal state while polling, either
  // kick off analysis or surface the failure -- done as an effect (not
  // during render) since both branches trigger further state updates.
  useEffect(() => {
    if (stage !== "processing" || !uploadId || !uploadStatus.data) return;
    if (uploadStatus.data.status === "SILVER_COMPLETED") {
      void runAnalysis(uploadId);
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
        title="Historical Data Upload"
        subtitle="Upload historical measurement data to analyze process behavior and create a baseline."
      />

      {stage === "form" && (
        <div className="flex flex-col gap-6">
          <section className="rounded-lg border border-surface-200 bg-surface-0 p-5">
            <h2 className="mb-4 text-sm font-semibold text-ink-900">Manufacturing Context</h2>
            <ContextSelector value={context} onChange={setContext} />
          </section>

          <section className="rounded-lg border border-surface-200 bg-surface-0 p-5">
            <h2 className="mb-1 text-sm font-semibold text-ink-900">Specification Limits</h2>
            <p className="mb-4 text-xs text-ink-500">
              {effectiveSpec.data
                ? `Using existing specification for this context (LSL ${effectiveSpec.data.lsl ?? "—"}, USL ${effectiveSpec.data.usl ?? "—"}).`
                : "Optional. Enter limits to enable Cp/Cpk/Pp/Ppk calculation for this context."}
            </p>
            <div className="grid grid-cols-3 gap-4">
              <NumberField label="LSL" value={lsl} onChange={setLsl} disabled={Boolean(effectiveSpec.data)} />
              <NumberField label="Target (optional)" value={target} onChange={setTarget} disabled={Boolean(effectiveSpec.data)} />
              <NumberField label="USL" value={usl} onChange={setUsl} disabled={Boolean(effectiveSpec.data)} />
            </div>
          </section>

          <section className="rounded-lg border border-surface-200 bg-surface-0 p-5">
            <h2 className="mb-1 text-sm font-semibold text-ink-900">SPC Configuration</h2>
            <p className="mb-4 text-xs text-ink-500">
              {effectiveConfig.data
                ? `Using existing configuration for this context (${effectiveConfig.data.chart_type}, subgroup size ${effectiveConfig.data.subgroup_size}).`
                : "Choose Auto Detect to let the backend engine recommend a chart type based on subgroup size."}
            </p>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <label className="flex flex-col gap-1.5 text-sm">
                <span className="font-medium text-ink-700">Chart Type</span>
                <select className="select" value={chartType} disabled={Boolean(effectiveConfig.data)} onChange={(e) => setChartType(e.target.value as ConfiguredChartType)}>
                  <option value="AUTO">Auto Detect</option>
                  <option value="IMR">I-MR</option>
                  <option value="XBAR_R">X-bar R</option>
                  <option value="XBAR_S">X-bar S</option>
                </select>
              </label>
              <label className="flex flex-col gap-1.5 text-sm">
                <span className="font-medium text-ink-700">Subgroup Size</span>
                <input
                  type="number"
                  min={1}
                  className="input"
                  value={subgroupSize}
                  disabled={Boolean(effectiveConfig.data)}
                  onChange={(e) => setSubgroupSize(Number(e.target.value) || 1)}
                />
              </label>
              <label className="flex flex-col gap-1.5 text-sm">
                <span className="font-medium text-ink-700">Subgroup Method</span>
                <select className="select" value={subgroupMethod} disabled={Boolean(effectiveConfig.data)} onChange={(e) => setSubgroupMethod(e.target.value as SubgroupMethod)}>
                  {SUBGROUP_METHODS.map((m) => (
                    <option key={m.value} value={m.value}>
                      {m.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </section>

          <section className="rounded-lg border border-surface-200 bg-surface-0 p-5">
            <h2 className="mb-4 text-sm font-semibold text-ink-900">Historical Measurement Data</h2>
            <CsvUpload file={file} onFileSelected={setFile} />
          </section>

          <div className="flex justify-end gap-3">
            <button type="button" onClick={handleCancel} className="btn btn-secondary">
              Cancel
            </button>
            <button type="button" onClick={handleSubmit} disabled={!canSubmit} className="btn btn-primary">
              Run Historical Analysis
            </button>
          </div>
        </div>
      )}

      {stage === "uploading" && <StepProgress steps={["Uploading CSV...", "Validating measurement data...", "Running SPC analysis..."]} currentStepIndex={0} />}

      {stage === "processing" && uploadStatus.data && (
        <div className="flex flex-col gap-4">
          <UploadProgress status={uploadStatus.data.status} errorMessage={uploadStatus.data.error_message} />
          {uploadStatus.data.total_rows != null && <UploadValidation upload={uploadStatus.data} />}
        </div>
      )}

      {stage === "analyzing" && <StepProgress steps={["Upload processed", "Running SPC analysis...", "Generating control charts..."]} currentStepIndex={1} />}

      {stage === "error" && (
        <ErrorState
          error={errorMessage ?? "Unable to process this file."}
          title="Upload failed"
          onRetry={handleCancel}
        />
      )}
    </div>
  );
}

function NumberField({
  label,
  value,
  onChange,
  disabled,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  disabled?: boolean;
}) {
  return (
    <label className="flex flex-col gap-1.5 text-sm">
      <span className="font-medium text-ink-700">{label}</span>
      <input type="number" step="any" className="input" value={value} disabled={disabled} onChange={(e) => onChange(e.target.value)} />
    </label>
  );
}
