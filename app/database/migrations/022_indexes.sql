-- Additional composite indexes supporting common dashboard/API query
-- patterns that are not already covered by the per-table indexes created
-- alongside each table above.

CREATE INDEX IF NOT EXISTS idx_uploads_context
    ON uploads (organization_id, plant_id, machine_id, product_id, parameter_id);

CREATE INDEX IF NOT EXISTS idx_analysis_runs_context
    ON analysis_runs (machine_id, product_id, operation_id, parameter_id, analysis_type);

CREATE INDEX IF NOT EXISTS idx_baselines_context_status
    ON baselines (machine_id, product_id, operation_id, parameter_id, status);

CREATE INDEX IF NOT EXISTS idx_manual_check_runs_context
    ON manual_check_runs (machine_id, product_id, operation_id, parameter_id, status);

CREATE INDEX IF NOT EXISTS idx_findings_type_severity
    ON findings (finding_type, severity);

CREATE INDEX IF NOT EXISTS idx_alerts_status_severity
    ON alerts (status, severity);
