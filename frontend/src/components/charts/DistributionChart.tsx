import { HistogramChart } from "./HistogramChart";
import type { SpecificationLimits } from "@/types";

interface DistributionChartProps {
  values: number[];
  mean?: number | null;
  specification?: SpecificationLimits | null;
  unit: string;
}

/**
 * Distribution view for the measurement data. The backend does not
 * currently return pre-computed density/KDE data, so this renders the
 * frequency histogram -- deliberately not a fabricated bell curve overlay,
 * since the actual data may not be normally distributed and inventing one
 * would misrepresent the process. If a future backend response includes
 * density estimation, this is the single place to render it.
 */
export function DistributionChart(props: DistributionChartProps) {
  return <HistogramChart {...props} />;
}
