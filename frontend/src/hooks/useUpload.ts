import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";

import { uploadsApi } from "@/api/uploads.api";
import type { UploadFormFields } from "@/types";

export const uploadStatusQueryKey = (uploadId: string) => ["upload-status", uploadId] as const;

/** Polls upload status while any non-terminal stage is in progress -- lets
 * a caller show live pipeline progress (BRONZE_LOADING -> ... ->
 * SILVER_COMPLETED) without the caller managing its own polling loop. */
export function useUploadStatus(uploadId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: uploadStatusQueryKey(uploadId ?? ""),
    queryFn: () => uploadsApi.getStatus(uploadId!),
    enabled: Boolean(uploadId) && enabled,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      const terminal = status === "SILVER_COMPLETED" || status === "FAILED";
      return terminal ? false : 1500;
    },
  });
}

export function useUploadHistorical() {
  const queryClient = useQueryClient();
  const [progress, setProgress] = useState(0);

  const mutation = useMutation({
    mutationFn: (fields: UploadFormFields) => {
      setProgress(0);
      return uploadsApi.uploadHistorical(fields, setProgress);
    },
    onSuccess: (upload) => {
      queryClient.setQueryData(uploadStatusQueryKey(upload.upload_id), { ...upload, history: [] });
    },
  });

  return { ...mutation, progress };
}

export function useUploadCurrent() {
  const queryClient = useQueryClient();
  const [progress, setProgress] = useState(0);

  const mutation = useMutation({
    mutationFn: (fields: UploadFormFields) => {
      setProgress(0);
      return uploadsApi.uploadCurrent(fields, setProgress);
    },
    onSuccess: (upload) => {
      queryClient.setQueryData(uploadStatusQueryKey(upload.upload_id), { ...upload, history: [] });
    },
  });

  return { ...mutation, progress };
}
