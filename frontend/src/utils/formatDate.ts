import { format, formatDistanceToNow, isValid, parseISO } from "date-fns";

function toDate(value: string | Date | null | undefined): Date | null {
  if (!value) return null;
  const date = typeof value === "string" ? parseISO(value) : value;
  return isValid(date) ? date : null;
}

export function formatDateTime(value: string | Date | null | undefined): string {
  const date = toDate(value);
  return date ? format(date, "MMM d, yyyy HH:mm") : "—";
}

export function formatDateOnly(value: string | Date | null | undefined): string {
  const date = toDate(value);
  return date ? format(date, "MMM d, yyyy") : "—";
}

export function formatTimeOnly(value: string | Date | null | undefined): string {
  const date = toDate(value);
  return date ? format(date, "HH:mm:ss") : "—";
}

export function formatRelativeTime(value: string | Date | null | undefined): string {
  const date = toDate(value);
  return date ? formatDistanceToNow(date, { addSuffix: true }) : "—";
}
