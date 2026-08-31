import { SPCControlChart } from "./SPCControlChart";
import type { AnalysisChart, RuleViolation, SpecificationLimits } from "@/types";

interface XBarRChartProps {
  chart: AnalysisChart;
  violations: RuleViolation[];
  specification?: SpecificationLimits | null;
  unit: string;
}

/** X-bar R: subgroup means chart + subgroup range chart. Subgroup means
 * and ranges are computed entirely by the backend SPC engine -- this
 * component only ever renders what it receives. */
export function XBarRChart({ chart, violations, specification, unit }: XBarRChartProps) {
  return (
    <div className="flex flex-col gap-4">
      <SPCControlChart
        chartTitle="X-bar Chart (Subgroup Means)"
        valueLabel="Subgroup Mean"
        points={chart.primary_chart.points}
        centerLine={chart.primary_chart.center_line}
        ucl={chart.primary_chart.ucl}
        lcl={chart.primary_chart.lcl}
        specification={specification}
        unit={unit}
        violations={violations}
      />
      {chart.secondary_chart && (
        <SPCControlChart
          chartTitle="Range Chart (R)"
          valueLabel="Subgroup Range"
          points={chart.secondary_chart.points}
          centerLine={chart.secondary_chart.center_line}
          ucl={chart.secondary_chart.ucl}
          lcl={chart.secondary_chart.lcl}
          unit={unit}
          violations={[]}
        />
      )}
    </div>
  );
}
