import { AlertCircle, AlertTriangle, BarChart3, CheckCircle2, ShieldCheck } from "lucide-react";
import { useMemo } from "react";

import { MetricCard } from "@/components/dashboard/MetricCard";
import { RecentAnalysis } from "@/components/dashboard/RecentAnalysis";
import { StatusCard } from "@/components/dashboard/StatusCard";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import { PageHeader } from "@/components/common/PageHeader";
import { useAnalysisList } from "@/hooks/useAnalysis";
import { useBaselines } from "@/hooks/useBaseline";
import { useManualCheckList } from "@/hooks/useMonitoring";
import { mergeAndSortRows } from "@/utils/analysisRows";

const STABLE_STATUSES = new Set(["IN_CONTROL", "NORMAL"]);
const WARNING_STATUSES = new Set(["WARNING"]);
const CRITICAL_STATUSES = new Set(["OUT_OF_CONTROL", "CRITICAL"]);

export function DashboardPage() {
  const activeBaselines = useBaselines({ status: "ACTIVE" });
  const historicalAnalyses = useAnalysisList({ analysisType: "HISTORICAL", limit: 100 });
  const monitoringChecks = useManualCheckList({ limit: 100 });

  const isLoading = activeBaselines.isLoading || historicalAnalyses.isLoading || monitoringChecks.isLoading;
  const error = activeBaselines.error ?? historicalAnalyses.error ?? monitoringChecks.error;

  const recentRows = useMemo(
    () => mergeAndSortRows(historicalAnalyses.data ?? [], monitoringChecks.data ?? []).slice(0, 10),
    [historicalAnalyses.data, monitoringChecks.data],
  );

  const allStatuses = useMemo(() => {
    const historicalStatuses = (historicalAnalyses.data ?? []).map((a) => a.stability_status ?? a.status);
    const monitoringStatuses = (monitoringChecks.data ?? []).map((c) => c.final_status ?? c.status);
    return [...historicalStatuses, ...monitoringStatuses];
  }, [historicalAnalyses.data, monitoringChecks.data]);

  const stableCount = allStatuses.filter((s) => STABLE_STATUSES.has(s)).length;
  const warningCount = allStatuses.filter((s) => WARNING_STATUSES.has(s)).length;
  const criticalCount = allStatuses.filter((s) => CRITICAL_STATUSES.has(s)).length;
  const totalAnalyses = (historicalAnalyses.data?.length ?? 0) + (monitoringChecks.data?.length ?? 0);

  if (isLoading) return <LoadingState message="Loading dashboard..." />;
  if (error) return <ErrorState error={error} title="Unable to load dashboard" />;

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="SPC Analytics Dashboard" subtitle="Monitor process stability, variation and capability." />

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <MetricCard label="Active Baselines" value={activeBaselines.data?.length ?? 0} icon={ShieldCheck} accent="brand" />
        <MetricCard label="Total Analyses" value={totalAnalyses} icon={BarChart3} accent="neutral" />
        <MetricCard label="Stable Processes" value={stableCount} icon={CheckCircle2} accent="normal" />
        <MetricCard label="Warning Processes" value={warningCount} icon={AlertTriangle} accent="warning" />
        <MetricCard label="Out of Control" value={criticalCount} icon={AlertCircle} accent="critical" />
      </div>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-ink-900">Recent Analysis</h2>
        <RecentAnalysis rows={recentRows} />
      </section>

      <section>
        <h2 className="mb-3 text-sm font-semibold text-ink-900">Process Status Overview</h2>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
          <StatusCard label="Stable" count={stableCount} icon={CheckCircle2} accent="normal" />
          <StatusCard label="Warning" count={warningCount} icon={AlertTriangle} accent="warning" />
          <StatusCard label="Out of Control" count={criticalCount} icon={AlertCircle} accent="critical" />
        </div>
      </section>
    </div>
  );
}
