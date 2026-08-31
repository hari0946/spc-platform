import { FileSpreadsheet, UploadCloud, X } from "lucide-react";
import { type DragEvent, useRef, useState } from "react";

import { formatInteger } from "@/utils/formatNumber";

interface CsvUploadProps {
  file: File | null;
  onFileSelected: (file: File | null) => void;
  disabled?: boolean;
  /** Total rows, once known from the backend upload response -- shown
   * alongside file metadata once available. */
  totalRows?: number | null;
}

const MAX_FILE_SIZE_BYTES = 200 * 1024 * 1024; // matches backend UPLOAD_MAX_FILE_SIZE_MB default

/** Drag-and-drop + click-to-browse CSV picker. Only ever hands a raw File
 * back to the caller -- upload/validation itself happens via the backend. */
export function CsvUpload({ file, onFileSelected, disabled, totalRows }: CsvUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  function validateAndSelect(candidate: File | undefined) {
    if (!candidate) {
      setValidationError("Please select a CSV file.");
      return;
    }
    if (!candidate.name.toLowerCase().endsWith(".csv")) {
      setValidationError("Invalid file format. Please upload a .csv file.");
      return;
    }
    if (candidate.size === 0) {
      setValidationError("The selected file is empty.");
      return;
    }
    if (candidate.size > MAX_FILE_SIZE_BYTES) {
      setValidationError("This file exceeds the maximum allowed upload size (200 MB).");
      return;
    }
    setValidationError(null);
    onFileSelected(candidate);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);
    if (disabled) return;
    validateAndSelect(event.dataTransfer.files[0]);
  }

  if (file) {
    return (
      <div className="flex items-center justify-between rounded-lg border border-surface-200 bg-surface-50 px-4 py-3">
        <div className="flex items-center gap-3">
          <FileSpreadsheet className="h-8 w-8 shrink-0 text-brand-600" aria-hidden="true" />
          <div className="text-sm">
            <p className="font-medium text-ink-900">{file.name}</p>
            <p className="text-ink-500">
              {formatFileSize(file.size)}
              {totalRows != null && ` · ${formatInteger(totalRows)} rows`}
            </p>
          </div>
        </div>
        {!disabled && (
          <button
            type="button"
            onClick={() => onFileSelected(null)}
            className="rounded p-1.5 text-ink-500 hover:bg-surface-100 hover:text-ink-900"
            aria-label="Remove selected file"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
    );
  }

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        onClick={() => !disabled && inputRef.current?.click()}
        onKeyDown={(e) => {
          if ((e.key === "Enter" || e.key === " ") && !disabled) inputRef.current?.click();
        }}
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed px-6 py-10 text-center transition-colors ${
          isDragging ? "border-brand-600 bg-brand-50" : "border-surface-300 bg-surface-50"
        } ${disabled ? "cursor-not-allowed opacity-60" : "hover:border-brand-600 hover:bg-brand-50"}`}
      >
        <UploadCloud className="h-8 w-8 text-ink-400" aria-hidden="true" />
        <p className="text-sm font-medium text-ink-700">Drag and drop your CSV file here, or click to browse</p>
        <p className="text-xs text-ink-500">CSV files only, up to 200 MB</p>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          className="sr-only"
          disabled={disabled}
          onChange={(e) => validateAndSelect(e.target.files?.[0])}
        />
      </div>
      {validationError && <p className="mt-2 text-sm text-status-critical">{validationError}</p>}
    </div>
  );
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}
