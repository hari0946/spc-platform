import { apiClient } from "./client";
import type { SpcConfiguration, SpcConfigurationCreateRequest, SpcConfigurationUpdateRequest } from "@/types";

export const configurationsApi = {
  list: async (): Promise<SpcConfiguration[]> => {
    const { data } = await apiClient.get<SpcConfiguration[]>("/spc/configurations");
    return data;
  },

  getById: async (id: string): Promise<SpcConfiguration> => {
    const { data } = await apiClient.get<SpcConfiguration>(`/spc/configurations/${id}`);
    return data;
  },

  getEffective: async (params: {
    parameterId: string;
    machineId?: string;
    productId?: string;
    operationId?: string;
  }): Promise<SpcConfiguration | null> => {
    const { data } = await apiClient.get<SpcConfiguration | null>("/spc/configurations/effective", {
      params: {
        parameter_id: params.parameterId,
        machine_id: params.machineId,
        product_id: params.productId,
        operation_id: params.operationId,
      },
    });
    return data;
  },

  create: async (request: SpcConfigurationCreateRequest): Promise<SpcConfiguration> => {
    const { data } = await apiClient.post<SpcConfiguration>("/spc/configurations", request);
    return data;
  },

  update: async (id: string, request: SpcConfigurationUpdateRequest): Promise<SpcConfiguration> => {
    const { data } = await apiClient.put<SpcConfiguration>(`/spc/configurations/${id}`, request);
    return data;
  },
};
