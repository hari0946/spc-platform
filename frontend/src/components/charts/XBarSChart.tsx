import { SPCControlChart } from "./SPCControlChart";
import type { AnalysisChart, RuleViolation, SpecificationLimits } from "@/types";

interface XBarSChartProps {
  chart: AnalysisChart;
  violations: RuleViolation[];
  specification?: SpecificationLimits | null;
  unit: string;
}

/** X-bar S: subgroup means chart + subgroup standard-deviation chart --
 * preferred over X-bar R for larger subgroups (the backend decides when). */
export function XBarSChart({ chart, violations, specification, unit }: XBarSChartProps) {
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
          chartTitle="S Chart (Standard Deviation)"
          valueLabel="Subgroup Std Dev"
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
