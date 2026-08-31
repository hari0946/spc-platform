import { Bell } from "lucide-react";
import { Link } from "react-router-dom";

import { useAlerts } from "@/hooks/useAlerts";

export function Header() {
  const { data: openAlerts } = useAlerts({ status: "OPEN" });
  const openCount = openAlerts?.length ?? 0;

  return (
    <header className="flex h-14 shrink-0 items-center justify-between border-b border-surface-200 bg-surface-0 px-5">
      <div />
      <div className="flex items-center gap-4">
        <Link
          to="/analyses"
          className="relative flex items-center justify-center rounded-md p-1.5 text-ink-500 hover:bg-surface-100 hover:text-ink-900"
          aria-label={`${openCount} open alerts`}
        >
          <Bell className="h-4 w-4" aria-hidden="true" />
          {openCount > 0 && (
            <span className="absolute -right-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-status-critical px-1 text-[10px] font-semibold text-white">
              {openCount > 99 ? "99+" : openCount}
            </span>
          )}
        </Link>
        <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-50 text-xs font-semibold text-brand-700">
          QE
        </div>
      </div>
    </header>
  );
}
