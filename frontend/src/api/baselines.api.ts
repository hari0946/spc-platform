import { apiClient } from "./client";
import type { Baseline, BaselineApproveRequest, BaselineCreateRequest, BaselineStatus } from "@/types";

export const baselinesApi = {
  create: async (request: BaselineCreateRequest): Promise<Baseline> => {
    const { data } = await apiClient.post<Baseline>("/baselines/create", request);
    return data;
  },

  approve: async (baselineId: string, request: BaselineApproveRequest): Promise<Baseline> => {
    const { data } = await apiClient.post<Baseline>(`/baselines/${baselineId}/approve`, request);
    return data;
  },

  list: async (filters?: {
    parameterId?: string;
    machineId?: string;
    productId?: string;
    operationId?: string;
    status?: BaselineStatus;
  }): Promise<Baseline[]> => {
    const { data } = await apiClient.get<Baseline[]>("/baselines", {
      params: {
        parameter_id: filters?.parameterId,
        machine_id: filters?.machineId,
        product_id: filters?.productId,
        operation_id: filters?.operationId,
        status: filters?.status,
      },
    });
    return data;
  },

  getById: async (baselineId: string): Promise<Baseline> => {
    const { data } = await apiClient.get<Baseline>(`/baselines/${baselineId}`);
    return data;
  },
};
