import type { ReactNode } from "react";

import { EmptyState } from "./EmptyState";
import { cn } from "@/utils/cn";

export interface DataTableColumn<T> {
  key: string;
  header: string;
  render: (row: T) => ReactNode;
  className?: string;
  headerClassName?: string;
}

interface DataTableProps<T> {
  columns: DataTableColumn<T>[];
  data: T[];
  keyExtractor: (row: T) => string;
  onRowClick?: (row: T) => void;
  emptyTitle?: string;
  emptyDescription?: string;
}

/** Generic table used by every list page (Recent Analysis, Violations,
 * Analysis History, ...). Scrolls horizontally on small screens instead of
 * breaking layout -- see the responsive design requirement. */
export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  onRowClick,
  emptyTitle = "No data found.",
  emptyDescription,
}: DataTableProps<T>) {
  if (data.length === 0) {
    return <EmptyState title={emptyTitle} description={emptyDescription} />;
  }

  return (
    <div className="scroll-thin overflow-x-auto rounded-lg border border-surface-200 bg-surface-0">
      <table className="w-full min-w-max text-left text-sm">
        <thead>
          <tr className="border-b border-surface-200 bg-surface-50">
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                className={cn("whitespace-nowrap px-4 py-2.5 font-medium text-ink-500", column.headerClassName)}
              >
                {column.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row) => (
            <tr
              key={keyExtractor(row)}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              className={cn(
                "border-b border-surface-100 last:border-b-0",
                onRowClick && "cursor-pointer hover:bg-surface-50",
              )}
              tabIndex={onRowClick ? 0 : undefined}
              role={onRowClick ? "button" : undefined}
              onKeyDown={
                onRowClick
                  ? (event) => {
                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        onRowClick(row);
                      }
                    }
                  : undefined
              }
            >
              {columns.map((column) => (
                <td key={column.key} className={cn("whitespace-nowrap px-4 py-2.5 text-ink-900", column.className)}>
                  {column.render(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
