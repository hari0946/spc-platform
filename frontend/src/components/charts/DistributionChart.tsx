import { HistogramChart } from "./HistogramChart";
import type { SpecificationLimits } from "@/types";

interface DistributionChartProps {
  values: number[];
  mean?: number | null;
  sigma?: number | null;
  specification?: SpecificationLimits | null;
  unit: string;
}

/**
 * Distribution view for the measurement data: a frequency histogram with a
 * fitted normal-distribution reference curve (standard SPC/capability
 * convention -- shows how closely the data resembles the normal shape that
 * Cp/Cpk's underlying math assumes). The curve is the fixed Gaussian PDF
 * formula evaluated at mean/sigma -- both backend-computed values passed
 * in as props -- never a statistic derived here from the raw values.
 */
export function DistributionChart(props: DistributionChartProps) {
  return <HistogramChart {...props} />;
}
