import { apiClient } from "./client";
import type { ManualCheckRequest, ManualCheckResult, ManualCheckSummary } from "@/types";

export interface ManualCheckListFilters {
  machineId?: string;
  productId?: string;
  parameterId?: string;
  limit?: number;
}

export const monitoringApi = {
  runCheck: async (request: ManualCheckRequest): Promise<ManualCheckResult> => {
    const { data } = await apiClient.post<ManualCheckResult>("/manual-check/run", request);
    return data;
  },

  getById: async (manualCheckId: string): Promise<ManualCheckResult> => {
    const { data } = await apiClient.get<ManualCheckResult>(`/manual-check/${manualCheckId}`);
    return data;
  },

  list: async (filters?: ManualCheckListFilters): Promise<ManualCheckSummary[]> => {
    const { data } = await apiClient.get<ManualCheckSummary[]>("/manual-check", {
      params: { machine_id: filters?.machineId, product_id: filters?.productId, parameter_id: filters?.parameterId, limit: filters?.limit },
    });
    return data;
  },
};
