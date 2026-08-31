import { Route, Routes } from "react-router-dom";

import { AppLayout } from "@/components/layout/AppLayout";
import { DashboardPage } from "@/pages/DashboardPage";
import { AnalysisDetailsPage } from "@/pages/Analyses/AnalysisDetailsPage";
import { AnalysisHistoryPage } from "@/pages/Analyses/AnalysisHistoryPage";
import { BaselineDetailsPage } from "@/pages/Baselines/BaselineDetailsPage";
import { BaselinesPage } from "@/pages/Baselines/BaselinesPage";
import { HistoricalAnalysisPage } from "@/pages/Historical/HistoricalAnalysisPage";
import { HistoricalUploadPage } from "@/pages/Historical/HistoricalUploadPage";
import { MonitoringResultPage } from "@/pages/Monitoring/MonitoringResultPage";
import { MonitoringUploadPage } from "@/pages/Monitoring/MonitoringUploadPage";
import { SettingsPage } from "@/pages/Settings/SettingsPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route path="/" element={<DashboardPage />} />

        <Route path="/historical/upload" element={<HistoricalUploadPage />} />
        <Route path="/historical/analysis/:analysisId" element={<HistoricalAnalysisPage />} />

        <Route path="/monitoring/upload" element={<MonitoringUploadPage />} />
        <Route path="/monitoring/result/:manualCheckId" element={<MonitoringResultPage />} />

        <Route path="/baselines" element={<BaselinesPage />} />
        <Route path="/baselines/:baselineId" element={<BaselineDetailsPage />} />

        <Route path="/analyses" element={<AnalysisHistoryPage />} />
        <Route path="/analyses/:analysisId" element={<AnalysisDetailsPage />} />

        <Route path="/settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}
