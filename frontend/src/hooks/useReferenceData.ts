import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { referenceApi } from "@/api/reference.api";

export function useOrganizations() {
  return useQuery({ queryKey: ["reference", "organizations"], queryFn: referenceApi.listOrganizations });
}

export function usePlants(organizationId: string | undefined) {
  return useQuery({
    queryKey: ["reference", "plants", organizationId],
    queryFn: () => referenceApi.listPlants(organizationId!),
    enabled: Boolean(organizationId),
  });
}

export function useMachines(plantId: string | undefined) {
  return useQuery({
    queryKey: ["reference", "machines", plantId],
    queryFn: () => referenceApi.listMachines(plantId!),
    enabled: Boolean(plantId),
  });
}

export function useProducts(organizationId: string | undefined) {
  return useQuery({
    queryKey: ["reference", "products", organizationId],
    queryFn: () => referenceApi.listProducts(organizationId!),
    enabled: Boolean(organizationId),
  });
}

export function useProcesses(organizationId: string | undefined) {
  return useQuery({
    queryKey: ["reference", "processes", organizationId],
    queryFn: () => referenceApi.listProcesses(organizationId!),
    enabled: Boolean(organizationId),
  });
}

export function useOperations(processId: string | undefined) {
  return useQuery({
    queryKey: ["reference", "operations", processId],
    queryFn: () => referenceApi.listOperations(processId!),
    enabled: Boolean(processId),
  });
}

export function useParameters() {
  return useQuery({ queryKey: ["reference", "parameters"], queryFn: referenceApi.listParameters });
}

export function useEffectiveSpecification(params: {
  parameterId: string | undefined;
  machineId?: string;
  productId?: string;
  operationId?: string;
}) {
  return useQuery({
    queryKey: ["reference", "specification", params],
    queryFn: () =>
      referenceApi.getEffectiveSpecification({
        parameterId: params.parameterId!,
        machineId: params.machineId,
        productId: params.productId,
        operationId: params.operationId,
      }),
    enabled: Boolean(params.parameterId),
  });
}

export function useCreateSpecification() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: referenceApi.createSpecification,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["reference", "specification"] }),
  });
}
