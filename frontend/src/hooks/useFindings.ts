import { useQuery } from "@tanstack/react-query";

import { findingsApi } from "@/api/findings.api";
import type { Severity } from "@/types";

export function useFindings(filters?: { severity?: Severity; findingType?: string; limit?: number }) {
  return useQuery({
    queryKey: ["findings", filters],
    queryFn: () => findingsApi.list(filters),
  });
}
