import type { FindingType, Severity } from "./api.types";

/** Mirrors app/schemas/findings.py. `statistical_fact` carries the raw
 * numbers behind the message (e.g. {baseline_cpk, current_cpk, cpk_change})
 * for optional detail display -- never re-derive or reinterpret it. */
export interface Finding {
  finding_id?: string;
  finding_type: FindingType;
  severity: Severity;
  message: string;
  statistical_fact: Record<string, unknown>;
  created_at?: string;
}
