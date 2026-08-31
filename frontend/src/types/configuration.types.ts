import type { RuleName, Severity, SubgroupMethod } from "./api.types";

export interface RuleConfig {
  rule_name: RuleName;
  enabled: boolean;
  severity: Severity;
  parameters: Record<string, unknown>;
}

/** chart_type accepts "AUTO" in addition to the three concrete chart types
 * -- letting the backend engine recommend one based on subgroup size. */
export type ConfiguredChartType = "AUTO" | "XBAR_R" | "XBAR_S" | "IMR";

/** Mirrors app/schemas/configuration.py SPCConfigurationResponse. */
export interface SpcConfiguration {
  spc_configuration_id: string;
  parameter_id: string;
  machine_id: string | null;
  product_id: string | null;
  operation_id: string | null;
  chart_type: ConfiguredChartType;
  subgroup_size: number;
  subgroup_method: SubgroupMethod;
  maximum_time_gap_seconds: number;
  minimum_sample_size: number;
  ruleset: RuleConfig[];
  sigma_method: string;
  capability_method: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SpcConfigurationCreateRequest {
  parameter_id: string;
  machine_id?: string;
  product_id?: string;
  operation_id?: string;
  chart_type?: ConfiguredChartType;
  subgroup_size?: number;
  subgroup_method?: SubgroupMethod;
  maximum_time_gap_seconds?: number;
  minimum_sample_size?: number;
  ruleset?: RuleConfig[];
  sigma_method?: string;
  capability_method?: string;
}

export type SpcConfigurationUpdateRequest = Partial<SpcConfigurationCreateRequest> & { is_active?: boolean };
