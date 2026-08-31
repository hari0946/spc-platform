import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { configurationsApi } from "@/api/configurations.api";
import type { SpcConfigurationCreateRequest, SpcConfigurationUpdateRequest } from "@/types";

export function useConfigurations() {
  return useQuery({ queryKey: ["spc-configurations"], queryFn: configurationsApi.list });
}

export function useConfiguration(id: string | undefined) {
  return useQuery({
    queryKey: ["spc-configurations", id],
    queryFn: () => configurationsApi.getById(id!),
    enabled: Boolean(id),
  });
}

export function useEffectiveConfiguration(params: {
  parameterId: string | undefined;
  machineId?: string;
  productId?: string;
  operationId?: string;
}) {
  return useQuery({
    queryKey: ["spc-configurations", "effective", params],
    queryFn: () =>
      configurationsApi.getEffective({
        parameterId: params.parameterId!,
        machineId: params.machineId,
        productId: params.productId,
        operationId: params.operationId,
      }),
    enabled: Boolean(params.parameterId),
  });
}

export function useCreateConfiguration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: SpcConfigurationCreateRequest) => configurationsApi.create(request),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["spc-configurations"] }),
  });
}

export function useUpdateConfiguration() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, request }: { id: string; request: SpcConfigurationUpdateRequest }) =>
      configurationsApi.update(id, request),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["spc-configurations"] }),
  });
}
