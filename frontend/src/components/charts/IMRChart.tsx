import { SPCControlChart } from "./SPCControlChart";
import type { AnalysisChart, RuleViolation, SpecificationLimits } from "@/types";

interface IMRChartProps {
  chart: AnalysisChart;
  violations: RuleViolation[];
  specification?: SpecificationLimits | null;
  unit: string;
}

/** I-MR: two separate, clearly distinct charts -- Individuals and Moving
 * Range -- never merged into one confusing combined view. */
export function IMRChart({ chart, violations, specification, unit }: IMRChartProps) {
  return (
    <div className="flex flex-col gap-4">
      <SPCControlChart
        chartTitle="Individuals Chart"
        valueLabel="Individual Value"
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
          chartTitle="Moving Range Chart"
          valueLabel="Moving Range"
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
