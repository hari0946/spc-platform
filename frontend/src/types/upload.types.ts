import type { UploadStatus, UploadType } from "./api.types";

/** Mirrors app/schemas/upload.py. */
export interface Upload {
  upload_id: string;
  upload_type: UploadType;
  file_name: string;
  status: UploadStatus;
  total_rows: number | null;
  valid_rows: number | null;
  invalid_rows: number | null;
  bronze_loaded: boolean;
  silver_loaded: boolean;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface UploadStatusHistoryEntry {
  status: string;
  message: string | null;
  created_at: string;
}

export interface UploadStatusDetail extends Upload {
  history: UploadStatusHistoryEntry[];
}

/** The multipart form fields accepted by POST /uploads/historical and
 * POST /uploads/current -- every *_id field is an opaque UUID string
 * naming manufacturing context, all optional except `file`. */
export interface UploadFormFields {
  file: File;
  columnMapping?: Record<string, string>;
  organizationId?: string;
  plantId?: string;
  productionLineId?: string;
  machineId?: string;
  productId?: string;
  processId?: string;
  operationId?: string;
  parameterId?: string;
  uploadedBy?: string;
}

/** Default column mapping for the reference client CSV shape used
 * throughout this platform's demo data
 * (DATE_TIME, MACHINE_NAME, PART_NUMBER, PROCESS_STEP, CHARACTERISTIC,
 * MEASURED_VALUE). Real deployments will differ per client export and
 * should let the user configure this instead of relying on the default. */
export const DEFAULT_COLUMN_MAPPING: Record<string, string> = {
  DATE_TIME: "event_timestamp",
  MACHINE_NAME: "machine_code",
  PART_NUMBER: "product_code",
  PROCESS_STEP: "operation_code",
  CHARACTERISTIC: "parameter_name",
  MEASURED_VALUE: "value",
};
