import type { Severity } from "./api.types";

export type AlertStatus = "OPEN" | "ACKNOWLEDGED" | "RESOLVED";

/** Mirrors app/schemas/alerts.py. */
export interface Alert {
  alert_id: string;
  manual_check_id: string | null;
  finding_id: string | null;
  machine_id: string | null;
  parameter_id: string | null;
  severity: Severity;
  status: AlertStatus;
  message: string;
  created_at: string;
  acknowledged_at: string | null;
  acknowledged_by: string | null;
  resolved_at: string | null;
  resolved_by: string | null;
}

export interface AlertAcknowledgeRequest {
  acknowledged_by?: string;
}
