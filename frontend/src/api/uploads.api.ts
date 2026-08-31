import { apiClient } from "./client";
import type { Upload, UploadFormFields, UploadStatusDetail, UploadType } from "@/types";

function buildFormData(fields: UploadFormFields): FormData {
  const form = new FormData();
  form.append("file", fields.file);
  if (fields.columnMapping) form.append("column_mapping", JSON.stringify(fields.columnMapping));
  if (fields.organizationId) form.append("organization_id", fields.organizationId);
  if (fields.plantId) form.append("plant_id", fields.plantId);
  if (fields.productionLineId) form.append("production_line_id", fields.productionLineId);
  if (fields.machineId) form.append("machine_id", fields.machineId);
  if (fields.productId) form.append("product_id", fields.productId);
  if (fields.processId) form.append("process_id", fields.processId);
  if (fields.operationId) form.append("operation_id", fields.operationId);
  if (fields.parameterId) form.append("parameter_id", fields.parameterId);
  if (fields.uploadedBy) form.append("uploaded_by", fields.uploadedBy);
  return form;
}

async function uploadCsv(
  uploadType: UploadType,
  fields: UploadFormFields,
  onProgress?: (percent: number) => void,
): Promise<Upload> {
  const path = uploadType === "HISTORICAL" ? "/uploads/historical" : "/uploads/current";
  const { data } = await apiClient.post<Upload>(path, buildFormData(fields), {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (event) => {
      if (onProgress && event.total) {
        onProgress(Math.round((event.loaded / event.total) * 100));
      }
    },
  });
  return data;
}

export const uploadsApi = {
  uploadHistorical: (fields: UploadFormFields, onProgress?: (percent: number) => void) =>
    uploadCsv("HISTORICAL", fields, onProgress),

  uploadCurrent: (fields: UploadFormFields, onProgress?: (percent: number) => void) =>
    uploadCsv("CURRENT", fields, onProgress),

  getStatus: async (uploadId: string): Promise<UploadStatusDetail> => {
    const { data } = await apiClient.get<UploadStatusDetail>(`/uploads/${uploadId}/status`);
    return data;
  },
};
