interface LegendEntry {
  label: string;
  colorClassName: string;
  lineStyle: "solid" | "dashed" | "dotted" | "marker";
}

const LINE_PREVIEW: Record<LegendEntry["lineStyle"], string> = {
  solid: "border-t-2",
  dashed: "border-t-2 border-dashed",
  dotted: "border-t-2 border-dotted",
  marker: "",
};

interface ChartLegendProps {
  entries: LegendEntry[];
}

/** Explicit legend combining color, a line-style swatch, and a text label
 * -- chart meaning is never conveyed by color alone. */
export function ChartLegend({ entries }: ChartLegendProps) {
  return (
    <ul className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs text-ink-700">
      {entries.map((entry) => (
        <li key={entry.label} className="flex items-center gap-1.5">
          {entry.lineStyle === "marker" ? (
            <span className={`h-2.5 w-2.5 rounded-full ${entry.colorClassName}`} aria-hidden="true" />
          ) : (
            <span className={`w-4 ${LINE_PREVIEW[entry.lineStyle]} ${entry.colorClassName}`} aria-hidden="true" />
          )}
          {entry.label}
        </li>
      ))}
    </ul>
  );
}

export type { LegendEntry };
