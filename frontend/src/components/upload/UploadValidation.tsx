import { AlertTriangle, CheckCircle2 } from "lucide-react";

import type { Upload } from "@/types";
import { formatInteger } from "@/utils/formatNumber";

interface UploadValidationProps {
  upload: Upload;
}

/** Row-level validation summary: total/valid/invalid counts, exactly as
 * the backend reports them -- never a frontend re-count. */
export function UploadValidation({ upload }: UploadValidationProps) {
  if (upload.total_rows == null) return null;

  const invalid = upload.invalid_rows ?? 0;
  const valid = upload.valid_rows ?? 0;

  return (
    <div className="grid grid-cols-3 gap-3">
      <SummaryTile label="Total Rows" value={formatInteger(upload.total_rows)} />
      <SummaryTile label="Valid Rows" value={formatInteger(valid)} tone="normal" />
      <SummaryTile label="Invalid Rows" value={formatInteger(invalid)} tone={invalid > 0 ? "warning" : "normal"} />

      {invalid > 0 && (
        <p className="col-span-3 flex items-start gap-2 rounded-md bg-status-warning-bg px-3 py-2 text-sm text-status-warning">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" aria-hidden="true" />
          {invalid} row{invalid === 1 ? "" : "s"} failed validation (missing values, invalid timestamps, unresolved
          machine/product/parameter context, or duplicates) and were excluded from SPC analysis. Valid rows were
          still processed.
        </p>
      )}
      {invalid === 0 && (
        <p className="col-span-3 flex items-center gap-2 rounded-md bg-status-normal-bg px-3 py-2 text-sm text-status-normal">
          <CheckCircle2 className="h-4 w-4 shrink-0" aria-hidden="true" />
          All rows passed validation.
        </p>
      )}
    </div>
  );
}

function SummaryTile({ label, value, tone = "neutral" }: { label: string; value: string; tone?: "neutral" | "normal" | "warning" }) {
  const toneClass = tone === "normal" ? "text-status-normal" : tone === "warning" ? "text-status-warning" : "text-ink-900";
  return (
    <div className="rounded-md border border-surface-200 px-3 py-2 text-center">
      <p className="text-xs text-ink-500">{label}</p>
      <p className={`text-lg font-semibold ${toneClass}`}>{value}</p>
    </div>
  );
}
