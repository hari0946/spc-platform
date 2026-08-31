/**
 * Centralized number formatting. Never scatter toFixed(2) through
 * components -- measurement precision genuinely differs by parameter
 * (a diameter in mm wants 3 decimals; a temperature in C wants 1), so every
 * formatter here takes an explicit (or sensibly-defaulted) precision
 * rather than hardcoding one globally.
 */

const DEFAULT_MEASUREMENT_DECIMALS = 4;
const DEFAULT_CAPABILITY_DECIMALS = 2;
const DEFAULT_PERCENT_DECIMALS = 1;

export function formatMeasurement(value: number | null | undefined, unit?: string, decimals = DEFAULT_MEASUREMENT_DECIMALS): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const formatted = value.toFixed(decimals);
  return unit ? `${formatted} ${unit}` : formatted;
}

export function formatCapability(value: number | null | undefined, decimals = DEFAULT_CAPABILITY_DECIMALS): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "N/A";
  return value.toFixed(decimals);
}

export function formatDelta(value: number | null | undefined, decimals = DEFAULT_CAPABILITY_DECIMALS): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "N/A";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(decimals)}`;
}

export function formatPercent(value: number | null | undefined, decimals = DEFAULT_PERCENT_DECIMALS): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "N/A";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(decimals)}%`;
}

export function formatInteger(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toLocaleString();
}

/**
 * Chart axis tick formatter. Rounds to a fixed decimal count *before*
 * converting to a string, which is the key difference from just calling
 * String(value) directly on a Recharts-generated tick -- an unrounded
 * float (e.g. 19.999999999999996, an artifact of the axis library's own
 * min/max/step arithmetic) would otherwise render as a long garbage digit
 * string instead of a clean "20".
 */
export function formatAxisTick(value: number | string, decimals = 4): string {
  const num = typeof value === "string" ? Number(value) : value;
  if (!Number.isFinite(num)) return String(value);
  return Number(num.toFixed(decimals)).toString();
}
