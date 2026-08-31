import { apiClient } from "./client";
import type { Alert, AlertAcknowledgeRequest, AlertStatus } from "@/types";

export const alertsApi = {
  list: async (filters?: { status?: AlertStatus; limit?: number }): Promise<Alert[]> => {
    const { data } = await apiClient.get<Alert[]>("/alerts", {
      params: { status: filters?.status, limit: filters?.limit },
    });
    return data;
  },

  acknowledge: async (alertId: string, request: AlertAcknowledgeRequest): Promise<Alert> => {
    const { data } = await apiClient.put<Alert>(`/alerts/${alertId}/acknowledge`, request);
    return data;
  },
};
