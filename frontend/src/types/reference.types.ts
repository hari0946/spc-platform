/** Read-only manufacturing context master data -- mirrors app/schemas/reference.py. */

export interface Organization {
  organization_id: string;
  name: string;
  code: string;
  description: string | null;
  active: boolean;
}

export interface Plant {
  plant_id: string;
  organization_id: string;
  name: string;
  code: string;
  timezone: string;
  country: string | null;
  active: boolean;
}

export interface Machine {
  machine_id: string;
  plant_id: string;
  production_line_id: string | null;
  name: string;
  code: string;
  machine_type: string | null;
  manufacturer: string | null;
  model: string | null;
  active: boolean;
}

export interface Product {
  product_id: string;
  organization_id: string;
  part_number: string;
  name: string;
  description: string | null;
  revision: string | null;
  active: boolean;
}

export interface Process {
  process_id: string;
  organization_id: string;
  name: string;
  code: string;
  description: string | null;
  active: boolean;
}

export interface Operation {
  operation_id: string;
  process_id: string;
  name: string;
  code: string;
  sequence_number: number | null;
  description: string | null;
  active: boolean;
}

export interface Parameter {
  parameter_id: string;
  name: string;
  description: string | null;
  data_type: string;
  unit: string;
  target_value: number | null;
  active: boolean;
}

export interface SpecificationRef {
  specification_id: string;
  parameter_id: string;
  machine_id: string | null;
  product_id: string | null;
  operation_id: string | null;
  lsl: number | null;
  usl: number | null;
  target: number | null;
  effective_from: string;
  effective_to: string | null;
  status: string;
}
