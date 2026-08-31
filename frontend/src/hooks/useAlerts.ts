import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { alertsApi } from "@/api/alerts.api";
import type { AlertAcknowledgeRequest, AlertStatus } from "@/types";

export function useAlerts(filters?: { status?: AlertStatus; limit?: number }) {
  return useQuery({
    queryKey: ["alerts", filters],
    queryFn: () => alertsApi.list(filters),
    refetchInterval: 30_000,
  });
}

export function useAcknowledgeAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ alertId, request }: { alertId: string; request: AlertAcknowledgeRequest }) =>
      alertsApi.acknowledge(alertId, request),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alerts"] }),
  });
}
