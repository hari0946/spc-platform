import { useMutation, useQuery } from "@tanstack/react-query";

import { monitoringApi, type ManualCheckListFilters } from "@/api/monitoring.api";
import type { ManualCheckRequest } from "@/types";

export function useManualCheckDetails(manualCheckId: string | undefined) {
  return useQuery({
    queryKey: ["manual-check", manualCheckId],
    queryFn: () => monitoringApi.getById(manualCheckId!),
    enabled: Boolean(manualCheckId),
  });
}

export function useManualCheckList(filters?: ManualCheckListFilters) {
  return useQuery({
    queryKey: ["manual-check-list", filters],
    queryFn: () => monitoringApi.list(filters),
  });
}

export function useRunMonitoringAnalysis() {
  return useMutation({
    mutationFn: (request: ManualCheckRequest) => monitoringApi.runCheck(request),
  });
}
