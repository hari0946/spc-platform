import { apiClient } from "./client";
import type { AnalysisSummary, AnalysisResult, HistoricalAnalysisRequest } from "@/types";

export interface AnalysisListFilters {
  analysisType?: "HISTORICAL" | "MANUAL_CHECK_CURRENT";
  machineId?: string;
  productId?: string;
  parameterId?: string;
  limit?: number;
}

export const analysisApi = {
  runHistorical: async (request: HistoricalAnalysisRequest): Promise<AnalysisResult> => {
    const { data } = await apiClient.post<AnalysisResult>("/analysis/historical", request);
    return data;
  },

  getById: async (analysisId: string): Promise<AnalysisResult> => {
    const { data } = await apiClient.get<AnalysisResult>(`/analysis/${analysisId}`);
    return data;
  },

  list: async (filters?: AnalysisListFilters): Promise<AnalysisSummary[]> => {
    const { data } = await apiClient.get<AnalysisSummary[]>("/analysis", {
      params: {
        analysis_type: filters?.analysisType,
        machine_id: filters?.machineId,
        product_id: filters?.productId,
        parameter_id: filters?.parameterId,
        limit: filters?.limit,
      },
    });
    return data;
  },
};
