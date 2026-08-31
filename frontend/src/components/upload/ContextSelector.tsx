import { useEffect } from "react";
import type { ReactNode } from "react";

import {
  useMachines,
  useOperations,
  useOrganizations,
  useParameters,
  usePlants,
  useProcesses,
  useProducts,
} from "@/hooks/useReferenceData";

export interface ContextSelection {
  organizationId: string;
  plantId: string;
  machineId: string;
  productId: string;
  processId: string;
  operationId: string;
  parameterId: string;
  /** Derived from the selected parameter's configured unit -- read-only,
   * surfaced so the caller can label specification/measurement inputs. */
  unit: string;
}

interface ContextSelectorProps {
  value: ContextSelection;
  onChange: (next: ContextSelection) => void;
}

const EMPTY_SELECTION: ContextSelection = {
  organizationId: "",
  plantId: "",
  machineId: "",
  productId: "",
  processId: "",
  operationId: "",
  parameterId: "",
  unit: "",
};

export { EMPTY_SELECTION };

/** Cascading manufacturing-context picker: Organization drives Plant,
 * Product, and Process; Plant drives Machine; Process drives Operation.
 * Parameter is an independent list. Every option is real reference data
 * fetched from the backend -- nothing here is hardcoded. */
export function ContextSelector({ value, onChange }: ContextSelectorProps) {
  const organizations = useOrganizations();
  const plants = usePlants(value.organizationId || undefined);
  const machines = useMachines(value.plantId || undefined);
  const products = useProducts(value.organizationId || undefined);
  const processes = useProcesses(value.organizationId || undefined);
  const operations = useOperations(value.processId || undefined);
  const parameters = useParameters();

  const selectedParameter = parameters.data?.find((p) => p.parameter_id === value.parameterId);

  useEffect(() => {
    const unit = selectedParameter?.unit ?? "";
    if (unit !== value.unit) onChange({ ...value, unit });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedParameter]);

  function update(patch: Partial<ContextSelection>) {
    onChange({ ...value, ...patch });
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <Field label="Organization" required>
        <select
          className="select"
          value={value.organizationId}
          onChange={(e) => update({ organizationId: e.target.value, plantId: "", machineId: "", productId: "", processId: "", operationId: "" })}
        >
          <option value="">Select organization…</option>
          {organizations.data?.map((org) => (
            <option key={org.organization_id} value={org.organization_id}>
              {org.name}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Plant" required disabled={!value.organizationId}>
        <select
          className="select"
          value={value.plantId}
          disabled={!value.organizationId}
          onChange={(e) => update({ plantId: e.target.value, machineId: "" })}
        >
          <option value="">Select plant…</option>
          {plants.data?.map((plant) => (
            <option key={plant.plant_id} value={plant.plant_id}>
              {plant.name}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Machine" disabled={!value.plantId}>
        <select className="select" value={value.machineId} disabled={!value.plantId} onChange={(e) => update({ machineId: e.target.value })}>
          <option value="">Select machine…</option>
          {machines.data?.map((machine) => (
            <option key={machine.machine_id} value={machine.machine_id}>
              {machine.name} ({machine.code})
            </option>
          ))}
        </select>
      </Field>

      <Field label="Product" disabled={!value.organizationId}>
        <select className="select" value={value.productId} disabled={!value.organizationId} onChange={(e) => update({ productId: e.target.value })}>
          <option value="">Select product…</option>
          {products.data?.map((product) => (
            <option key={product.product_id} value={product.product_id}>
              {product.name} ({product.part_number})
            </option>
          ))}
        </select>
      </Field>

      <Field label="Process" disabled={!value.organizationId}>
        <select
          className="select"
          value={value.processId}
          disabled={!value.organizationId}
          onChange={(e) => update({ processId: e.target.value, operationId: "" })}
        >
          <option value="">Select process…</option>
          {processes.data?.map((process) => (
            <option key={process.process_id} value={process.process_id}>
              {process.name}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Operation" disabled={!value.processId}>
        <select className="select" value={value.operationId} disabled={!value.processId} onChange={(e) => update({ operationId: e.target.value })}>
          <option value="">Select operation…</option>
          {operations.data?.map((operation) => (
            <option key={operation.operation_id} value={operation.operation_id}>
              {operation.name}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Parameter" required>
        <select className="select" value={value.parameterId} onChange={(e) => update({ parameterId: e.target.value })}>
          <option value="">Select parameter…</option>
          {parameters.data?.map((parameter) => (
            <option key={parameter.parameter_id} value={parameter.parameter_id}>
              {parameter.name}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Measurement Unit">
        <input className="select bg-surface-50" value={value.unit} readOnly placeholder="Determined by parameter" />
      </Field>
    </div>
  );
}

function Field({
  label,
  required,
  disabled,
  children,
}: {
  label: string;
  required?: boolean;
  disabled?: boolean;
  children: ReactNode;
}) {
  return (
    <label className={`flex flex-col gap-1.5 text-sm ${disabled ? "opacity-60" : ""}`}>
      <span className="font-medium text-ink-700">
        {label}
        {required && <span className="ml-0.5 text-status-critical">*</span>}
      </span>
      {children}
    </label>
  );
}
