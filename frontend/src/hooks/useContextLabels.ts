import { useMachines, useOperations, useParameters, usePlants, useProcesses, useProducts } from "./useReferenceData";

/** Resolves the human-readable names behind an analysis/manual-check
 * context's raw IDs, by composing the existing list-by-parent reference
 * hooks (using organization_id/plant_id/process_id already present on the
 * context to scope each lookup). Falls back to a short id fragment while
 * loading or if a name can't be resolved -- never blocks rendering. */
export function useContextLabels(context: {
  organization_id: string | null;
  plant_id: string | null;
  machine_id: string | null;
  product_id: string | null;
  process_id?: string | null;
  operation_id: string | null;
  parameter_id: string;
}) {
  const plants = usePlants(context.organization_id ?? undefined);
  const machines = useMachines(context.plant_id ?? undefined);
  const products = useProducts(context.organization_id ?? undefined);
  const processes = useProcesses(context.organization_id ?? undefined);
  const operations = useOperations(context.process_id ?? undefined);
  const parameters = useParameters();

  const fallback = (id: string | null | undefined) => (id ? `#${id.slice(0, 8)}` : "—");

  return {
    plantName: context.plant_id ? plants.data?.find((p) => p.plant_id === context.plant_id)?.name ?? fallback(context.plant_id) : "—",
    machineName: context.machine_id ? machines.data?.find((m) => m.machine_id === context.machine_id)?.name ?? fallback(context.machine_id) : "—",
    productName: context.product_id ? products.data?.find((p) => p.product_id === context.product_id)?.name ?? fallback(context.product_id) : "—",
    processName: context.process_id ? processes.data?.find((p) => p.process_id === context.process_id)?.name ?? fallback(context.process_id) : "—",
    operationName: context.operation_id ? operations.data?.find((o) => o.operation_id === context.operation_id)?.name ?? fallback(context.operation_id) : "—",
    parameterName: parameters.data?.find((p) => p.parameter_id === context.parameter_id)?.name ?? fallback(context.parameter_id),
  };
}
