import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { AnalysisMetadata } from "@/components/analysis/AnalysisMetadata";
import { AnalysisSummary } from "@/components/analysis/AnalysisSummary";
import { CapabilityPanel } from "@/components/analysis/CapabilityPanel";
import { ControlLimitPanel } from "@/components/analysis/ControlLimitPanel";
import { StatisticsPanel } from "@/components/analysis/StatisticsPanel";
import { ViolationsTable } from "@/components/analysis/ViolationsTable";
import { DistributionChart } from "@/components/charts/DistributionChart";
import { SPCChartRenderer } from "@/components/charts/SPCChartRenderer";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingState } from "@/components/common/LoadingState";
import { PageHeader } from "@/components/common/PageHeader";
import { useAnalysisDetails } from "@/hooks/useAnalysis";
import { useApproveBaseline, useCreateBaseline } from "@/hooks/useBaseline";

// Historical analysis has no "findings" of its own (findings are only
// generated for Phase 2 baseline comparisons) -- Violations/Distribution
// cover what a historical run actually produces.
const TABS = ["Overview", "Statistics", "Capability", "Control Limits", "Violations", "Distribution"] as const;
type Tab = (typeof TABS)[number];

export function HistoricalAnalysisPage() {
  const { analysisId } = useParams<{ analysisId: string }>();
  const navigate = useNavigate();
  const { data: analysis, isLoading, error, refetch } = useAnalysisDetails(analysisId);
  const [activeTab, setActiveTab] = useState<Tab>("Overview");
  const [baselineMessage, setBaselineMessage] = useState<string | null>(null);

  const createBaseline = useCreateBaseline();
  const approveBaseline = useApproveBaseline();

  if (isLoading) return <LoadingState message="Loading analysis results..." />;
  if (error || !analysis) return <ErrorState error={error} title="Unable to load analysis" onRetry={refetch} />;

  async function handleSaveBaseline() {
    if (!analysis) return;
    setBaselineMessage(null);
    try {
      const draft = await createBaseline.mutateAsync({ analysis_id: analysis.analysis_id });
      setBaselineMessage(`Baseline saved as draft (ID: ${draft.baseline_id.slice(0, 8)}). Review it before approving.`);
    } catch {
      setBaselineMessage("Unable to save baseline draft.");
    }
  }

  async function handleSaveAndApprove() {
    if (!analysis) return;
    setBaselineMessage(null);
    try {
      const draft = await createBaseline.mutateAsync({ analysis_id: analysis.analysis_id });
      const approved = await approveBaseline.mutateAsync({ baselineId: draft.baseline_id, request: {} });
      navigate(`/baselines/${approved.baseline_id}`);
    } catch {
      setBaselineMessage("Unable to save and approve baseline.");
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Historical SPC Analysis"
        actions={
          <div className="flex items-center gap-2">
            <button type="button" onClick={handleSaveBaseline} disabled={createBaseline.isPending} className="btn btn-secondary">
              Save as Draft Baseline
            </button>
            <button type="button" onClick={handleSaveAndApprove} disabled={createBaseline.isPending || approveBaseline.isPending} className="btn btn-primary">
              Save & Approve Baseline
            </button>
          </div>
        }
      />

      {baselineMessage && <p className="rounded-md bg-brand-50 px-3 py-2 text-sm text-brand-700">{baselineMessage}</p>}

      <AnalysisMetadata analysis={analysis} />
      <AnalysisSummary analysis={analysis} />

      <div className="flex gap-1 overflow-x-auto border-b border-surface-200">
        {TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            className={`shrink-0 border-b-2 px-3 py-2 text-sm font-medium ${
              activeTab === tab ? "border-brand-600 text-brand-700" : "border-transparent text-ink-500 hover:text-ink-900"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === "Overview" && (
        <SPCChartRenderer chart={analysis.chart} violations={analysis.stability.violations} specification={analysis.specification} unit={analysis.unit} />
      )}
      {activeTab === "Statistics" && <StatisticsPanel analysis={analysis} />}
      {activeTab === "Capability" && (
        <CapabilityPanel capability={analysis.capability} specification={analysis.specification} unit={analysis.unit} warnings={analysis.warnings} />
      )}
      {activeTab === "Control Limits" && <ControlLimitPanel chart={analysis.chart.primary_chart} specification={analysis.specification} unit={analysis.unit} />}
      {activeTab === "Violations" && <ViolationsTable violations={analysis.stability.violations} />}
      {activeTab === "Distribution" && (
        <DistributionChart
          values={analysis.chart.primary_chart.points.map((p) => p.value)}
          mean={analysis.statistics.mean}
          sigma={analysis.statistics.overall_sigma}
          specification={analysis.specification}
          unit={analysis.unit}
        />
      )}
    </div>
  );
}
