import { CheckCircle2, XCircle } from "lucide-react";

import { StepProgress } from "@/components/common/LoadingState";
import type { UploadStatus } from "@/types";

const PIPELINE_STAGES: { status: UploadStatus; label: string }[] = [
  { status: "UPLOADED", label: "File received" },
  { status: "BRONZE_LOADING", label: "Storing raw data (Bronze)" },
  { status: "BRONZE_COMPLETED", label: "Raw data stored" },
  { status: "VALIDATING", label: "Validating measurement data..." },
  { status: "VALIDATION_COMPLETED", label: "Validation complete" },
  { status: "SILVER_LOADING", label: "Storing cleaned data (Silver)" },
  { status: "SILVER_COMPLETED", label: "Ready for analysis" },
];

interface UploadProgressProps {
  status: UploadStatus;
  errorMessage?: string | null;
}

/** Shows which pipeline stage is active, driven by the backend's real
 * upload status -- never a single undifferentiated spinner. */
export function UploadProgress({ status, errorMessage }: UploadProgressProps) {
  if (status === "FAILED") {
    return (
      <div className="flex flex-col items-center gap-2 py-10 text-center" role="alert">
        <XCircle className="h-8 w-8 text-status-critical" aria-hidden="true" />
        <p className="font-medium text-ink-900">Upload failed</p>
        <p className="max-w-sm text-sm text-ink-500">{errorMessage ?? "Unable to process this file."}</p>
      </div>
    );
  }

  if (status === "SILVER_COMPLETED") {
    return (
      <div className="flex flex-col items-center gap-2 py-10 text-center">
        <CheckCircle2 className="h-8 w-8 text-status-normal" aria-hidden="true" />
        <p className="font-medium text-ink-900">Upload processed successfully</p>
      </div>
    );
  }

  const currentIndex = PIPELINE_STAGES.findIndex((s) => s.status === status);
  return <StepProgress steps={PIPELINE_STAGES.map((s) => s.label)} currentStepIndex={Math.max(currentIndex, 0)} />;
}
