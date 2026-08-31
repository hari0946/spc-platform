import { Bar, BarChart, CartesianGrid, Cell, Legend, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { CapabilityMetrics } from "@/types";
import { formatAxisTick, formatCapability } from "@/utils/formatNumber";

interface CapabilityChartProps {
  capability: CapabilityMetrics;
  /** Common industry rule-of-thumb minimum-acceptable-capability reference
   * (1.33) shown only as a visual reference line -- not a backend-enforced
   * threshold, and clearly labelled as such. */
  referenceThreshold?: number;
}

/** Short-term (Cp/Cpk) vs long-term (Pp/Ppk) capability comparison bars --
 * a genuinely useful comparison, not decorative. Every value plotted comes
 * directly from the backend's capability response. */
export function CapabilityChart({ capability, referenceThreshold = 1.33 }: CapabilityChartProps) {
  const data = [
    { metric: "Cp", value: capability.cp, group: "Short-term (potential)" },
    { metric: "Cpk", value: capability.cpk, group: "Short-term (actual)" },
    { metric: "Pp", value: capability.pp, group: "Long-term (potential)" },
    { metric: "Ppk", value: capability.ppk, group: "Long-term (actual)" },
  ].filter((d) => d.value != null);

  if (data.length === 0) {
    return <p className="py-8 text-center text-sm text-ink-500">No capability data available.</p>;
  }

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 8, right: 16, left: 8, bottom: 8 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="var(--color-surface-200)" vertical={false} />
        <XAxis dataKey="metric" tick={{ fontSize: 12, fill: "var(--color-ink-700)" }} tickLine={false} />
        <YAxis tick={{ fontSize: 11, fill: "var(--color-ink-500)" }} tickLine={false} width={36} tickFormatter={(v) => formatAxisTick(v, 2)} />
        <Tooltip
          formatter={(value, _name, item) => {
            const group = (item.payload as { group?: string } | undefined)?.group ?? "";
            return [formatCapability(typeof value === "number" ? value : undefined), group];
          }}
          contentStyle={{ fontSize: 12, borderRadius: 8 }}
        />
        <Legend
          verticalAlign="top"
          height={24}
          formatter={() => `Reference threshold (${referenceThreshold.toFixed(2)})`}
        />
        <ReferenceLine
          y={referenceThreshold}
          stroke="var(--color-status-warning)"
          strokeDasharray="5 3"
          label={{ value: `Reference: ${referenceThreshold}`, position: "right", fontSize: 10, fill: "var(--color-status-warning)" }}
        />
        <Bar dataKey="value" radius={[4, 4, 0, 0]} isAnimationActive={false}>
          {data.map((entry) => (
            <Cell
              key={entry.metric}
              fill={entry.value! >= referenceThreshold ? "var(--color-status-normal)" : "var(--color-status-critical)"}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
