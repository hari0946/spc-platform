import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/** Standard shadcn-style class combiner: merges conditional class lists and
 * resolves conflicting Tailwind utilities (e.g. "p-2 p-4" -> "p-4"). */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
