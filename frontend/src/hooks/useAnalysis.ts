import { useMutation, useQuery } from "@tanstack/react-query";

import { analysisApi, type AnalysisListFilters } from "@/api/analysis.api";
import type { HistoricalAnalysisRequest } from "@/types";

export function useAnalysisDetails(analysisId: string | undefined) {
  return useQuery({
    queryKey: ["analysis", analysisId],
    queryFn: () => analysisApi.getById(analysisId!),
    enabled: Boolean(analysisId),
  });
}

export function useAnalysisList(filters?: AnalysisListFilters) {
  return useQuery({
    queryKey: ["analysis-list", filters],
    queryFn: () => analysisApi.list(filters),
  });
}

export function useRunHistoricalAnalysis() {
  return useMutation({
    mutationFn: (request: HistoricalAnalysisRequest) => analysisApi.runHistorical(request),
  });
}
