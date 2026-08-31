import { useQuery } from "@tanstack/react-query";
import { Navigate, useParams } from "react-router-dom";

import { analysisApi } from "@/api/analysis.api";
import { LoadingState } from "@/components/common/LoadingState";

/**
 * Generic entry point for /analyses/:id -- resolves whether the id
 * belongs to a historical analysis or a monitoring check, then redirects
 * to the concrete page that actually renders it (HistoricalAnalysisPage
 * or MonitoringResultPage). Direct navigation from the History/Dashboard
 * "View" action already knows the type and skips this page entirely; this
 * exists as a resilient fallback for any link that only has a bare id.
 */
export function AnalysisDetailsPage() {
  const { analysisId } = useParams<{ analysisId: string }>();

  const probe = useQuery({
    queryKey: ["analysis-details-probe", analysisId],
    queryFn: () => analysisApi.getById(analysisId!),
    enabled: Boolean(analysisId),
    retry: false,
  });

  if (!analysisId) return <Navigate to="/analyses" replace />;
  if (probe.isLoading) return <LoadingState message="Resolving analysis..." />;
  if (probe.isSuccess) return <Navigate to={`/historical/analysis/${analysisId}`} replace />;
  // Not a historical analysis id -- assume it's a manual check id instead.
  return <Navigate to={`/monitoring/result/${analysisId}`} replace />;
}
