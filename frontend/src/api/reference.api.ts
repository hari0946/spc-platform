import { apiClient } from "./client";
import type { Machine, Operation, Organization, Parameter, Plant, Process, Product, SpecificationRef } from "@/types";

export const referenceApi = {
  listOrganizations: async (): Promise<Organization[]> => {
    const { data } = await apiClient.get<Organization[]>("/reference/organizations");
    return data;
  },
  listPlants: async (organizationId: string): Promise<Plant[]> => {
    const { data } = await apiClient.get<Plant[]>("/reference/plants", { params: { organization_id: organizationId } });
    return data;
  },
  listMachines: async (plantId: string): Promise<Machine[]> => {
    const { data } = await apiClient.get<Machine[]>("/reference/machines", { params: { plant_id: plantId } });
    return data;
  },
  listProducts: async (organizationId: string): Promise<Product[]> => {
    const { data } = await apiClient.get<Product[]>("/reference/products", { params: { organization_id: organizationId } });
    return data;
  },
  listProcesses: async (organizationId: string): Promise<Process[]> => {
    const { data } = await apiClient.get<Process[]>("/reference/processes", { params: { organization_id: organizationId } });
    return data;
  },
  listOperations: async (processId: string): Promise<Operation[]> => {
    const { data } = await apiClient.get<Operation[]>("/reference/operations", { params: { process_id: processId } });
    return data;
  },
  listParameters: async (): Promise<Parameter[]> => {
    const { data } = await apiClient.get<Parameter[]>("/reference/parameters");
    return data;
  },
  getEffectiveSpecification: async (params: {
    parameterId: string;
    machineId?: string;
    productId?: string;
    operationId?: string;
  }): Promise<SpecificationRef | null> => {
    const { data } = await apiClient.get<SpecificationRef | null>("/reference/specification", {
      params: {
        parameter_id: params.parameterId,
        machine_id: params.machineId,
        product_id: params.productId,
        operation_id: params.operationId,
      },
    });
    return data;
  },

  createSpecification: async (request: {
    parameterId: string;
    lsl?: number;
    usl?: number;
    target?: number;
    machineId?: string;
    productId?: string;
    operationId?: string;
    createdBy?: string;
  }): Promise<SpecificationRef> => {
    const { data } = await apiClient.post<SpecificationRef>("/reference/specifications", {
      parameter_id: request.parameterId,
      lsl: request.lsl,
      usl: request.usl,
      target: request.target,
      machine_id: request.machineId,
      product_id: request.productId,
      operation_id: request.operationId,
      created_by: request.createdBy,
    });
    return data;
  },
};
