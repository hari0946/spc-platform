import type { ComponentType, ReactNode } from "react";
import { Inbox } from "lucide-react";

interface EmptyStateProps {
  icon?: ComponentType<{ className?: string }>;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

export function EmptyState({ icon: Icon = Inbox, title, description, action, className }: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-surface-300 px-6 py-12 text-center ${className ?? ""}`}>
      <Icon className="h-8 w-8 text-ink-400" aria-hidden="true" />
      <p className="font-medium text-ink-700">{title}</p>
      {description && <p className="max-w-sm text-sm text-ink-500">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}
