import { IMRChart } from "./IMRChart";
import { XBarRChart } from "./XBarRChart";
import { XBarSChart } from "./XBarSChart";
import type { AnalysisChart, RuleViolation, SpecificationLimits } from "@/types";

interface SPCChartRendererProps {
  chart: AnalysisChart;
  violations: RuleViolation[];
  specification?: SpecificationLimits | null;
  unit: string;
}

/** Dispatches to the correct chart-type component based on
 * `chart.type` -- the single place that maps a backend chart_type to a UI
 * component, so pages never need their own switch statement. */
export function SPCChartRenderer({ chart, violations, specification, unit }: SPCChartRendererProps) {
  const props = { chart, violations, specification, unit };
  switch (chart.type) {
    case "IMR":
      return <IMRChart {...props} />;
    case "XBAR_R":
      return <XBarRChart {...props} />;
    case "XBAR_S":
      return <XBarSChart {...props} />;
    default:
      return null;
  }
}
