import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { baselinesApi } from "@/api/baselines.api";
import type { BaselineApproveRequest, BaselineCreateRequest, BaselineStatus } from "@/types";

export function useBaselines(filters?: { parameterId?: string; machineId?: string; productId?: string; operationId?: string; status?: BaselineStatus }) {
  return useQuery({
    queryKey: ["baselines", filters],
    queryFn: () => baselinesApi.list(filters),
  });
}

export function useActiveBaseline(params: { parameterId: string | undefined; machineId?: string; productId?: string; operationId?: string }) {
  return useQuery({
    queryKey: ["baselines", { ...params, status: "ACTIVE" as BaselineStatus }],
    queryFn: () =>
      baselinesApi.list({
        parameterId: params.parameterId,
        machineId: params.machineId,
        productId: params.productId,
        operationId: params.operationId,
        status: "ACTIVE",
      }),
    enabled: Boolean(params.parameterId),
    select: (baselines) => baselines[0] ?? null,
  });
}

export function useBaselineDetails(baselineId: string | undefined) {
  return useQuery({
    queryKey: ["baseline", baselineId],
    queryFn: () => baselinesApi.getById(baselineId!),
    enabled: Boolean(baselineId),
  });
}

export function useCreateBaseline() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: BaselineCreateRequest) => baselinesApi.create(request),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["baselines"] }),
  });
}

export function useApproveBaseline() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ baselineId, request }: { baselineId: string; request: BaselineApproveRequest }) =>
      baselinesApi.approve(baselineId, request),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["baselines"] }),
  });
}
