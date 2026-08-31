import { apiClient } from "./client";
import type { Finding, Severity } from "@/types";

export const findingsApi = {
  list: async (filters?: { severity?: Severity; findingType?: string; limit?: number }): Promise<Finding[]> => {
    const { data } = await apiClient.get<Finding[]>("/findings", {
      params: { severity: filters?.severity, finding_type: filters?.findingType, limit: filters?.limit },
    });
    return data;
  },
};
